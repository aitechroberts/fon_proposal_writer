# backend/pipeline/__init__.py
"""Pipeline tasks for RFP processing - runs directly without Prefect."""

from .tasks import (
    download_files_task,
    run_dspy_pipeline_task,
    generate_and_upload_task,
    generate_proposal_task,
    zip_outputs_task,
)

__all__ = [
    "download_files_task",
    "run_dspy_pipeline_task", 
    "generate_and_upload_task",
    "generate_proposal_task",
    "zip_outputs_task",
]
