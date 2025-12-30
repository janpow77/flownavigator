"""Test configuration and fixtures."""

import asyncio
import os
from datetime import datetime, timezone
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings
from app.core.security import create_access_token
from app.models.base import Base


# Flag to determine test mode
# If TEST_AGAINST_CONTAINER is set, tests will connect to running backend
# Otherwise, tests use ASGITransport directly against the app
TEST_AGAINST_CONTAINER = os.getenv("TEST_AGAINST_CONTAINER", "").lower() == "true"
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


@pytest_asyncio.fixture(loop_scope="session", scope="session")
async def setup_database():
    """Create database tables for testing."""
    engine = get_or_create_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Don't drop tables - let CI handle cleanup


@pytest_asyncio.fixture(loop_scope="session")
async def test_db(setup_database) -> AsyncGenerator[AsyncSession, None]:
    """Get database session for tests."""
    factory = get_or_create_session_factory()
    async with factory() as session:
        yield session


@pytest_asyncio.fixture(loop_scope="session")
async def test_user(test_db: AsyncSession) -> dict:
    """Create or get a test user."""
    # Try to get existing user
    result = await test_db.execute(
        text("SELECT id, tenant_id, email, role FROM users LIMIT 1")
    )
    row = result.fetchone()

    if row:
        return {
            "id": str(row[0]),
            "tenant_id": str(row[1]),
            "email": row[2],
            "role": row[3],
        }

    # Create a test user if none exists
    import uuid

    user_id = uuid.uuid4()
    tenant_id = uuid.uuid4()

    now = datetime.now(timezone.utc)

    await test_db.execute(
        text(
            """
            INSERT INTO tenants (id, name, type, status, created_at, updated_at)
            VALUES (:id, :name, :type, :status, :created_at, :updated_at)
            ON CONFLICT (id) DO NOTHING
            """
        ),
        {
            "id": tenant_id,
            "name": "Test Tenant",
            "type": "authority",
            "status": "active",
            "created_at": now,
            "updated_at": now,
        },
    )

    await test_db.execute(
        text(
            """
            INSERT INTO users (id, tenant_id, email, hashed_password, first_name, last_name, role, is_active, created_at, updated_at)
            VALUES (:id, :tenant_id, :email, :password, :first_name, :last_name, :role, true, :created_at, :updated_at)
            ON CONFLICT (email) DO NOTHING
            """
        ),
        {
            "id": user_id,
            "tenant_id": tenant_id,
            "email": "test@example.com",
            "password": "$2b$12$dummy_hashed_password_for_testing",
            "first_name": "Test",
            "last_name": "User",
            "role": "system_admin",
            "created_at": now,
            "updated_at": now,
        },
    )
    await test_db.commit()

    return {
        "id": str(user_id),
        "tenant_id": str(tenant_id),
        "email": "test@example.com",
        "role": "system_admin",
    }


@pytest_asyncio.fixture(loop_scope="session")
async def auth_headers(test_user: dict) -> dict:
    """Auth headers with bearer token."""
    token = create_access_token(
        data={
            "sub": test_user["id"],
            "tenant_id": test_user["tenant_id"],
            "role": test_user["role"],
        }
    )
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture(loop_scope="session")
async def client(setup_database) -> AsyncGenerator[AsyncClient, None]:
    """Create test client."""
    if TEST_AGAINST_CONTAINER:
        # Connect to running backend container
        async_client = AsyncClient(
            base_url=TEST_BASE_URL,
            timeout=30.0,
            http2=False,
        )
    else:
        # Use ASGITransport for direct app testing
        from app.main import app

        transport = ASGITransport(app=app)
        async_client = AsyncClient(
            transport=transport,
            base_url="http://test",
            timeout=30.0,
        )

    try:
        yield async_client
    finally:
        try:
            await asyncio.wait_for(async_client.aclose(), timeout=1.0)
        except Exception:
            pass


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
