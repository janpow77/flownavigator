#!/bin/bash
#
# Create an admin user with full system privileges (system_admin role)
#
# Usage:
#   ./scripts/create-admin.sh                              # Use defaults
#   ./scripts/create-admin.sh admin@example.com MyPassword # Custom credentials
#   ./scripts/create-admin.sh email password FirstName LastName
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

echo ""
echo "========================================"
echo "FlowNavigator - Create Admin User"
echo "========================================"

# Check if backend container is running
if ! docker ps --format '{{.Names}}' | grep -q "flownavigator-backend"; then
    echo "ERROR: Backend container is not running!"
    echo "Please start the application first with:"
    echo "  docker-compose up -d"
    exit 1
fi

# Execute the Python script inside the backend container
docker exec -it flownavigator-backend python -c "
import asyncio
import os
from datetime import datetime, timezone
from uuid import uuid4
from passlib.context import CryptContext
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')

async def create_admin():
    email = '${1:-admin@flownavigator.local}'
    password = '${2:-Admin123!}'
    first_name = '${3:-System}'
    last_name = '${4:-Administrator}'

    database_url = os.getenv('DATABASE_URL')
    engine = create_async_engine(database_url, echo=False)

    async with engine.begin() as conn:
        # Check existing
        result = await conn.execute(
            text('SELECT id, role FROM users WHERE email = :email'),
            {'email': email}
        )
        existing = result.fetchone()
        if existing:
            print(f'User {email} already exists with role: {existing[1]}')
            return

        tenant_id = str(uuid4())
        user_id = str(uuid4())
        now = datetime.now(timezone.utc)

        # Create tenant
        await conn.execute(
            text('''
                INSERT INTO tenants (id, name, type, status, created_at, updated_at)
                VALUES (:id, :name, :type, :status, :created_at, :updated_at)
            '''),
            {'id': tenant_id, 'name': 'System Administration', 'type': 'group',
             'status': 'active', 'created_at': now, 'updated_at': now}
        )

        # Create user
        hashed = pwd_context.hash(password)
        await conn.execute(
            text('''
                INSERT INTO users (id, tenant_id, email, hashed_password, first_name, last_name, role, is_active, created_at, updated_at)
                VALUES (:id, :tenant_id, :email, :hashed_password, :first_name, :last_name, :role, true, :created_at, :updated_at)
            '''),
            {'id': user_id, 'tenant_id': tenant_id, 'email': email, 'hashed_password': hashed,
             'first_name': first_name, 'last_name': last_name, 'role': 'system_admin',
             'created_at': now, 'updated_at': now}
        )

        print('')
        print('=' * 50)
        print('Admin user created successfully!')
        print('=' * 50)
        print(f'  Email:    {email}')
        print(f'  Password: {password}')
        print(f'  Role:     system_admin (full privileges)')
        print('=' * 50)
        print('')
        print('Login at: http://localhost:3001')

    await engine.dispose()

asyncio.run(create_admin())
"

echo ""
