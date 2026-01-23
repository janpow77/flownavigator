#!/usr/bin/env python3
"""Create an admin user with full system privileges (system_admin role)."""

import asyncio
import os
import sys
from datetime import datetime, timezone
from uuid import uuid4

# Add backend app to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "apps", "backend"))

from passlib.context import CryptContext
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Password hashing (same as app/core/security.py)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password: str) -> str:
    """Generate password hash."""
    return pwd_context.hash(password)


async def create_admin_user(
    email: str,
    password: str,
    first_name: str = "Admin",
    last_name: str = "User",
) -> None:
    """Create admin user with system_admin role."""

    # Get database URL from environment or use default
    database_url = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://flowaudit:dev_password@localhost:5436/flowaudit"
    )

    print(f"Connecting to database...")
    engine = create_async_engine(database_url, echo=False)

    async with engine.begin() as conn:
        # Check if user already exists
        result = await conn.execute(
            text("SELECT id, email, role FROM users WHERE email = :email"),
            {"email": email}
        )
        existing = result.fetchone()

        if existing:
            print(f"User with email '{email}' already exists!")
            print(f"  ID: {existing[0]}")
            print(f"  Role: {existing[2]}")
            await engine.dispose()
            return

        # Create IDs
        tenant_id = str(uuid4())
        user_id = str(uuid4())
        now = datetime.now(timezone.utc)

        # Create system tenant first (required for FK constraint)
        print("Creating system tenant...")
        await conn.execute(
            text("""
                INSERT INTO tenants (id, name, type, status, created_at, updated_at)
                VALUES (:id, :name, :type, :status, :created_at, :updated_at)
                ON CONFLICT (id) DO NOTHING
            """),
            {
                "id": tenant_id,
                "name": "System Administration",
                "type": "group",
                "status": "active",
                "created_at": now,
                "updated_at": now,
            }
        )

        # Hash password
        hashed_password = get_password_hash(password)

        # Create admin user
        print(f"Creating admin user '{email}'...")
        await conn.execute(
            text("""
                INSERT INTO users (
                    id, tenant_id, email, hashed_password,
                    first_name, last_name, role, is_active,
                    created_at, updated_at
                )
                VALUES (
                    :id, :tenant_id, :email, :hashed_password,
                    :first_name, :last_name, :role, true,
                    :created_at, :updated_at
                )
            """),
            {
                "id": user_id,
                "tenant_id": tenant_id,
                "email": email,
                "hashed_password": hashed_password,
                "first_name": first_name,
                "last_name": last_name,
                "role": "system_admin",
                "created_at": now,
                "updated_at": now,
            }
        )

        await conn.commit()

    await engine.dispose()

    print("\n" + "=" * 50)
    print("Admin user created successfully!")
    print("=" * 50)
    print(f"  Email:      {email}")
    print(f"  Password:   {password}")
    print(f"  Role:       system_admin (full privileges)")
    print(f"  User ID:    {user_id}")
    print(f"  Tenant ID:  {tenant_id}")
    print("=" * 50)
    print("\nYou can now login at: http://localhost:3001")


def main():
    """Main entry point."""
    # Default credentials
    email = os.getenv("ADMIN_EMAIL", "admin@flownavigator.local")
    password = os.getenv("ADMIN_PASSWORD", "Admin123!")
    first_name = os.getenv("ADMIN_FIRST_NAME", "System")
    last_name = os.getenv("ADMIN_LAST_NAME", "Administrator")

    # Allow command line arguments
    if len(sys.argv) >= 3:
        email = sys.argv[1]
        password = sys.argv[2]
    if len(sys.argv) >= 4:
        first_name = sys.argv[3]
    if len(sys.argv) >= 5:
        last_name = sys.argv[4]

    print("\n" + "=" * 50)
    print("FlowNavigator - Admin User Creation")
    print("=" * 50)

    asyncio.run(create_admin_user(email, password, first_name, last_name))


if __name__ == "__main__":
    main()
