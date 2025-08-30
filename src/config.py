# src/config.py
from pydantic import BaseSettings

class Settings(BaseSettings):
    az_openai_api_key: str = ""
    az_openai_endpoint: str = ""
    az_openai_deployment: str = "gpt-4o-mini"
    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""
    langfuse_host: str = "https://cloud.langfuse.com"
    az_blob_conn: str = ""
    az_blob_container: str = "rfp-poc"

    class Config:
        env_prefix = ""
        case_sensitive = False

settings = Settings()
