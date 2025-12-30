"""Test configuration and fixtures."""

import asyncio
import os
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings
from app.core.security import create_access_token


# Test against running backend container (internal port in container)
TEST_BASE_URL = os.getenv("TEST_BASE_URL", "http://localhost:8000")

# Shared engine and session factory - created once per test session
_test_engine: AsyncEngine | None = None
_test_session_factory: async_sessionmaker | None = None


def get_or_create_engine() -> AsyncEngine:
    """Get or create test engine."""
    global _test_engine
    if _test_engine is None:
        _test_engine = create_async_engine(
            str(settings.database_url),
            echo=False,
            future=True,
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=10,
        )
    return _test_engine


def get_or_create_session_factory() -> async_sessionmaker:
    """Get or create session factory."""
    global _test_session_factory
    if _test_session_factory is None:
        _test_session_factory = async_sessionmaker(
            get_or_create_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )
    return _test_session_factory


@pytest.fixture(scope="session")
def event_loop_policy():
    """Return the event loop policy."""
    return asyncio.DefaultEventLoopPolicy()


@pytest_asyncio.fixture(loop_scope="session")
async def test_db() -> AsyncGenerator[AsyncSession, None]:
    """Get database session for tests."""
    factory = get_or_create_session_factory()
    async with factory() as session:
        yield session


@pytest_asyncio.fixture(loop_scope="session")
async def auth_headers(test_db: AsyncSession) -> dict:
    """Auth headers with bearer token from existing user."""
    result = await test_db.execute(
        text("SELECT id, tenant_id, email, role FROM users LIMIT 1")
    )
    row = result.fetchone()

    if row:
        user_data = {
            "id": str(row[0]),
            "tenant_id": str(row[1]),
            "email": row[2],
            "role": row[3],
        }
    else:
        user_data = {
            "id": "a217effe-b1a5-4e31-9dc0-18008cb1d1a5",
            "tenant_id": "34b77286-7a3f-4f3e-899e-d61eb8c2ec54",
            "email": "admin@test.de",
            "role": "system_admin",
        }

    token = create_access_token(
        data={
            "sub": user_data["id"],
            "tenant_id": user_data["tenant_id"],
            "role": user_data["role"],
        }
    )
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture(loop_scope="session")
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Create test client that connects to running backend."""
    # Create client without connection pooling to avoid teardown issues
    client = AsyncClient(
        base_url=TEST_BASE_URL,
        timeout=30.0,
        http2=False,
    )
    try:
        yield client
    finally:
        # Close synchronously to avoid event loop issues
        try:
            await asyncio.wait_for(client.aclose(), timeout=1.0)
        except Exception:
            pass  # Ignore cleanup errors


@pytest_asyncio.fixture(loop_scope="session")
async def cleanup_test_cases(test_db: AsyncSession):
    """Cleanup test cases after tests."""
    yield
    try:
        await test_db.execute(
            text(
                "DELETE FROM audit_case_findings WHERE audit_case_id IN (SELECT id FROM audit_cases WHERE case_number LIKE 'TEST-%')"
            )
        )
        await test_db.execute(
            text(
                "DELETE FROM audit_logs WHERE entity_id IN (SELECT id FROM audit_cases WHERE case_number LIKE 'TEST-%')"
            )
        )
        await test_db.execute(
            text("DELETE FROM audit_cases WHERE case_number LIKE 'TEST-%'")
        )
        await test_db.commit()
    except Exception:
        await test_db.rollback()
