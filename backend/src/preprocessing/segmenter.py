# src/preprocessing/segmenter.py
import re
from typing import Iterable, List, Tuple, Dict, Optional

def heading_aware_chunks(
    pages: List[Tuple[int, str]],
    max_chars: int = 6000,
    overlap: int = 600
) -> Iterable[Dict]:
    """
    Yield chunks based on page boundaries, only splitting pages if they exceed max_chars.
    Each chunk will be roughly one page unless the page is too long.
    """
    
    for page_num, page_text in pages:
        # If page is within size limit, yield it as a single chunk
        if len(page_text) <= max_chars:
            yield {
                "text": page_text,
                "start_page": page_num,
                "end_page": page_num,
                "section": f"Page {page_num}"
            }
        else:
            # Page is too long, split it into smaller chunks
            # Try to split at paragraph boundaries
            chunks_from_page = []
            current_chunk = ""
            
            paragraphs = page_text.split("\n\n")
            
            for para in paragraphs:
                if len(current_chunk) + len(para) + 2 > max_chars and current_chunk:
                    # Yield current chunk
                    chunks_from_page.append(current_chunk)
                    # Start new chunk with overlap
                    current_chunk = current_chunk[-overlap:] if overlap > 0 else ""
                
                if current_chunk:
                    current_chunk += "\n\n" + para
                else:
                    current_chunk = para
            
            # Add final chunk if any
            if current_chunk:
                chunks_from_page.append(current_chunk)
            
            # Yield all chunks from this page
            for i, chunk_text in enumerate(chunks_from_page):
                yield {
                    "text": chunk_text,
                    "start_page": page_num,
                    "end_page": page_num,
                    "section": f"Page {page_num}" if len(chunks_from_page) == 1 
                              else f"Page {page_num} (part {i+1}/{len(chunks_from_page)})"
                }