# backend/api/main.py
import logging
import json
from pathlib import Path

# #region agent log H1
def _debug_log(hyp, loc, msg, data=None):
    try:
        p = Path("/root/fon_proposal_writer/.cursor/debug.log")
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "a") as f:
            f.write(json.dumps({"hypothesisId": hyp, "location": loc, "message": msg, "data": data or {}, "timestamp": __import__("time").time()}) + "\n")
    except: pass
_debug_log("H1", "api/main.py:top", "Module load started")
# #endregion

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

# #region agent log H1
_debug_log("H1", "api/main.py:pre-import-routes", "About to import api.routes")
# #endregion

try:
    from api.routes import router
    # #region agent log H1
    _debug_log("H1", "api/main.py:post-import-routes", "Successfully imported api.routes")
    # #endregion
except Exception as e:
    # #region agent log H1
    _debug_log("H1", "api/main.py:import-routes-error", f"Failed to import api.routes: {e}")
    # #endregion
    raise

# #region agent log H3
_debug_log("H3", "api/main.py:pre-import-config", "About to import config.settings")
# #endregion

try:
    from config import settings
    # #region agent log H3
    _debug_log("H3", "api/main.py:post-import-config", "Successfully imported config", {"blob_container": settings.azure_blob_container})
    # #endregion
except Exception as e:
    # #region agent log H3
    _debug_log("H3", "api/main.py:import-config-error", f"Failed to import config: {e}")
    # #endregion
    raise

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
log = logging.getLogger("backend")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # #region agent log H2
    _debug_log("H2", "api/main.py:lifespan-start", "FastAPI lifespan startup triggered")
    # #endregion
    log.info("Starting RFP Compliance Matrix Backend API")
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
