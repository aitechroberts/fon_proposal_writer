# Decoupled Architecture Implementation Summary

## 🏗️ Architecture Overview

The monolithic Streamlit app has been transformed into a simple two-tier architecture:

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

**Key Architecture Decisions:**
- **Direct Processing**: Backend runs DSPy pipeline directly as FastAPI background tasks
- **No External Orchestration**: No Prefect work pools or deployments required
- **Simple Deployment**: Just two Azure Container Apps (frontend + backend)
- **ZIP Output**: All outputs bundled into single downloadable archive

## 📁 Project Structure

```
fon_proposal_writer/
├── frontend/                    # Streamlit UI
│   ├── Dockerfile              # Container configuration
│   ├── app.py                  # UI with API integration
│   └── pyproject.toml          # Python dependencies (uv)
├── backend/                     # FastAPI REST API + Pipeline
│   ├── Dockerfile              # Container configuration
│   ├── api/                    # API layer
│   │   ├── main.py             # FastAPI application
│   │   ├── routes.py           # API endpoints + pipeline runner
│   │   └── models.py           # Pydantic schemas
│   ├── prefect_flows/          # Task functions (called directly)
│   │   ├── extraction_flow.py  # Flow definition (for reference)
│   │   └── tasks.py            # Task implementations
│   ├── config.py               # Backend settings
│   └── pyproject.toml          # Python dependencies (uv)
├── shared/                      # Common configuration
│   └── config.py               # Shared settings
├── docker-compose.yml           # Local testing orchestration
└── app/                         # Core DSPy modules
    ├── main.py                  # DSPy pipeline entry point
    └── src/                     # Extraction, proposal, export modules
        ├── extraction/          # DSPy extraction modules
        ├── proposal/            # DSPy proposal writing modules
        ├── matrix/              # Excel export
        └── io/                  # Document loaders
```

## 🚀 Key Components

### Frontend (Streamlit)
**File**: `frontend/app.py`

**Features**:
- Modern card-based UI with Parker Tide branding
- Real-time job status monitoring with progress bars
- File upload with drag-and-drop
- Job history sidebar
- Download buttons for matrix, proposal, and ZIP archive
- HigherGov integration (optional)

**Key Functions**:
- `submit_job()` - Submit processing job to backend API
- `get_job_status()` - Poll job status with progress updates
- `get_job_results()` - Retrieve SAS URLs for downloads
- `check_backend_health()` - Verify backend connectivity

### Backend (FastAPI)
**File**: `backend/api/routes.py`

**API Endpoints**:
- `POST /api/v1/jobs/submit` - Submit new processing job
- `GET /api/v1/jobs/{job_id}/status` - Get job status with progress
- `GET /api/v1/jobs/{job_id}/results` - Get job results (SAS URLs)
- `GET /api/v1/health` - Health check endpoint

**Pipeline Execution**:
The backend runs the DSPy pipeline directly in `run_pipeline_direct()`:

```python
def run_pipeline_direct(job_id: str, job_data: JobSubmission):
    # 1. Download files from Azure Blob
    downloaded_files = download_files_task.fn(blob_urls, job_id)
    
    # 2. Run DSPy extraction pipeline
    requirements = run_dspy_pipeline_task.fn(opportunity_id, downloaded_files)
    
    # 3. Generate compliance matrix (Excel/CSV/JSON)
    matrix_result = generate_and_upload_task.fn(requirements, job_id, ...)
    
    # 4. Generate proposal document (Word)
    proposal_result = generate_proposal_task.fn(requirements, job_id, ...)
    
    # 5. Create ZIP of all outputs
    zip_sas_url = zip_outputs_task.fn(matrix_paths, proposal_path, job_id, ...)
```

### Task Functions
**File**: `backend/prefect_flows/tasks.py`

**Tasks** (called directly, not via Prefect):
- `download_files_task` - Download files from Azure Blob Storage
- `run_dspy_pipeline_task` - Execute DSPy extraction pipeline
- `generate_and_upload_task` - Create Excel/CSV/JSON, upload to Blob
- `generate_proposal_task` - Create Word proposal document
- `zip_outputs_task` - Bundle all outputs into ZIP archive

## 🔄 Data Flow

### 1. Job Submission
```
User uploads files → Streamlit → POST /api/v1/jobs/submit → FastAPI
```

### 2. Processing (Background Task)
```
FastAPI background task → Download files → DSPy extraction → 
Generate matrix → Generate proposal → Create ZIP → Upload to Blob
```

### 3. Status Polling
```
Frontend polls GET /api/v1/jobs/{id}/status every 2 seconds while running
```

### 4. Results Retrieval
```
GET /api/v1/jobs/{id}/results → Returns SAS URLs for:
  - Compliance matrix (Excel)
  - Proposal document (Word)
  - ZIP archive (all outputs)
```

## 📦 Output Files

Each job produces:
1. **Compliance Matrix** (`{name}.matrix.xlsx`) - Excel with extracted requirements
2. **Requirements JSON** (`{name}.requirements.json`) - Raw JSON data
3. **Requirements CSV** (`{name}.matrix.csv`) - CSV export
4. **Proposal Document** (`{name}.proposal.docx`) - Word document
5. **ZIP Archive** (`{name}.outputs.zip`) - All of the above bundled

## 🔧 Configuration

### Backend Environment Variables

**Required:**
```bash
AZURE_API_KEY=...                      # Azure OpenAI API key
AZURE_API_BASE=...                     # Azure OpenAI endpoint
AZURE_API_VERSION=2024-12-01-preview
AZURE_OPENAI_DEPLOYMENT=gpt-4.1
AZURE_STORAGE_CONNECTION_STRING=...    # Azure Blob Storage
AZURE_BLOB_CONTAINER=proposal-container
```

**Optional:**
```bash
LANGFUSE_PUBLIC_KEY=...                # Observability
LANGFUSE_SECRET_KEY=...
LANGFUSE_HOST=https://cloud.langfuse.com
HIGHERGOV_API_KEY=...                  # HigherGov integration
DOCUMENTINTELLIGENCE_ENDPOINT=...      # Azure Doc Intelligence
DOCUMENTINTELLIGENCE_API_KEY=...
```

### Frontend Environment Variables

**Required:**
```bash
BACKEND_API_URL=https://your-backend.azurecontainerapps.io
```

**Optional:**
```bash
HIGHERGOV_API_KEY=...                  # If using HigherGov feature
STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
```

## 🐳 Docker Compose (Local Dev)

```bash
docker compose up --build

# Frontend: http://localhost:8501
# Backend:  http://localhost:8000
# API Docs: http://localhost:8000/docs
```

## 🚀 Deployment (Azure Container Apps)

### Simple Two-Container Setup

1. **Build & push images** to ACR
2. **Deploy backend ACA** with env vars + secrets
3. **Deploy frontend ACA** pointing to backend URL
4. **Add secrets via Portal** (AZURE_API_KEY, AZURE_STORAGE_CONNECTION_STRING)

No Prefect Cloud, work pools, or external orchestration needed.

### Required Secrets (Backend)
- `AZURE_API_KEY` - Azure OpenAI key
- `AZURE_STORAGE_CONNECTION_STRING` - Blob storage connection

### Required Env Vars (Frontend)
- `BACKEND_API_URL` - Backend ACA URL

## 🎨 UI Features

- **Parker Tide Branding**: Navy/cyan gradient theme
- **Progress Tracking**: Real-time percentage updates
- **Status Indicators**: Color-coded (queued/running/completed/failed)
- **Download Options**: Individual files or ZIP archive
- **Job History**: Sidebar with recent submissions

## 📋 Migration from Prefect Architecture

**Removed:**
- Prefect Cloud dependency
- Work pool configuration
- Deployment commands
- Prefect automations

**Simplified:**
- Backend runs pipeline directly
- No external orchestration
- Faster job startup (no remote dispatch)
- Simpler deployment (just two containers)

**Preserved:**
- All DSPy extraction logic
- Proposal writing pipeline
- Azure Blob Storage integration
- ZIP output bundling
- Real-time progress updates
