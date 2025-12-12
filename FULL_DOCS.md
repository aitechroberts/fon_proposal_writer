# RFP Compliance Matrix Generator — Full Documentation

> **Purpose**: Transform government RFP (Request for Proposal) documents into structured compliance matrices using AI-powered extraction with DSPy and Azure OpenAI.

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Architecture](#2-architecture)
3. [Data Model](#3-data-model)
4. [DSPy Pipeline](#4-dspy-pipeline)
5. [Data Orchestration (Prefect)](#5-data-orchestration-prefect)
6. [API Reference](#6-api-reference)
7. [Document Processing](#7-document-processing)
8. [Integrations](#8-integrations)
9. [Configuration Reference](#9-configuration-reference)
10. [UI Guidelines](#10-ui-guidelines)
11. [Deployment](#11-deployment)
12. [Legacy Code](#12-legacy-code)

---

## 1. System Overview

### What It Does

The RFP Compliance Matrix Generator:

1. **Ingests** RFP documents (PDF, Word, Excel) from manual uploads or HigherGov API
2. **Extracts** compliance requirements using DSPy modules backed by Azure OpenAI
3. **Classifies** each requirement into categories (Technical, Submission, Eligibility, etc.)
4. **Grounds** requirements with exact quotes, page numbers, and section references
5. **Exports** a structured Excel compliance matrix for proposal teams

### Key Technologies

| Layer | Technology |
|-------|------------|
| Frontend | Streamlit (Python) |
| Backend API | FastAPI |
| Orchestration | Prefect Cloud (push work pools) |
| AI Framework | DSPy with Azure OpenAI (GPT-4.1) |
| Document Parsing | pypdf, python-docx, openpyxl, Azure Document Intelligence |
| Storage | Azure Blob Storage |
| Observability | Langfuse |
| Package Management | `uv` with `pyproject.toml` |

---

## 2. Architecture

### High-Level Diagram

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Streamlit     │    │   FastAPI       │    │   Prefect       │
│   Frontend      │◄──►│   Backend       │◄──►│   Cloud         │
│   (Port 8501)   │    │   (Port 8000)   │    │   (Push Pool)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                     │                       │
         ▼                     ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   File Upload   │    │   Job Queue     │    │   Azure Blob    │
│   & Results     │    │   (In-Memory)   │    │   Storage       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Project Structure

```
fon_proposal_writer/
├── frontend/                    # Streamlit UI
│   ├── app.py                  # Main UI application
│   ├── Dockerfile
│   ├── pyproject.toml
│   └── static/logo.png         # Company branding
├── backend/                     # FastAPI REST API
│   ├── api/
│   │   ├── main.py             # FastAPI app entry point
│   │   ├── routes.py           # API endpoint handlers
│   │   └── models.py           # Pydantic request/response schemas
│   ├── prefect_flows/
│   │   ├── extraction_flow.py  # Main Prefect flow definition
│   │   └── tasks.py            # Prefect tasks (download, process, upload)
│   ├── Dockerfile
│   └── pyproject.toml
├── shared/                      # Shared configuration
│   └── config.py               # Pydantic Settings (env vars)
├── app/                         # ⚠️ LEGACY — original monolithic app
│   ├── main.py                 # DSPy pipeline entry point
│   └── src/                    # Core extraction modules (still in use)
│       ├── extraction/         # DSPy modules and signatures
│       ├── io/                 # Document loaders
│       ├── matrix/             # Excel export
│       ├── integrations/       # HigherGov API client
│       └── config.py           # App-level settings
├── docker-compose.yml          # Local dev orchestration
├── prefect-automations.yaml    # Prefect event triggers
├── ARCHITECTURE.md             # Architecture summary
├── UI.md                       # UI guidelines
└── FULL_DOCS.md                # This file
```

### Data Flow

1. **Job Submission**
   ```
   User → Streamlit UI → POST /api/v1/jobs/submit → FastAPI → Prefect Cloud
   ```

2. **Processing**
   ```
   Prefect Cloud → Download from Blob → DSPy Pipeline → Generate Excel → Upload to Blob
   ```

3. **Results Retrieval**
   ```
   Frontend polls GET /api/v1/jobs/{id}/status → On completion → GET /api/v1/jobs/{id}/results → SAS URL
   ```

---

## 3. Data Model

### Core Entities

#### JobSubmission (Request)

```python
class JobSubmission(BaseModel):
    opportunity_id: str           # HigherGov ID or user-defined identifier
    custom_filename: str | None   # Output file name (optional)
    use_highergov: bool = False   # Fetch docs from HigherGov API
    blob_urls: list[str] | None   # Pre-uploaded Azure Blob URLs
```

#### JobStatus (Enum)

```python
class JobStatus(str, Enum):
    QUEUED = "queued"       # Job submitted, waiting for worker
    RUNNING = "running"     # Prefect flow executing
    COMPLETED = "completed" # Success, results available
    FAILED = "failed"       # Error occurred
```

#### JobStatusResponse

```python
class JobStatusResponse(BaseModel):
    job_id: str
    status: JobStatus
    created_at: datetime
    updated_at: datetime
    progress: float | None        # 0-100 percentage
    message: str | None           # Human-readable status
    prefect_flow_run_id: str | None
```

#### JobResult

```python
class JobResult(BaseModel):
    job_id: str
    status: JobStatus
    sas_url: str | None           # Azure Blob SAS URL for download
    file_count: int | None        # Number of requirements extracted
    error_message: str | None     # If failed
    created_at: datetime
    completed_at: datetime | None
```

### Requirement Schema

Each extracted requirement contains:

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Auto-generated unique ID |
| `category` | string | Classification category (see below) |
| `modality` | string | Obligation level: SHALL, MUST, SHOULD, MAY, WILL, REQUIRED, PROHIBITED |
| `quote` | string | Exact text from source document |
| `section` | string | Document section reference |
| `page_start` | int | Starting page number |
| `page_end` | int | Ending page number |
| `confidence` | float | Extraction confidence (0.0–1.0) |
| `source` | string | Extraction source ("llm", "rule") |
| `doc_name` | string | Original filename |
| `doc_type` | string | File extension (pdf, docx, xlsx) |

### Requirement Categories

The classifier assigns one of these categories:

- Submission
- Eligibility & Set-Asides
- Contract Type & Terms
- Pricing & Payment
- Evaluation & Award
- Technical Approach & Capability
- Management & Staffing
- Personnel & Qualifications
- Security (Personnel & Facility)
- Privacy & Data Protection
- Compliance & Regulatory
- Flowdowns & Subcontracting
- Performance & Deliverables
- Schedule & Milestones
- Quality Assurance
- Operations & Sustainment
- Supply Chain & Property Management
- Customer Service & Communications
- Training & Workforce Development
- Risk Management & Oversight Authority
- Technology
- Accessibility Sustainability
- General Administrative

---

## 4. DSPy Pipeline

### Overview

The extraction pipeline uses **DSPy** (Declarative Self-Improving Python) to structure LLM interactions with Azure OpenAI. DSPy provides:

- **Signatures**: Typed input/output contracts for LLM calls
- **Modules**: Reusable components wrapping Signatures
- **Predictors**: Execute signatures against the configured LM

### Pipeline Stages

```
┌─────────────┐    ┌──────────────┐    ┌─────────────┐
│  Extractor  │ → │ BatchClassify │ → │ BatchGround │ → Requirements
│  (per chunk)│    │  (batched)    │    │  (batched)  │
└─────────────┘    └──────────────┘    └─────────────┘
```

### Stage 1: Extraction (`Extractor`)

**Purpose**: Extract raw requirements from document chunks.

**DSPy Signature** (`ExtractReqs`):

```python
class ExtractReqs(dspy.Signature):
    """Extract requirements from RFP text chunk.
    
    Output: JSON array of requirement objects with fields:
    - id, category, modality, quote, section, page_start, page_end, confidence
    
    Categories: Technical, AdminFormat, Submission, Eligibility, Other
    Modality: SHALL, MUST, SHOULD, MAY, WILL, REQUIRED, PROHIBITED
    """
    chunk_text: str = InputField()
    requirements_json: str = OutputField(prefix="JSON:")
```

**Module Implementation**:

```python
class Extractor(dspy.Module):
    def __init__(self, retries=2):
        self.pred = dspy.Predict(ExtractReqs)
        self.retries = retries
    
    def forward(self, chunk: dict) -> list[dict]:
        out = self.pred(chunk_text=chunk["text"])
        return json.loads(out.requirements_json)
```

**Behavior**:
- Called once per document chunk (default: 1 page per chunk)
- Returns list of raw requirement dicts
- Retries with explicit JSON instruction on parse failure

### Stage 2: Classification (`BatchClassifier`)

**Purpose**: Normalize categories and modalities for all extracted requirements.

**DSPy Signature** (`BatchClassifyReq`):

```python
class BatchClassifyReq(dspy.Signature):
    """Classify requirements into predefined categories.
    
    Input: JSON array of requirement objects
    Output: JSON array with corrected category/modality fields
    
    Categories: Submission, Eligibility & Set-Asides, Technical Approach, ...
    """
    reqs_json: str = InputField()
    classified_json: str = OutputField()
```

**Batching Strategy**:
- Groups requirements into batches (default: 20 per call)
- Preserves `_idx` field for result alignment
- Merges classified fields back onto original requirements

### Stage 3: Grounding (`BatchGrounder`)

**Purpose**: Validate and enrich requirements with exact evidence from source text.

**DSPy Signature** (`BatchGroundReq`):

```python
class BatchGroundReq(dspy.Signature):
    """Ground requirements with evidence from source chunk.
    
    For each requirement, verify and refine:
    - Exact quote location
    - Page numbers
    - Section references
    """
    chunk_text: str = InputField()
    reqs_json: str = InputField()
    grounded_json: str = OutputField()
```

**Behavior**:
- Processes requirements grouped by source chunk
- Validates quotes exist in chunk text
- Refines page/section metadata

### DSPy Configuration

```python
def _init_dspy_direct():
    # 1. Patch litellm for consistent max_tokens
    litellm.completion = _force_max_tokens_completion  # Always 32000
    
    # 2. Configure Azure OpenAI
    azure_model = f"azure/{settings.azure_openai_deployment}"
    lm = dspy.LM(
        model=azure_model,
        api_key=settings.azure_api_key,
        api_base=f"{settings.azure_api_base}/openai/v1/",
        temperature=0.0,
        max_tokens=32000,
    )
    
    # 3. Set global DSPy config
    dspy.configure(
        lm=lm,
        adapter=dspy.JSONAdapter(),
        track_usage=False,
        cache=False
    )
```

### Environment Knobs

| Variable | Default | Description |
|----------|---------|-------------|
| `MAX_CHUNKS` | 0 | Limit chunks processed (0 = all) |
| `MAX_CHARS` | 12000 | Truncate long chunks |
| `PAGES_PER_CHUNK` | 1 | Pages grouped per extraction call |
| `BATCH_SIZE` | 20 | Requirements per classify/ground batch |
| `LOG_LLM` | false | Dump raw LLM responses to disk |
| `CLEAR_CACHE` | false | Clear DSPy cache on startup |

---

## 5. Data Orchestration (Prefect)

### Flow Definition

**File**: `backend/prefect_flows/extraction_flow.py`

```python
@flow(name="extract-compliance-requirements")
def extraction_flow(
    job_id: str,
    opportunity_id: str,
    custom_filename: str = None,
    use_highergov: bool = False,
    blob_urls: list[str] = None
) -> dict:
    """Main processing flow."""
    
    # Step 1: Download files
    downloaded_files = download_files_task(blob_urls or [], job_id)
    
    # Step 2: Run DSPy pipeline
    requirements = run_dspy_pipeline_task(opportunity_id, downloaded_files)
    
    # Step 3: Generate outputs and upload
    sas_url = generate_and_upload_task(
        requirements, job_id, opportunity_id, custom_filename
    )
    
    return {"job_id": job_id, "sas_url": sas_url, "file_count": len(requirements)}
```

### Tasks

#### `download_files_task`

Downloads files from Azure Blob to local temp directory.

```python
@task(name="download-files-from-blob")
def download_files_task(blob_urls: list[str], job_id: str) -> list[Path]:
    temp_dir = Path(tempfile.mkdtemp(prefix=f"job_{job_id}_"))
    # ... download each blob to temp_dir
    return downloaded_files
```

#### `run_dspy_pipeline_task`

Executes the DSPy extraction pipeline.

```python
@task(name="run-dspy-pipeline")
def run_dspy_pipeline_task(opportunity_id: str, input_files: list[Path]) -> list[dict]:
    from main import run_dspy_pipeline
    return run_dspy_pipeline(opportunity_id, input_files)
```

#### `generate_and_upload_task`

Creates Excel/JSON/CSV outputs and uploads to Azure Blob.

```python
@task(name="generate-and-upload-outputs")
def generate_and_upload_task(requirements, job_id, opportunity_id, custom_filename) -> str:
    # Generate Excel file
    save_excel(requirements, final_xlsx)
    
    # Upload to Azure Blob
    blob_client.upload_blob(...)
    
    # Generate 24-hour SAS URL
    sas_url = generate_blob_sas(...)
    return sas_url
```

### Prefect Automations

**File**: `prefect-automations.yaml`

```yaml
# Trigger on flow completion
name: notify-processing-complete
trigger:
  type: event
  expect: ["prefect.flow-run.Completed"]
  match_related:
    prefect.resource.name: "extract-compliance-requirements"
actions:
  - type: run-deployment
    parameters:
      job_id: "{{ event.resource.parameters.job_id }}"
      sas_url: "{{ event.resource.result.sas_url }}"
      status: "completed"

# Handle failures
name: handle-processing-failure
trigger:
  type: event
  expect: ["prefect.flow-run.Failed"]
actions:
  - type: run-deployment
    parameters:
      job_id: "{{ event.resource.parameters.job_id }}"
      error_message: "{{ event.resource.state.message }}"
      status: "failed"
```

### Work Pool Configuration

- **Type**: Prefect Push Work Pool (serverless)
- **Compute**: Prefect Cloud managed (75 free CPU hours)
- **GPU**: Not currently used (API calls to Azure OpenAI)

---

## 6. API Reference

### Base URL

```
http://localhost:8000/api/v1
```

### Endpoints

#### `POST /jobs/submit`

Submit a new extraction job.

**Request Body**:
```json
{
  "opportunity_id": "RFQ1781397",
  "custom_filename": "my-compliance-matrix",
  "use_highergov": false,
  "blob_urls": ["https://storage.blob.core.windows.net/..."]
}
```

**Response** (202 Accepted):
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "queued",
  "created_at": "2025-12-10T14:30:00Z",
  "updated_at": "2025-12-10T14:30:00Z",
  "progress": 0.0,
  "message": "Job queued for processing"
}
```

#### `GET /jobs/{job_id}/status`

Poll job status.

**Response**:
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "running",
  "created_at": "2025-12-10T14:30:00Z",
  "updated_at": "2025-12-10T14:31:00Z",
  "progress": 45.0,
  "message": "Processing in progress...",
  "prefect_flow_run_id": "abc123"
}
```

#### `GET /jobs/{job_id}/results`

Retrieve completed job results.

**Response** (on success):
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "sas_url": "https://storage.blob.core.windows.net/container/file.xlsx?sas=...",
  "file_count": 127,
  "created_at": "2025-12-10T14:30:00Z",
  "completed_at": "2025-12-10T14:35:00Z"
}
```

#### `GET /health`

Health check endpoint.

**Response**:
```json
{
  "status": "healthy",
  "timestamp": "2025-12-10T14:30:00Z",
  "version": "1.0.0"
}
```

---

## 7. Document Processing

### Supported Formats

| Format | Extension | Loader |
|--------|-----------|--------|
| PDF | `.pdf` | pypdf (standard) or Azure Document Intelligence (forms) |
| Word | `.docx`, `.doc` | python-docx |
| Excel | `.xlsx`, `.xls` | openpyxl |

### Smart Loader Logic

**File**: `app/src/io/smart_loader.py`

```python
def load_document_smart(file_path: str) -> list[tuple[int, str]]:
    """
    1. Try standard extraction (pypdf/docx/xlsx)
    2. Detect if it's a government form
    3. If form → use Azure Document Intelligence
    4. Return list of (page_num, text) tuples
    """
```

### Form Detection

Documents are routed to Azure Document Intelligence if:

1. **Poor extraction**: < 100 characters extracted (likely scanned)
2. **Government form indicators**: Filename or content contains "DD Form", "SF Form", "GS", "OMB"

### Page Chunking

Documents are split into chunks for processing:

```python
def _group_pages_into_chunks(pages, pages_per_chunk=1):
    """
    Combine N pages into a single chunk for extraction.
    Each chunk tracks: text, section, start_page, end_page
    """
```

---

## 8. Integrations

### HigherGov API

**File**: `app/src/integrations/highergov.py`

**Purpose**: Fetch RFP documents directly from HigherGov/SAM.gov.

**Usage**:
```python
from src.integrations.highergov import ingest_highergov_opportunity

# Downloads all files to data/inputs/{opportunity_id}/
files = ingest_highergov_opportunity("RFQ1781397")
```

**Supported Input Formats**:
- HigherGov URL with `?searchID=...`
- SAM.gov solicitation number (e.g., `RFQ1781397`)
- Numeric notice ID

**API Flow**:
1. Resolve opportunity via `/api-external/opportunity/`
2. Fetch document index via `document_path`
3. Download files (URLs expire ~60 minutes)

### Azure Blob Storage

**Purpose**: Store uploaded files and generated outputs.

**Operations**:
- Upload input files for processing
- Store generated Excel/JSON/CSV outputs
- Generate SAS URLs for secure download (24-hour expiry)

### Langfuse (Observability)

**Purpose**: Track LLM calls, costs, and latency.

**Configuration**:
```bash
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_HOST=https://cloud.langfuse.com
```

---

## 9. Configuration Reference

### Environment Variables

#### Azure OpenAI (Required)

```bash
AZURE_API_KEY=your-api-key
AZURE_API_BASE=https://your-resource.openai.azure.com
AZURE_API_VERSION=2024-12-01-preview
AZURE_OPENAI_DEPLOYMENT=gpt-4.1
```

#### Azure Storage (Required)

```bash
AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;AccountName=...
AZURE_BLOB_CONTAINER=proposal-container
```

#### Prefect Cloud (Required for distributed mode)

```bash
PREFECT_API_URL=https://api.prefect.cloud/api/accounts/{account}/{workspace}
PREFECT_API_KEY=pnu_...
```

#### HigherGov (Optional)

```bash
HIGHERGOV_API_KEY=your-highergov-key
```

#### Azure Document Intelligence (Optional)

```bash
DOCUMENTINTELLIGENCE_ENDPOINT=https://your-resource.cognitiveservices.azure.com
DOCUMENTINTELLIGENCE_API_KEY=your-key
```

#### Langfuse (Optional)

```bash
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_HOST=https://cloud.langfuse.com
```

#### Application Settings

```bash
DEBUG=false
LOG_LEVEL=INFO
```

### Settings Class

**File**: `shared/config.py`

```python
class Settings(BaseSettings):
    azure_api_key: str = Field(alias="AZURE_API_KEY")
    azure_api_base: str = Field(alias="AZURE_API_BASE")
    # ... see file for full list
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": False,
        "extra": "ignore"
    }
```

---

## 10. UI Guidelines

See `UI.md` for detailed UI patterns. Summary:

### Branding

- **Primary palette**: Navy `#04395E`, Cyan `#00A3E0`
- **Typography**: Inter font family
- **Logo**: `frontend/static/logo.png` or via env vars

### Components

- **Cards**: Use `st.container(border=True)` with `.card-header`
- **Status indicators**: Color-coded (blue=queued, orange=running, green=completed, red=failed)
- **Progress**: Real-time polling with `st.progress()`

### Layout

- Wide layout with 2:1 column split
- Sidebar for job history
- Gradient header with logo badge

---

## 11. Deployment

### Local Development

```bash
# Start services
docker compose up --build

# Access
# Frontend: http://localhost:8501
# Backend: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### Production (Azure Container Apps)

1. **Build and push images**
2. **Configure environment variables** in Azure
3. **Deploy frontend and backend** as separate containers
4. **Set up Prefect Cloud** deployment and work pool
5. **Configure custom domain** (optional)

### Prefect Cloud Setup

1. Create Prefect Cloud account
2. Create push work pool (`prefect-serverless`)
3. Deploy extraction flow:
   ```bash
   python -m backend.prefect_flows.extraction_flow
   ```
4. Configure automations from `prefect-automations.yaml`

---

## 12. Legacy Code

### ⚠️ `app/` Directory

The `app/` directory contains the **original monolithic Streamlit app** before the decoupled architecture refactor.

**Status**: Preserved but not actively used in the new architecture.

**Files**:
- `app/app.py` — Original Streamlit UI (replaced by `frontend/app.py`)
- `app/main.py` — DSPy pipeline entry point (still imported by Prefect tasks)
- `app/src/` — Core extraction modules (still in active use)

**Migration Notes**:
- The `app/src/` modules are mounted into the backend container
- New code should be added to `frontend/`, `backend/`, or `shared/`
- Do not modify `app/app.py` — it's kept for rollback purposes

---

## Appendix: File Quick Reference

| Path | Purpose |
|------|---------|
| `frontend/app.py` | Streamlit UI |
| `backend/api/main.py` | FastAPI entry point |
| `backend/api/routes.py` | API endpoint handlers |
| `backend/api/models.py` | Pydantic schemas |
| `backend/prefect_flows/extraction_flow.py` | Prefect flow |
| `backend/prefect_flows/tasks.py` | Prefect tasks |
| `shared/config.py` | Shared settings |
| `app/main.py` | DSPy pipeline (core logic) |
| `app/src/extraction/modules.py` | DSPy modules |
| `app/src/extraction/signatures.py` | DSPy signatures |
| `app/src/io/smart_loader.py` | Document loader |
| `app/src/matrix/export_excel.py` | Excel export |
| `app/src/integrations/highergov.py` | HigherGov client |
| `docker-compose.yml` | Local orchestration |
| `prefect-automations.yaml` | Prefect event triggers |

---

*Last updated: December 2025*

