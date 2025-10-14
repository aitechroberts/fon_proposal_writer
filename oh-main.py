# main.py
"""
Simplified main entry point for RFP compliance extraction.
Uses the refactored modular components.
"""
from __future__ import annotations

import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

from langfuse import observe, get_client
from azure.storage.blob import BlobServiceClient

# Import refactored components
from src.config import settings
from src.observability.tracing import initialize_tracing, flush_traces
from src.pipeline.run_experiment import initialize_dspy, run_experiment as run_pipeline_experiment
from src.io.loaders import pdf_to_pages

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.debug else logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def setup_azure_blob() -> BlobServiceClient:
    """Initialize Azure Blob Storage client."""
    try:
        blob_service = BlobServiceClient.from_connection_string(
            settings.azure_storage_connection_string
        )
        container_client = blob_service.get_container_client(settings.azure_blob_container)
        
        # Ensure container exists
        try:
            container_client.create_container()
            logger.info(f"Created blob container: {settings.azure_blob_container}")
        except Exception:
            logger.debug(f"Blob container {settings.azure_blob_container} already exists")
        
        return blob_service
    except Exception as e:
        logger.error(f"Failed to setup Azure Blob Storage: {e}")
        raise

def upload_json_to_blob(blob_service: BlobServiceClient, data: Dict[str, Any], 
                       prefix: str = "runs") -> str:
    """Upload JSON data to Azure Blob Storage."""
    try:
        container_client = blob_service.get_container_client(settings.azure_blob_container)
        timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        blob_name = f"{prefix}/requirements_{timestamp}.json"
        
        json_data = json.dumps(data, indent=2, ensure_ascii=False)
        container_client.upload_blob(name=blob_name, data=json_data, overwrite=True)
        
        logger.info(f"Uploaded results to blob: {blob_name}")
        return blob_name
    except Exception as e:
        logger.error(f"Failed to upload to blob storage: {e}")
        raise

def read_text_from_pdfs(pdf_paths: List[str]) -> List[Dict[str, Any]]:
    """Extract text from PDF files."""
    docs = []
    for path in pdf_paths:
        try:
            logger.info(f"Reading PDF: {path}")
            pages = pdf_to_pages(path)
            text = "\n".join(page_text for _, page_text in pages)
            docs.append({"path": path, "text": text, "pages": len(pages)})
        except Exception as e:
            logger.error(f"Failed to read PDF {path}: {e}")
            continue
    
    return docs

@observe(name="main_experiment_run")
def run_experiment(pdf_paths: List[str]) -> Dict[str, Any]:
    """Run the complete experiment pipeline."""
    try:
        # Initialize components
        initialize_tracing()
        initialize_dspy()
        blob_service = setup_azure_blob()
        
        # Extract text from PDFs
        docs = read_text_from_pdfs(pdf_paths)
        if not docs:
            raise ValueError("No valid PDF documents found")
        
        logger.info(f"Processing {len(docs)} documents")
        
        # For now, use the simple extraction approach
        # In the future, this could call the full pipeline
        results = []
        for doc in docs:
            # This is a simplified version - the full pipeline would use
            # the modular components from src.pipeline.run_experiment
            result = {
                "source_path": doc["path"],
                "requirements": [],  # Would be populated by extraction pipeline
                "meta": {
                    "pages": doc["pages"],
                    "text_length": len(doc["text"]),
                    "extraction_method": "simplified"
                }
            }
            results.append(result)
        
        # Create final payload
        payload = {
            "meta": {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "dspy_model": f"azure/{settings.azure_openai_deployment}",
                "model_type": settings.dspy_model_type,
                "langfuse_host": settings.langfuse_host,
                "total_documents": len(docs),
                "total_requirements": sum(len(r["requirements"]) for r in results)
            },
            "documents": results,
        }
        
        # Upload to blob storage
        blob_name = upload_json_to_blob(blob_service, payload)
        payload["artifact"] = {
            "azure_blob": {
                "container": settings.azure_blob_container,
                "name": blob_name
            }
        }
        
        return payload
        
    except Exception as e:
        logger.error(f"Experiment failed: {e}")
        raise

def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python main.py <file1.pdf> <file2.pdf> ...")
        print("       python main.py --pipeline <input_dir> [experiment_name]")
        sys.exit(1)
    
    try:
        # Check if using pipeline mode
        if sys.argv[1] == "--pipeline":
            if len(sys.argv) < 3:
                print("Pipeline mode requires input directory")
                sys.exit(1)
            
            input_dir = sys.argv[2]
            exp_name = sys.argv[3] if len(sys.argv) > 3 else "baseline"
            
            logger.info(f"Running pipeline experiment on {input_dir}")
            results = run_pipeline_experiment(input_dir, exp_name)
            print(f"Pipeline completed. Processed {len(results)} files.")
            
        else:
            # Simple mode - process individual PDFs
            pdf_paths = sys.argv[1:]
            
            # Validate PDF files exist
            valid_paths = []
            for path in pdf_paths:
                if Path(path).exists() and path.lower().endswith('.pdf'):
                    valid_paths.append(path)
                else:
                    logger.warning(f"Skipping invalid PDF path: {path}")
            
            if not valid_paths:
                print("No valid PDF files provided")
                sys.exit(1)
            
            logger.info(f"Processing {len(valid_paths)} PDF files")
            result = run_experiment(valid_paths)
            
            # Print summary
            print(json.dumps(result, indent=2)[:4000])
            if len(json.dumps(result, indent=2)) > 4000:
                print("\n... (output truncated)")
        
        # Ensure all traces are sent
        flush_traces()
        
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Application failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
