# src/preprocessing/segmenter.py
import re
from typing import Iterable, List, Tuple, Dict, Optional

Heading = Dict[str, str]

# Broader heading detector: allows (), /, &, :, , and typical numeric schemes.
HEADING_RX = re.compile(
    r"""
    ^\s*
    (?:
        (?:(?:Section|Sec\.|§)\s+)?                 # optional "Section" label
        (?P<num>\d+(?:\.\d+){0,3})?                 # optional dotted number like 3, 3.1, 3.8.1.2
        [\s\-:/.]*
    )?
    (?P<title>[A-Z][A-Za-z0-9()&/\- ,.:]{2,})       # title starting with a letter, reasonably short line
    \s*$
    """,
    re.X | re.M
)

def _is_heading_line(line: str) -> Optional[str]:
    """Return the cleaned heading text if line looks like a heading; else None."""
    line = line.strip()
    if not line:
        return None
    m = HEADING_RX.match(line)
    if not m:
        return None

    # Heuristics to avoid shouting normal sentences:
    # - short-ish lines
    # - or has a dotted number, or begins with 'Section/Sec./§', or is mostly uppercase.
    title = m.group("title") or ""
    num   = m.group("num")
    short_enough = len(line) <= 120
    mostly_caps  = sum(ch.isupper() for ch in line if ch.isalpha()) >= 0.6 * sum(1 for ch in line if ch.isalpha())

    if num or line.lstrip().startswith(("Section", "Sec.", "§")) or mostly_caps or short_enough:
        return line
    return None


def heading_aware_chunks(
    pages: List[Tuple[int, str]],
    max_chars: int = 6000,
    overlap: int = 600
) -> Iterable[Dict]:
    """
    Yield dicts with text, start_page, end_page, and section.
    - Splits at headings when encountered.
    - Also enforces max_chars with soft breaks.
    - Maintains correct page spans through overlaps.
    """
    buf: str = ""
    buf_start_page: Optional[int] = None
    buf_end_page: Optional[int] = None
    current_section: str = "Unknown"

    def flush():
        nonlocal buf, buf_start_page, buf_end_page, current_section
        if buf and buf_start_page is not None and buf_end_page is not None:
            out = {
                "text": buf,
                "start_page": buf_start_page,
                "end_page": buf_end_page,
                "section": current_section
            }
            yield out

    for page_no, raw_text in pages:
        # Normalize line endings and collapse excessive blank lines
        text = raw_text.replace("\r\n", "\n").replace("\r", "\n")
        # Process line-by-line so headings can trigger boundaries mid-page
        for line in text.split("\n"):
            heading = _is_heading_line(line)

            if heading:
                # Start a new chunk at this heading
                if buf:
                    # Flush the chunk up to the previous line
                    for out in flush():
                        yield out
                    # Set overlap *within the same page*; it's safe to mark the new start_page as current page
                    buf = buf[-overlap:] if overlap > 0 else ""
                    buf_start_page = page_no if buf else None
                    buf_end_page = page_no if buf else None

                current_section = heading
                # Heading line itself should belong to the new chunk
                if not buf:
                    buf = heading
                    buf_start_page = page_no
                    buf_end_page = page_no
                else:
                    buf += "\n" + heading
                    buf_end_page = page_no
                continue

            # Not a heading: append the line
            if not buf:
                buf = line
                buf_start_page = page_no
                buf_end_page = page_no
            else:
                buf += "\n" + line
                buf_end_page = page_no

            # Enforce max size with a soft cut (prefer paragraph boundary if possible)
            if len(buf) >= max_chars:
                # try to cut at last blank line or sentence end
                cut_at = max(buf.rfind("\n\n", 0, max_chars), buf.rfind(". ", 0, max_chars))
                if cut_at < max_chars * 0.5:
                    cut_at = max_chars  # no good soft break; hard cut

                chunk_text = buf[:cut_at].rstrip()
                tail = buf[cut_at:].lstrip("\n")

                # Flush the chunk
                if chunk_text:
                    out = {
                        "text": chunk_text,
                        "start_page": buf_start_page,
                        "end_page": buf_end_page,  # conservative: content flowed to current page
                        "section": current_section
                    }
                    yield out

                # Prepare next buffer with overlap from the tail
                keep = ((chunk_text[-overlap:] if overlap > 0 else "") + tail).lstrip("\n")
                buf = keep
                # Since the carried text is from the *current* page, reset start to current page
                buf_start_page = page_no if buf else None
                buf_end_page = page_no if buf else None

    # Final flush
    if buf and buf_start_page is not None and buf_end_page is not None:
        yield {
            "text": buf,
            "start_page": buf_start_page,
            "end_page": buf_end_page,
            "section": current_section
        }
