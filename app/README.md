# RFP Compliance Matrix Extraction (POC)

End-to-end, observable proof-of-concept that turns government RFPs into a compliance matrix with citations. It combines a regex pre-pass for cheap high-precision wins with a three-stage DSPy 3 pipeline (Extract → Classify → Ground), and ships artifacts (JSON/CSV/Excel) to Azure Blob. All runs are traced in Langfuse v3 with lightweight experiment stats.

**Tech:** DSPy 3.x, Langfuse v3 (OTel-native), Azure OpenAI (v1 Responses compatible), pypdf 6, Azure Blob, optional Azure Document Intelligence fallback for table-heavy PDFs.

## Why this exists

- **RFPs are long.** You need a fast way to pull requirements (MUST/SHALL/SHOULD, fonts, page limits, forms, deadlines, eval weights, certifications).
- **LLMs are expensive.** We do a regex pre-pass first, then target LLM calls by chunk/section.
- **You need traceability.** Every stage and artifact is observable via Langfuse v3, with run-level scores.

## What it does

1. **Load** PDFs/DOCX → text (pypdf 6 for PDFs).
2. **Segment** with heading-aware chunks (preserve section context).
3. **Regex pre-pass:** obvious requirements + admin rules (fonts/page limits/forms) and extra patterns (deadlines, eval criteria, certifications).
4. **DSPy 3 pipeline:**
   - **Extract** candidate requirements → strict JSON (via JSONAdapter).
   - **Classify** category & modality.
   - **Ground** evidence quote and page span.
5. **Merge & dedupe** (naive; semantic dedupe is an optional extension).
6. **Confidence scoring** (regex vs LLM, stage agreement boosts).
7. **Export** JSON + CSV + Excel; upload to Azure Blob.
8. **Observe:** traces, inputs/outputs, token/cost in Langfuse v3; simple run stats as scores.

## Repository layout

```
rfp-compliance-poc/
├─ README.md
├─ requirements.txt
├─ config.yaml                 # prompt variants (aggressive / conservative)
├─ .env.example
├─ data/
│  ├─ inputs/                  # drop PDFs/DOCX here
│  └─ gold/ (train|val)        # a few hand labels for optimizer/eval
├─ docs/
│  ├─ Schema.md
│  └─ Playbook.md
├─ src/
│  ├─ config.py                # env & settings (pydantic-settings)
│  ├─ observability/
│  │  ├─ tracing.py            # Langfuse v3 + DSPy OpenInference hook
│  │  └─ metrics.py            # lightweight run stats → Langfuse scores
│  ├─ experiments/
│  │  └─ config_variants.py    # load/apply YAML prompt variants
│  ├─ io/
│  │  ├─ loaders.py            # pypdf/docx → text (+ page/section map)
│  │  ├─ storage.py            # Azure Blob upload helpers
│  │  └─ ai_docint.py          # (optional) Document Intelligence fallback
│  ├─ preprocessing/
│  │  ├─ segmenter.py          # heading-aware chunking with overlap
│  │  └─ regex_pass.py         # SHALL/MUST + deadlines/eval/cert patterns
│  ├─ extraction/
│  │  ├─ signatures.py         # DSPy Signatures: Extract / Classify / Ground
│  │  ├─ modules.py            # DSPy Modules per stage
│  │  ├─ merge_dedupe.py
│  │  └─ confidence.py
│  ├─ matrix/
│  │  ├─ export.py             # JSON & CSV
│  │  └─ export_excel.py       # Excel for stakeholders
│  ├─ optimize/
│  │  └─ mipro_runner.py       # DSPy MIPROv2/COPRO on small gold set
│  ├─ evaluation/
│  │  └─ metrics_eval.py
│  └─ pipeline/
│     └─ run_experiment.py     # CLI harness: load→segment→regex→LLM→merge→export→stats
└─ scripts/
   ├─ bootstrap_env.sh
   └─ sample_run.sh
```

## Prereqs

- Python 3.10+
- Accounts/keys: Azure OpenAI, Azure Blob, Langfuse.
- (Optional) Azure AI Document Intelligence if you process table-heavy PDFs (prebuilt layout model).

## Install

```bash
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

**Key packages (why):**
- **DSPy 3** (LM programming; supports providers like `openai/*` and `azure/<deployment>`).
- **Langfuse v3** (OTel-native tracing + scores; `@observe` decorator).
- **openinference-instrumentation-dspy** (auto-trace DSPy to OTel).
- **pypdf 6** (text extraction).
- **azure-storage-blob** (upload artifacts).
- **azure-ai-documentintelligence** (optional fallback).

## Configure

Copy `.env.example` → `.env` and fill in values:

```bash
# Azure OpenAI (v1 / Responses compatible)
AZURE_API_KEY=...
AZURE_API_BASE=https://<your-resource>.openai.azure.com
AZURE_API_VERSION=2025-05-01-preview
AZURE_OPENAI_DEPLOYMENT=gpt-4o-mini     # your *deployment name* in Azure

# Langfuse v3
LANGFUSE_PUBLIC_KEY=...
LANGFUSE_SECRET_KEY=...
LANGFUSE_HOST=https://cloud.langfuse.com

# Azure Blob Storage
AZURE_STORAGE_CONNECTION_STRING=...
AZURE_BLOB_CONTAINER=rfp-poc

# (Optional) Azure AI Document Intelligence
DOCUMENTINTELLIGENCE_ENDPOINT=...
DOCUMENTINTELLIGENCE_API_KEY=...
```

**Why these URLs & versions?** Azure's Responses API uses the base URL pattern `https://<resource>.openai.azure.com/openai/v1/` and current preview API versions; the SDK and docs note Responses as the primary API path. If you use chat-completions instead, that still works—just keep your deployment/model consistent.

Set prompt variants in `config.yaml` (hot-swappable):

```yaml
prompt_variants:
  aggressive:
    temperature: 0.1
    extract_hidden_requirements: true
  conservative:
    temperature: 0.0
    strict_keyword_matching: true
default_variant: conservative
```

## Quickstart

1. Put a few PDFs in `data/inputs/`.
2. Run the experiment harness:

```bash
python -m src.pipeline.run_experiment --inputs data/inputs --exp baseline
```

**You'll get:**
- `*.requirements.json` — normalized requirement objects (IDs, modality/category, quote, page span, confidence).
- `*.matrix.csv` and `*.matrix.xlsx` — stakeholder-friendly compliance matrix.
- Artifacts uploaded to Azure Blob (container from `.env`).
- A full trace in Langfuse with inputs/outputs/tokens/cost per stage and run-level scores.

## How the pipeline works

### Data flow (high level)

```
PDF/DOCX → text            → chunks (heading-aware)
                      ↘
               Regex pre-pass  → requirement hits (deadlines / eval / certs / fonts / page limits / forms)
                      ↘
           DSPy Extract → Classify → Ground  → merged & deduped → confidence
                                                          ↘
                                               CSV / JSON / Excel → Azure Blob + Langfuse scores
```

- **Regex pre-pass:** finds obvious SHALL/MUST/etc., deadlines, evaluation criteria, certifications quickly.
- **DSPy 3:** a small program of three Predict stages with JSONAdapter to keep outputs strict JSON (easier to parse & validate).
- **Observability:**
  - Use `@observe` on the run function to create a trace.
  - DSPy calls are auto-instrumented via OpenInference for DSPy (emits OTel spans → Langfuse).
  - Record scores (e.g., average confidence) on the trace to compare experiments.

## Working with Azure services

- **Blob uploads:** use `BlobServiceClient` and `upload_blob(..., overwrite=True)` to push artifacts (simple & reliable).
- **Document Intelligence (optional):** for complex, layout-heavy PDFs, call the prebuilt layout model via `DocumentIntelligenceClient.begin_analyze_document("prebuilt-layout", ...)` to extract tables/paragraph roles and feed them back to the LLM as structured hints.

## Tuning & experiments

- **Flip prompt variants** in `config.yaml` (aggressive vs conservative) without code changes.
- **Create 20–50 labeled snippets** in `data/gold/train|val/` and run the DSPy MIPROv2/COPRO optimizer to improve extraction/classification prompts and few-shots. (DSPy 3 exposes provider-style LMs like `openai/*` and `azure/<deployment>`; configure via env vars).
- **Track run-level metrics** (counts by modality/category, avg confidence) as Langfuse scores for quick A/B comparisons.

## Limits & extensions

- **Context windows:** keep chunk sizes modest and target the likely sections ("Instructions to Offerors," "Evaluation") first to avoid overruns.
- **Semantic dedupe:** optionally embed (label + quote) and drop near-duplicates by cosine similarity; add later if needed.
- **Retrieval:** add Azure AI Search (vector+keyword hybrid) only when you need cross-RFP search/analytics.
- **Throughput:** if you later host a model behind an OpenAI-compatible endpoint (e.g., vLLM), keep DSPy's program as-is and point to the new `api_base`.

## Troubleshooting

- **Azure OpenAI 404 / 400:** confirm you're using the Responses base path (`/openai/v1/`), set a valid API version, and your deployment name matches the model you call.
- **No text from PDF:** some PDFs are scanned/complex—use Document Intelligence layout to extract tables/paragraph roles, or try OCR upstream.
- **Missing traces:** ensure `LANGFUSE_*` envs are set and the process isn't exiting before the exporter flushes; use `langfuse.get_client().flush()` at the end of short runs.

## Security & data handling

- Store secrets only in `.env` (never commit).
- Artifacts (JSON/CSV/XLSX) can contain excerpts of RFPs; limit container access and apply storage lifecycle as needed.
- Use Azure role-based access control (RBAC) for Blob; prefer private containers.

## License & acknowledgments

- Built on DSPy (Stanford NLP, open-source) and Langfuse (OTel-native SDK).
- Uses pypdf for PDF parsing and Azure SDKs for storage & document analysis.

## Appendix: key references

- **DSPy:** Language Models quickstart; JSONAdapter docs.
- **Langfuse v3:** `@observe` decorator & OTel-native SDK.
- **Azure OpenAI:** Responses API (v1) usage & base URL.
- **Azure Blob:** Python upload quickstart & examples.
- **pypdf 6:** text extraction.
- **Document Intelligence:** prebuilt layout model overview & SDK.

If you need this README exported with your org-specific env names and guardrails, tell me your naming and I'll tailor it.