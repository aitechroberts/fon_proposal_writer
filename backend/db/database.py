# backend/db/database.py
"""
Async SQLAlchemy database connection with connection pooling.

Configuration:
- pool_size=5: Adequate for ~15 concurrent users
- max_overflow=2: Allow 2 extra connections during bursts
- pool_pre_ping=True: Prevents stale connections
"""

import logging
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool

from config import settings

log = logging.getLogger(__name__)

# Build async database URL from settings
# Convert postgresql:// to postgresql+asyncpg:// for async driver
DATABASE_URL = getattr(settings, 'database_url', None) or ""

if DATABASE_URL:
    if DATABASE_URL.startswith("postgresql://"):
        ASYNC_DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif DATABASE_URL.startswith("postgres://"):
        ASYNC_DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)
    else:
        ASYNC_DATABASE_URL = DATABASE_URL
else:
    ASYNC_DATABASE_URL = ""

# Create async engine with connection pooling
# Only create if DATABASE_URL is configured
if ASYNC_DATABASE_URL:
    engine = create_async_engine(
        ASYNC_DATABASE_URL,
        pool_size=5,         # Max 15 users = 5 is plenty
        max_overflow=2,      # Allow 2 extra in bursts
        pool_pre_ping=True,  # Prevents stale connections
        echo=settings.debug,  # Log SQL in debug mode
    )
    
    # Create async session factory
    AsyncSessionLocal = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )
else:
    # No database configured - use None placeholders
    engine = None
    AsyncSessionLocal = None
    log.warning("DATABASE_URL not configured - database features disabled")


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for FastAPI routes that need database access.
    
    Usage:
        @router.get("/jobs")
        async def list_jobs(db: AsyncSession = Depends(get_db)):
            ...
    """
    if AsyncSessionLocal is None:
        raise RuntimeError("Database not configured. Set DATABASE_URL environment variable.")
    
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db() -> None:
    """
    Initialize database tables.
    
    Call this on application startup to ensure tables exist.
    For production, you may want to run migrations instead.
    """
    # #region agent log
    import json, time
    def _debug_log(hyp, msg, data=None):
        try:
            with open("/root/fon_proposal_writer/.cursor/debug.log", "a") as f:
                f.write(json.dumps({"hypothesisId": hyp, "location": "database.py:init_db", "message": msg, "data": data or {}, "timestamp": int(time.time()*1000), "sessionId": "debug-session"}) + "\n")
        except: pass
    # #endregion
    
    # #region agent log
    _debug_log("E", "init_db called", {"engine_exists": engine is not None, "DATABASE_URL_set": bool(DATABASE_URL)})
    # #endregion
    
    if engine is None:
        log.warning("Database not configured - skipping table creation")
        # #region agent log
        _debug_log("E", "Engine is None - skipping table creation", {})
        # #endregion
        return
    
    from .models import Base
    
    try:
        async with engine.begin() as conn:
            # #region agent log
            _debug_log("E", "Connected to database, creating tables", {})
            # #endregion
            # Create all tables
            await conn.run_sync(Base.metadata.create_all)
        
        # #region agent log
        _debug_log("E", "Tables created successfully", {})
        # #endregion
        log.info("Database tables initialized")
    except Exception as e:
        # #region agent log
        _debug_log("E", "EXCEPTION during table creation", {"error": str(e), "error_type": type(e).__name__})
        # #endregion
        raise

