"""Structured logging configuration."""

import logging
import sys
from typing import Any

import structlog
from structlog.types import Processor

from app.core.config import settings


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
