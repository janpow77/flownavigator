"""FastAPI Application entrypoint."""

import uuid
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api import router as api_router
from app.core.config import settings
from app.core.database import close_db, init_db, async_session_factory
from app.core.logging import (
    setup_logging,
    get_logger,
    bind_request_context,
    clear_request_context,
)
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


@app.middleware("http")
async def logging_middleware(request: Request, call_next) -> Response:
    """Add request logging and context."""
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))

    # Get user_id from auth header if available
    user_id = None
    if hasattr(request.state, "user") and request.state.user:
        user_id = str(request.state.user.id)

    # Bind context for structured logging
    bind_request_context(
        request_id=request_id,
        method=request.method,
        path=request.url.path,
        user_id=user_id,
    )

    logger.info(
        "Request started",
        client_ip=request.client.host if request.client else "unknown",
    )

    try:
        response = await call_next(request)
        logger.info("Request completed", status_code=response.status_code)
        response.headers["X-Request-ID"] = request_id
        return response
    except Exception as exc:
        logger.exception("Request failed", error=str(exc))
        raise
    finally:
        clear_request_context()


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
        async with async_session_factory() as session:
            await session.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception as e:
        logger.error("Database health check failed", error=str(e))
        db_status = "unhealthy"

    return {
        "api": "healthy",
        "database": db_status,
    }
