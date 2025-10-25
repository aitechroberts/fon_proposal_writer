# backend/prefect_flows/extraction_flow.py
import logging
from pathlib import Path
from typing import List, Dict, Any
from prefect import flow, get_run_logger
from prefect.deployments import Deployment
from prefect.server.schemas.schedules import CronSchedule

from .tasks import download_files_task, run_dspy_pipeline_task, generate_and_upload_task

@flow(name="extract-compliance-requirements")
def extraction_flow(
    job_id: str,
    opportunity_id: str,
    custom_filename: str = None,
    use_highergov: bool = False,
    blob_urls: List[str] = None
) -> Dict[str, Any]:
    """
    Main Prefect flow for extracting compliance requirements from RFP documents.
    
    Args:
        job_id: Unique job identifier
        opportunity_id: Opportunity ID for processing
        custom_filename: Custom output filename (optional)
        use_highergov: Whether to use HigherGov integration
        blob_urls: List of Azure Blob URLs for uploaded files
    
    Returns:
        Dictionary with job results including SAS URL and file count
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
        
        # Step 2: Run DSPy processing pipeline
        logger.info("Step 2: Running DSPy processing pipeline")
        requirements = run_dspy_pipeline_task(opportunity_id, downloaded_files)
        
        if not requirements:
            logger.warning(f"No requirements extracted for job {job_id}")
            return {
                "job_id": job_id,
                "status": "completed",
                "sas_url": "",
                "file_count": 0,
                "message": "No requirements found in documents"
            }
        
        logger.info(f"Extracted {len(requirements)} requirements")
        
        # Step 3: Generate outputs and upload to Azure Blob
        logger.info("Step 3: Generating outputs and uploading to Azure Blob")
        sas_url = generate_and_upload_task(
            requirements, 
            job_id, 
            opportunity_id, 
            custom_filename
        )
        
        logger.info(f"Flow completed successfully for job {job_id}")
        
        return {
            "job_id": job_id,
            "status": "completed",
            "sas_url": sas_url,
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
            "blob_urls": []
        },
        tags=["rfp-processing", "compliance-matrix", "dspy"]
    )
    
    # Apply deployment to Prefect Cloud
    deployment_id = deployment.apply()
    print(f"Deployment created with ID: {deployment_id}")
    print(f"Deployment name: extract-compliance-requirements")
    print("You can now create Prefect Automations to trigger this flow!")
