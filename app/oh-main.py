def import_from_highergov_and_process(opportunity_id: str, output_name: str = None) -> str:
    """
    Import files from HigherGov and process them through the pipeline.
    
    Args:
        opportunity_id: HigherGov or SAM.gov opportunity ID
        output_name: Custom name for output files (optional)
        
    Returns:
        SAS URL for downloading Excel compliance matrix
    """
    log.info("=" * 60)
    log.info("Importing files from HigherGov for: %s", opportunity_id)
    log.info("=" * 60)
    
    # Step 1: Download files from HigherGov
    try:
        files = ingest_highergov_opportunity(opportunity_id)
        log.info(
            "Downloaded %d file(s) from HigherGov: %s",
            len(files),
            [f.name for f in files]
        )
    except Exception as e:
        log.error(f"Failed to download from HigherGov: {e}")
        raise
    
    # Step 2: Process using existing pipeline
    log.info("Starting document processing pipeline...")
    try:
        sas_url = process_opportunity(opportunity_id, output_name=output_name)  # ← FIXED!
        log.info("Processing complete for HigherGov opportunity: %s", opportunity_id)
        return sas_url
    except Exception as e:
        log.error(f"Processing failed: {e}")
        raise