# shared/config.py
from pydantic import Field
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application settings using pydantic-settings v2."""
    
    # Azure OpenAI Configuration
    azure_api_key: str = Field(default="", alias="AZURE_API_KEY")
    azure_api_base: str = Field(default="", alias="AZURE_API_BASE")
    azure_api_version: str = Field(default="2024-12-01-preview", alias="AZURE_API_VERSION")
    azure_openai_deployment: str = Field(default="gpt-4.1", alias="AZURE_OPENAI_DEPLOYMENT")
    
    # Langfuse Configuration
    langfuse_public_key: str = Field(default="", alias="LANGFUSE_PUBLIC_KEY")
    langfuse_secret_key: str = Field(default="", alias="LANGFUSE_SECRET_KEY")
    langfuse_host: str = Field(default="https://cloud.langfuse.com", alias="LANGFUSE_HOST")
    
    # Azure Storage Configuration
    azure_storage_connection_string: str = Field(default="", alias="AZURE_STORAGE_CONNECTION_STRING")
    azure_blob_container: str = Field(default="proposal-container", alias="AZURE_BLOB_CONTAINER")
    
    # Optional Azure Document Intelligence
    documentintelligence_endpoint: str | None = Field(default=None, alias="DOCUMENTINTELLIGENCE_ENDPOINT")
    documentintelligence_api_key: str | None = Field(default=None, alias="DOCUMENTINTELLIGENCE_API_KEY")
    
    # DSPy Configuration
    dspy_model_type: str = Field(default="chat", alias="DSPY_MODEL_TYPE")
    
    # Prefect Configuration
    prefect_api_url: str = Field(default="https://api.prefect.cloud/api/accounts", alias="PREFECT_API_URL")
    prefect_api_key: str = Field(default="", alias="PREFECT_API_KEY")
    
    # HigherGov Configuration
    highergov_api_key: str = Field(default="", alias="HIGHERGOV_API_KEY")
    
    # Application Settings
    debug: bool = Field(default=False, alias="DEBUG")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore"
    }

settings = Settings()
