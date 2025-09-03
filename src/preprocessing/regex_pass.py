import regex as re

DEADLINE_RX       = re.compile(r"\b(due|submit(?:ted)?|deadline)\b.*?(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})", re.I | re.S)
EVAL_CRITERIA_RX  = re.compile(r"\b(evaluation|scoring|weight(?:ed|ing))\b.*?(\d+\s*(?:points?|%|percent))", re.I | re.S)
CERTIFICATION_RX  = re.compile(r"\b(certif(?:y|ication)|attest|ISO\s*\d{3,5}|CMMI|FedRAMP|SOC\s*2)\b", re.I)

EXTRA_PATTERNS = [
    (DEADLINE_RX,      "deadline"),
    (EVAL_CRITERIA_RX, "eval_criteria"),
    (CERTIFICATION_RX, "certification"),
]

def fast_hits(chunk: dict):
    # keep your existing patterns, then include:
    matches = []
    text = chunk["text"]
    for rx, kind in EXTRA_PATTERNS:
        for m in rx.finditer(text):
            matches.append({
                "kind": kind,
                "match": m.group(0).strip(),
                "section": chunk["section"],
                "start_page": chunk["start_page"],
                "end_page": chunk["end_page"],
                "source": "regex",
            })
    # ...plus your earlier matches; set confidence in step 5 below
    return matches
