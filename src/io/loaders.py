# src/io/loaders.py
from pypdf import PdfReader
from docx import Document
from openpyxl import load_workbook

def pdf_to_pages(path: str) -> list[tuple[int,str]]:
    r = PdfReader(path)
    return [(i+1, p.extract_text() or "") for i, p in enumerate(r.pages)]

def docx_to_pages(path: str) -> list[tuple[int,str]]:
    """Extract text from DOCX - treats whole doc as 'page 1' for now"""
    doc = Document(path)
    
    # Extract all text from paragraphs and tables
    full_text = []
    
    # Get paragraph text
    for para in doc.paragraphs:
        if para.text.strip():
            full_text.append(para.text)
    
    # Get text from tables
    for table in doc.tables:
        for row in table.rows:
            row_text = [cell.text.strip() for cell in row.cells if cell.text.strip()]
            if row_text:
                full_text.append(" | ".join(row_text))
    
    combined_text = "\n".join(full_text)
    return [(1, combined_text)]

def xlsx_to_pages(path: str) -> list[tuple[int,str]]:
    """Extract text from Excel using only openpyxl"""
    wb = load_workbook(path, data_only=True)
    pages = []
    
    for sheet_num, sheet in enumerate(wb.worksheets, 1):
        rows = []
        for row in sheet.iter_rows(values_only=True):
            if any(row):  # Skip empty rows
                row_text = " | ".join(str(cell) if cell else "" for cell in row)
                rows.append(row_text)
        
        pages.append((sheet_num, "\n".join(rows)))
    
    return pages

def docx_to_pages(path: str) -> list[tuple[int,str]]:
    doc = Document(path)
    # naive: treat each paragraph as “page 1”; for real DOCX, keep section/heading map
    text = "\n".join(p.text for p in doc.paragraphs)
    return [(1, text)]
