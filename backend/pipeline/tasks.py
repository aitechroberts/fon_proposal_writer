# backend/pipeline/tasks.py
"""
Pipeline tasks for RFP extraction and proposal generation.
These run directly in the backend container without Prefect orchestration.
"""
import os
import tempfile
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from zipfile import ZipFile

from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions

from config import settings

log = logging.getLogger(__name__)


def _blob_account_parts() -> Dict[str, str]:
    """Parse Azure storage connection string into parts."""
    return {
        kv.split("=", 1)[0]: kv.split("=", 1)[1]
        for kv in settings.azure_storage_connection_string.split(";")
        if "=" in kv
    }


def _safe_file_base(custom_filename: Optional[str], opportunity_id: str, job_id: str) -> str:
    """Generate a safe filename base."""
    import re
    file_base_name = custom_filename or opportunity_id or job_id
    file_base_name = re.sub(r"[^\w\s-]", "", file_base_name).strip()
    file_base_name = re.sub(r"[-\s]+", "-", file_base_name)
    return file_base_name or job_id


def download_files_task(blob_urls: List[str], job_id: str) -> List[Path]:
    """Download files from Azure Blob Storage to local temp directory."""
    if not blob_urls:
        log.warning(f"No blob URLs provided for job {job_id}")
        return []
    
    temp_dir = Path(tempfile.mkdtemp(prefix=f"job_{job_id}_"))
    downloaded_files = []
    
    blob_service = BlobServiceClient.from_connection_string(
        settings.azure_storage_connection_string
    )
    container_name = settings.azure_blob_container
    
    for i, blob_url in enumerate(blob_urls):
        try:
            # Extract blob path from URL
            # URL format: https://{account}.blob.core.windows.net/{container}/{blob_path}?{sas}
            url_without_query = blob_url.split('?')[0]
            
            # Find the blob path after the container name
            container_marker = f"/{container_name}/"
            if container_marker in url_without_query:
                blob_path = url_without_query.split(container_marker, 1)[1]
            else:
                blob_path = url_without_query.split('/')[-1]
            
            # Local filename is the original filename (last part after any slashes)
            local_filename = blob_path.split('/')[-1]
            # Remove UUID prefix if present (format: {uuid}_{original_filename})
            if '_' in local_filename and len(local_filename.split('_')[0]) == 36:
                local_filename = '_'.join(local_filename.split('_')[1:])
            
            local_path = temp_dir / local_filename
            
            # Download blob using full blob path
            blob_client = blob_service.get_blob_client(
                container=container_name,
                blob=blob_path
            )
            
            with open(local_path, "wb") as f:
                download_stream = blob_client.download_blob()
                f.write(download_stream.readall())
            
            downloaded_files.append(local_path)
            log.info(f"Downloaded {blob_path} -> {local_filename} for job {job_id}")
            
        except Exception as e:
            log.error(f"Failed to download {blob_url} for job {job_id}: {e}")
            continue
    
    log.info(f"Downloaded {len(downloaded_files)} files for job {job_id}")
    return downloaded_files


def run_dspy_pipeline_task(opportunity_id: str, input_files: List[Path]) -> List[Dict[str, Any]]:
    """Run the DSPy processing pipeline on input files."""
    if not input_files:
        log.warning(f"No input files provided for opportunity {opportunity_id}")
        return []
    
    # Import from the local src directory
    from main import run_dspy_pipeline
    
    log.info(f"Starting DSPy pipeline for {len(input_files)} files")
    
    try:
        results = run_dspy_pipeline(opportunity_id, input_files)
        log.info(f"DSPy pipeline completed: {len(results)} requirements extracted")
        return results
    except Exception as e:
        log.error(f"DSPy pipeline failed: {e}")
        raise


def generate_and_upload_task(
    requirements: List[Dict[str, Any]],
    job_id: str,
    opportunity_id: str,
    custom_filename: str = None
) -> Dict[str, Any]:
    """Generate Excel/JSON/CSV outputs, upload XLSX, and keep local paths for zipping."""
    if not requirements:
        log.warning(f"No requirements to process for job {job_id}")
        return {"requirements_sas_url": "", "file_count": 0, "local_paths": {}}

    from main import _save_json, _save_csv
    from src.matrix.export_excel import save_excel

    output_dir = Path("outputs")
    output_dir.mkdir(parents=True, exist_ok=True)

    file_base_name = _safe_file_base(custom_filename, opportunity_id, job_id)

    final_json = output_dir / f"{file_base_name}.requirements.json"
    final_csv = output_dir / f"{file_base_name}.matrix.csv"
    final_xlsx = output_dir / f"{file_base_name}.matrix.xlsx"

    _save_json(requirements, final_json)
    _save_csv(requirements, final_csv)
    save_excel(requirements, final_xlsx)

    log.info(f"Generated outputs: {len(requirements)} requirements")

    # Upload XLSX to Azure Blob
    blob_service = BlobServiceClient.from_connection_string(settings.azure_storage_connection_string)
    blob_client = blob_service.get_blob_client(container=settings.azure_blob_container, blob=final_xlsx.name)
    with open(final_xlsx, "rb") as f:
        blob_client.upload_blob(f, overwrite=True)

    # Generate SAS URL
    parts = _blob_account_parts()
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
        expiry=datetime.utcnow() + timedelta(hours=24),
    )
    requirements_sas_url = f"https://{account_name}.blob.core.windows.net/{settings.azure_blob_container}/{final_xlsx.name}?{sas}"

    log.info(f"Uploaded results for job {job_id}: {requirements_sas_url}")

    return {
        "requirements_sas_url": requirements_sas_url,
        "file_count": len(requirements),
        "local_paths": {
            "json": str(final_json),
            "csv": str(final_csv),
            "xlsx": str(final_xlsx),
        },
    }


def generate_proposal_task(
    requirements: List[Dict[str, Any]],
    job_id: str,
    opportunity_id: str,
    custom_filename: str = None,
    use_two_stage: bool = False
) -> Dict[str, Any]:
    """
    Generate proposal document from extracted requirements.
    
    Args:
        requirements: List of extracted requirement dicts
        job_id: Unique job identifier
        opportunity_id: Opportunity ID for naming
        custom_filename: Custom output filename (optional)
        use_two_stage: Whether to use two-stage DSPy writer (default: single-pass)
        
    Returns:
        Dict with SAS URL and local paths for the generated Word document
    """
    if not requirements:
        log.warning(f"No requirements for proposal generation in job {job_id}")
        return {"proposal_sas_url": "", "local_path": ""}
    
    from src.proposal.modules import run_proposal_pipeline
    from src.proposal.export_word import export_proposal_to_word, sections_to_text
    
    log.info(f"Starting proposal generation for {len(requirements)} requirements")
    
    try:
        # Run the proposal writing pipeline
        sections = run_proposal_pipeline(requirements, use_two_stage=use_two_stage)
        log.info(f"Generated {len(sections)} proposal sections")
        
        output_dir = Path("outputs")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        file_base_name = _safe_file_base(custom_filename, opportunity_id, job_id)
        
        # Save as text (intermediate)
        text_path = output_dir / f"{file_base_name}.proposal.txt"
        text_content = sections_to_text(sections)
        text_path.write_text(text_content, encoding="utf-8")
        log.info(f"Saved intermediate text: {text_path}")
        
        # Export to Word document
        docx_path = output_dir / f"{file_base_name}.proposal.docx"
        export_proposal_to_word(
            sections=sections,
            path=docx_path,
            title=f"Technical Proposal - {opportunity_id or 'Response'}"
        )
        log.info(f"Generated Word document: {docx_path}")
        
        # Upload to Azure Blob Storage
        blob_service = BlobServiceClient.from_connection_string(
            settings.azure_storage_connection_string
        )
        
        blob_client = blob_service.get_blob_client(
            container=settings.azure_blob_container,
            blob=docx_path.name
        )
        
        with open(docx_path, "rb") as f:
            blob_client.upload_blob(f, overwrite=True)
        
        # Generate SAS URL for download
        parts = _blob_account_parts()
        account_name = parts.get("AccountName")
        account_key = parts.get("AccountKey")
        
        if not account_name or not account_key:
            raise RuntimeError("AZURE_STORAGE_CONNECTION_STRING missing AccountName/AccountKey.")
        
        sas = generate_blob_sas(
            account_name=account_name,
            container_name=settings.azure_blob_container,
            blob_name=docx_path.name,
            account_key=account_key,
            permission=BlobSasPermissions(read=True),
            expiry=datetime.utcnow() + timedelta(hours=24),
        )
        
        sas_url = f"https://{account_name}.blob.core.windows.net/{settings.azure_blob_container}/{docx_path.name}?{sas}"
        
        log.info(f"Uploaded proposal for job {job_id}: {sas_url}")
        
        return {
            "proposal_sas_url": sas_url,
            "local_path": str(docx_path),
            "text_path": str(text_path),
        }
        
    except Exception as e:
        log.error(f"Proposal generation failed for job {job_id}: {e}")
        raise


def zip_outputs_task(
    matrix_paths: Dict[str, str],
    proposal_path: Optional[str],
    job_id: str,
    opportunity_id: str,
    custom_filename: Optional[str] = None,
) -> str:
    """Zip all generated outputs and upload to Azure Blob Storage."""
    file_base_name = _safe_file_base(custom_filename, opportunity_id, job_id)
    output_dir = Path("outputs")
    output_dir.mkdir(parents=True, exist_ok=True)

    zip_path = output_dir / f"{file_base_name}.outputs.zip"

    # Collect files that exist
    files_to_zip = []
    for p in matrix_paths.values():
        if p and Path(p).exists():
            files_to_zip.append(Path(p))
    if proposal_path and Path(proposal_path).exists():
        files_to_zip.append(Path(proposal_path))

    if not files_to_zip:
        log.warning(f"No files to zip for job {job_id}")
        return ""

    with ZipFile(zip_path, "w") as zf:
        for file_path in files_to_zip:
            zf.write(file_path, arcname=file_path.name)

    # Upload ZIP to Azure Blob
    blob_service = BlobServiceClient.from_connection_string(settings.azure_storage_connection_string)
    blob_client = blob_service.get_blob_client(
        container=settings.azure_blob_container,
        blob=zip_path.name,
    )
    with open(zip_path, "rb") as f:
        blob_client.upload_blob(f, overwrite=True)

    # Generate SAS URL
    parts = _blob_account_parts()
    account_name = parts.get("AccountName")
    account_key = parts.get("AccountKey")
    if not account_name or not account_key:
        raise RuntimeError("AZURE_STORAGE_CONNECTION_STRING missing AccountName/AccountKey.")

    sas = generate_blob_sas(
        account_name=account_name,
        container_name=settings.azure_blob_container,
        blob_name=zip_path.name,
        account_key=account_key,
        permission=BlobSasPermissions(read=True),
        expiry=datetime.utcnow() + timedelta(hours=24),
    )
    zip_sas_url = f"https://{account_name}.blob.core.windows.net/{settings.azure_blob_container}/{zip_path.name}?{sas}"

    log.info(f"Uploaded ZIP for job {job_id}: {zip_sas_url}")

    # Cleanup all local files
    for file_path in files_to_zip + [zip_path]:
        try:
            Path(file_path).unlink(missing_ok=True)
        except Exception as e:
            log.warning(f"Failed to cleanup file {file_path}: {e}")

    return zip_sas_url

