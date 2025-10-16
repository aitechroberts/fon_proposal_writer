# Dockerfile
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy dependency files first (better caching)
COPY pyproject.toml ./
# Copy uv.lock if it exists, but don't fail if missing
COPY uv.lock* ./

# Install dependencies with caching
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --no-dev || uv sync --no-dev --no-cache

# Set up venv in PATH
ENV VIRTUAL_ENV=/app/.venv
ENV PATH="/app/.venv/bin:${PATH}"
ENV PYTHONPATH="/app:${PYTHONPATH}"

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p data/inputs tmp_outputs outputs logs

# Streamlit configuration
EXPOSE 8501
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
ENV STREAMLIT_SERVER_FILE_WATCHER_TYPE=none

# Performance & stability settings
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Run Streamlit
CMD ["uv", "run", "streamlit", "run", "app.py", \
     "--server.port=8501", \
     "--server.address=0.0.0.0", \
     "--server.headless=true"]