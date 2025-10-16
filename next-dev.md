RFP Compliance Extraction - Development Session Summary
Project Overview
Python application that extracts compliance requirements from government RFP PDFs using DSPy 3.x + Azure OpenAI, with Langfuse observability and Azure Blob storage. Built with Streamlit UI for easy submission.
Tech Stack:

DSPy 3.x with Azure OpenAI (gpt-4.1 deployment)
LiteLLM for LLM abstraction
Langfuse v3 for tracing/observability
Azure Blob Storage for artifact delivery
openpyxl for Excel generation
Streamlit for UI


Key Architecture Decisions
1. Batched Processing Pipeline
We batch LLM calls to reduce cost and latency:

Extract: 1 call per grouped chunk (configurable pages per chunk)
Classify: Batch of 25 requirements per call
Ground: Batch of 25 requirements per call per chunk

Why batching? Original approach made 1 LLM call per requirement (600+ calls for a 50-page doc). Batching reduced this to ~30-40 calls.
2. Two-File Output Strategy
tmp_outputs/          # Per-document debug files
├── doc1.requirements.json
├── doc1.matrix.csv
└── doc1.matrix.xlsx

outputs/              # Combined production files (uploaded to blob)
├── {opportunity_id}.requirements.json
├── {opportunity_id}.matrix.csv
└── {opportunity_id}.matrix.xlsx
Both directories deleted after successful blob upload to prevent disk bloat in production.
3. Configuration via pydantic-settings
All env vars loaded through src/config.py using pydantic-settings (NOT python-dotenv). Access vars via settings.azure_api_key, NOT os.getenv().

Critical Fixes Applied
1. Nested Dict Serialization Bug (FIXED)
Problem: LLM responses contained nested dicts like {'evidence': {'page': 11, 'quote': '...'}} which crashed Excel export.
Solution: Added defensive serialization in export_excel.py:
pythonif isinstance(val, (dict, list, set, tuple)):
    val = json.dumps(val, ensure_ascii=False)
2. Duplicate Requirements Bug (FIXED)
Problem: Requirements were being added twice - once as grounded_all, then again as valid_reqs.
Solution: Only extend results with valid_reqs (after validation), not both.
3. LiteLLM Token Limit Override (FIXED)
Problem: LiteLLM was capping max_tokens at 4000 despite GPT-4.1 supporting 32k.
Solution: Monkey-patch litellm.completion() to force max_tokens=32000:
python_original_completion = litellm.completion


@wraps(_original_completion)
def _patched_completion(*args, **kwargs):
    if kwargs.get('max_tokens', 0) < 16000:
        kwargs['max_tokens'] = 32000
    return _original_completion(*args, **kwargs)

litellm.completion = _patched_completion
4. Schema Validation & Normalization (ADDED)
Added validation in run_dspy_pipeline() to skip requirements missing critical fields (label, category, modality, quote). Logs skipped count.
5. Excel Formatting (ENHANCED)

Capitalized column headers (page_start → Page Start)
Excel Table with banded rows (alternating colors)
Filter dropdowns on headers
Frozen header row
Auto-sized columns


Environment Variables (.env)
bash# Azure OpenAI (REQUIRED)
AZURE_API_KEY=your-key
AZURE_API_BASE=https://your-resource.openai.azure.com
AZURE_API_VERSION=2024-12-01-preview
AZURE_OPENAI_DEPLOYMENT=gpt-4.1

# Azure Storage (REQUIRED)
AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;AccountName=...
AZURE_BLOB_CONTAINER=proposal-container

# Langfuse (OPTIONAL but recommended)
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_HOST=https://cloud.langfuse.com

# Pipeline Tuning
BATCH_SIZE=25              # Requirements per batch (classify/ground)
PAGES_PER_CHUNK=1          # Pages to group before extraction
MAX_CHUNKS=0               # 0 = no limit
MAX_CHARS=12000            # Truncate very long chunks

# Debug
LOG_LEVEL=INFO
CLEAR_CACHE=0              # Set to 1 to clear DSPy cache on startup
SKIP_CLEANUP=0             # Set to 1 to preserve tmp_outputs/outputs for debugging
LOG_LLM=0                  # Set to 1 to dump raw LLM responses to raw_llm/
```

---

## File Structure
```
fon_proposal_writer/
├── main.py                    # Pipeline orchestration + Streamlit entry point
├── app.py                     # Streamlit UI (calls main.process_opportunity)
├── logging_config.py          # Centralized logging setup
├── .env                       # Environment variables (NOT committed)
├── data/
│   └── inputs/
│       └── {opportunity_id}/  # Place PDFs here
├── src/
│   ├── config.py              # pydantic-settings config
│   ├── extraction/
│   │   ├── modules.py         # Extractor, BatchClassifier, BatchGrounder
│   │   ├── signatures.py      # DSPy Signatures (ExtractReqs, ClassifyReq, etc.)
│   │   ├── confidence.py      # Confidence scoring
│   │   └── merge_dedupe.py    # Deduplication (not currently used)
│   ├── matrix/
│   │   └── export_excel.py    # openpyxl-based Excel generation
│   ├── io/
│   │   └── loaders.py         # PDF text extraction (pypdf)
│   └── preprocessing/
│       ├── segmenter.py       # Heading-aware chunking
│       └── regex_pass.py      # Fast regex pre-pass (deadlines, eval criteria, etc.)
├── tmp_outputs/               # Per-doc debug files (deleted after upload)
└── outputs/                   # Combined files (deleted after upload)

DSPy Signatures (src/extraction/signatures.py)
ExtractReqs
Input: chunk_text (multi-page text)
Output: requirements_json (JSON array of requirement objects)
BatchClassifyReq
Input: reqs_json (JSON array of requirements)
Output: classified_json (JSON array with category/modality normalized)
BatchGroundReq
Input: chunk_text + reqs_json
Output: grounded_json (JSON array with evidence quotes and page spans)
Critical: All signatures return strict JSON via dspy.JSONAdapter().

Known Issues & Limitations
1. Index Alignment in Batch Processing
LLM sometimes drops or reorders items in batch responses. We mitigate by:

Attaching _idx field to each requirement
Instructing LLM to echo _idx unchanged
Re-aligning results by _idx in _run_once()

Still fragile - if LLM completely ignores instructions, we return originals unchanged (which causes downstream errors).
2. No Semantic Deduplication
Currently using naive dedup in merge_dedupe.py (not enabled). Requirements like:

"The contractor SHALL submit reports monthly"
"Reports MUST be submitted each month"

Are treated as separate requirements. Future: add embedding-based similarity check.
3. Confidence Scoring is Simplistic
In confidence.py, we use heuristics:

Regex hits: 0.65 (if SHALL/MUST) or 0.55
LLM hits: 0.85 (base) → 0.95 (if classified + grounded)

No actual model confidence scores. Future: use logprobs or ensemble voting.
4. No Parallel Processing
Processing is sequential (document by document, chunk by chunk). For large batches (10+ documents), consider:

asyncio concurrent processing
Prefect for job queue (see PREFECT_GUIDE.md in docs)


Performance Characteristics
Test Case: 2 PDFs (26 pages + 57 pages = 83 pages total)
Results:

Total time: ~7 minutes
Requirements extracted: ~858 (502 + 356)
LLM calls: ~60 (20 extract + 20 classify batches + 20 ground batches)
Cost: ~$0.30-0.50 per run (at GPT-4.1 pricing)

Bottlenecks:

Grounding takes longest (~2-8s per batch)
Classification occasionally fails to parse JSON (needs retry)


Debugging Tips
View Raw LLM Responses
bashLOG_LLM=1 streamlit run app.py
# Check raw_llm/ directory for dumps
Keep Output Files for Inspection
bashSKIP_CLEANUP=1 streamlit run app.py
# tmp_outputs/ and outputs/ won't be deleted
Clear DSPy Cache
bashrm -rf .dspy_cache/
# Or set CLEAR_CACHE=1 in .env
Test with Fewer Chunks
bashMAX_CHUNKS=5 BATCH_SIZE=10 streamlit run app.py
```

---

## Azure Blob Upload Details

**Function:** `_upload_blob_and_sas()` in `main.py`

**Process:**
1. Upload `{opportunity_id}.matrix.xlsx` to blob
2. Generate 1-hour read-only SAS URL
3. Return URL to Streamlit for download link
4. Clean up local files

**SAS URL format:**
```
https://{account}.blob.core.windows.net/{container}/{blob}?{sas_token}

Important Code Patterns
1. Batch Processing with Index Preservation
python# Attach indices for alignment
reqs_with_idx = []
for i, r in enumerate(reqs):
    item = dict(r)
    item["_idx"] = i
    reqs_with_idx.append(item)

# LLM call returns result with _idx echoed

# Re-align by index
by_idx = {int(obj["_idx"]): obj for obj in result if "_idx" in obj}
merged = []
for i, orig in enumerate(reqs_with_idx):
    classified = by_idx.get(i, {})
    merged_item = dict(orig)
    merged_item.update(classified)
    merged.append(merged_item)
2. Defensive Excel Serialization
pythonif isinstance(val, (dict, list, set, tuple)):
    val = json.dumps(val, ensure_ascii=False)
3. Config Access Pattern
python# CORRECT
conn_str = settings.azure_storage_connection_string

# WRONG - won't work with pydantic-settings
conn_str = os.getenv("AZURE_STORAGE_CONNECTION_STRING")

Next Steps / Future Enhancements

Parallel Processing: Process multiple documents concurrently
Prompt Optimization: Use DSPy's MIPROv2 with labeled training data
Better Error Recovery: Retry failed batches with smaller batch sizes
Requirement Linking: Identify dependencies between requirements
Section-Aware Extraction: Target specific RFP sections ("Instructions to Offerors", "Evaluation Criteria")
Web UI Improvements: Progress bar, real-time logs, cancel button

Combine Matrices: 


RESOURCE_GROUP="proposal-rg"
LOCATION="eastus"
ACR_NAME="proposalapp"  # Unique name
APP_NAME="proposal-extractor"
ENVIRONMENT_NAME="proposal-env"
IMAGE_NAME="proposal-app"

# Create environment
az containerapp env create \
  --name $ENVIRONMENT_NAME \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION

# Get ACR credentials
ACR_USERNAME=$(az acr credential show --name $ACR_NAME --query username -o tsv)
ACR_PASSWORD=$(az acr credential show --name $ACR_NAME --query passwords[0].value -o tsv)

# Create app
az containerapp create \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --environment $ENVIRONMENT_NAME \
  --image $ACR_SERVER/$IMAGE_NAME:latest \
  --registry-server $ACR_SERVER \
  --registry-username $ACR_USERNAME \
  --registry-password $ACR_PASSWORD \
  --target-port 8501 \
  --ingress external \
  --min-replicas 1 \
  --max-replicas 3 \

source .env

az containerapp secret set \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --secrets \
    azure-api-key="$AZURE_API_KEY" \
    azure-api-base="$AZURE_API_BASE" \
    azure-openai-deployment="$AZURE_OPENAI_DEPLOYMENT" \
    azure-storage-connection="$AZURE_STORAGE_CONNECTION_STRING" \
    azure-storage-key="AZURE_STORAGE_KEY" \
    langfuse-public-key="$LANGFUSE_PUBLIC_KEY" \
    langfuse-secret-key="$LANGFUSE_SECRET_KEY" \
    highergov-api-key="$HIGHERGOV_API_KEY"

az containerapp update \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --set-env-vars \
    AZURE_API_KEY=secretref:azure-api-key \
    AZURE_API_BASE=secretref:azure-api-base \
    AZURE_API_VERSION=2024-12-01-preview \
    AZURE_OPENAI_DEPLOYMENT=secretref:azure-openai-deployment \
    AZURE_STORAGE_CONNECTION_STRING=secretref:azure-storage-connection \
    AZURE_STORAGE_KEY=secretref:azure-storage-key \
    AZURE_BLOB_CONTAINER=proposal-container \
    LANGFUSE_PUBLIC_KEY=secretref:langfuse-public-key \
    LANGFUSE_SECRET_KEY=secretref:langfuse-secret-key \
    LANGFUSE_HOST=https://cloud.langfuse.com \
    HIGHERGOV_API_KEY=secretref:highergov-api-key \
    LOG_LEVEL=INFO