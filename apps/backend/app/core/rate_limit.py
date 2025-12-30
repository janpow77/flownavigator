"""Rate limiting configuration using slowapi."""

from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.config import settings


def get_user_identifier(request: Request) -> str:
    """Get identifier for rate limiting - user_id if authenticated, else IP."""
    # Try to get user from request state (set by auth middleware)
    if hasattr(request.state, "user") and request.state.user:
        return f"user:{request.state.user.id}"
    # Fall back to IP address
    return get_remote_address(request)


# Create limiter instance
limiter = Limiter(
    key_func=get_user_identifier,
    default_limits=["200/minute", "1000/hour"],
    storage_uri="memory://",  # Use Redis in production: "redis://localhost:6379"
    strategy="fixed-window",
)


def rate_limit_exceeded_handler(
    request: Request, exc: RateLimitExceeded
) -> JSONResponse:
    """Custom handler for rate limit exceeded errors."""
    return JSONResponse(
        status_code=429,
        content={
            "detail": "Zu viele Anfragen. Bitte versuchen Sie es später erneut.",
            "retry_after": exc.detail,
        },
        headers={"Retry-After": str(exc.detail)},
    )


def setup_rate_limiting(app: FastAPI) -> None:
    """Configure rate limiting for the FastAPI app."""
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)


# Decorator shortcuts for common limits
def limit_auth(limit: str = "5/minute"):
    """Rate limit for authentication endpoints (stricter)."""
    return limiter.limit(limit)


def limit_write(limit: str = "30/minute"):
    """Rate limit for write operations."""
    return limiter.limit(limit)


def limit_read(limit: str = "100/minute"):
    """Rate limit for read operations."""
    return limiter.limit(limit)
