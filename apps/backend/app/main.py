"""FastAPI Application entrypoint."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api import router as api_router
from app.core.config import settings
from app.core.database import close_db, init_db, get_session_factory
from app.core.logging import setup_logging, get_logger, LoggingMiddleware
from app.core.rate_limit import setup_rate_limiting

# Initialize logging
setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler."""
    logger.info("Starting FlowAudit API", version="0.1.0", debug=settings.debug)

    # Startup
    await init_db()
    logger.info("Database initialized")

    yield

    # Shutdown
    logger.info("Shutting down FlowAudit API")
    await close_db()


app = FastAPI(
    title=settings.app_name,
    description="FlowAudit Platform API - Prüfbehörden-Management-System",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# Rate limiting
setup_rate_limiting(app)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Logging middleware (pure ASGI, no BaseHTTPMiddleware issues)
app.add_middleware(LoggingMiddleware)

# Include API router
app.include_router(api_router, prefix=settings.api_prefix)


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Basic health check endpoint."""
    return {"status": "healthy"}


@app.get("/api/health")
async def api_health_check() -> dict[str, str]:
    """Extended health check with database connectivity."""
    try:
        async with get_session_factory()() as session:
            await session.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception as e:
        logger.error("Database health check failed", error=str(e))
        db_status = "unhealthy"

    return {
        "api": "healthy",
        "database": db_status,
    }
