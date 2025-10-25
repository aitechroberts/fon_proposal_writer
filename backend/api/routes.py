# backend/api/routes.py
import uuid
import logging
from datetime import datetime
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, BackgroundTasks
from azure.storage.blob import BlobServiceClient
import prefect
from prefect.deployments import run_deployment

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
        "prefect_flow_run_id": None,
        "progress": 0.0,
        "message": "Job queued for processing"
    }
    
    # Trigger Prefect flow in background
    background_tasks.add_task(trigger_prefect_flow, job_id, job_data)
    
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
    
    # If job is running, check Prefect status
    if job["status"] == JobStatus.RUNNING and job["prefect_flow_run_id"]:
        try:
            # Update status from Prefect
            flow_run = prefect.get_client().read_flow_run(job["prefect_flow_run_id"])
            if flow_run.state.is_completed():
                job["status"] = JobStatus.COMPLETED
                job["progress"] = 100.0
                job["message"] = "Processing completed successfully"
            elif flow_run.state.is_failed():
                job["status"] = JobStatus.FAILED
                job["message"] = f"Processing failed: {flow_run.state.message}"
            else:
                # Estimate progress based on flow run state
                job["progress"] = min(90.0, job["progress"] + 10.0)
                job["message"] = "Processing in progress..."
            
            job["updated_at"] = datetime.utcnow()
        except Exception as e:
            log.warning(f"Failed to check Prefect status for job {job_id}: {e}")
    
    return JobStatusResponse(
        job_id=job_id,
        status=job["status"],
        created_at=job["created_at"],
        updated_at=job["updated_at"],
        progress=job["progress"],
        message=job["message"],
        prefect_flow_run_id=job["prefect_flow_run_id"]
    )

@router.get("/jobs/{job_id}/results", response_model=JobResult)
async def get_job_results(job_id: str):
    """Get the results of a completed job."""
    if job_id not in jobs_db:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs_db[job_id]
    
    if job["status"] == JobStatus.COMPLETED:
        # Retrieve SAS URL from job metadata
        sas_url = job.get("sas_url")
        file_count = job.get("file_count", 0)
        
        return JobResult(
            job_id=job_id,
            status=job["status"],
            sas_url=sas_url,
            file_count=file_count,
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
    return HealthResponse(
        timestamp=datetime.utcnow()
    )

async def trigger_prefect_flow(job_id: str, job_data: JobSubmission):
    """Trigger Prefect flow for job processing."""
    try:
        # Update job status to running
        jobs_db[job_id]["status"] = JobStatus.RUNNING
        jobs_db[job_id]["updated_at"] = datetime.utcnow()
        jobs_db[job_id]["message"] = "Starting Prefect flow..."
        
        # Prepare flow parameters
        flow_params = {
            "job_id": job_id,
            "opportunity_id": job_data.opportunity_id,
            "custom_filename": job_data.custom_filename,
            "use_highergov": job_data.use_highergov,
            "blob_urls": job_data.blob_urls or []
        }
        
        # Run Prefect deployment
        # Note: Replace "extract-compliance-requirements" with your actual deployment name
        flow_run = run_deployment(
            name="extract-compliance-requirements",
            parameters=flow_params,
            timeout=3600  # 1 hour timeout
        )
        
        # Store flow run ID
        jobs_db[job_id]["prefect_flow_run_id"] = str(flow_run.id)
        jobs_db[job_id]["message"] = "Prefect flow started"
        
        log.info(f"Prefect flow {flow_run.id} started for job {job_id}")
        
    except Exception as e:
        log.error(f"Failed to trigger Prefect flow for job {job_id}: {e}")
        jobs_db[job_id]["status"] = JobStatus.FAILED
        jobs_db[job_id]["error_message"] = str(e)
        jobs_db[job_id]["updated_at"] = datetime.utcnow()
