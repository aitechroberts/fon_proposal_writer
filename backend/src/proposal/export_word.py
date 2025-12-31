# backend/src/proposal/export_word.py
"""
Word document export utility for proposal generation.

Exports proposal sections to a properly formatted Word document with:
- Part headings in Heading 1 style
- Section headings (category names) in Heading 2 style
- Content in Normal style with 12pt Times New Roman font
- Proper newline separators between sections

Supports two output modes:
- Cited proposal: Original with citations in [brackets]
- Clean proposal: Citations removed using regex
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import List, Dict, Any, Union

from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.style import WD_STYLE_TYPE

logger = logging.getLogger(__name__)

PathLike = Union[str, Path]


def strip_citations(text: str) -> str:
    """
    Remove all bracketed citations from text.
    
    Citations are text within square brackets, e.g., [Section 3.2] or [Page 5].
    This function removes them for clean proposal output.
    
    Args:
        text: Input text potentially containing citations
        
    Returns:
        Text with all [...] citations removed
        
    Examples:
        >>> strip_citations("We will comply [Section 3.2] with requirements.")
        "We will comply  with requirements."
        >>> strip_citations("The approach [Page 5] ensures [Ref 1] success.")
        "The approach  ensures  success."
    """
    if not text:
        return text
    
    # Remove all content within square brackets, including the brackets
    # Pattern matches [...] where ... can be any characters except newlines
    cleaned = re.sub(r'\[[^\]]*\]', '', text)
    
    # Clean up any double spaces that may result from removal
    cleaned = re.sub(r'  +', ' ', cleaned)
    
    return cleaned.strip()


def _configure_normal_style(doc: Document) -> None:
    """Configure the Normal style for body text."""
    style = doc.styles["Normal"]
    font = style.font
    font.name = "Times New Roman"
    font.size = Pt(12)
    
    # Paragraph formatting
    para_format = style.paragraph_format
    para_format.space_after = Pt(12)
    para_format.line_spacing = 1.15


def _configure_heading_styles(doc: Document) -> None:
    """Configure heading styles for parts and sections."""
    # Heading 1 - Part headings
    h1 = doc.styles["Heading 1"]
    h1.font.name = "Times New Roman"
    h1.font.size = Pt(16)
    h1.font.bold = True
    h1.paragraph_format.space_before = Pt(24)
    h1.paragraph_format.space_after = Pt(12)
    
    # Heading 2 - Section/Category headings  
    h2 = doc.styles["Heading 2"]
    h2.font.name = "Times New Roman"
    h2.font.size = Pt(14)
    h2.font.bold = True
    h2.paragraph_format.space_before = Pt(18)
    h2.paragraph_format.space_after = Pt(6)


def export_proposal_to_word(
    sections: List[Dict[str, Any]],
    path: PathLike,
    title: str = "Technical Proposal"
) -> Path:
    """
    Export proposal sections to a Word document.
    
    Args:
        sections: List of section dicts with keys:
            - part: Part name (e.g., "Part 1: The Promise (BLUF)")
            - category: Category name (e.g., "Technical Approach & Capability")
            - content: Section content text
        path: Output file path
        title: Optional document title for header
        
    Returns:
        Path to the generated Word document
    """
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Exporting proposal to Word: {out_path}")
    
    # Create document
    doc = Document()
    
    # Configure styles
    _configure_normal_style(doc)
    _configure_heading_styles(doc)
    
    # Add title
    title_para = doc.add_heading(title, level=0)
    title_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    # Track current part to add part headings
    current_part = None
    
    for section in sections:
        part = section.get("part", "")
        category = section.get("category", "Unknown Section")
        content = section.get("content", "")
        
        # Add part heading if changed
        if part and part != current_part:
            doc.add_heading(part, level=1)
            current_part = part
        
        # Add section heading (category name)
        doc.add_heading(category, level=2)
        
        # Add content
        if content:
            # Split content into paragraphs and add each
            paragraphs = content.split("\n\n")
            for para_text in paragraphs:
                para_text = para_text.strip()
                if para_text:
                    # Handle single newlines within paragraphs
                    para_text = para_text.replace("\n", " ")
                    para = doc.add_paragraph(para_text)
                    para.style = doc.styles["Normal"]
        else:
            # Add placeholder if no content
            para = doc.add_paragraph("[Content to be developed]")
            para.style = doc.styles["Normal"]
    
    # Save document
    doc.save(out_path)
    
    logger.info(f"Proposal exported successfully: {len(sections)} sections")
    return out_path


def export_clean_proposal_to_word(
    sections: List[Dict[str, Any]],
    path: PathLike,
    title: str = "Technical Proposal"
) -> Path:
    """
    Export proposal sections to a Word document with citations removed.
    
    This is the "clean" version of the proposal suitable for final submission.
    All text within square brackets [like this] is removed.
    
    Args:
        sections: List of section dicts with keys:
            - part: Part name (e.g., "Part 1: The Promise (BLUF)")
            - category: Category name (e.g., "Technical Approach & Capability")
            - content: Section content text (may contain citations)
        path: Output file path
        title: Optional document title for header
        
    Returns:
        Path to the generated Word document
    """
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Exporting clean proposal (citations removed) to Word: {out_path}")
    
    # Create document
    doc = Document()
    
    # Configure styles
    _configure_normal_style(doc)
    _configure_heading_styles(doc)
    
    # Add title
    title_para = doc.add_heading(title, level=0)
    title_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    # Track current part to add part headings
    current_part = None
    
    for section in sections:
        part = section.get("part", "")
        category = section.get("category", "Unknown Section")
        content = section.get("content", "")
        
        # Add part heading if changed
        if part and part != current_part:
            doc.add_heading(part, level=1)
            current_part = part
        
        # Add section heading (category name)
        doc.add_heading(category, level=2)
        
        # Add content WITH CITATIONS STRIPPED
        if content:
            # Remove citations from content
            clean_content = strip_citations(content)
            
            # Split content into paragraphs and add each
            paragraphs = clean_content.split("\n\n")
            for para_text in paragraphs:
                para_text = para_text.strip()
                if para_text:
                    # Handle single newlines within paragraphs
                    para_text = para_text.replace("\n", " ")
                    para = doc.add_paragraph(para_text)
                    para.style = doc.styles["Normal"]
        else:
            # Add placeholder if no content
            para = doc.add_paragraph("[Content to be developed]")
            para.style = doc.styles["Normal"]
    
    # Save document
    doc.save(out_path)
    
    logger.info(f"Clean proposal exported successfully: {len(sections)} sections")
    return out_path


def export_proposal_from_text(
    text_content: str,
    path: PathLike,
    title: str = "Technical Proposal"
) -> Path:
    """
    Export a plain text proposal to Word document.
    
    This parses a text document with section markers and converts to Word.
    Expected format:
        ============================================================
        Part 1: The Promise (BLUF)
        ============================================================
        
        ----------------------------------------
        Technical Approach & Capability
        ----------------------------------------
        
        [content...]
    
    Args:
        text_content: Plain text proposal with section markers
        path: Output file path
        title: Optional document title
        
    Returns:
        Path to the generated Word document
    """
    # Parse the text content into sections
    sections: List[Dict[str, Any]] = []
    current_part = ""
    current_category = ""
    content_lines: List[str] = []
    
    lines = text_content.split("\n")
    i = 0
    
    while i < len(lines):
        line = lines[i].strip()
        
        # Check for part heading (preceded by ===)
        if line.startswith("=") and len(line) > 10:
            # Save previous section if exists
            if current_category and content_lines:
                sections.append({
                    "part": current_part,
                    "category": current_category,
                    "content": "\n".join(content_lines).strip()
                })
                content_lines = []
            
            # Get part name from next non-empty line
            i += 1
            while i < len(lines) and not lines[i].strip():
                i += 1
            if i < len(lines) and not lines[i].strip().startswith("="):
                current_part = lines[i].strip()
            i += 1
            
        # Check for section heading (preceded by ---)
        elif line.startswith("-") and len(line) > 10:
            # Save previous section if exists
            if current_category and content_lines:
                sections.append({
                    "part": current_part,
                    "category": current_category,
                    "content": "\n".join(content_lines).strip()
                })
                content_lines = []
            
            # Get category name from next non-empty line
            i += 1
            while i < len(lines) and not lines[i].strip():
                i += 1
            if i < len(lines) and not lines[i].strip().startswith("-"):
                current_category = lines[i].strip()
            i += 1
            
        else:
            # Content line
            if current_category:
                content_lines.append(lines[i])
            i += 1
    
    # Save last section
    if current_category and content_lines:
        sections.append({
            "part": current_part,
            "category": current_category,
            "content": "\n".join(content_lines).strip()
        })
    
    return export_proposal_to_word(sections, path, title)


def sections_to_text(sections: List[Dict[str, Any]]) -> str:
    """
    Convert structured sections to plain text format.
    
    Args:
        sections: List of section dicts
        
    Returns:
        Plain text string with section markers
    """
    lines: List[str] = []
    current_part = None
    
    for section in sections:
        part = section.get("part", "")
        category = section.get("category", "")
        content = section.get("content", "")
        
        # Add part heading if changed
        if part and part != current_part:
            if current_part is not None:
                lines.append("")  # Separator between parts
            lines.append("=" * 60)
            lines.append(part)
            lines.append("=" * 60)
            lines.append("")
            current_part = part
        
        # Add section
        lines.append("-" * 40)
        lines.append(category)
        lines.append("-" * 40)
        lines.append("")
        lines.append(content)
        lines.append("")
    
    return "\n".join(lines)
