# backend/api/main.py
import logging
import sys
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

# Add shared config to path
sys.path.append("/shared")
sys.path.append("/app/src")

from api.routes import router
from config import settings

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
log = logging.getLogger("backend")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    log.info("Starting RFP Compliance Matrix Backend API")
    log.info(f"Prefect API URL: {settings.prefect_api_url}")
    log.info(f"Azure Blob Container: {settings.azure_blob_container}")
    yield
    log.info("Shutting down RFP Compliance Matrix Backend API")

# Create FastAPI app
app = FastAPI(
    title="RFP Compliance Matrix API",
    description="Backend API for RFP compliance matrix extraction",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(router, prefix="/api/v1")

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "RFP Compliance Matrix Backend API",
        "version": "1.0.0",
        "docs": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )
