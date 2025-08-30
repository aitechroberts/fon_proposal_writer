# src/extraction/merge_dedupe.py
import hashlib

def canonical_id(req):
    h = hashlib.sha1((req.get("label","") + req.get("quote","")).encode()).hexdigest()[:8]
    return f"R-{h}"

def merge_requirements(all_reqs):
    # naive dedupe by quote+label
    seen, merged = set(), []
    for r in all_reqs:
        key = (r.get("label","").lower(), r.get("quote","").strip().lower())
        if key in seen: 
            continue
        seen.add(key)
        r["id"] = r.get("id") or canonical_id(r)
        merged.append(r)
    return merged
