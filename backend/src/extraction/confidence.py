def calculate_confidence(req: dict):
    src = req.get("source")  # "regex" | "llm"
    base = 0.5
    if src == "regex":
        mod = (req.get("modality") or "").upper()
        base = 0.65 if mod in {"SHALL","MUST","REQUIRED"} else 0.55
    elif src == "llm":
        base = 0.85
        if req.get("classified") and req.get("grounded"):
            base = 0.95
    # small boosts for short, unambiguous quotes
    q = (req.get("quote") or "").strip()
    if 10 <= len(q) <= 240:
        base += 0.02
    return round(min(base, 0.99), 2)
