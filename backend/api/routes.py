# backend/api/routes.py
import uuid
import logging
import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks, UploadFile, File, Query, Depends
from azure.storage.blob import BlobServiceClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, asc

from .models import (
    JobSubmission, JobStatusResponse, JobResult, JobStatus, HealthResponse,
    JobListItem, JobListResponse
)
from config import settings

log = logging.getLogger(__name__)
router = APIRouter()

# In-memory job storage for in-progress jobs
# Completed jobs are persisted to PostgreSQL
jobs_db: Dict[str, Dict[str, Any]] = {}


def _save_completed_job_to_db(
    job_id: str,
    job_name: str,
    created_at: datetime,
    completed_at: datetime,
    requirements_sas_url: Optional[str],
    clean_proposal_sas_url: Optional[str],
    cited_proposal_sas_url: Optional[str],
    zip_sas_url: Optional[str],
    file_count: int
) -> None:
    """
    Save a completed job to the PostgreSQL database.
    
    This is called synchronously from the background task after successful completion.
    Creates a fresh async engine/session to avoid event loop conflicts.
    Uses URL.create() for proper handling of passwords with special characters.
    """
    try:
        from urllib.parse import urlparse, parse_qs
        from sqlalchemy import URL
        from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
        from db.models import Job
        from config import settings
        
        raw_url = (settings.database_url or "").strip()
        
        if not raw_url:
            log.warning("Database not configured - skipping job persistence")
            return
        
        # Parse the DATABASE_URL to extract components
        # This handles special characters in passwords properly
        try:
            parsed = urlparse(raw_url)
            
            # Extract query parameters (like sslmode)
            query_params = parse_qs(parsed.query) if parsed.query else {}
            # Flatten single-value lists
            query_dict = {k: v[0] if len(v) == 1 else v for k, v in query_params.items()}
            
            # Ensure sslmode is set for Azure PostgreSQL
            if "sslmode" not in query_dict:
                query_dict["sslmode"] = "require"
            
            # Build the async URL using SQLAlchemy's URL.create()
            # This properly handles password encoding
            db_url = URL.create(
                drivername="postgresql+asyncpg",
                username=parsed.username,
                password=parsed.password,
                host=parsed.hostname,
                port=parsed.port or 5432,
                database=parsed.path.lstrip("/") if parsed.path else "postgres",
                query=query_dict
            )
            
            log.info(f"Database URL parsed successfully: host={parsed.hostname}, db={parsed.path.lstrip('/')}")
            
        except Exception as parse_err:
            log.error(f"Failed to parse DATABASE_URL: {parse_err}")
            return
        
        async def _save():
            # Create a fresh engine for this operation (avoids event loop conflicts)
            engine = create_async_engine(db_url, echo=False)
            async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
            
            try:
                async with async_session() as session:
                    job = Job(
                        id=uuid.UUID(job_id),
                        job_name=job_name,
                        created_at=created_at,
                        completed_at=completed_at,
                        requirements_sas_url=requirements_sas_url,
                        clean_proposal_sas_url=clean_proposal_sas_url,
                        cited_proposal_sas_url=cited_proposal_sas_url,
                        zip_sas_url=zip_sas_url,
                        file_count=file_count,
                    )
                    session.add(job)
                    await session.commit()
                    log.info(f"Saved completed job {job_id} to database")
            finally:
                await engine.dispose()
        
        # Run async operation from sync context with fresh event loop
        asyncio.run(_save())
        
    except Exception as e:
        log.error(f"Failed to save job {job_id} to database: {e}")
        # Don't raise - job completed successfully, just database persistence failed


@router.post("/jobs/submit", response_model=JobStatusResponse)
async def submit_job(job_data: JobSubmission, background_tasks: BackgroundTasks):
    """Submit a new job for processing."""
    job_id = str(uuid.uuid4())
    now = datetime.utcnow()
    
    # Store job metadata in memory (for in-progress tracking)
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
        "clean_proposal_sas_url": None,
        "cited_proposal_sas_url": None,
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
            clean_proposal_sas_url=job.get("clean_proposal_sas_url"),
            cited_proposal_sas_url=job.get("cited_proposal_sas_url"),
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


@router.get("/jobs", response_model=JobListResponse)
async def list_jobs(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search by job name"),
    sort_by: str = Query("created_at", description="Sort field"),
    sort_order: str = Query("desc", description="Sort order (asc or desc)")
):
    """
    List completed jobs from the database with pagination.
    
    Only completed jobs are stored in the database; in-progress jobs
    are tracked in-memory and not returned by this endpoint.
    """
    try:
        from db.database import AsyncSessionLocal
        from db.models import Job
        
        if AsyncSessionLocal is None:
            # Database not configured - return empty list
            return JobListResponse(
                jobs=[],
                total=0,
                page=page,
                limit=limit,
                total_pages=0
            )
        
        async with AsyncSessionLocal() as session:
            # Build base query
            query = select(Job)
            count_query = select(func.count(Job.id))
            
            # Apply search filter (parameterized to prevent SQL injection)
            if search:
                search_pattern = f"%{search}%"
                query = query.where(Job.job_name.ilike(search_pattern))
                count_query = count_query.where(Job.job_name.ilike(search_pattern))
            
            # Get total count
            total_result = await session.execute(count_query)
            total = total_result.scalar() or 0
            
            # Apply sorting
            sort_column = getattr(Job, sort_by, Job.created_at)
            if sort_order.lower() == "asc":
                query = query.order_by(asc(sort_column))
            else:
                query = query.order_by(desc(sort_column))
            
            # Apply pagination
            offset = (page - 1) * limit
            query = query.offset(offset).limit(limit)
            
            # Execute query
            result = await session.execute(query)
            jobs = result.scalars().all()
            
            # Convert to response model
            job_items = [
                JobListItem(
                    id=str(job.id),
                    job_name=job.job_name,
                    created_at=job.created_at,
                    completed_at=job.completed_at,
                    requirements_sas_url=job.requirements_sas_url,
                    clean_proposal_sas_url=job.clean_proposal_sas_url,
                    cited_proposal_sas_url=job.cited_proposal_sas_url,
                    zip_sas_url=job.zip_sas_url,
                    file_count=job.file_count or 0,
                )
                for job in jobs
            ]
            
            total_pages = (total + limit - 1) // limit if total > 0 else 0
            
            return JobListResponse(
                jobs=job_items,
                total=total,
                page=page,
                limit=limit,
                total_pages=total_pages
            )
            
    except Exception as e:
        log.error(f"Failed to list jobs: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve jobs")


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
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
    
    On successful completion, saves the job to PostgreSQL database.
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
        
        # Step 4: Generate proposal documents (if requested) - now generates both cited and clean
        clean_proposal_sas_url = ""
        cited_proposal_sas_url = ""
        clean_proposal_path = None
        cited_proposal_path = None
        
        if job_data.generate_proposal:
            log.info(f"Job {job_id}: Generating proposal documents")
            jobs_db[job_id]["message"] = "Generating proposals..."
            jobs_db[job_id]["progress"] = 70.0
            
            try:
                proposal_result = generate_proposal_task(
                    requirements=requirements,
                    job_id=job_id,
                    opportunity_id=job_data.opportunity_id,
                    custom_filename=job_data.custom_filename,
                    use_two_stage=job_data.use_two_stage_writer
                )
                clean_proposal_sas_url = proposal_result.get("clean_proposal_sas_url", "")
                cited_proposal_sas_url = proposal_result.get("cited_proposal_sas_url", "")
                clean_proposal_path = proposal_result.get("clean_proposal_path")
                cited_proposal_path = proposal_result.get("cited_proposal_path")
                
                jobs_db[job_id]["clean_proposal_sas_url"] = clean_proposal_sas_url
                jobs_db[job_id]["cited_proposal_sas_url"] = cited_proposal_sas_url
            except Exception as e:
                log.error(f"Job {job_id}: Proposal generation failed (non-fatal): {e}")
        
        # Step 5: Create ZIP of all outputs
        log.info(f"Job {job_id}: Creating ZIP archive")
        jobs_db[job_id]["message"] = "Creating download archive..."
        jobs_db[job_id]["progress"] = 90.0
        
        zip_sas_url = zip_outputs_task(
            matrix_paths=matrix_paths,
            clean_proposal_path=clean_proposal_path,
            cited_proposal_path=cited_proposal_path,
            job_id=job_id,
            opportunity_id=job_data.opportunity_id,
            custom_filename=job_data.custom_filename
        )
        jobs_db[job_id]["zip_sas_url"] = zip_sas_url
        
        # Done - mark as completed
        completed_at = datetime.utcnow()
        jobs_db[job_id]["status"] = JobStatus.COMPLETED
        jobs_db[job_id]["message"] = "Processing completed successfully"
        jobs_db[job_id]["completed_at"] = completed_at
        jobs_db[job_id]["progress"] = 100.0
        
        log.info(f"Job {job_id}: Pipeline completed successfully")
        
        # Save completed job to database (write-only on success)
        job_name = job_data.custom_filename or job_data.opportunity_id
        _save_completed_job_to_db(
            job_id=job_id,
            job_name=job_name,
            created_at=jobs_db[job_id]["created_at"],
            completed_at=completed_at,
            requirements_sas_url=requirements_sas_url,
            clean_proposal_sas_url=clean_proposal_sas_url,
            cited_proposal_sas_url=cited_proposal_sas_url,
            zip_sas_url=zip_sas_url,
            file_count=len(requirements)
        )
        
    except Exception as e:
        log.error(f"Job {job_id}: Pipeline failed: {e}")
        jobs_db[job_id]["status"] = JobStatus.FAILED
        jobs_db[job_id]["error_message"] = str(e)
        jobs_db[job_id]["updated_at"] = datetime.utcnow()
