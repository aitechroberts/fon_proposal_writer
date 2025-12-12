# backend/prefect_flows/extraction_flow.py
import logging
from pathlib import Path
from typing import List, Dict, Any
from prefect import flow, get_run_logger
from prefect.deployments import Deployment
from prefect.server.schemas.schedules import CronSchedule

from .tasks import (
    download_files_task,
    run_dspy_pipeline_task,
    generate_and_upload_task,
    generate_proposal_task,
)

@flow(name="extract-compliance-requirements")
def extraction_flow(
    job_id: str,
    opportunity_id: str,
    custom_filename: str = None,
    use_highergov: bool = False,
    blob_urls: List[str] = None,
    generate_proposal: bool = True,
    use_two_stage_writer: bool = False
) -> Dict[str, Any]:
    """
    Main Prefect flow for extracting compliance requirements from RFP documents
    and generating a proposal document.
    
    Args:
        job_id: Unique job identifier
        opportunity_id: Opportunity ID for processing
        custom_filename: Custom output filename (optional)
        use_highergov: Whether to use HigherGov integration
        blob_urls: List of Azure Blob URLs for uploaded files
        generate_proposal: Whether to generate proposal document (default: True)
        use_two_stage_writer: Use two-stage DSPy writer for higher quality (default: False)
    
    Returns:
        Dictionary with job results including both requirements and proposal SAS URLs
    """
    logger = get_run_logger()
    logger.info(f"Starting extraction flow for job {job_id}, opportunity {opportunity_id}")
    
    try:
        # Step 1: Download files from Azure Blob Storage
        logger.info("Step 1: Downloading files from Azure Blob Storage")
        downloaded_files = download_files_task(blob_urls or [], job_id)
        
        if not downloaded_files:
            logger.warning(f"No files downloaded for job {job_id}")
            return {
                "job_id": job_id,
                "status": "failed",
                "error": "No files available for processing",
                "file_count": 0
            }
        
        logger.info(f"Downloaded {len(downloaded_files)} files for processing")
        
        # Step 2: Run DSPy processing pipeline (requirements extraction)
        logger.info("Step 2: Running DSPy requirements extraction pipeline")
        requirements = run_dspy_pipeline_task(opportunity_id, downloaded_files)
        
        if not requirements:
            logger.warning(f"No requirements extracted for job {job_id}")
            return {
                "job_id": job_id,
                "status": "completed",
                "requirements_sas_url": "",
                "proposal_sas_url": "",
                "file_count": 0,
                "message": "No requirements found in documents"
            }
        
        logger.info(f"Extracted {len(requirements)} requirements")
        
        # Step 3: Generate requirements outputs and upload to Azure Blob
        logger.info("Step 3: Generating requirements matrix and uploading to Azure Blob")
        requirements_sas_url = generate_and_upload_task(
            requirements, 
            job_id, 
            opportunity_id, 
            custom_filename
        )
        
        # Step 4: Generate proposal document (chained pipeline)
        proposal_sas_url = ""
        if generate_proposal:
            logger.info("Step 4: Generating proposal document")
            try:
                proposal_sas_url = generate_proposal_task(
                    requirements=requirements,
                    job_id=job_id,
                    opportunity_id=opportunity_id,
                    custom_filename=custom_filename,
                    use_two_stage=use_two_stage_writer
                )
                logger.info(f"Proposal document generated successfully")
            except Exception as e:
                logger.error(f"Proposal generation failed (non-fatal): {e}")
                # Continue - requirements extraction succeeded even if proposal failed
        
        logger.info(f"Flow completed successfully for job {job_id}")
        
        return {
            "job_id": job_id,
            "status": "completed",
            "requirements_sas_url": requirements_sas_url,
            "proposal_sas_url": proposal_sas_url,
            "file_count": len(requirements),
            "message": "Processing completed successfully"
        }
        
    except Exception as e:
        logger.error(f"Flow failed for job {job_id}: {str(e)}")
        return {
            "job_id": job_id,
            "status": "failed",
            "error": str(e),
            "file_count": 0
        }
    
    finally:
        # Cleanup downloaded files
        try:
            for file_path in downloaded_files:
                if file_path.exists():
                    file_path.unlink()
            logger.info("Cleaned up downloaded files")
        except Exception as e:
            logger.warning(f"Failed to cleanup downloaded files: {e}")

# Create deployment configuration
if __name__ == "__main__":
    # Create deployment for Prefect Cloud
    deployment = Deployment.build_from_flow(
        flow=extraction_flow,
        name="extract-compliance-requirements",
        work_pool_name="prefect-serverless",  # Use Prefect's serverless work pool
        parameters={
            "job_id": "default-job-id",
            "opportunity_id": "default-opportunity", 
            "custom_filename": None,
            "use_highergov": False,
            "blob_urls": [],
            "generate_proposal": True,
            "use_two_stage_writer": False
        },
        tags=["rfp-processing", "compliance-matrix", "proposal-writing", "dspy"]
    )
    
    # Apply deployment to Prefect Cloud
    deployment_id = deployment.apply()
    print(f"Deployment created with ID: {deployment_id}")
    print(f"Deployment name: extract-compliance-requirements")
    print("You can now create Prefect Automations to trigger this flow!")
