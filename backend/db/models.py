# backend/db/models.py
"""
SQLAlchemy models for FON Advisors Proposal Writer.

The jobs table stores completed jobs only (after successful blob upload).
In-progress jobs are tracked in-memory.
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, String, Integer, DateTime, Text, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    pass


class Job(Base):
    """
    Completed job record.
    
    Only written to database after successful pipeline completion
    and blob upload. In-progress jobs use in-memory storage.
    """
    __tablename__ = "jobs"
    
    # Primary key - uses the same job_id from in-memory tracking
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Job identification
    job_name = Column(String(255), nullable=False, index=True)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Output URLs (Azure Blob SAS URLs)
    requirements_sas_url = Column(Text, nullable=True)
    clean_proposal_sas_url = Column(Text, nullable=True)
    cited_proposal_sas_url = Column(Text, nullable=True)
    zip_sas_url = Column(Text, nullable=True)
    
    # Metadata
    file_count = Column(Integer, default=0)
    
    # Indexes for common queries
    __table_args__ = (
        # Index for sorting by date (newest first)
        Index('idx_jobs_created_at', created_at.desc()),
        # Index for searching by job name
        Index('idx_jobs_job_name', job_name),
    )
    
    def __repr__(self) -> str:
        return f"<Job(id={self.id}, job_name='{self.job_name}', created_at={self.created_at})>"
    
    def to_dict(self) -> dict:
        """Convert to dictionary for API responses."""
        return {
            "id": str(self.id),
            "job_name": self.job_name,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "requirements_sas_url": self.requirements_sas_url,
            "clean_proposal_sas_url": self.clean_proposal_sas_url,
            "cited_proposal_sas_url": self.cited_proposal_sas_url,
            "zip_sas_url": self.zip_sas_url,
            "file_count": self.file_count,
        }


# SQL to create table manually (for reference):
"""
CREATE TABLE jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMP NOT NULL DEFAULT NOW(),
    requirements_sas_url TEXT,
    clean_proposal_sas_url TEXT,
    cited_proposal_sas_url TEXT,
    zip_sas_url TEXT,
    file_count INTEGER DEFAULT 0
);

-- Performance indexes
CREATE INDEX idx_jobs_created_at ON jobs(created_at DESC);
CREATE INDEX idx_jobs_job_name ON jobs(job_name);
"""

