# README.md - Decoupled Architecture
# RFP Compliance Matrix Generator - Decoupled Frontend/Backend

This is the decoupled version of the RFP Compliance Matrix Generator, featuring:

- **Frontend**: Modern Streamlit UI with enhanced visuals and real-time job monitoring
- **Backend**: FastAPI REST API for job management and Prefect integration
- **Orchestration**: Prefect Cloud for serverless GPU processing
- **Testing**: Docker Compose for local development and testing

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Streamlit     │    │   FastAPI       │    │   Prefect      │
│   Frontend      │◄──►│   Backend       │◄──►│   Cloud        │
│   (Port 8501)   │    │   (Port 8000)   │    │   (Serverless) │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   File Upload   │    │   Job Queue     │    │   Azure Blob    │
│   & Results     │    │   & Status      │    │   Storage       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Quick Start

1. **Setup Environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

2. **Start Services**:
   ```bash
   docker-compose up --build
   ```

3. **Access Applications**:
   - Frontend: http://localhost:8501
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

## Services

### Frontend (Streamlit)
- Modern card-based UI with custom CSS
- Real-time job status monitoring
- File upload with progress indicators
- Job history sidebar
- HigherGov integration

### Backend (FastAPI)
- RESTful API endpoints
- Job lifecycle management
- Prefect Cloud integration
- Azure Blob Storage handling
- Health checks and monitoring

### Prefect Flows
- Serverless GPU processing
- Document extraction pipeline
- Azure Blob integration
- Error handling and retries

## API Endpoints

- `POST /api/v1/jobs/submit` - Submit new processing job
- `GET /api/v1/jobs/{job_id}/status` - Get job status
- `GET /api/v1/jobs/{job_id}/results` - Get job results
- `GET /api/v1/health` - Health check

## Development

### Local Development
```bash
# Backend only
cd backend
pip install -r requirements.txt
uvicorn api.main:app --reload

# Frontend only
cd frontend
pip install -r requirements.txt
streamlit run app.py
```

### Testing
```bash
# Full stack testing
docker-compose up --build

# Test with sample files
curl -X POST http://localhost:8000/api/v1/jobs/submit \
  -H "Content-Type: application/json" \
  -d '{"opportunity_id": "test-123", "use_highergov": false, "blob_urls": []}'
```

## Deployment

### Azure Container Apps
1. Build and push images to Azure Container Registry
2. Deploy frontend to minimal Container App
3. Deploy backend to Container App with Prefect integration
4. Configure environment variables in Azure

### Prefect Cloud Setup
1. Create Prefect Cloud account
2. Set up serverless work pool (75 free GPU hours)
3. Deploy extraction flow to Prefect Cloud
4. Configure webhook endpoints for Azure Event Grid

## Configuration

Key environment variables:
- `PREFECT_API_KEY` - Prefect Cloud API key
- `AZURE_STORAGE_CONNECTION_STRING` - Azure Blob Storage
- `AZURE_API_KEY` - Azure OpenAI API key
- `HIGHERGOV_API_KEY` - HigherGov API key (optional)

## Migration from Monolithic

This decoupled architecture preserves all existing functionality:
- ✅ HigherGov integration
- ✅ Azure Blob Storage
- ✅ DSPy processing pipeline
- ✅ Excel/JSON/CSV outputs
- ✅ Langfuse observability

New capabilities:
- ✅ Asynchronous processing
- ✅ Real-time job monitoring
- ✅ Serverless GPU scaling
- ✅ Modern UI/UX
- ✅ API-first architecture
