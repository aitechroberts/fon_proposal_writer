# src/extraction/merge_dedupe.py
import re, hashlib
from typing import Dict, List, Tuple
from rapidfuzz import fuzz

def _norm_text(s: str) -> str:
    s = s.lower().strip()
    s = re.sub(r'\b(shall|must|will|should|may)\b', 'must', s)          # modality unify
    s = re.sub(r'\b(?:cover\\s*letter|cl)\b', 'cover letter', s)        # common aliases
    s = re.sub(r'\\s+', ' ', s)
    s = re.sub(r'(\\d{1,2})\\s*(am|pm)\\s*(et)?', r'\\1\\2', s)          # simplify times
    return s

def _core(req: Dict) -> str:
    label = _norm_text(req.get("label",""))
    quote = _norm_text(req.get("quote",""))
    # strip boilerplate fragments typical in RFPs
    quote = re.sub(r'^(?:quoters?|offerors?)\\s+must\\s+', '', quote)
    return (label + " — " + quote).strip()

def _canon_key(req: Dict) -> str:
    core = _core(req)
    cat  = (req.get("category") or "").lower()
    return hashlib.sha1(f"{core}|{cat}".encode()).hexdigest()[:12]

def merge_dedupe(reqs: List[Dict]) -> List[Dict]:
    # Pass 1: deterministic merge
    by_key: Dict[str, Dict] = {}
    for r in reqs:
        k = _canon_key(r)
        if k not in by_key:
            r = dict(r)
            r["id"] = r.get("id") or f"R-{k}"
            r["sources"] = [ {"doc": r.get("doc") or r.get("source"),
                               "page": r.get("page_start"),
                               "section": r.get("section"),
                               "quote": r.get("quote")} ]
            r["requires_adjudication"] = False
            r["conflict_fields"] = []
            by_key[k] = r
        else:
            by_key[k]["sources"].append({ "doc": r.get("doc") or r.get("source"),
                                          "page": r.get("page_start"),
                                          "section": r.get("section"),
                                          "quote": r.get("quote") })
            # simple confidence winner
            if ((r.get("confidence") or 0) > (by_key[k].get("confidence")) or 0):
                for f in ("label","quote","modality","category","section","page_start","page_end","confidence"):
                    if r.get(f) is not None:
                        by_key[k][f] = r.get(f)

    # Pass 2: semantic collapse (RapidFuzz)
    items = list(by_key.values())
    n = len(items)
    merged = [False]*n
    out: List[Dict] = []
    for i in range(n):
        if merged[i]: continue
        base = items[i]
        for j in range(i+1, n):
            if merged[j]: continue
            # quick lexical block: share ≥3 rare tokens
            if len(set(_core(base)).intersection(set(_core(items[j])))) < 3:
                continue
            score = fuzz.token_set_ratio(_core(base), _core(items[j]))
            if score >= 90:
                # union citations
                base["sources"].extend(items[j]["sources"])
                merged[j] = True
        out.append(base)
    return out
