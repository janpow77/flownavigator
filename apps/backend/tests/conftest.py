"""Test configuration and fixtures."""

import asyncio
import os
from datetime import datetime, timezone
from typing import AsyncGenerator
import uuid

# Set TESTING environment variable BEFORE importing app modules
os.environ["TESTING"] = "true"

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

# Import database functions - use lazy-loaded getters
from app.core.database import (
    get_engine,
    get_session_factory,
    reset_engine,
    Base,
)
from app.core.security import create_access_token

# Import all models to register them with Base.metadata
import app.models  # noqa: F401


@pytest.fixture(scope="session")
def event_loop_policy():
    """Return the event loop policy."""
    return asyncio.DefaultEventLoopPolicy()


@pytest_asyncio.fixture(loop_scope="session", scope="session")
async def setup_database():
    """Reset and create database tables.

    Resetting the engine ensures it's created within the pytest-asyncio
    event loop, avoiding 'Event loop is closed' errors.
    """
    # Reset any existing engine to ensure fresh creation in this event loop
    reset_engine()

    # Now get engine and create tables
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    # Cleanup: dispose engine properly
    await engine.dispose()
    reset_engine()


@pytest_asyncio.fixture(loop_scope="session")
async def test_db(setup_database) -> AsyncGenerator:
    """Get database session using lazy session factory."""
    factory = get_session_factory()
    async with factory() as session:
        yield session


@pytest_asyncio.fixture(loop_scope="session")
async def test_user(test_db) -> dict:
    """Create or get a test user."""
    # Try to get existing user
    result = await test_db.execute(
        text(
            "SELECT id, tenant_id, email, role FROM users WHERE email = 'test@example.com'"
        )
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
    """Create test client using ASGITransport with app."""
    # Import app here to ensure database is set up first
    from app.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport,
        base_url="http://test",
        timeout=30.0,
    ) as async_client:
        yield async_client


@pytest_asyncio.fixture(loop_scope="session")
async def cleanup_test_cases(test_db):
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
