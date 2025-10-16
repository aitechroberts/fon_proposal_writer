# src/io/ai_docint_enhanced.py
"""
Enhanced Azure Document Intelligence integration for government forms.
Handles structured forms, tables, checkboxes with better formatting.
"""

import os
import logging
from typing import List, Tuple, Dict, Any
from pathlib import Path


logger = logging.getLogger(__name__)


def _get_document_intelligence_client():
    """Lazy initialization of Azure Document Intelligence client."""
    from azure.ai.documentintelligence import DocumentIntelligenceClient
    from azure.core.credentials import AzureKeyCredential
    
    endpoint = os.getenv("DOCUMENTINTELLIGENCE_ENDPOINT")
    key = os.getenv("DOCUMENTINTELLIGENCE_API_KEY")
    
    if not endpoint or not key:
        raise RuntimeError(
            "Azure Document Intelligence not configured. Set:\n"
            "  DOCUMENTINTELLIGENCE_ENDPOINT=https://your-resource.cognitiveservices.azure.com/\n"
            "  DOCUMENTINTELLIGENCE_API_KEY=your-key"
        )
    
    client = DocumentIntelligenceClient(
        endpoint=endpoint,
        credential=AzureKeyCredential(key)
    )
    return client


def extract_structured_form(pdf_path: str, max_chunk_chars: int = 3000) -> List[Tuple[int, str]]:
    """
    Extract structured data from government forms using Document Intelligence.
    
    DI returns dense text (~6000 chars/page), so we chunk by characters
    while preserving table boundaries.

    Features:
    - Detects tables and preserves structure
    - Identifies checkboxes (checked/unchecked)
    - Extracts form fields (key-value pairs)
    - Maintains reading order
    - Handles multi-column layouts
    
    Returns:
        List of (page_num, formatted_text) tuples
    """
    client = _get_document_intelligence_client()
    
    logger.info(f"Starting Document Intelligence analysis: {Path(pdf_path).name}")
    
    # Read PDF
    with open(pdf_path, "rb") as f:
        pdf_data = f.read()
    
    # Start analysis (LRO - Long Running Operation)
    try:
        poller = client.begin_analyze_document(
            model_id="prebuilt-layout",
            body=pdf_data,
            content_type="application/pdf"
        )
    except Exception as e:
        logger.error(f"Failed to start Document Intelligence: {e}")
        raise RuntimeError(f"Document Intelligence failed: {e}")
    
    # Wait for completion
    logger.debug("Waiting for analysis to complete...")
    result = poller.result()
    logger.info("Document Intelligence analysis complete")
    
    if not result.pages:
        logger.warning("No pages found in result")
        return [(1, "[No content extracted]")]
    
    formatted_pages: List[Tuple[int, str]] = []
    for page_idx, page in enumerate(result.pages, start=1):
        page_text = _format_page_content(page, result, page_idx)
        formatted_pages.append((page_idx, page_text))
    
    logger.info(f"Extracted {len(formatted_pages)} pages from form")
    
    # Track usage for cost monitoring
    try:
        from .smart_loader import record_document_intelligence
        record_document_intelligence(len(formatted_pages))
    except ImportError:
        pass

    chunked_pages = []
    for page_num, page_text in formatted_pages:
        if len(page_text) <= max_chunk_chars:
            chunked_pages.append((page_num, page_text))
        else:
            # Split into chunks, preserving table boundaries
            chunks = _smart_chunk_text(page_text, max_chunk_chars)
            for i, chunk in enumerate(chunks):
                chunked_pages.append((page_num, chunk))
    return chunked_pages


def _format_page_content(page: Any, result: Any, page_num: int) -> str:
    """
    Format a single page's content with structure preservation.
    
    Order of content:
    1. Form fields (key-value pairs)
    2. Tables
    3. Paragraphs (reading order)
    4. Selection marks (checkboxes)
    """
    sections = []
    
    # Extract form fields
    fields = _extract_form_fields(result, page_num)
    if fields:
        sections.append("[FORM FIELDS]")
        for key, value in fields.items():
            sections.append(f"{key}: {value}")
        sections.append("")
    
    # Extract tables
    tables = _extract_tables(result, page_num)
    if tables:
        for table_text in tables:
            sections.append("[TABLE]")
            sections.append(table_text)
            sections.append("[/TABLE]")
            sections.append("")
    
    # Extract paragraphs in reading order
    paragraphs = _extract_paragraphs(result, page_num)
    if paragraphs:
        sections.extend(paragraphs)
    
    # Extract checkboxes
    checkboxes = _extract_selection_marks(page)
    if checkboxes:
        sections.append("")
        sections.append("[CHECKBOXES]")
        for checkbox_text in checkboxes:
            sections.append(checkbox_text)
        sections.append("")
    
    return "\n".join(sections)

def _smart_chunk_text(text: str, max_chars: int) -> List[str]:
    """
    Intelligently chunk text while preserving structure.
    
    Strategy:
    - Never split tables (keep [TABLE]...[/TABLE] together)
    - Never split form fields section
    - Try to break at double newlines (paragraphs)
    - Preserve section markers
    - Add overlap for context
    
    Args:
        text: Text to chunk
        max_chars: Maximum characters per chunk
        
    Returns:
        List of text chunks
    """
    # If text is already small enough, return as-is
    if len(text) <= max_chars:
        return [text]
    
    chunks = []
    current_chunk = []
    current_length = 0
    overlap_lines = 2  # Keep last 2 lines for context
    
    # Split into logical sections
    lines = text.split('\n')
    i = 0
    
    while i < len(lines):
        line = lines[i]
        
        # Detect table boundaries
        if line.strip() == "[TABLE]":
            # Find matching [/TABLE]
            table_end = i + 1
            while table_end < len(lines) and lines[table_end].strip() != "[/TABLE]":
                table_end += 1
            
            # Get entire table
            table_lines = lines[i:table_end + 1]
            table_text = '\n'.join(table_lines)
            table_length = len(table_text)
            
            # If table alone exceeds max_chars, keep it anyway (don't split tables)
            if table_length > max_chars:
                # If current chunk has content, save it first
                if current_chunk:
                    chunks.append('\n'.join(current_chunk))
                    current_chunk = []
                    current_length = 0
                
                # Add table as its own chunk
                chunks.append(table_text)
                i = table_end + 1
                continue
            
            # If adding table would exceed limit, save current chunk
            if current_length + table_length > max_chars and current_chunk:
                chunks.append('\n'.join(current_chunk))
                # Keep last few lines for overlap
                current_chunk = current_chunk[-overlap_lines:] if len(current_chunk) > overlap_lines else []
                current_length = sum(len(l) for l in current_chunk)
            
            # Add table to current chunk
            current_chunk.extend(table_lines)
            current_length += table_length
            i = table_end + 1
            continue
        
        # Detect form fields section
        if line.strip() == "[FORM FIELDS]":
            # Find end of form fields (next blank line or section marker)
            fields_end = i + 1
            while fields_end < len(lines) and lines[fields_end].strip() and not lines[fields_end].startswith('['):
                fields_end += 1
            
            fields_lines = lines[i:fields_end]
            fields_text = '\n'.join(fields_lines)
            fields_length = len(fields_text)
            
            # If adding fields would exceed limit, save current chunk
            if current_length + fields_length > max_chars and current_chunk:
                chunks.append('\n'.join(current_chunk))
                current_chunk = current_chunk[-overlap_lines:] if len(current_chunk) > overlap_lines else []
                current_length = sum(len(l) for l in current_chunk)
            
            # Add fields to current chunk
            current_chunk.extend(fields_lines)
            current_length += fields_length
            i = fields_end
            continue
        
        # Regular line processing
        line_length = len(line) + 1  # +1 for newline
        
        # If adding this line exceeds limit, save current chunk
        if current_length + line_length > max_chars and current_chunk:
            chunks.append('\n'.join(current_chunk))
            # Keep last few lines for overlap
            current_chunk = current_chunk[-overlap_lines:] if len(current_chunk) > overlap_lines else []
            current_length = sum(len(l) + 1 for l in current_chunk)
        
        # Add line to current chunk
        current_chunk.append(line)
        current_length += line_length
        i += 1
    
    # Add final chunk
    if current_chunk:
        chunks.append('\n'.join(current_chunk))
    
    return chunks

def _extract_form_fields(result: Any, page_num: int) -> Dict[str, str]:
    """Extract key-value pairs from form fields."""
    fields = {}
    
    if not hasattr(result, 'key_value_pairs') or not result.key_value_pairs:
        return fields
    
    for kv in result.key_value_pairs:
        # Check if field is on this page
        if hasattr(kv, 'key') and hasattr(kv.key, 'bounding_regions'):
            if kv.key.bounding_regions and kv.key.bounding_regions[0].page_number == page_num:
                key = kv.key.content if hasattr(kv.key, 'content') else ""
                value = kv.value.content if hasattr(kv, 'value') and hasattr(kv.value, 'content') else ""
                
                if key and value:
                    fields[key.strip()] = value.strip()
    
    return fields


def _extract_tables(result: Any, page_num: int) -> List[str]:
    """Extract and format tables."""
    tables = []
    
    if not hasattr(result, 'tables') or not result.tables:
        return tables
    
    for table in result.tables:
        # Check if table is on this page
        if table.bounding_regions and table.bounding_regions[0].page_number != page_num:
            continue
        
        # Build table as 2D array
        max_row = max(cell.row_index for cell in table.cells) + 1
        max_col = max(cell.column_index for cell in table.cells) + 1
        
        grid = [["" for _ in range(max_col)] for _ in range(max_row)]
        
        for cell in table.cells:
            content = cell.content or ""
            grid[cell.row_index][cell.column_index] = content
        
        # Format as text table
        formatted_rows = []
        for row in grid:
            formatted_rows.append(" | ".join(str(cell) for cell in row))
        
        tables.append("\n".join(formatted_rows))
    
    return tables


def _extract_paragraphs(result: Any, page_num: int) -> List[str]:
    """Extract paragraphs in reading order."""
    paragraphs = []
    
    if not hasattr(result, 'paragraphs') or not result.paragraphs:
        return paragraphs
    
    for para in result.paragraphs:
        # Check if paragraph is on this page
        if para.bounding_regions and para.bounding_regions[0].page_number == page_num:
            content = para.content or ""
            if content.strip():
                paragraphs.append(content.strip())
    
    return paragraphs


def _extract_selection_marks(page: Any) -> List[str]:
    """Extract checkbox states."""
    checkboxes = []
    
    if not hasattr(page, 'selection_marks') or not page.selection_marks:
        return checkboxes
    
    for mark in page.selection_marks:
        state = "☑" if mark.state == "selected" else "☐"
        # Try to get nearby text as context (simplified)
        checkboxes.append(f"{state} Checkbox at ({mark.polygon[0]}, {mark.polygon[1]})")
    
    return checkboxes


def extract_tables_only(pdf_path: str) -> List[Dict[str, Any]]:
    """
    Extract only tables from document (for pricing sheets, etc.).
    
    Returns list of table dictionaries with:
    - page: page number
    - rows: list of lists (table data)
    - row_count: number of rows
    - column_count: number of columns
    """
    client = _get_document_intelligence_client()
    
    with open(pdf_path, "rb") as f:
        poller = client.begin_analyze_document("prebuilt-layout", analyze_request=f.read())
    
    result = poller.result()
    
    extracted_tables = []
    
    if result.tables:
        for table in result.tables:
            max_row = max(cell.row_index for cell in table.cells) + 1
            max_col = max(cell.column_index for cell in table.cells) + 1
            
            grid = [["" for _ in range(max_col)] for _ in range(max_row)]
            
            for cell in table.cells:
                grid[cell.row_index][cell.column_index] = cell.content or ""
            
            extracted_tables.append({
                "page": table.bounding_regions[0].page_number if table.bounding_regions else 0,
                "rows": grid,
                "row_count": max_row,
                "column_count": max_col
            })
    
    logger.info(f"Extracted {len(extracted_tables)} tables")
    return extracted_tables


def estimate_document_intelligence_cost(num_pages: int) -> float:
    """
    Estimate Azure Document Intelligence cost.
    
    Pricing: $1.50 per 1000 pages (as of 2025)
    """
    return (num_pages / 1000) * 1.50

