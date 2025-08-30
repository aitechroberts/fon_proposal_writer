# src/pipeline/run_experiment.py
import os
import logging
from pathlib import Path
from typing import Tuple, List, Dict, Any

import dspy
from langfuse import observe, get_client
from pypdf import PdfReader

# Local imports
from ..config import settings
from ..experiments.config_variants import load_variant, apply_variant
from ..preprocessing.regex_pass import fast_hits
from ..preprocessing.segmenter import heading_aware_chunks
from ..extraction.modules import Extractor, Classifier, Grounder
from ..extraction.confidence import calculate_confidence
from ..extraction.merge_dedupe import merge_requirements
from ..matrix.export import save_json, save_csv
from ..matrix.export_excel import save_excel
from ..observability.metrics import log_experiment_metadata
from ..io.loaders import pdf_to_pages

logger = logging.getLogger(__name__)

def initialize_dspy() -> None:
    """Initialize DSPy with proper configuration."""
    try:
        variant = load_variant()
        
        # Configure DSPy LM with Azure OpenAI
        lm = dspy.LM(
            f"azure/{settings.azure_openai_deployment}",
            model_type=settings.dspy_model_type,
            temperature=variant.temperature,
            max_tokens=4000
        )
        
        # Set up DSPy with JSON adapter for structured output
        dspy.configure(lm=lm, adapter=dspy.JSONAdapter())
        
        logger.info(f"DSPy initialized with model: {settings.azure_openai_deployment}")
        
    except Exception as e:
        logger.error(f"Failed to initialize DSPy: {e}")
        raise

def pdf_to_text(path: str) -> str:
    """Extract text from PDF using pypdf."""
    try:
        pages = pdf_to_pages(path)
        return "\n".join(text for _, text in pages)
    except Exception as e:
        logger.error(f"Failed to extract text from {path}: {e}")
        raise

@observe(name="experiment_run")
def run_one(file_path: str, exp_name: str) -> Tuple[str, str, str, Dict[str, Any]]:
    """Run a single experiment on a file."""
    try:
        # Initialize DSPy if not already done
        if not hasattr(dspy.settings, 'lm') or dspy.settings.lm is None:
            initialize_dspy()
        
        # Apply variant configuration
        variant = load_variant()
        apply_variant(variant)
        
        # Extract text and create chunks
        logger.info(f"Processing file: {file_path}")
        text = pdf_to_text(file_path)
        pages = [(1, text)]  # Simple page mapping for now
        chunks = list(heading_aware_chunks(pages))
        
        logger.info(f"Created {len(chunks)} chunks from {file_path}")
        
        # Initialize extraction modules
        extractor = Extractor()
        classifier = Classifier()
        grounder = Grounder()
        
        reqs: List[Dict[str, Any]] = []
        
        # Process each chunk
        for i, chunk in enumerate(chunks):
            logger.debug(f"Processing chunk {i+1}/{len(chunks)}")
            
            # Regex pre-pass for fast hits
            try:
                for hit in fast_hits(chunk):
                    req = {
                        "id": "",
                        "label": hit["match"][:120],
                        "category": "Other",
                        "modality": "UNKNOWN",
                        "quote": hit["match"],
                        "section": chunk["section"],
                        "page_start": chunk["start_page"],
                        "page_end": chunk["end_page"],
                        "source": "regex"
                    }
                    req["confidence"] = calculate_confidence(req)
                    reqs.append(req)
            except Exception as e:
                logger.warning(f"Regex processing failed for chunk {i}: {e}")
            
            # LLM extraction stages
            try:
                extracted_reqs = extractor(chunk)
                for req in extracted_reqs:
                    req["source"] = "llm"
                    
                    # Classify requirement
                    req = classifier(req)
                    req["classified"] = True
                    
                    # Ground with evidence
                    req = grounder(chunk, req)
                    req["grounded"] = True
                    
                    # Calculate confidence
                    req["confidence"] = calculate_confidence(req)
                    reqs.append(req)
                    
            except Exception as e:
                logger.warning(f"LLM processing failed for chunk {i}: {e}")
        
        logger.info(f"Extracted {len(reqs)} total requirements")
        
        # Merge and deduplicate
        merged = merge_requirements(reqs)
        logger.info(f"After merging: {len(merged)} unique requirements")
        
        # Generate output paths
        base_path = Path(file_path)
        out_json = str(base_path.with_suffix(f".{exp_name}.requirements.json"))
        out_csv = str(base_path.with_suffix(f".{exp_name}.matrix.csv"))
        out_xlsx = str(base_path.with_suffix(f".{exp_name}.matrix.xlsx"))
        
        # Save outputs
        try:
            save_json(merged, out_json)
            save_csv(merged, out_csv)
            save_excel(merged, out_xlsx)
            logger.info(f"Saved outputs: {out_json}, {out_csv}, {out_xlsx}")
        except Exception as e:
            logger.error(f"Failed to save outputs: {e}")
            raise
        
        # Log experiment metadata to Langfuse
        try:
            stats = log_experiment_metadata(exp_name, merged)
            get_client().flush()  # Ensure telemetry is sent
        except Exception as e:
            logger.warning(f"Failed to log experiment metadata: {e}")
            stats = {}
        
        return out_json, out_csv, out_xlsx, stats
        
    except Exception as e:
        logger.error(f"Experiment failed for {file_path}: {e}")
        raise

def run_experiment(input_dir: str, exp_name: str = "baseline") -> List[Tuple[str, str, str, Dict[str, Any]]]:
    """Run experiments on all PDF files in input directory."""
    input_path = Path(input_dir)
    if not input_path.exists():
        raise FileNotFoundError(f"Input directory not found: {input_dir}")
    
    pdf_files = list(input_path.glob("*.pdf"))
    if not pdf_files:
        logger.warning(f"No PDF files found in {input_dir}")
        return []
    
    logger.info(f"Found {len(pdf_files)} PDF files to process")
    
    results = []
    for pdf_file in pdf_files:
        try:
            result = run_one(str(pdf_file), exp_name)
            results.append(result)
        except Exception as e:
            logger.error(f"Failed to process {pdf_file}: {e}")
            continue
    
    logger.info(f"Successfully processed {len(results)}/{len(pdf_files)} files")
    return results

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Run RFP compliance extraction experiment")
    parser.add_argument("--inputs", required=True, help="Input directory containing PDF files")
    parser.add_argument("--exp", default="baseline", help="Experiment name")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    
    args = parser.parse_args()
    
    # Configure logging
    level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(level=level, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    try:
        results = run_experiment(args.inputs, args.exp)
        print(f"Experiment completed. Processed {len(results)} files.")
    except Exception as e:
        logger.error(f"Experiment failed: {e}")
        exit(1)
