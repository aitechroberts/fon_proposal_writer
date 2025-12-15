# backend/Dockerfile
# Build from backend directory: docker build -t proposal-backend ./backend
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
&& rm -rf /var/lib/apt/lists/*

# Install dependencies to /opt/venv (outside /app to avoid volume mount conflicts)
WORKDIR /opt
COPY pyproject.toml ./
COPY uv.lock* ./

# Install dependencies with caching
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --no-dev || uv sync --no-dev --no-cache

# Set up venv in PATH (installed to /opt/.venv by uv)
ENV VIRTUAL_ENV=/opt/.venv
ENV PATH="/opt/.venv/bin:${PATH}"

WORKDIR /app
ENV PYTHONPATH="/app:/app/src"

# Copy all application code
COPY . .

# Create necessary directories
RUN mkdir -p data/inputs tmp_outputs outputs logs

# FastAPI configuration
EXPOSE 8000
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Run FastAPI
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
