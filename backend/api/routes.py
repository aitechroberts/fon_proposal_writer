# backend/api/routes.py
import uuid
import logging
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException, BackgroundTasks, UploadFile, File
from azure.storage.blob import BlobServiceClient

# #region agent log
def _debug_log(hyp, loc, msg, data=None):
    try:
        p = Path("/root/fon_proposal_writer/.cursor/debug.log")
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "a") as f:
            f.write(json.dumps({"hypothesisId": hyp, "location": loc, "message": msg, "data": data or {}, "timestamp": __import__("time").time()}) + "\n")
    except: pass
_debug_log("H1", "api/routes.py:top", "routes.py module loading")
# #endregion

from .models import JobSubmission, JobStatusResponse, JobResult, JobStatus, HealthResponse
from config import settings

log = logging.getLogger(__name__)
router = APIRouter()

# In-memory job storage (replace with database in production)
jobs_db: Dict[str, Dict[str, Any]] = {}


@router.post("/jobs/submit", response_model=JobStatusResponse)
async def submit_job(job_data: JobSubmission, background_tasks: BackgroundTasks):
    """Submit a new job for processing."""
    job_id = str(uuid.uuid4())
    now = datetime.utcnow()
    
    # Store job metadata
    jobs_db[job_id] = {
        "job_id": job_id,
        "status": JobStatus.QUEUED,
        "created_at": now,
        "updated_at": now,
        "opportunity_id": job_data.opportunity_id,
        "custom_filename": job_data.custom_filename,
        "use_highergov": job_data.use_highergov,
        "blob_urls": job_data.blob_urls or [],
        "generate_proposal": job_data.generate_proposal,
        "use_two_stage_writer": job_data.use_two_stage_writer,
        "requirements_sas_url": None,
        "proposal_sas_url": None,
        "zip_sas_url": None,
        "file_count": 0,
        "progress": 0.0,
        "message": "Job queued for processing"
    }
    
    # Run pipeline directly in background (no Prefect deployment needed)
    background_tasks.add_task(run_pipeline_direct, job_id, job_data)
    
    log.info(f"Job {job_id} submitted for opportunity {job_data.opportunity_id}")
    
    return JobStatusResponse(
        job_id=job_id,
        status=JobStatus.QUEUED,
        created_at=now,
        updated_at=now,
        progress=0.0,
        message="Job queued for processing"
    )


@router.get("/jobs/{job_id}/status", response_model=JobStatusResponse)
async def get_job_status(job_id: str):
    """Get the current status of a job."""
    if job_id not in jobs_db:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs_db[job_id]
    
    return JobStatusResponse(
        job_id=job_id,
        status=job["status"],
        created_at=job["created_at"],
        updated_at=job["updated_at"],
        progress=job["progress"],
        message=job["message"]
    )


@router.get("/jobs/{job_id}/results", response_model=JobResult)
async def get_job_results(job_id: str):
    """Get the results of a completed job."""
    if job_id not in jobs_db:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs_db[job_id]
    
    if job["status"] == JobStatus.COMPLETED:
        return JobResult(
            job_id=job_id,
            status=job["status"],
            requirements_sas_url=job.get("requirements_sas_url"),
            proposal_sas_url=job.get("proposal_sas_url"),
            zip_sas_url=job.get("zip_sas_url"),
            file_count=job.get("file_count", 0),
            created_at=job["created_at"],
            completed_at=job.get("completed_at")
        )
    elif job["status"] == JobStatus.FAILED:
        return JobResult(
            job_id=job_id,
            status=job["status"],
            error_message=job.get("error_message", "Processing failed"),
            created_at=job["created_at"],
            completed_at=job.get("completed_at")
        )
    else:
        raise HTTPException(status_code=202, detail="Job not yet completed")


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    # #region agent log H4
    _debug_log("H4", "api/routes.py:health", "Health endpoint called")
    # #endregion
    return HealthResponse(
        timestamp=datetime.utcnow()
    )


@router.post("/files/upload")
async def upload_files(files: List[UploadFile] = File(...)):
    """Upload files to Azure Blob Storage and return blob URLs."""
    if not settings.azure_storage_connection_string:
        raise HTTPException(status_code=500, detail="Azure Storage not configured")
    
    blob_service = BlobServiceClient.from_connection_string(
        settings.azure_storage_connection_string
    )
    container_name = settings.azure_blob_container
    
    uploaded_urls = []
    for file in files:
        try:
            # Generate unique blob name
            blob_name = f"uploads/{uuid.uuid4()}_{file.filename}"
            blob_client = blob_service.get_blob_client(
                container=container_name,
                blob=blob_name
            )
            
            # Read and upload file content
            content = await file.read()
            blob_client.upload_blob(content, overwrite=True)
            
            # Return the blob URL (backend will use connection string to access)
            blob_url = f"https://{blob_service.account_name}.blob.core.windows.net/{container_name}/{blob_name}"
            uploaded_urls.append(blob_url)
            
            log.info(f"Uploaded {file.filename} to {blob_url}")
        except Exception as e:
            log.error(f"Failed to upload {file.filename}: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to upload {file.filename}: {str(e)}")
    
    return {"blob_urls": uploaded_urls}


def run_pipeline_direct(job_id: str, job_data: JobSubmission):
    """
    Run the DSPy pipeline directly in the backend container.
    No external orchestration needed - just call the pipeline functions.
    """
    from pipeline.tasks import (
        download_files_task,
        run_dspy_pipeline_task,
        generate_and_upload_task,
        generate_proposal_task,
        zip_outputs_task,
    )
    
    try:
        # Update job status to running
        jobs_db[job_id]["status"] = JobStatus.RUNNING
        jobs_db[job_id]["updated_at"] = datetime.utcnow()
        jobs_db[job_id]["message"] = "Starting pipeline..."
        jobs_db[job_id]["progress"] = 5.0
        
        # Step 1: Download files from Azure Blob Storage
        log.info(f"Job {job_id}: Downloading files")
        jobs_db[job_id]["message"] = "Downloading files..."
        jobs_db[job_id]["progress"] = 10.0
        
        downloaded_files = download_files_task(job_data.blob_urls or [], job_id)
        
        if not downloaded_files:
            jobs_db[job_id]["status"] = JobStatus.FAILED
            jobs_db[job_id]["error_message"] = "No files available for processing"
            jobs_db[job_id]["updated_at"] = datetime.utcnow()
            return
        
        # Step 2: Run DSPy processing pipeline
        log.info(f"Job {job_id}: Running DSPy pipeline on {len(downloaded_files)} files")
        jobs_db[job_id]["message"] = "Extracting requirements..."
        jobs_db[job_id]["progress"] = 30.0
        
        requirements = run_dspy_pipeline_task(job_data.opportunity_id, downloaded_files)
        
        if not requirements:
            jobs_db[job_id]["status"] = JobStatus.COMPLETED
            jobs_db[job_id]["message"] = "No requirements found in documents"
            jobs_db[job_id]["file_count"] = 0
            jobs_db[job_id]["completed_at"] = datetime.utcnow()
            jobs_db[job_id]["progress"] = 100.0
            return
        
        jobs_db[job_id]["file_count"] = len(requirements)
        
        # Step 3: Generate requirements matrix and upload
        log.info(f"Job {job_id}: Generating requirements matrix")
        jobs_db[job_id]["message"] = "Generating compliance matrix..."
        jobs_db[job_id]["progress"] = 50.0
        
        matrix_result = generate_and_upload_task(
            requirements,
            job_id,
            job_data.opportunity_id,
            job_data.custom_filename
        )
        requirements_sas_url = matrix_result["requirements_sas_url"]
        matrix_paths = matrix_result["local_paths"]
        
        jobs_db[job_id]["requirements_sas_url"] = requirements_sas_url
        
        # Step 4: Generate proposal document (if requested)
        proposal_sas_url = ""
        proposal_path = None
        if job_data.generate_proposal:
            log.info(f"Job {job_id}: Generating proposal document")
            jobs_db[job_id]["message"] = "Generating proposal..."
            jobs_db[job_id]["progress"] = 70.0
            
            try:
                proposal_result = generate_proposal_task(
                    requirements=requirements,
                    job_id=job_id,
                    opportunity_id=job_data.opportunity_id,
                    custom_filename=job_data.custom_filename,
                    use_two_stage=job_data.use_two_stage_writer
                )
                proposal_sas_url = proposal_result["proposal_sas_url"]
                proposal_path = proposal_result["local_path"]
                jobs_db[job_id]["proposal_sas_url"] = proposal_sas_url
            except Exception as e:
                log.error(f"Job {job_id}: Proposal generation failed (non-fatal): {e}")
        
        # Step 5: Create ZIP of all outputs
        log.info(f"Job {job_id}: Creating ZIP archive")
        jobs_db[job_id]["message"] = "Creating download archive..."
        jobs_db[job_id]["progress"] = 90.0
        
        zip_sas_url = zip_outputs_task(
            matrix_paths=matrix_paths,
            proposal_path=proposal_path,
            job_id=job_id,
            opportunity_id=job_data.opportunity_id,
            custom_filename=job_data.custom_filename
        )
        jobs_db[job_id]["zip_sas_url"] = zip_sas_url
        
        # Done
        jobs_db[job_id]["status"] = JobStatus.COMPLETED
        jobs_db[job_id]["message"] = "Processing completed successfully"
        jobs_db[job_id]["completed_at"] = datetime.utcnow()
        jobs_db[job_id]["progress"] = 100.0
        
        log.info(f"Job {job_id}: Pipeline completed successfully")
        
    except Exception as e:
        log.error(f"Job {job_id}: Pipeline failed: {e}")
        jobs_db[job_id]["status"] = JobStatus.FAILED
        jobs_db[job_id]["error_message"] = str(e)
        jobs_db[job_id]["updated_at"] = datetime.utcnow()
