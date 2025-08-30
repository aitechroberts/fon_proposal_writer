from collections import Counter
from statistics import mean
from langfuse import get_client

def log_experiment_metadata(exp_name: str, results: list[dict]):
    lf = get_client()
    meta = {
        "total_requirements": len(results),
        "by_modality": dict(Counter((r.get("modality") or "UNK").upper() for r in results)),
        "by_category": dict(Counter(r.get("category","Other") for r in results)),
        "regex_vs_llm": dict(Counter(r.get("source","llm") for r in results)),
        "avg_confidence": float(mean([r.get("confidence",0.0) for r in results]) if results else 0.0),
    }
    # Attach as categorical+numeric scores (shows up in Scores & on the trace)
    lf.score_current_trace(name=f"{exp_name}_avg_confidence", value=meta["avg_confidence"])     # NUMERIC
    lf.score_current_trace(name=f"{exp_name}_modality_json",  value=1, data_type="BOOLEAN",     # just a marker
                           comment=str(meta["by_modality"]))
    return meta
