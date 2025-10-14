# main.py
from __future__ import annotations

import os
import json
import csv
import time
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List

# Excel writer you prefer
from src.matrix.export_excel import save_excel

# Pipeline pieces
from src.io.loaders import pdf_to_pages
from src.preprocessing.segmenter import heading_aware_chunks

# DSPy + settings
import dspy
from src.config import settings

# Azure Blob
from azure.storage.blob import (
    BlobServiceClient,
    generate_blob_sas,
    BlobSasPermissions,
)


# ---------------------------------------------------
# Logging configuration
# ---------------------------------------------------
_LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, _LOG_LEVEL, logging.INFO),
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
log = logging.getLogger("main")

# Optional raw dumps of LLM outputs (already-parsed artifacts)
LOG_LLM = os.getenv("LOG_LLM", "0") in ("1", "true", "TRUE", "yes", "YES")
RAW_DIR = Path(os.getenv("RAW_DUMP_DIR", "raw_llm"))

# ---------------------------------------------------
# Simple serializers for tmp/combined JSON/CSV
# ---------------------------------------------------
def _save_json(items: List[Dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)

def _save_csv(items: List[Dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not items:
        headers = ["label", "category", "modality", "quote", "section",
                   "page_start", "page_end", "source", "confidence", "doc_name"]
    else:
        keys = set()
        for it in items:
            keys.update(it.keys())
        headers = sorted(keys)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=headers)
        w.writeheader()
        for it in items:
            w.writerow(it)

# ---------------------------------------------------
# DSPy init (force Azure for LiteLLM)
# ---------------------------------------------------
def _init_dspy_direct() -> None:
    """
    Configure DSPy/LiteLLM to use Azure OpenAI explicitly.
    Export the environment variables LiteLLM expects, then configure the LM.
    """
    # Normalize base (no trailing slash)
    base = (settings.azure_api_base or "").rstrip("/")

    # Export envs for LiteLLM
    os.environ["AZURE_API_KEY"] = settings.azure_api_key or ""
    os.environ["AZURE_API_BASE"] = base
    os.environ["AZURE_API_VERSION"] = settings.azure_api_version or "2024-12-01-preview"
    # Safety: some LiteLLM codepaths look at OPENAI_* even for Azure
    os.environ["OPENAI_API_KEY"] = settings.azure_api_key or ""

    # Model name in LiteLLM for Azure: "azure/<deployment>"
    azure_model = f"azure/{settings.azure_openai_deployment}"

    # Configure LM once per request
    lm = dspy.LM(
        model=azure_model,              # <-- force Azure provider via model prefix
        api_key=settings.azure_api_key, # (still pass it, but envs are canonical)
        api_base=f"{base}/openai/v1/",  # Azure OpenAI REST shape
        temperature=0.0,
        max_tokens=32700,
    )
    dspy.configure(lm=lm, adapter=dspy.JSONAdapter(), track_usage=False, cache=True)

    # Apply variant (optional) without importing run_experiment
    try:
        from src.experiments.config_variants import load_variant, apply_variant
        variant = load_variant()
        apply_variant(variant)
        log.info(
            "Applied variant and configured Azure LM: dep=%r base=%r version=%r",
            settings.azure_openai_deployment, base, settings.azure_api_version
        )
    except Exception as e:
        log.warning("Variant not applied (optional): %s", e)
        log.info(
            "Configured Azure LM: dep=%r base=%r version=%r",
            settings.azure_openai_deployment, base, settings.azure_api_version
        )

# ---------------------------------------------------
# Core DSPy pipeline (no preprocessing, no dedupe)
# ---------------------------------------------------
def run_dspy_pipeline(opportunity_id: str, input_pdfs: List[Path]) -> List[Dict[str, Any]]:
    """
    1) Initialize DSPy (Azure via LiteLLM).
    2) For each PDF:
        - pdf_to_pages
        - heading_aware_chunks
        - cap chunks by MAX_CHUNKS (default 40)
        - cap chunk text length by MAX_CHARS (default 8000)
        - Extractor -> Classifier -> Grounder
    3) Return flat list of raw requirement dicts (no dedupe).
    """
    _init_dspy_direct()

    # Import robust modules AFTER dspy.configure so Predict(...) binds correctly
    from src.extraction.modules import Extractor, Classifier, Grounder

    extractor = Extractor()
    classifier = Classifier()
    grounder   = Grounder()

    max_chunks = int(os.getenv("MAX_CHUNKS", "40"))
    max_chars  = int(os.getenv("MAX_CHARS", "8000"))

    results: List[Dict[str, Any]] = []

    for pdf_path in input_pdfs:
        log.info("Loading pages for: %s", pdf_path.name)
        t0 = time.perf_counter()
        pages = pdf_to_pages(str(pdf_path))
        t1 = time.perf_counter()
        log.info("Loaded %d pages in %.2fs from %s", len(pages), t1 - t0, pdf_path.name)

        chunks = list(heading_aware_chunks(pages))
        if max_chunks > 0:
            chunks = chunks[:max_chunks]
        log.info("Chunks selected for %s: %d (MAX_CHUNKS=%s)", pdf_path.name, len(chunks), max_chunks)

        # Extract
        all_extracted: List[Dict[str, Any]] = []
        for idx, chunk in enumerate(chunks, start=1):
            text = chunk.get("text", "") or ""
            if max_chars > 0 and len(text) > max_chars:
                chunk = dict(chunk)
                chunk["text"] = text[:max_chars] + "\n\n[TRUNCATED FOR LENGTH]"
            preview = (chunk.get("text") or "")[:160].replace("\n", " ")
            log.debug("[EXTRACT] %s chunk %d/%d len=%d preview=%r",
                      pdf_path.name, idx, len(chunks), len(chunk.get("text","")), preview)

            t_ex0 = time.perf_counter()
            reqs = extractor(chunk)  # robust parse + retries inside module
            t_ex1 = time.perf_counter()

            if LOG_LLM:
                RAW_DIR.mkdir(parents=True, exist_ok=True)
                (RAW_DIR / f"extract_{pdf_path.stem}_{idx:04d}.json").write_text(
                    json.dumps(reqs, ensure_ascii=False, indent=2), encoding="utf-8"
                )

            log.info("[EXTRACT] %s chunk %d -> %d reqs in %.2fs",
                     pdf_path.name, idx, len(reqs), t_ex1 - t_ex0)
            all_extracted.extend(reqs)

        # Classify
        classified_reqs: List[Dict[str, Any]] = []
        for i, r in enumerate(all_extracted, start=1):
            log.debug("[CLASSIFY] %s item %d/%d label=%r",
                      pdf_path.name, i, len(all_extracted), r.get("label","")[:80])
            t_c0 = time.perf_counter()
            cls = classifier(r)
            t_c1 = time.perf_counter()

            if LOG_LLM:
                (RAW_DIR / f"classify_{pdf_path.stem}_{i:04d}.json").write_text(
                    json.dumps(cls, ensure_ascii=False, indent=2), encoding="utf-8"
                )

            log.info("[CLASSIFY] %s item %d OK in %.2fs",
                     pdf_path.name, i, t_c1 - t_c0)
            classified_reqs.append(cls)

        # Ground
        grounded_reqs: List[Dict[str, Any]] = []
        for i, req in enumerate(classified_reqs, start=1):
            chunk_index = min((i-1) // 2, max(0, len(chunks) - 1))
            source_chunk = chunks[chunk_index]
            log.debug("[GROUND] %s item %d/%d -> chunk #%d",
                      pdf_path.name, i, len(classified_reqs), chunk_index + 1)

            t_g0 = time.perf_counter()
            grounded = grounder(source_chunk, req)  # robust parse + retries inside module
            t_g1 = time.perf_counter()

            if LOG_LLM:
                (RAW_DIR / f"ground_{pdf_path.stem}_{i:04d}.json").write_text(
                    json.dumps(grounded, ensure_ascii=False, indent=2), encoding="utf-8"
                )

            log.info("[GROUND] %s item %d OK in %.2fs", pdf_path.name, i, t_g1 - t_g0)

            grounded["doc_name"] = pdf_path.name
            grounded.setdefault("label", grounded.get("label", grounded.get("title", "")))
            grounded.setdefault("category", grounded.get("category", "Other"))
            grounded.setdefault("modality", grounded.get("modality", "UNKNOWN"))
            grounded.setdefault("quote", grounded.get("quote", ""))
            grounded.setdefault("section", grounded.get("section", ""))
            grounded.setdefault("page_start", grounded.get("page_start", ""))
            grounded.setdefault("page_end", grounded.get("page_end", ""))
            grounded.setdefault("source", grounded.get("source", "llm"))

            grounded_reqs.append(grounded)

        log.info("File %s done: extracted=%d classified=%d grounded=%d",
                 pdf_path.name, len(all_extracted), len(classified_reqs), len(grounded_reqs))

        results.extend(grounded_reqs)

    return results

# ---------------------------------------------------
# Azure Blob upload + SAS
# ---------------------------------------------------
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

# ---------------------------------------------------
# Public entry called by Streamlit
# ---------------------------------------------------
def process_opportunity(opportunity_id: str) -> str:
    """
    - Locate PDFs: data/inputs/<ID>/*.pdf if <ID> exists else data/inputs/*.pdf
    - Run DSPy pipeline (no preprocessing, no dedupe)
    - Save per-doc tmp (json/csv/xlsx) under tmp_outputs/
    - Save combined outputs under outputs/
    - Upload final XLSX to Azure Blob and return SAS URL
    """
    inputs_root = Path("data/inputs")
    specific_dir = inputs_root / opportunity_id if opportunity_id else None

    if specific_dir and specific_dir.exists():
        pdfs = sorted(specific_dir.glob("*.pdf"))
    else:
        pdfs = sorted(inputs_root.glob("*.pdf"))

    if not pdfs:
        raise FileNotFoundError(
            f"No PDFs found for opportunity '{opportunity_id}'. "
            f"Place files in data/inputs/{opportunity_id}/ or data/inputs/."
        )

    log.info("Processing %d PDF(s) for %s", len(pdfs), opportunity_id or "[default inputs]")

    combined_reqs = run_dspy_pipeline(opportunity_id, pdfs)

    # Save per-doc tmp artifacts
    tmp_dir = Path("tmp_outputs")
    tmp_dir.mkdir(parents=True, exist_ok=True)
    for p in pdfs:
        doc_items = [r for r in combined_reqs if r.get("doc_name") == p.name]
        base = f"{p.stem}.{opportunity_id or 'default'}"
        _save_json(doc_items, tmp_dir / f"{base}.requirements.json")
        _save_csv(doc_items, tmp_dir / f"{base}.matrix.csv")
        save_excel(doc_items, tmp_dir / f"{base}.matrix.xlsx")
        log.info("Saved tmp outputs for %s (%d rows)", p.name, len(doc_items))

    # Save combined artifacts
    out_dir = Path("outputs")
    out_dir.mkdir(parents=True, exist_ok=True)
    final_json = out_dir / f"{(opportunity_id or 'default')}.requirements.json"
    final_csv  = out_dir / f"{(opportunity_id or 'default')}.matrix.csv"
    final_xlsx = out_dir / f"{(opportunity_id or 'default')}.matrix.xlsx"

    _save_json(combined_reqs, final_json)
    _save_csv(combined_reqs, final_csv)
    save_excel(combined_reqs, final_xlsx)
    log.info("Final combined XLSX: %s (%d rows)", final_xlsx, len(combined_reqs))

    # Upload to Azure Blob + SAS
    conn_str = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
    container = os.getenv("AZURE_BLOB_CONTAINER")
    if not conn_str or not container:
        raise RuntimeError("Set AZURE_STORAGE_CONNECTION_STRING and AZURE_BLOB_CONTAINER env vars.")
    sas_url = _upload_blob_and_sas(final_xlsx, container, conn_str, sas_hours=1)
    log.info("Uploaded to blob & generated SAS URL.")
    return sas_url
