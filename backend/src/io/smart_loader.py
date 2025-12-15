# src/io/smart_loader.py
"""
Simplified intelligent document loader with binary routing:
- Standard documents → pypdf/python-docx/openpyxl (free, fast)
- Government forms → Azure Document Intelligence (accurate, structured)
"""

import logging
from pathlib import Path
from typing import List, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)


def detect_is_government_form(pages: List[Tuple[int, str]], file_path: str) -> bool:
    """
    Detect if document is a government form requiring structured extraction.
    
    Returns:
        True if government form, False if standard document
    """
    # Combine first 3 pages for analysis
    sample_text = " ".join(text for _, text in pages[:3]).lower()
    char_count = len(sample_text.strip())
    name = Path(file_path).name.lower()

    logger.debug(f"Analyzing {Path(file_path).name}: {char_count} chars extracted")
    
    # PRIORITY 1: Poor extraction = likely scanned form
    if char_count < 100:
        logger.info(f"Detected FORM (poor extraction, likely scanned): {char_count} chars")
        return True
    
    # PRIORITY 2: Government form keyword detection
    form_indicators = ["form","dd form", "dd", "sf form", "sf", "gs", "omb"]
    lowered_file = [part.lower() for part in name.split()]
    matches = [indicator for indicator in form_indicators if indicator in lowered_file or indicator in sample_text]
    
    # Decision threshold: 1+ matches = form
    if len(matches) >= 1:
        logger.info(f"Detected FORM Gov from {matches}")
        return True
    
    # Default: standard document
    logger.info(f"Detected STANDARD document")
    return False


def load_document_smart(file_path: str) -> List[Tuple[int, str]]:
    """
    Smart document loader with binary routing.
    
    Process:
    1. Try standard extraction (pypdf/docx/xlsx)
    2. Detect if it's a government form
    3. If form → use Azure Document Intelligence
    4. If standard → return standard extraction
    
    Returns:
        List of (page_num, text) tuples
    """
    path = Path(file_path)
    suffix = path.suffix.lower()
    
    logger.info(f"Loading document: {path.name}")
    
    # Step 1: Try standard extraction
    try:
        if suffix == '.pdf':
            from .loaders import pdf_to_pages
            pages = pdf_to_pages(file_path)
        elif suffix in ['.docx', '.doc']:
            from .loaders import docx_to_pages
            pages = docx_to_pages(file_path)
        elif suffix in ['.xlsx', '.xls']:
            from .loaders import excel_to_pages
            pages = excel_to_pages(file_path)
        else:
            raise ValueError(f"Unsupported file type: {suffix}")
    except Exception as e:
        logger.error(f"Standard extraction failed: {e}")
        return [(1, f"[Extraction failed: {e}]")]
    
    # Step 2: Detect if it's a government form (only for PDFs)
    if suffix == '.pdf':
        is_form = detect_is_government_form(pages, file_path)
        
        if is_form:
            # Step 3: Route to Document Intelligence
            logger.info("→ Routing to Azure Document Intelligence")
            try:
                from .ai_docint_enhanced import extract_structured_form
                pages = extract_structured_form(file_path)
                logger.info(f"✓ Document Intelligence extracted {len(pages)} pages")
            except Exception as e:
                logger.error(f"Document Intelligence failed: {e}")
                logger.warning("→ Falling back to standard extraction")
                # Keep standard extraction result as fallback
                record_document_intelligence(len(pages))
    # Step 4: Return extraction (either standard or Document Intelligence)
    record_standard()
    logger.info(f"✓ Loaded {len(pages)} pages from {path.name}")
    return pages


# ============= Statistics Tracking =============

class ExtractionStats:
    """Track extraction method usage for cost monitoring."""
    
    def __init__(self):
        self.standard_count = 0
        self.document_intelligence_count = 0
        self.total_pages_di = 0
    
    def record_standard(self):
        self.standard_count += 1
    
    def record_document_intelligence(self, pages: int):
        self.document_intelligence_count += 1
        self.total_pages_di += pages
    
    def summary(self) -> str:
        total = self.standard_count + self.document_intelligence_count
        if total == 0:
            return "No documents processed"
        
        di_cost = (self.total_pages_di / 1000) * 1.50
        
        lines = [
            "Extraction Statistics:",
            f"  Standard (free): {self.standard_count} documents",
            f"  Document Intelligence: {self.document_intelligence_count} documents ({self.total_pages_di} pages)",
            f"  Estimated Azure DI cost: ${di_cost:.4f}"
        ]
        return "\n".join(lines)


# Global stats tracker
_stats = ExtractionStats()


def record_standard():
    """Record a standard extraction."""
    _stats.record_standard()


def record_document_intelligence(pages: int):
    """Record a Document Intelligence extraction."""
    _stats.record_document_intelligence(pages)


def get_extraction_stats() -> str:
    """Get summary of extraction statistics."""
    return _stats.summary()