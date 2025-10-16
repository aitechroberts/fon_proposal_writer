# src/extraction/openai_client.py  (optional helper)
from langfuse.openai import openai as lf_openai  # Langfuse-instrumented OpenAI
from src.config import settings

client = lf_openai.OpenAI(
    api_key=settings.az_openai_api_key,
    base_url=f"{settings.az_openai_endpoint}/openai/v1/"
)
# For AoAI, model param is your deployment name when you call client.chat/ responses.
