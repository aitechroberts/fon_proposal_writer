# src/observability/tracing.py
import os
from langfuse import get_client
from openinference.instrumentation.dspy import DSPyInstrumentor

_lf = get_client()            # reads LANGFUSE_* envs
DSPyInstrumentor().instrument()  # one-liner: auto-trace DSPy calls to Langfuse
