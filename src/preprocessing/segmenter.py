# src/preprocessing/segmenter.py
import re
from typing import Iterable

def heading_aware_chunks(pages: list[tuple[int,str]], max_chars=6000, overlap=600) -> Iterable[dict]:
    """
    Returns chunks with page spans + a 'section' (best-guess from headings).
    """
    buf, start_page, last_section = "", None, "Unknown"
    heading_rx = re.compile(r"^\s*(Section|Sec\.|§)?\s*[A-Z0-9][\w\-\. ]{0,80}$", re.M)

    for page, text in pages:
        if start_page is None:
            start_page = page
        # capture last seen heading to carry into chunk
        m = list(heading_rx.finditer(text))
        if m:
            last_section = m[-1].group(0).strip()
        for para in text.split("\n\n"):
            if len(buf) + len(para) > max_chars and buf:
                yield {"text": buf, "start_page": start_page, "end_page": page, "section": last_section}
                buf = buf[-overlap:]  # simple overlap
                start_page = page
            buf += ("\n\n" + para)
    if buf:
        yield {"text": buf, "start_page": start_page or 1, "end_page": pages[-1][0], "section": last_section}
