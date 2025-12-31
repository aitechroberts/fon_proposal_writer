# backend/api/main.py
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

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
    log.info("Starting FON Advisors Proposal Writer Backend API")
    log.info(f"Azure Blob Container: {settings.azure_blob_container}")
    
    # Initialize database tables
    try:
        from db.database import init_db
        await init_db()
        log.info("Database initialized successfully")
    except Exception as e:
        log.warning(f"Database initialization skipped or failed: {e}")
    
    yield
    log.info("Shutting down FON Advisors Proposal Writer Backend API")

# Create FastAPI app
app = FastAPI(
    title="FON Advisors Proposal Writer API",
    description="Backend API for RFP compliance matrix extraction and proposal generation",
    version="2.0.0",
    lifespan=lifespan
)

# Configure CORS from environment variable
# CORS_ORIGINS can be "*" for development or comma-separated list of allowed origins
# Example: "https://proposal-frontend.azurecontainerapps.io,http://localhost:3000"
def _get_cors_origins() -> list[str]:
    """Parse CORS_ORIGINS from settings."""
    origins_str = settings.cors_origins.strip()
    if origins_str == "*":
        return ["*"]
    # Split by comma and strip whitespace
    return [origin.strip() for origin in origins_str.split(",") if origin.strip()]

cors_origins = _get_cors_origins()
log.info(f"CORS configured for origins: {cors_origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
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
