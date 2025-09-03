# src/io/loaders.py
from pypdf import PdfReader
from docx import Document

def pdf_to_pages(path: str) -> list[tuple[int,str]]:
    r = PdfReader(path)
    return [(i+1, p.extract_text() or "") for i, p in enumerate(r.pages)]

def docx_to_pages(path: str) -> list[tuple[int,str]]:
    doc = Document(path)
    # naive: treat each paragraph as “page 1”; for real DOCX, keep section/heading map
    text = "\n".join(p.text for p in doc.paragraphs)
    return [(1, text)]
