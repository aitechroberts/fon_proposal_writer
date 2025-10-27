# backend/api/models.py
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class JobStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class JobSubmission(BaseModel):
    opportunity_id: str = Field(..., description="Opportunity ID for processing")
    custom_filename: Optional[str] = Field(None, description="Custom output filename")
    use_highergov: bool = Field(False, description="Whether to use HigherGov integration")
    blob_urls: Optional[List[str]] = Field(None, description="Azure Blob URLs for uploaded files")

class JobStatusResponse(BaseModel):
    job_id: str
    status: JobStatus
    created_at: datetime
    updated_at: datetime
    progress: Optional[float] = Field(None, description="Progress percentage (0-100)")
    message: Optional[str] = Field(None, description="Status message")
    prefect_flow_run_id: Optional[str] = Field(None, description="Prefect flow run ID")

class JobResult(BaseModel):
    job_id: str
    status: JobStatus
    sas_url: Optional[str] = Field(None, description="SAS URL for downloading results")
    file_count: Optional[int] = Field(None, description="Number of requirements extracted")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    created_at: datetime
    completed_at: Optional[datetime] = None

class HealthResponse(BaseModel):
    status: str = "healthy"
    timestamp: datetime
    version: str = "1.0.0"
