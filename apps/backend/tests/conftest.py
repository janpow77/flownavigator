"""Test configuration and fixtures."""

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
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

# Import database config and models
from app.core.config import settings
from app.core.database import Base, get_db
from app.core.security import create_access_token

# Import all models to register them with Base.metadata
import app.models  # noqa: F401


# Cached test user data
_test_user_cache = None


@pytest_asyncio.fixture
async def db_engine():
    """Create a fresh engine for each test."""
    engine = create_async_engine(
        str(settings.database_url),
        echo=False,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
    )

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Cleanup
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session_factory(db_engine):
    """Create session factory for tests."""
    return async_sessionmaker(
        db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )


@pytest_asyncio.fixture
async def test_db(db_session_factory) -> AsyncGenerator[AsyncSession, None]:
    """Get database session for each test."""
    async with db_session_factory() as session:
        yield session
        # Rollback any uncommitted changes
        await session.rollback()


@pytest_asyncio.fixture
async def test_user(test_db) -> dict:
    """Create or get a test user."""
    global _test_user_cache

    # Try to get existing user from cache and verify
    if _test_user_cache is not None:
        try:
            result = await test_db.execute(
                text("SELECT id FROM users WHERE id = :id"),
                {"id": uuid.UUID(_test_user_cache["id"])},
            )
            if result.fetchone():
                return _test_user_cache
        except Exception:
            pass

    # Try to get existing user from database
    result = await test_db.execute(
        text(
            "SELECT id, tenant_id, email, role FROM users "
            "WHERE email = 'test@example.com'"
        )
    )
    row = result.fetchone()

    if row:
        _test_user_cache = {
            "id": str(row[0]),
            "tenant_id": str(row[1]),
            "email": row[2],
            "role": row[3],
        }
        return _test_user_cache

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
            INSERT INTO users (
                id, tenant_id, email, hashed_password,
                first_name, last_name, role, is_active,
                created_at, updated_at
            )
            VALUES (
                :id, :tenant_id, :email, :password,
                :first_name, :last_name, :role, true,
                :created_at, :updated_at
            )
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

    _test_user_cache = {
        "id": str(user_id),
        "tenant_id": str(tenant_id),
        "email": "test@example.com",
        "role": "system_admin",
    }
    return _test_user_cache


@pytest_asyncio.fixture
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


@pytest_asyncio.fixture
async def client(db_session_factory) -> AsyncGenerator[AsyncClient, None]:
    """Create test client with overridden database dependency."""
    from app.main import app

    # Override the get_db dependency to use the test session
    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        async with db_session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport,
        base_url="http://test",
        timeout=30.0,
    ) as async_client:
        yield async_client

    # Clear the override after test
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def cleanup_test_cases(test_db):
    """Cleanup test cases after tests."""
    yield
    try:
        await test_db.execute(
            text(
                "DELETE FROM audit_case_findings WHERE audit_case_id IN "
                "(SELECT id FROM audit_cases WHERE case_number LIKE 'TEST-%')"
            )
        )
        await test_db.execute(
            text(
                "DELETE FROM audit_logs WHERE entity_id IN "
                "(SELECT id FROM audit_cases WHERE case_number LIKE 'TEST-%')"
            )
        )
        await test_db.execute(
            text("DELETE FROM audit_cases WHERE case_number LIKE 'TEST-%'")
        )
        await test_db.commit()
    except Exception:
        await test_db.rollback()
