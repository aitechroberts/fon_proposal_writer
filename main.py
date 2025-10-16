# main.py
from __future__ import annotations
# Base Libraries
import os
import json
import csv
import time
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Tuple, Dict, Any

# External
from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions
import litellm
import dspy

# Modules
from src.matrix.export_excel import save_excel
from src.io.loaders import load_document
from src.io.smart_loader import load_document_smart, get_extraction_stats
from src.config import settings


# -------------------- Logging --------------------
_LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, _LOG_LEVEL, logging.INFO),
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
log = logging.getLogger("main")
log.info("Starting processing")

CLEAR_CACHE_ON_STARTUP = os.getenv("CLEAR_CACHE", "0") in ("1", "true", "TRUE", "yes")

if CLEAR_CACHE_ON_STARTUP:
    try:
        import dspy
        if hasattr(dspy, 'cache'):
            dspy.cache.reset_memory_cache()
            if hasattr(dspy.cache, 'disk_cache'):
                dspy.cache.disk_cache.clear()
            log.info("✓ DSPy cache cleared on startup")
    except Exception as e:
        log.warning(f"Failed to clear cache: {e}")


LOG_LLM = os.getenv("LOG_LLM", "0") in ("1", "true", "TRUE", "yes", "YES")
RAW_DIR = Path(os.getenv("RAW_DUMP_DIR", "raw_llm"))

CLEAR_CACHE_ON_STARTUP = os.getenv("CLEAR_CACHE", "0") in ("1", "true", "TRUE", "yes")

if CLEAR_CACHE_ON_STARTUP:
    try:
        import dspy
        if hasattr(dspy, 'cache'):
            dspy.cache.reset_memory_cache()
            if hasattr(dspy.cache, 'disk_cache'):
                dspy.cache.disk_cache.clear()
            log.info("✓ DSPy cache cleared on startup")
    except Exception as e:
        log.warning(f"Failed to clear cache: {e}")

# -------------------- IO helpers --------------------
def _save_json(items: List[Dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)

def _save_csv(items: List[Dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    headers = (
        ["category","modality","quote","section","page_start","page_end","source","confidence","doc_name"]
        if not items else sorted({k for r in items for k in r.keys()})
    )
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=headers)
        w.writeheader()
        for it in items:
            w.writerow(it)

# -------------------- Azure Blob --------------------
def _upload_blob_and_sas(local_path: Path, container: str, conn_str: str, sas_hours: int = 1) -> str:
    blob_service = BlobServiceClient.from_connection_string(conn_str)
    blob_client = blob_service.get_blob_client(container=container, blob=local_path.name)
    with open(local_path, "rb") as f:
        blob_client.upload_blob(f, overwrite=True)

    parts = {kv.split("=", 1)[0]: kv.split("=", 1)[1] for kv in conn_str.split(";") if "=" in kv}
    account_name = parts.get("AccountName")
    account_key  = parts.get("AccountKey")
    if not account_name or not account_key:
        raise RuntimeError("AZURE_STORAGE_CONNECTION_STRING missing AccountName/AccountKey.")

    sas = generate_blob_sas(
        account_name=account_name,
        container_name=container,
        blob_name=local_path.name,
        account_key=account_key,
        permission=BlobSasPermissions(read=True),
        expiry=datetime.utcnow() + timedelta(hours=sas_hours),
    )
    return f"https://{account_name}.blob.core.windows.net/{container}/{local_path.name}?{sas}"

# -------------------- Cleanup helper --------------------
def _cleanup_outputs() -> None:
    """Delete tmp_outputs and outputs directories after successful upload."""
    import shutil
    
    dirs_to_clean = [Path("tmp_outputs"), Path("outputs")]
        # Allow disabling cleanup for debugging
    if os.getenv("SKIP_CLEANUP", "0") == "1":
        log.info("Skipping cleanup (SKIP_CLEANUP=1)")
        return
    
    for dir_path in dirs_to_clean:
        if dir_path.exists():
            try:
                shutil.rmtree(dir_path)
                log.info("Cleaned up directory: %s", dir_path)
            except Exception as e:
                log.warning("Failed to cleanup %s: %s", dir_path, e)

def _init_dspy_direct() -> None:
    """
    Configure DSPy - patch litellm.completion FIRST before anything else.
    """
    from functools import wraps
    
    # STEP 1: PATCH LITELLM FIRST (before any DSPy objects are created)
    _original_litellm_completion = litellm.completion
    
    @wraps(_original_litellm_completion)
    def _force_max_tokens_completion(*args, **kwargs):
        # ALWAYS force max_tokens to 32000
        original_max = kwargs.get('max_tokens')
        kwargs['max_tokens'] = 32000
        
        if original_max and original_max != 32000:
            log.debug(f"⚠️ Overriding max_tokens: {original_max} -> 32000")
        
        return _original_litellm_completion(*args, **kwargs)
    
    litellm.completion = _force_max_tokens_completion
    log.info("✅ Patched litellm.completion to force max_tokens=32000")
    
    # STEP 2: Set up environment
    base = (settings.azure_api_base or "").rstrip("/")
    os.environ["AZURE_API_KEY"] = settings.azure_api_key or ""
    os.environ["AZURE_API_BASE"] = base
    os.environ["AZURE_API_VERSION"] = settings.azure_api_version or "2024-12-01-preview"
    os.environ["OPENAI_API_KEY"] = settings.azure_api_key or ""
    
    litellm.drop_params = True
    litellm.set_verbose = False
    
    # STEP 3: Create DSPy LM (will use patched litellm.completion)
    azure_model = f"azure/{settings.azure_openai_deployment}"
    
    lm = dspy.LM(
        model=azure_model,
        api_key=settings.azure_api_key,
        api_base=f"{base}/openai/v1/",
        temperature=0.0,
        max_tokens=32000,  # Won't matter, patch will force it anyway
    )
    
    # STEP 4: Configure DSPy (ONLY ONCE!)
    dspy.configure(lm=lm, adapter=dspy.JSONAdapter(), track_usage=False, cache=False)
    
    log.info(
        "Configured DSPy: deployment=%r, litellm.completion PATCHED for max_tokens=32000",
        settings.azure_openai_deployment
    )
    
    # Optional variant application
    try:
        from src.experiments.config_variants import load_variant, apply_variant
        variant = load_variant()
        apply_variant(variant)
        log.info("Applied variant: dep=%r base=%r version=%r",
                settings.azure_openai_deployment, base, settings.azure_api_version)
    except Exception as e:
        log.warning("Variant not applied (optional): %s", e)

# -------------------- Page grouping --------------------
def _group_pages_into_chunks(pages: List[Tuple[int,str]], pages_per_chunk: int) -> List[Dict[str, Any]]:
    """
    Take (page_num, text) list and return chunk dicts combining N pages each.
    Each chunk keeps section label and page_start/end for traceability.
    """
    chunks: List[Dict[str, Any]] = []
    buf_text: List[str] = []
    start_page = None
    for idx, (pnum, ptxt) in enumerate(pages, start=1):
        if start_page is None:
            start_page = pnum
        buf_text.append(f"[Page {pnum}]\n{ptxt}")
        if idx % pages_per_chunk == 0:
            end_page = pnum
            chunks.append({
                "text": "\n\n".join(buf_text),
                "section": f"Pages {start_page}-{end_page}",
                "start_page": start_page,
                "end_page": end_page,
            })
            buf_text, start_page = [], None
    if buf_text:
        end_page = pages[-1][0]
        chunks.append({
            "text": "\n\n".join(buf_text),
            "section": f"Pages {start_page}-{end_page}" if start_page is not None else f"Up to {end_page}",
            "start_page": start_page or pages[0][0],
            "end_page": end_page,
        })
    return chunks

# -------------------- Core pipeline --------------------
def run_dspy_pipeline(opportunity_id: str, input_files: List[Path]) -> List[Dict[str, Any]]:
    """
    Process multiple documents (PDF, Word, Excel) and extract requirements.
    
    1) Initialize DSPy (Azure via LiteLLM).
    2) Batched Calls:
      - Group pages into larger chunks (default 1 page each)
      - One Extractor call per grouped chunk
      - BatchClassifier across many requirements (default 25 per call)
      - BatchGrounder per chunk in batches (default 25 per call)
    """
    _init_dspy_direct()

    # Import AFTER configure so predictors bind correctly
    from src.extraction.modules import Extractor, BatchClassifier, BatchGrounder

    extractor       = Extractor()
    batch_classifier = BatchClassifier()
    batch_grounder   = BatchGrounder()

    # knobs
    max_chunks       = int(os.getenv("MAX_CHUNKS", "0"))         # 0 = no cap
    max_chars        = int(os.getenv("MAX_CHARS", "12000"))      # truncate very long chunks
    pages_per_chunk  = int(os.getenv("PAGES_PER_CHUNK", "1"))   # changed default to 1
    batch_size       = int(os.getenv("BATCH_SIZE", "20"))

    results: List[Dict[str, Any]] = []

    for file_path in input_files:
        file_type = file_path.suffix.lower()
        log.info(f"Loading {file_type} file: {file_path.name}")
        
        t0 = time.perf_counter()
        
        try:
            # Universal loader - handles PDF, Word, Excel
            pages = load_document_smart(str(file_path))
        except Exception as e:
            log.error(f"Failed to load {file_path.name}: {e}")
            continue  # Skip this file and move to next
        
        t1 = time.perf_counter()
        log.info(f"Loaded {len(pages)} pages/sections in {t1 - t0:.2f}s from {file_path.name}")

        # Group pages into chunks
        grouped = _group_pages_into_chunks(pages, pages_per_chunk)
        if max_chunks > 0:
            grouped = grouped[:max_chunks]
        log.info(f"Grouped chunks for {file_path.name}: {len(grouped)} (pages_per_chunk={pages_per_chunk})")

        # ---------- Extract per grouped chunk ----------
        extracted_all: List[Dict[str, Any]] = []
        per_chunk_extracted: List[List[Dict[str, Any]]] = []
        
        for idx, chunk in enumerate(grouped, start=1):
            text = chunk.get("text", "") or ""
            if max_chars > 0 and len(text) > max_chars:
                chunk = dict(chunk)
                chunk["text"] = text[:max_chars] + "\n\n[TRUNCATED FOR LENGTH]"
            
            preview = (chunk["text"] or "")[:180].replace("\n", " ")
            log.debug(f"[EXTRACT] {file_path.name} chunk {idx}/{len(grouped)} len={len(chunk['text'])} preview={preview!r}")

            te0 = time.perf_counter()
            reqs = extractor(chunk)
            te1 = time.perf_counter()
            
            for r in reqs:
                r.setdefault("source", "llm")
                r["_gidx"] = idx - 1  # Track which chunk this came from
            
            extracted_all.extend(reqs)
            per_chunk_extracted.append(reqs)
            
            if LOG_LLM:
                RAW_DIR.mkdir(parents=True, exist_ok=True)
                (RAW_DIR / f"extract_{file_path.stem}_g{idx:03d}.json").write_text(
                    json.dumps(reqs, ensure_ascii=False, indent=2), encoding="utf-8"
                )
            
            log.info(f"[EXTRACT] {file_path.name} chunk {idx} -> {len(reqs)} reqs in {te1 - te0:.2f}s")

        # ---------- Batch classify across ALL extracted ----------
        classified_all: List[Dict[str, Any]] = []
        for start in range(0, len(extracted_all), batch_size):
            batch = extracted_all[start:start+batch_size]
            if not batch:
                continue
            
            tc0 = time.perf_counter()
            cls_batch = batch_classifier(batch)
            tc1 = time.perf_counter()
            
            if LOG_LLM:
                (RAW_DIR / f"classify_{file_path.stem}_{start:05d}.json").write_text(
                    json.dumps(cls_batch, ensure_ascii=False, indent=2), encoding="utf-8"
                )
            
            log.info(f"[CLASSIFY] {file_path.name} items {start+1}..{start+len(batch)} -> {len(cls_batch)} in {tc1 - tc0:.2f}s")
            classified_all.extend(cls_batch)

        # ---------- Batch ground per grouped chunk ----------
        grounded_all: List[Dict[str, Any]] = []
        by_gidx: Dict[int, List[Dict[str, Any]]] = {}
        
        for r in classified_all:
            gidx = int(r.get("_gidx", 0))
            by_gidx.setdefault(gidx, []).append(r)

        for idx, chunk in enumerate(grouped):
            cls_for_chunk = by_gidx.get(idx, [])
            if not cls_for_chunk:
                continue
            
            for start in range(0, len(cls_for_chunk), batch_size):
                b = cls_for_chunk[start:start+batch_size]
                tg0 = time.perf_counter()
                grd_batch = batch_grounder(chunk, b)
                tg1 = time.perf_counter()
                
                if LOG_LLM:
                    (RAW_DIR / f"ground_{file_path.stem}_g{idx:03d}_{start:05d}.json").write_text(
                        json.dumps(grd_batch, ensure_ascii=False, indent=2), encoding="utf-8"
                    )
                
                log.info(f"[GROUND] {file_path.name} chunk {idx+1} items {start+1}..{start+len(b)} -> {len(grd_batch)} in {tg1 - tg0:.2f}s")
                grounded_all.extend(grd_batch)

        # ---------- Normalize, validate & tag doc ----------
        valid_reqs = []
        skipped_count = 0
        
        for r in grounded_all:
            # Clean up internal fields
            r.pop("_gidx", None)
            r.pop("_idx", None)
            
            # Handle schema mismatches
            if "page" in r and "page_start" not in r:
                r["page_start"] = r.pop("page")
            if "page" in r and "page_end" not in r:
                r["page_end"] = r.get("page")
            
            # Normalize to expected schema
            r["doc_name"] = file_path.name
            r["doc_type"] = file_type[1:]  # .pdf -> pdf, .docx -> docx
            r.setdefault("category", r.get("category", "Other"))
            r.setdefault("modality", r.get("modality", "UNKNOWN"))
            r.setdefault("quote", r.get("quote", ""))
            r.setdefault("section", r.get("section", ""))
            r.setdefault("page_start", r.get("page_start", ""))
            r.setdefault("page_end", r.get("page_end", ""))
            r.setdefault("source", r.get("source", "llm"))
            r.setdefault("confidence", 0.5)
            
            # Validate minimum required fields
            required_fields = ["category", "modality", "quote"]
            if all(r.get(f) for f in required_fields):
                valid_reqs.append(r)
            else:
                skipped_count += 1
                missing = [f for f in required_fields if not r.get(f)]
                log.warning(f"SKIPPING invalid requirement (missing {missing})")

        log.info(
            f"File {file_path.name} done: extracted={len(extracted_all)} "
            f"classified={len(classified_all)} grounded={len(grounded_all)} "
            f"valid={len(valid_reqs)} skipped={skipped_count}"
        )

        results.extend(valid_reqs)
    
    return results

# -------------------- Streamlit entry --------------------
def process_opportunity(opportunity_id: str) -> str:
    """
    Process all documents (PDF, Word, Excel) for an opportunity.
    
    Supported formats:
    - PDF: .pdf
    - Word: .docx, .doc
    - Excel: .xlsx, .xls
    """
    inputs_root = Path("data/inputs")
    specific_dir = inputs_root / opportunity_id if opportunity_id else None

    # Discover all supported file types
    supported_extensions = ["*.pdf", "*.docx", "*.doc", "*.xlsx", "*.xls"]
    all_files = []
    
    if specific_dir and specific_dir.exists():
        # Get files from opportunity-specific directory
        for pattern in supported_extensions:
            all_files.extend(specific_dir.glob(pattern))
    else:
        # Get files from root inputs directory
        for pattern in supported_extensions:
            all_files.extend(inputs_root.glob(pattern))
    
    # Sort for consistent processing order
    all_files = sorted(all_files)

    if not all_files:
        raise FileNotFoundError(
            f"No supported files found for opportunity '{opportunity_id}'. "
            f"Place files in data/inputs/{opportunity_id}/ or data/inputs/\n"
            f"Supported formats: PDF (.pdf), Word (.docx, .doc), Excel (.xlsx, .xls)"
        )

    # Log what we found (grouped by file type)
    file_type_counts = {}
    for f in all_files:
        ext = f.suffix.lower()
        file_type_counts[ext] = file_type_counts.get(ext, 0) + 1
    
    file_summary = ", ".join(f"{count} {ext}" for ext, count in sorted(file_type_counts.items()))
    log.info(
        "Processing %d file(s) for %s: %s",
        len(all_files),
        opportunity_id or "[default inputs]",
        file_summary
    )

    # Run extraction pipeline
    combined_reqs = run_dspy_pipeline(opportunity_id, all_files)

    # Save per-document outputs to tmp_outputs/
    tmp_dir = Path("tmp_outputs")
    tmp_dir.mkdir(parents=True, exist_ok=True)
    
    for file_path in all_files:
        doc_items = [r for r in combined_reqs if r.get("doc_name") == file_path.name]
        base = f"{file_path.stem}.{opportunity_id or 'default'}"
        
        _save_json(doc_items, tmp_dir / f"{base}.requirements.json")
        _save_csv(doc_items, tmp_dir / f"{base}.matrix.csv")
        save_excel(doc_items, tmp_dir / f"{base}.matrix.xlsx")
        
        log.info("Saved tmp outputs for %s (%d rows)", file_path.name, len(doc_items))

    # Save combined outputs to outputs/
    out_dir = Path("outputs")
    out_dir.mkdir(parents=True, exist_ok=True)
    
    final_json = out_dir / f"{(opportunity_id or 'default')}.requirements.json"
    final_csv = out_dir / f"{(opportunity_id or 'default')}.matrix.csv"
    final_xlsx = out_dir / f"{(opportunity_id or 'default')}.matrix.xlsx"

    _save_json(combined_reqs, final_json)
    log.info(f"Saved {final_json}")
    
    _save_csv(combined_reqs, final_csv)
    log.info(f"Saved {final_csv}")
    
    try:
        save_excel(combined_reqs, final_xlsx)
        log.info("Final combined XLSX: %s (%d rows)", final_xlsx, len(combined_reqs))
    except Exception as e:
        log.error(f"Failed to save final XLSX: {e}")
        raise

    # Upload to Azure Blob Storage
    conn_str = settings.azure_storage_connection_string
    container = settings.azure_blob_container
    
    if not conn_str or not container:
        raise RuntimeError(
            "Set AZURE_STORAGE_CONNECTION_STRING and AZURE_BLOB_CONTAINER in .env file."
        )
    
    sas_url = _upload_blob_and_sas(final_xlsx, container, conn_str, sas_hours=1)
    log.info("Uploaded to blob & generated SAS URL.")
    
    # Log extraction statistics (shows standard vs Document Intelligence usage)
    log.info("\n" + get_extraction_stats())
    
    # Cleanup local files after successful upload
    _cleanup_outputs()
    
    return sas_url
