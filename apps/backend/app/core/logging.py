"""Structured logging configuration."""

import logging
import sys
import uuid

import structlog
from structlog.types import Processor
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.core.config import settings


class LoggingMiddleware:
    """Pure ASGI middleware for request logging.

    This avoids BaseHTTPMiddleware which has known issues with
    background tasks and async cleanup in tests.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request_id = str(uuid.uuid4())

        # Extract request info
        method = scope.get("method", "")
        path = scope.get("path", "")

        # Check for X-Request-ID header
        headers = dict(scope.get("headers", []))
        if b"x-request-id" in headers:
            request_id = headers[b"x-request-id"].decode()

        # Bind context for structured logging
        bind_request_context(
            request_id=request_id,
            method=method,
            path=path,
        )

        logger = get_logger(__name__)

        # Get client IP
        client = scope.get("client")
        client_ip = client[0] if client else "unknown"

        logger.info("Request started", client_ip=client_ip)

        status_code = 500  # Default in case of error

        async def send_wrapper(message: Message) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message.get("status", 500)
                # Add X-Request-ID header
                headers = list(message.get("headers", []))
                headers.append((b"x-request-id", request_id.encode()))
                message["headers"] = headers
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
            logger.info("Request completed", status_code=status_code)
        except Exception as exc:
            logger.exception("Request failed", error=str(exc))
            raise
        finally:
            clear_request_context()


def setup_logging() -> None:
    """Configure structured logging with structlog."""
    # Determine log level from settings
    log_level = logging.DEBUG if settings.debug else logging.INFO

    # Shared processors for all loggers
    shared_processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.ExtraAdder(),
    ]

    if settings.debug:
        # Development: colored console output
        processors: list[Processor] = [
            *shared_processors,
            structlog.dev.ConsoleRenderer(colors=True),
        ]
    else:
        # Production: JSON output
        processors = [
            *shared_processors,
            structlog.processors.dict_tracebacks,
            structlog.processors.JSONRenderer(),
        ]

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Configure standard library logging to use structlog
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=log_level,
    )

    # Reduce noise from third-party libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.INFO if settings.debug else logging.WARNING
    )


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    """Get a structured logger instance."""
    return structlog.get_logger(name)


# Request context binding
def bind_request_context(
    request_id: str,
    method: str,
    path: str,
    user_id: str | None = None,
) -> None:
    """Bind request context to all log messages."""
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(
        request_id=request_id,
        method=method,
        path=path,
        user_id=user_id,
    )


def clear_request_context() -> None:
    """Clear request context after request completes."""
    structlog.contextvars.clear_contextvars()
