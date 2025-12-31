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
from urllib.parse import urlparse, parse_qs

from sqlalchemy import URL
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from config import settings

log = logging.getLogger(__name__)

# Build async database URL from settings using URL.create()
# This properly handles passwords with special characters
DATABASE_URL = (getattr(settings, 'database_url', None) or "").strip()

engine = None
AsyncSessionLocal = None

if DATABASE_URL:
    try:
        # Parse the DATABASE_URL to extract components
        parsed = urlparse(DATABASE_URL)
        
        # Extract query parameters (like sslmode)
        query_params = parse_qs(parsed.query) if parsed.query else {}
        # Flatten single-value lists
        query_dict = {k: v[0] if len(v) == 1 else v for k, v in query_params.items()}
        
        # Ensure sslmode is set for Azure PostgreSQL
        if "sslmode" not in query_dict:
            query_dict["sslmode"] = "require"
        
        # Build the async URL using SQLAlchemy's URL.create()
        # This properly handles password encoding
        ASYNC_DATABASE_URL = URL.create(
            drivername="postgresql+asyncpg",
            username=parsed.username,
            password=parsed.password,
            host=parsed.hostname,
            port=parsed.port or 5432,
            database=parsed.path.lstrip("/") if parsed.path else "postgres",
            query=query_dict
        )
        
        log.info(f"Database configured: host={parsed.hostname}, db={parsed.path.lstrip('/')}")
        
        # Create async engine with connection pooling
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
        
    except Exception as e:
        log.error(f"Failed to parse DATABASE_URL: {e}")
        engine = None
        AsyncSessionLocal = None
else:
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
    if engine is None:
        log.warning("Database not configured - skipping table creation")
        return
    
    from .models import Base
    
    async with engine.begin() as conn:
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)
    
    log.info("Database tables initialized")
