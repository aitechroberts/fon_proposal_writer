# backend/prefect_flows/tasks.py
import os
import tempfile
import logging
from pathlib import Path
from typing import List, Dict, Any
from azure.storage.blob import BlobServiceClient
from datetime import datetime, timedelta
from azure.storage.blob import generate_blob_sas, BlobSasPermissions

from prefect import task
from config import settings

log = logging.getLogger(__name__)

@task(name="download-files-from-blob")
def download_files_task(blob_urls: List[str], job_id: str) -> List[Path]:
    """Download files from Azure Blob Storage to local temp directory."""
    if not blob_urls:
        log.warning(f"No blob URLs provided for job {job_id}")
        return []
    
    # Create temp directory for this job
    temp_dir = Path(tempfile.mkdtemp(prefix=f"job_{job_id}_"))
    downloaded_files = []
    
    blob_service = BlobServiceClient.from_connection_string(
        settings.azure_storage_connection_string
    )
    
    for i, blob_url in enumerate(blob_urls):
        try:
            # Extract blob name from URL
            blob_name = blob_url.split('/')[-1].split('?')[0]
            local_path = temp_dir / blob_name
            
            # Download blob
            blob_client = blob_service.get_blob_client(
                container=settings.azure_blob_container,
                blob=blob_name
            )
            
            with open(local_path, "wb") as f:
                download_stream = blob_client.download_blob()
                f.write(download_stream.readall())
            
            downloaded_files.append(local_path)
            log.info(f"Downloaded {blob_name} for job {job_id}")
            
        except Exception as e:
            log.error(f"Failed to download {blob_url} for job {job_id}: {e}")
            continue
    
    log.info(f"Downloaded {len(downloaded_files)} files for job {job_id}")
    return downloaded_files

@task(name="run-dspy-pipeline")
def run_dspy_pipeline_task(opportunity_id: str, input_files: List[Path]) -> List[Dict[str, Any]]:
    """Run the DSPy processing pipeline on input files."""
    if not input_files:
        log.warning(f"No input files provided for opportunity {opportunity_id}")
        return []
    
    # Import the existing pipeline logic
    import sys
    sys.path.append("/app/src")
    
    from main import run_dspy_pipeline
    
    log.info(f"Starting DSPy pipeline for {len(input_files)} files")
    
    try:
        # Run the existing pipeline
        results = run_dspy_pipeline(opportunity_id, input_files)
        log.info(f"DSPy pipeline completed: {len(results)} requirements extracted")
        return results
    except Exception as e:
        log.error(f"DSPy pipeline failed: {e}")
        raise

@task(name="generate-and-upload-outputs")
def generate_and_upload_task(
    requirements: List[Dict[str, Any]], 
    job_id: str, 
    opportunity_id: str,
    custom_filename: str = None
) -> str:
    """Generate Excel/JSON/CSV outputs and upload to Azure Blob."""
    if not requirements:
        log.warning(f"No requirements to process for job {job_id}")
        return ""
    
    # Import existing export functions
    import sys
    sys.path.append("/app/src")
    
    from main import _save_json, _save_csv
    from src.matrix.export_excel import save_excel
    
    # Create output directory
    output_dir = Path("outputs")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate filename
    file_base_name = custom_filename or opportunity_id or job_id
    import re
    file_base_name = re.sub(r'[^\w\s-]', '', file_base_name).strip()
    file_base_name = re.sub(r'[-\s]+', '-', file_base_name)
    
    # Generate outputs
    final_json = output_dir / f"{file_base_name}.requirements.json"
    final_csv = output_dir / f"{file_base_name}.matrix.csv"
    final_xlsx = output_dir / f"{file_base_name}.matrix.xlsx"
    
    _save_json(requirements, final_json)
    _save_csv(requirements, final_csv)
    save_excel(requirements, final_xlsx)
    
    log.info(f"Generated outputs: {len(requirements)} requirements")
    
    # Upload to Azure Blob Storage
    blob_service = BlobServiceClient.from_connection_string(
        settings.azure_storage_connection_string
    )
    
    # Upload Excel file (main output)
    blob_client = blob_service.get_blob_client(
        container=settings.azure_blob_container,
        blob=final_xlsx.name
    )
    
    with open(final_xlsx, "rb") as f:
        blob_client.upload_blob(f, overwrite=True)
    
    # Generate SAS URL for download
    parts = {kv.split("=", 1)[0]: kv.split("=", 1)[1] for kv in settings.azure_storage_connection_string.split(";") if "=" in kv}
    account_name = parts.get("AccountName")
    account_key = parts.get("AccountKey")
    
    if not account_name or not account_key:
        raise RuntimeError("AZURE_STORAGE_CONNECTION_STRING missing AccountName/AccountKey.")
    
    sas = generate_blob_sas(
        account_name=account_name,
        container_name=settings.azure_blob_container,
        blob_name=final_xlsx.name,
        account_key=account_key,
        permission=BlobSasPermissions(read=True),
        expiry=datetime.utcnow() + timedelta(hours=24),  # 24 hour expiry
    )
    
    sas_url = f"https://{account_name}.blob.core.windows.net/{settings.azure_blob_container}/{final_xlsx.name}?{sas}"
    
    log.info(f"Uploaded results for job {job_id}: {sas_url}")
    
    # Cleanup local files
    try:
        final_json.unlink(missing_ok=True)
        final_csv.unlink(missing_ok=True)
        final_xlsx.unlink(missing_ok=True)
        log.info("Cleaned up local output files")
    except Exception as e:
        log.warning(f"Failed to cleanup local files: {e}")
    
    return sas_url
