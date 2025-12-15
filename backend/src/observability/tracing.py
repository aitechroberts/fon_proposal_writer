# src/observability/tracing.py
import logging
from typing import Optional

from langfuse import Langfuse, get_client
from openinference.instrumentation.dspy import DSPyInstrumentor

from ..config import settings

logger = logging.getLogger(__name__)

# Global Langfuse client
_langfuse_client: Optional[Langfuse] = None

def initialize_tracing() -> Langfuse:
    """Initialize Langfuse tracing and DSPy instrumentation."""
    global _langfuse_client
    
    if _langfuse_client is not None:
        return _langfuse_client
    
    try:
        # Initialize Langfuse client with explicit configuration
        _langfuse_client = Langfuse(
            public_key=settings.langfuse_public_key,
            secret_key=settings.langfuse_secret_key,
            host=settings.langfuse_host,
            debug=settings.debug
        )
        
        # Initialize DSPy instrumentation for automatic tracing
        DSPyInstrumentor().instrument()
        
        logger.info(f"Tracing initialized with Langfuse host: {settings.langfuse_host}")
        return _langfuse_client
        
    except Exception as e:
        logger.error(f"Failed to initialize tracing: {e}")
        raise

def get_langfuse_client() -> Langfuse:
    """Get the Langfuse client, initializing if necessary."""
    if _langfuse_client is None:
        return initialize_tracing()
    return _langfuse_client

def flush_traces() -> None:
    """Flush any pending traces to Langfuse."""
    try:
        client = get_client()
        client.flush()
        logger.debug("Flushed traces to Langfuse")
    except Exception as e:
        logger.warning(f"Failed to flush traces: {e}")

# Auto-initialize tracing when module is imported
try:
    initialize_tracing()
except Exception as e:
    logger.warning(f"Failed to auto-initialize tracing: {e}")
