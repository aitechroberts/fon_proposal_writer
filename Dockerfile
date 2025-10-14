# Use the official uv image with Python 3.12
# (contains Python + uv preinstalled on Debian Bookworm)
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

# System packages (build essentials for native wheels if needed)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy only project files needed to resolve dependencies first (better layer caching)
# If you have a uv.lock, copy it too for reproducible builds
COPY pyproject.toml ./
COPY uv.lock ./ 

# Install dependencies into a project-local venv (.venv) using uv
# --frozen uses uv.lock strictly; drop it if you don't commit a lock yet
# --no-dev avoids dev extras in prod images
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --no-dev --frozen || uv sync --no-dev

# Make the venv available on PATH for non-`uv run` usage too
ENV VIRTUAL_ENV=/app/.venv
ENV PATH="/app/.venv/bin:${PATH}"

# Now copy the rest of your repo (src/, app.py, main.py, data/, etc.)
COPY . .

# Streamlit runs on 8501
EXPOSE 8501
ENV STREAMLIT_DISABLE_TELEMETRY=true
ENV PYTHONUNBUFFERED=1

# If your import paths need it (e.g., src/ as a package)
ENV PYTHONPATH="/app:${PYTHONPATH}"

# Run Streamlit via uv (ensures the project venv and deps are used)
CMD ["uv", "run", "streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
