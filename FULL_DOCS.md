# RFP Compliance Matrix Generator — Full Documentation

> **Purpose**: Transform government RFP (Request for Proposal) documents into structured compliance matrices and draft proposal documents using AI-powered extraction with DSPy and Azure OpenAI.

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Architecture](#2-architecture)
3. [Data Model](#3-data-model)
4. [DSPy Pipeline](#4-dspy-pipeline)
5. [Proposal Writing Pipeline](#5-proposal-writing-pipeline)
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
5. **Generates** a draft proposal document addressing extracted requirements
6. **Exports** Excel compliance matrix + Word proposal document + ZIP bundle

### Key Technologies

| Layer | Technology |
|-------|------------|
| Frontend | Streamlit (Python) |
| Backend API | FastAPI |
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
│   Streamlit     │    │   FastAPI       │    │   Azure Blob    │
│   Frontend      │◄──►│   Backend       │◄──►│   Storage       │
│   (Port 8501)   │    │   (Port 8000)   │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │
         ▼                       ▼
┌─────────────────┐    ┌─────────────────┐
│   File Upload   │    │  DSPy Pipeline  │
│   & Results     │    │  (Background)   │
└─────────────────┘    └─────────────────┘
```

**Key Design Decisions:**
- **Direct Processing**: Backend runs DSPy pipeline as FastAPI background tasks
- **No External Orchestration**: No Prefect work pools or deployments required
- **Simple Deployment**: Two Azure Container Apps (frontend + backend)
- **ZIP Output**: All outputs bundled into single downloadable archive

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
│   │   ├── routes.py           # API endpoints + pipeline runner
│   │   └── models.py           # Pydantic request/response schemas
│   ├── prefect_flows/
│   │   ├── extraction_flow.py  # Flow definition (reference)
│   │   └── tasks.py            # Task implementations
│   ├── config.py               # Backend settings
│   ├── Dockerfile
│   └── pyproject.toml
├── shared/                      # Shared configuration
│   └── config.py               # Pydantic Settings (env vars)
├── app/                         # Core DSPy modules
│   ├── main.py                 # DSPy pipeline entry point
│   └── src/                    # Core extraction modules
│       ├── extraction/         # DSPy extraction modules
│       ├── proposal/           # DSPy proposal writing modules
│       ├── io/                 # Document loaders
│       ├── matrix/             # Excel export
│       ├── integrations/       # HigherGov API client
│       └── config.py           # App-level settings
├── docker-compose.yml          # Local dev orchestration
├── ARCHITECTURE.md             # Architecture summary
├── EXECUTE_PLAN.md             # Deployment guide
├── PROPOSAL_PIPELINE_PLAN.md   # Proposal pipeline details
└── FULL_DOCS.md                # This file
```

### Data Flow

1. **Job Submission**
   ```
   User → Streamlit UI → POST /api/v1/jobs/submit → FastAPI background task
   ```

2. **Processing (in backend)**
   ```
   Download from Blob → DSPy Extraction → Generate Matrix → Generate Proposal → ZIP → Upload to Blob
   ```

3. **Results Retrieval**
   ```
   Frontend polls GET /api/v1/jobs/{id}/status → On completion → GET /api/v1/jobs/{id}/results → SAS URLs
   ```

---

## 3. Data Model

### Core Entities

#### JobSubmission (Request)

```python
class JobSubmission(BaseModel):
    opportunity_id: str                    # HigherGov ID or user-defined identifier
    custom_filename: str | None = None     # Output file name (optional)
    use_highergov: bool = False            # Fetch docs from HigherGov API
    blob_urls: list[str] | None = None     # Pre-uploaded Azure Blob URLs
    generate_proposal: bool = True         # Generate proposal document
    use_two_stage_writer: bool = False     # Use higher-quality two-stage writer
```

#### JobStatus (Enum)

```python
class JobStatus(str, Enum):
    QUEUED = "queued"       # Job submitted, waiting
    RUNNING = "running"     # Pipeline executing
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
```

#### JobResult

```python
class JobResult(BaseModel):
    job_id: str
    status: JobStatus
    requirements_sas_url: str | None   # Excel matrix download
    proposal_sas_url: str | None       # Word document download
    zip_sas_url: str | None            # All outputs bundled
    file_count: int | None             # Number of requirements extracted
    error_message: str | None          # If failed
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
    """
    chunk_text: str = InputField()
    requirements_json: str = OutputField(prefix="JSON:")
```

**Behavior**:
- Called once per document chunk (default: 1 page per chunk)
- Returns list of raw requirement dicts
- Retries with explicit JSON instruction on parse failure

### Stage 2: Classification (`BatchClassifier`)

**Purpose**: Normalize categories and modalities for all extracted requirements.

**Batching Strategy**:
- Groups requirements into batches (default: 20 per call)
- Preserves `_idx` field for result alignment
- Merges classified fields back onto original requirements

### Stage 3: Grounding (`BatchGrounder`)

**Purpose**: Validate and enrich requirements with exact evidence from source text.

**Behavior**:
- Processes requirements grouped by source chunk
- Validates quotes exist in chunk text
- Refines page/section metadata

### DSPy Configuration

```python
def _init_dspy_direct():
    # Configure Azure OpenAI
    azure_model = f"azure/{settings.azure_openai_deployment}"
    lm = dspy.LM(
        model=azure_model,
        api_key=settings.azure_api_key,
        api_base=f"{settings.azure_api_base}/openai/v1/",
        temperature=0.0,
        max_tokens=32000,
    )
    
    # Set global DSPy config
    dspy.configure(
        lm=lm,
        adapter=dspy.JSONAdapter(),
        track_usage=False,
        cache=False
    )
```

---

## 5. Proposal Writing Pipeline

### Overview

After requirements extraction, the proposal pipeline generates a draft Word document organized into 4 parts with 12 categories.

### Proposal Structure

```python
PROPOSAL_SECTIONS = {
    "Part 1: The Promise (BLUF)": [
        "Technical Approach & Capability",
        "Schedule & Milestones",
    ],
    "Part 2: The Solution (Customer Focus)": [
        "Performance & Deliverables",
        "Operations & Sustainment",
        "Customer Service & Communications",
    ],
    "Part 3: The People (Low Risk)": [
        "Personnel & Qualifications",
        "Training & Workforce Development",
        "Management & Staffing",
    ],
    "Part 4: The Safety Net (Compliance)": [
        "Quality Assurance",
        "Security (Personnel & Facility)",
        "Risk Management & Oversight Authority",
        "Flowdowns & Subcontracting",
    ],
}
```

### Writer Approaches

**Single-Pass (Default)**: Fast, generates each section in one LLM call.

**Two-Stage (Optional)**: Higher quality, slower. First analyzes themes, then drafts content.

### Word Export

Using `python-docx`:
- Title page with document title
- Part headings (Heading 1)
- Section headings (Heading 2)
- Content (Normal, 12pt Times New Roman)
- Page breaks between parts

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
  "blob_urls": ["https://storage.blob.core.windows.net/..."],
  "generate_proposal": true,
  "use_two_stage_writer": false
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
  "message": "Generating proposal..."
}
```

#### `GET /jobs/{job_id}/results`

Retrieve completed job results.

**Response** (on success):
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "requirements_sas_url": "https://storage.blob.core.windows.net/.../matrix.xlsx?sas=...",
  "proposal_sas_url": "https://storage.blob.core.windows.net/.../proposal.docx?sas=...",
  "zip_sas_url": "https://storage.blob.core.windows.net/.../outputs.zip?sas=...",
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

### Azure Blob Storage

**Purpose**: Store uploaded files and generated outputs.

**Operations**:
- Upload input files for processing
- Store generated Excel/JSON/CSV/Word outputs
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
- **Downloads**: Three buttons (ZIP, Matrix, Proposal)

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

1. **Build and push images** to ACR
2. **Deploy backend ACA** with env vars
3. **Add secrets via Portal** (AZURE_API_KEY, AZURE_STORAGE_CONNECTION_STRING)
4. **Deploy frontend ACA** pointing to backend URL
5. **Smoke test** end-to-end

See `EXECUTE_PLAN.md` for detailed commands.

### Required Backend Secrets

- `AZURE_API_KEY` - Azure OpenAI key
- `AZURE_STORAGE_CONNECTION_STRING` - Blob storage connection

### Required Frontend Env Vars

- `BACKEND_API_URL` - Backend ACA URL

---

## 12. Legacy Code

### ⚠️ `app/` Directory

The `app/` directory contains the **original monolithic Streamlit app** plus core DSPy modules that are still in active use.

**Status**: Core modules (`app/src/`) are still used; `app/app.py` is preserved but not active.

**Files**:
- `app/app.py` — Original Streamlit UI (replaced by `frontend/app.py`)
- `app/main.py` — DSPy pipeline entry point (still used by backend)
- `app/src/` — Core extraction and proposal modules (actively used)

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
| `backend/api/routes.py` | API endpoints + pipeline runner |
| `backend/api/models.py` | Pydantic schemas |
| `backend/prefect_flows/tasks.py` | Task implementations |
| `shared/config.py` | Shared settings |
| `app/main.py` | DSPy pipeline (core logic) |
| `app/src/extraction/modules.py` | DSPy extraction modules |
| `app/src/extraction/signatures.py` | DSPy extraction signatures |
| `app/src/proposal/modules.py` | DSPy proposal modules |
| `app/src/proposal/signatures.py` | DSPy proposal signatures |
| `app/src/proposal/export_word.py` | Word document export |
| `app/src/io/smart_loader.py` | Document loader |
| `app/src/matrix/export_excel.py` | Excel export |
| `app/src/integrations/highergov.py` | HigherGov client |
| `docker-compose.yml` | Local orchestration |

---

## Output Files

Each completed job produces:

| File | Description |
|------|-------------|
| `{name}.matrix.xlsx` | Compliance matrix (Excel) |
| `{name}.matrix.csv` | Compliance matrix (CSV) |
| `{name}.requirements.json` | Raw requirements (JSON) |
| `{name}.proposal.docx` | Draft proposal (Word) |
| `{name}.outputs.zip` | All outputs bundled |

---

*Last updated: December 2025*
