# main.py
from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Iterable

# ---- Config (pydantic v2 + pydantic-settings) -------------------------------
from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    # Langfuse v3 (OTel SDK)
    LANGFUSE_PUBLIC_KEY: str = Field(..., alias="LANGFUSE_PUBLIC_KEY")
    LANGFUSE_SECRET_KEY: str = Field(..., alias="LANGFUSE_SECRET_KEY")
    LANGFUSE_HOST: str = "https://cloud.langfuse.com"  # or https://us.cloud.langfuse.com

    # Azure OpenAI (used both by DSPy and direct SDK)
    AZURE_API_KEY: str | None = None         # DSPy / LiteLLM expects AZURE_* by default
    AZURE_API_BASE: str | None = None        # e.g., https://<resource>.openai.azure.com
    AZURE_API_VERSION: str | None = "2025-05-01-preview"

    # If calling the Azure OpenAI SDK client directly via Langfuse wrapper:
    AZURE_OPENAI_API_KEY: str | None = None  # same value as AZURE_API_KEY typically
    AZURE_OPENAI_ENDPOINT: str | None = None # same as AZURE_API_BASE

    # Azure Storage
    AZURE_STORAGE_CONNECTION_STRING: str
    AZURE_BLOB_CONTAINER: str = "experiments"

    # DSPy model config
    AZURE_OPENAI_DEPLOYMENT: str = "gpt-4o-mini"  # your deployment name, not model name
    DSPY_MODEL_TYPE: str = "chat"  # or "responses" to use Azure v1 Responses path

    # Misc
    DEBUG: bool = False

    model_config = {"env_file": ".env", "extra": "ignore"}

cfg = Settings()

# ---- Langfuse v3 setup (OTel-based) & OpenAI wrapper ------------------------
from langfuse import get_client, observe, Langfuse
# If you call the OpenAI SDK directly anywhere (outside DSPy), use the wrapped client:
from langfuse.openai import AzureOpenAI  # drop-in replacement for openai.AzureOpenAI

lf = Langfuse(  # you can also rely purely on env vars; this just makes it explicit
    public_key=cfg.LANGFUSE_PUBLIC_KEY,
    secret_key=cfg.LANGFUSE_SECRET_KEY,
    host=cfg.LANGFUSE_HOST,
    debug=cfg.DEBUG,
)

# Example direct Azure OpenAI client (optional, e.g., for embeddings):
aoai = AzureOpenAI(
    api_key=cfg.AZURE_OPENAI_API_KEY or cfg.AZURE_API_KEY,
    base_url=f"{(cfg.AZURE_OPENAI_ENDPOINT or cfg.AZURE_API_BASE).rstrip('/')}/openai/v1/",
    api_version=cfg.AZURE_API_VERSION or "2025-05-01-preview",
)

# ---- DSPy 3 configuration ---------------------------------------------------
from openinference.instrumentation.dspy import DSPyInstrumentor
DSPyInstrumentor().instrument()  # auto-trace DSPy into OTel → Langfuse  # noqa

import dspy

# DSPy 3 supports provider/model like "azure/<deployment>" and can use the new Responses API.
# Set AZURE_* env vars (already provided via Settings), then:
lm = dspy.LM(
    f"azure/{cfg.AZURE_OPENAI_DEPLOYMENT}",
    model_type=cfg.DSPY_MODEL_TYPE,    # "chat" or "responses"
    temperature=0.0,
    max_tokens=4000,
)
dspy.configure(lm=lm)
# (DSPy will read AZURE_API_KEY / AZURE_API_BASE / AZURE_API_VERSION per docs)

# Make JSON structured output the default (uses OpenAI structured responses if available)
dspy.settings.adapter = dspy.JSONAdapter()

# ---- PDF ingestion (pypdf 6) -----------------------------------------------
from pypdf import PdfReader  # pypdf 6.x

def read_text_from_pdfs(paths: Iterable[str]) -> list[dict]:
    """Return [{'path': ..., 'text': ...}, ...] for each PDF path."""
    docs = []
    for path in paths:
        reader = PdfReader(path)
        parts = []
        for i, page in enumerate(reader.pages):
            # extract_text() works well for most native PDFs; orientation arg is supported in pypdf 6
            parts.append(page.extract_text() or "")
        docs.append({"path": path, "text": "\n".join(parts)})
    return docs

# ---- DSPy signature & module for requirement extraction ---------------------
from dspy import Signature, InputField, OutputField, Predict

class ExtractRequirements(Signature):
    """Extract proposal-compliance requirements from provided text, targeting
    mandatory (MUST, SHALL), recommended (SHOULD), and any formatting/structure rules
    (font, spacing, page limits, file format, forms, etc.). Return strict JSON."""
    text = InputField(desc="The source text from a solicitation or instruction section.")
    requirements_json = OutputField(
        desc=(
            "A JSON object with keys: "
            "`requirements: [ {id, type, verbatim, normalized, category, priority, source_citation} ]`, "
            "and `meta: { extractor_version }`. Use absolute character spans for `source_citation` when possible."
        ),
        prefix="JSON:",  # nudge structured output
    )

class RequirementExtractor(dspy.Module):
    def __init__(self):
        super().__init__()
        self.predict = Predict(ExtractRequirements)

    def forward(self, text: str):
        out = self.predict(text=text)
        return out.requirements_json

# ---- Azure Blob storage (persist outputs & traces) --------------------------
from azure.storage.blob import BlobServiceClient  # azure-storage-blob

blob_service = BlobServiceClient.from_connection_string(cfg.AZURE_STORAGE_CONNECTION_STRING)
container_client = blob_service.get_container_client(cfg.AZURE_BLOB_CONTAINER)
try:
    container_client.create_container()
except Exception:
    pass  # already exists

def upload_json_to_blob(data: dict, *, prefix: str = "runs") -> str:
    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    name = f"{prefix}/requirements_{ts}.json"
    container_client.upload_blob(name=name, data=json.dumps(data, indent=2), overwrite=True)
    return name

# ---- Orchestrate one experiment run ----------------------------------------
@observe(name="experiment_run")  # Langfuse v3 decorator groups spans/traces
def run_experiment(pdf_paths: list[str]) -> dict:
    docs = read_text_from_pdfs(pdf_paths)

    extractor = RequirementExtractor()
    results: list[dict] = []

    for doc in docs:
        # You can add more stages (e.g., normalization pass, citation alignment) as separate DSPy modules
        requirements_json_str = extractor(text=doc["text"])
        try:
            parsed = json.loads(requirements_json_str)
        except Exception:
            # Ensure always-valid JSON for downstream consumers
            parsed = {"requirements": [], "meta": {"parse_error": True, "raw": requirements_json_str}}

        results.append({
            "source_path": doc["path"],
            "requirements": parsed.get("requirements", []),
            "meta": parsed.get("meta", {}),
        })

    payload = {
        "meta": {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "dspy_model": f"azure/{cfg.AZURE_OPENAI_DEPLOYMENT}",
            "model_type": cfg.DSPY_MODEL_TYPE,
            "langfuse_host": cfg.LANGFUSE_HOST,
        },
        "documents": results,
    }

    # Store artifacts
    blob_name = upload_json_to_blob(payload)
    payload["artifact"] = {"azure_blob": {"container": cfg.AZURE_BLOB_CONTAINER, "name": blob_name}}
    return payload

if __name__ == "__main__":
    # Example usage: python main.py (make sure .env is set and PDFs exist)
    import sys
    pdfs = sys.argv[1:]  # pass PDF paths as args
    if not pdfs:
        print("Usage: python main.py <file1.pdf> <file2.pdf> ...")
        raise SystemExit(2)

    out = run_experiment(pdfs)
    # Flush telemetry for short-lived runs
    get_client().flush()

    print(json.dumps(out, indent=2)[:4000])
