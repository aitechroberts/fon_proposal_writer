def process_opportunity(opportunity_id: str, output_name: str = None) -> str:
    """
    Process opportunity and generate compliance matrix.
    
    Args:
        opportunity_id: The opportunity ID (used for input folder)
        output_name: Custom name for output files (optional, defaults to opportunity_id)
    
    Returns:
        SAS URL for downloading the Excel file
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

    # Use custom output_name if provided, otherwise fall back to opportunity_id
    file_base_name = output_name or opportunity_id or 'default'
    
    # Sanitize filename (remove invalid characters)
    import re
    file_base_name = re.sub(r'[^\w\s-]', '', file_base_name).strip()
    file_base_name = re.sub(r'[-\s]+', '-', file_base_name)

    # per-doc tmp outputs (still using opportunity_id for organization)
    tmp_dir = Path("tmp_outputs"); tmp_dir.mkdir(parents=True, exist_ok=True)
    for p in pdfs:
        doc_items = [r for r in combined_reqs if r.get("doc_name") == p.name]
        base = f"{p.stem}.{opportunity_id or 'default'}"
        _save_json(doc_items, tmp_dir / f"{base}.requirements.json")
        _save_csv(doc_items,  tmp_dir / f"{base}.matrix.csv")
        save_excel(doc_items, tmp_dir / f"{base}.matrix.xlsx")
        log.info("Saved tmp outputs for %s (%d rows)", p.name, len(doc_items))

    # Final combined outputs using custom filename
    out_dir = Path("outputs"); out_dir.mkdir(parents=True, exist_ok=True)
    final_json = out_dir / f"{file_base_name}.requirements.json"
    final_csv  = out_dir / f"{file_base_name}.matrix.csv"
    final_xlsx = out_dir / f"{file_base_name}.matrix.xlsx"

    _save_json(combined_reqs, final_json)
    log.info(f"Saved {final_json}")
    _save_csv(combined_reqs,  final_csv)
    log.info(f"Saved {final_csv}")
    try:
        save_excel(combined_reqs, final_xlsx)
        log.info("Final combined XLSX: %s (%d rows)", final_xlsx, len(combined_reqs))
    except Exception as e:
        log.error(f"Failed to save final XLSX: {e}")
        raise

    # Upload to blob storage
    conn_str = settings.azure_storage_connection_string
    container = settings.azure_blob_container
    if not conn_str or not container:
        raise RuntimeError("Set AZURE_STORAGE_CONNECTION_STRING and AZURE_BLOB_CONTAINER in .env file.")
    
    sas_url = _upload_blob_and_sas(final_xlsx, container, conn_str, sas_hours=1)
    log.info("Uploaded to blob & generated SAS URL.")
    
    # Cleanup local files after successful upload
    _cleanup_outputs()
    
    return sas_url