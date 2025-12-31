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
    generate_proposal: bool = Field(True, description="Whether to generate proposal document")
    use_two_stage_writer: bool = Field(False, description="Use two-stage DSPy writer for higher quality")

class JobStatusResponse(BaseModel):
    job_id: str
    status: JobStatus
    created_at: datetime
    updated_at: datetime
    progress: Optional[float] = Field(None, description="Progress percentage (0-100)")
    message: Optional[str] = Field(None, description="Status message")

class JobResult(BaseModel):
    job_id: str
    status: JobStatus
    requirements_sas_url: Optional[str] = Field(None, description="SAS URL for downloading requirements matrix (Excel)")
    clean_proposal_sas_url: Optional[str] = Field(None, description="SAS URL for downloading clean proposal (citations removed)")
    cited_proposal_sas_url: Optional[str] = Field(None, description="SAS URL for downloading cited proposal (with citations)")
    zip_sas_url: Optional[str] = Field(None, description="SAS URL for downloading all outputs as a ZIP")
    file_count: Optional[int] = Field(None, description="Number of requirements extracted")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    created_at: datetime
    completed_at: Optional[datetime] = None

class HealthResponse(BaseModel):
    status: str = "healthy"
    timestamp: datetime
    version: str = "1.0.0"

# Models for Previous Jobs endpoint
class JobListItem(BaseModel):
    """Single job in the jobs list."""
    id: str
    job_name: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    requirements_sas_url: Optional[str] = None
    clean_proposal_sas_url: Optional[str] = None
    cited_proposal_sas_url: Optional[str] = None
    zip_sas_url: Optional[str] = None
    file_count: int = 0

class JobListResponse(BaseModel):
    """Paginated list of completed jobs."""
    jobs: List[JobListItem]
    total: int
    page: int
    limit: int
    total_pages: int
