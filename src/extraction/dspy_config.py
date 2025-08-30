# src/extraction/dspy_config.py
import dspy
from src.config import settings
from src.observability import tracing  # noqa: F401 (side-effect: auto-instrument)

lm = dspy.LM(
    model=f"openai/{settings.az_openai_deployment}",
    model_type="chat",
    api_provider="azure",
    api_key=settings.az_openai_api_key,
    api_base=f"{settings.az_openai_endpoint}/openai/deployments/{settings.az_openai_deployment}",
    # api_version not required for v1 base_url, but keep if you’re pinned to old preview
)

dspy.configure(lm=lm)
