# at top
from langfuse import observe, get_client
from src.experiments.config_variants import load_variant, apply_variant
from src.preprocessing.regex_pass import fast_hits
from src.extraction.confidence import calculate_confidence
from src.matrix.export_excel import save_excel
from src.observability.metrics import log_experiment_metadata
from pypdf import PdfReader  # pypdf 6 API

# ensure DSPy LM uses Azure v1 Responses if you want:
import dspy
variant = load_variant()
# Example: switch to "responses" quickly when needed
lm = dspy.LM(f"azure/{os.getenv('AZURE_OPENAI_DEPLOYMENT','gpt-4o-mini')}",
             model_type=os.getenv("DSPY_MODEL_TYPE","chat"), temperature=variant.temperature)
dspy.configure(lm=lm, adapter=dspy.JSONAdapter())  # JSON-first adapter per docs
# (Refs: DSPy LM & JSONAdapter APIs)  # :contentReference[oaicite:9]{index=9}

def pdf_to_text(path: str) -> str:
    r = PdfReader(path); return "\n".join(p.extract_text() or "" for p in r.pages)  # pypdf 6
# :contentReference[oaicite:10]{index=10}

@observe(name="experiment_run")
def run_one(file_path: str, exp_name: str):
    apply_variant(variant)

    text = pdf_to_text(file_path)
    chunks = list(heading_aware_chunks([(1, text)]))  # your existing segmenter

    extractor, classifier, grounder = Extractor(), Classifier(), Grounder()
    reqs = []

    for ch in chunks:
        # 0) regex fast-path
        for hit in fast_hits(ch):
            r = {
                "id": "", "label": hit["match"][:120], "category": "Other",
                "modality": "UNKNOWN", "quote": hit["match"],
                "section": ch["section"], "page_start": ch["start_page"], "page_end": ch["end_page"],
                "source": "regex"
            }
            r["confidence"] = calculate_confidence(r)
            reqs.append(r)

        # 1..3) LLM stages
        for r in extractor(ch):
            r["source"] = "llm"
            r = classifier(r); r["classified"] = True
            r = grounder(ch, r); r["grounded"] = True
            r["confidence"] = calculate_confidence(r)
            reqs.append(r)

    merged = merge_requirements(reqs)

    # Persist JSON/CSV as before, plus Excel
    out_json = file_path + f".{exp_name}.requirements.json"
    out_csv  = file_path + f".{exp_name}.matrix.csv"
    out_xlsx = file_path + f".{exp_name}.matrix.xlsx"
    save_json(merged, out_json); save_csv(merged, out_csv); save_excel(merged, out_xlsx)

    # Simple experiment stats → Langfuse
    stats = log_experiment_metadata(exp_name, merged)
    get_client().flush()  # ensure v3 SDK ships data

    return out_json, out_csv, out_xlsx, stats
