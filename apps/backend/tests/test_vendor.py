"""Tests for Vendor API endpoints (Layer 0)."""

import uuid
from datetime import datetime, timezone, date

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import text

from app.core.security import create_access_token, get_password_hash
from app.models.vendor import VendorRole


# Test data
TEST_VENDOR_DATA = {
    "name": "FlowAudit GmbH",
    "contact_email": "support@flowaudit.de",
    "billing_email": "billing@flowaudit.de",
    "address_city": "Berlin",
    "address_country": "Deutschland",
}

TEST_VENDOR_USER_DATA = {
    "email": "vendoruser@flowaudit.de",
    "password": "securepassword123",
    "first_name": "Test",
    "last_name": "VendorUser",
    "role": "vendor_admin",
}


@pytest_asyncio.fixture
async def vendor(test_db) -> dict:
    """Create a test vendor."""
    vendor_id = uuid.uuid4()
    now = datetime.now(timezone.utc)

    await test_db.execute(
        text(
            """
            INSERT INTO vendors (id, name, contact_email, billing_email,
                address_city, address_country, created_at, updated_at)
            VALUES (:id, :name, :contact_email, :billing_email,
                :address_city, :address_country, :created_at, :updated_at)
            ON CONFLICT (id) DO NOTHING
            """
        ),
        {
            "id": vendor_id,
            **TEST_VENDOR_DATA,
            "created_at": now,
            "updated_at": now,
        },
    )
    await test_db.commit()

    return {"id": str(vendor_id), **TEST_VENDOR_DATA}


@pytest_asyncio.fixture
async def vendor_admin(test_db, vendor) -> dict:
    """Create a vendor admin user."""
    user_id = uuid.uuid4()
    now = datetime.now(timezone.utc)
    email = f"admin_{user_id.hex[:8]}@flowaudit.de"

    await test_db.execute(
        text(
            """
            INSERT INTO vendor_users (id, vendor_id, email, hashed_password,
                role, first_name, last_name, is_active, created_at, updated_at)
            VALUES (:id, :vendor_id, :email, :hashed_password,
                :role, :first_name, :last_name, true, :created_at, :updated_at)
            """
        ),
        {
            "id": user_id,
            "vendor_id": uuid.UUID(vendor["id"]),
            "email": email,
            "hashed_password": get_password_hash("password123"),
            "role": "vendor_admin",
            "first_name": "Admin",
            "last_name": "User",
            "created_at": now,
            "updated_at": now,
        },
    )
    await test_db.commit()

    return {
        "id": str(user_id),
        "vendor_id": vendor["id"],
        "email": email,
        "role": "vendor_admin",
    }


@pytest_asyncio.fixture
async def vendor_support(test_db, vendor) -> dict:
    """Create a vendor support user."""
    user_id = uuid.uuid4()
    now = datetime.now(timezone.utc)
    email = f"support_{user_id.hex[:8]}@flowaudit.de"

    await test_db.execute(
        text(
            """
            INSERT INTO vendor_users (id, vendor_id, email, hashed_password,
                role, first_name, last_name, is_active, created_at, updated_at)
            VALUES (:id, :vendor_id, :email, :hashed_password,
                :role, :first_name, :last_name, true, :created_at, :updated_at)
            """
        ),
        {
            "id": user_id,
            "vendor_id": uuid.UUID(vendor["id"]),
            "email": email,
            "hashed_password": get_password_hash("password123"),
            "role": "vendor_support",
            "first_name": "Support",
            "last_name": "User",
            "created_at": now,
            "updated_at": now,
        },
    )
    await test_db.commit()

    return {
        "id": str(user_id),
        "vendor_id": vendor["id"],
        "email": email,
        "role": "vendor_support",
    }


@pytest_asyncio.fixture
async def vendor_developer(test_db, vendor) -> dict:
    """Create a vendor developer user."""
    user_id = uuid.uuid4()
    now = datetime.now(timezone.utc)
    email = f"developer_{user_id.hex[:8]}@flowaudit.de"

    await test_db.execute(
        text(
            """
            INSERT INTO vendor_users (id, vendor_id, email, hashed_password,
                role, first_name, last_name, is_active, created_at, updated_at)
            VALUES (:id, :vendor_id, :email, :hashed_password,
                :role, :first_name, :last_name, true, :created_at, :updated_at)
            """
        ),
        {
            "id": user_id,
            "vendor_id": uuid.UUID(vendor["id"]),
            "email": email,
            "hashed_password": get_password_hash("password123"),
            "role": "vendor_developer",
            "first_name": "Developer",
            "last_name": "User",
            "created_at": now,
            "updated_at": now,
        },
    )
    await test_db.commit()

    return {
        "id": str(user_id),
        "vendor_id": vendor["id"],
        "email": email,
        "role": "vendor_developer",
    }


@pytest_asyncio.fixture
async def vendor_qa(test_db, vendor) -> dict:
    """Create a vendor QA user."""
    user_id = uuid.uuid4()
    now = datetime.now(timezone.utc)
    email = f"qa_{user_id.hex[:8]}@flowaudit.de"

    await test_db.execute(
        text(
            """
            INSERT INTO vendor_users (id, vendor_id, email, hashed_password,
                role, first_name, last_name, is_active, created_at, updated_at)
            VALUES (:id, :vendor_id, :email, :hashed_password,
                :role, :first_name, :last_name, true, :created_at, :updated_at)
            """
        ),
        {
            "id": user_id,
            "vendor_id": uuid.UUID(vendor["id"]),
            "email": email,
            "hashed_password": get_password_hash("password123"),
            "role": "vendor_qa",
            "first_name": "QA",
            "last_name": "User",
            "created_at": now,
            "updated_at": now,
        },
    )
    await test_db.commit()

    return {
        "id": str(user_id),
        "vendor_id": vendor["id"],
        "email": email,
        "role": "vendor_qa",
    }


@pytest_asyncio.fixture
def vendor_admin_headers(vendor_admin) -> dict:
    """Auth headers for vendor admin."""
    token = create_access_token(
        data={
            "sub": vendor_admin["id"],
            "type": "vendor",
            "role": vendor_admin["role"],
        }
    )
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
def vendor_support_headers(vendor_support) -> dict:
    """Auth headers for vendor support."""
    token = create_access_token(
        data={
            "sub": vendor_support["id"],
            "type": "vendor",
            "role": vendor_support["role"],
        }
    )
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
def vendor_developer_headers(vendor_developer) -> dict:
    """Auth headers for vendor developer."""
    token = create_access_token(
        data={
            "sub": vendor_developer["id"],
            "type": "vendor",
            "role": vendor_developer["role"],
        }
    )
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
def vendor_qa_headers(vendor_qa) -> dict:
    """Auth headers for vendor QA."""
    token = create_access_token(
        data={
            "sub": vendor_qa["id"],
            "type": "vendor",
            "role": vendor_qa["role"],
        }
    )
    return {"Authorization": f"Bearer {token}"}


class TestVendorAPI:
    """Tests for Vendor API endpoints."""

    @pytest.mark.asyncio
    async def test_vendor_admin_access(
        self, client: AsyncClient, vendor_admin_headers: dict, vendor: dict
    ):
        """AC-1.4.1: vendor_admin kann alle Endpoints aufrufen."""
        # GET vendor
        response = await client.get("/api/v1/vendor", headers=vendor_admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == vendor["name"]

        # GET users
        response = await client.get("/api/v1/vendor/users", headers=vendor_admin_headers)
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_vendor_support_readonly(
        self, client: AsyncClient, vendor_support_headers: dict, vendor: dict
    ):
        """AC-1.4.2: vendor_support hat nur Lesezugriff."""
        # GET erlaubt
        response = await client.get("/api/v1/vendor", headers=vendor_support_headers)
        assert response.status_code == 200

        # POST/PUT verboten
        response = await client.post(
            "/api/v1/vendor/users",
            headers=vendor_support_headers,
            json={
                "email": "new@flowaudit.de",
                "password": "password123",
                "first_name": "New",
                "last_name": "User",
                "role": "vendor_support",
            },
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_developer_create_module(
        self, client: AsyncClient, vendor_developer_headers: dict
    ):
        """AC-1.4.3: vendor_developer kann Module erstellen."""
        response = await client.post(
            "/api/v1/modules",
            headers=vendor_developer_headers,
            json={
                "name": "Test-Module",
                "version": "1.0.0",
                "description": "Test module for development",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "development"
        assert data["name"] == "Test-Module"

    @pytest.mark.asyncio
    async def test_qa_release_module(
        self, client: AsyncClient, vendor_developer_headers: dict, vendor_qa_headers: dict
    ):
        """AC-1.4.4: vendor_qa kann Module releasen."""
        # Create module as developer
        response = await client.post(
            "/api/v1/modules",
            headers=vendor_developer_headers,
            json={
                "name": "Release-Test-Module",
                "version": "1.0.0",
                "description": "Module for release test",
            },
        )
        assert response.status_code == 201
        module_id = response.json()["id"]

        # Release as QA
        response = await client.post(
            f"/api/v1/modules/{module_id}/release",
            headers=vendor_qa_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "released"
        assert data["released_at"] is not None

    @pytest.mark.asyncio
    async def test_no_access_for_regular_users(
        self, client: AsyncClient, auth_headers: dict
    ):
        """AC-1.4.5: Normale User haben keinen Zugriff."""
        response = await client.get("/api/v1/vendor", headers=auth_headers)
        assert response.status_code == 401  # Invalid token type

    @pytest.mark.asyncio
    async def test_create_vendor_user_all_roles(
        self, client: AsyncClient, vendor_admin_headers: dict
    ):
        """AC-1.1.2: VendorUser kann mit allen 4 Rollen erstellt werden."""
        roles = ["vendor_admin", "vendor_support", "vendor_developer", "vendor_qa"]
        unique_suffix = uuid.uuid4().hex[:8]

        for role in roles:
            response = await client.post(
                "/api/v1/vendor/users",
                headers=vendor_admin_headers,
                json={
                    "email": f"{role}_{unique_suffix}@flowaudit.de",
                    "password": "password123",
                    "first_name": "Test",
                    "last_name": role,
                    "role": role,
                },
            )
            assert response.status_code == 201, f"Failed for role {role}: {response.json()}"
            data = response.json()
            assert data["role"] == role


class TestCustomerAPI:
    """Tests for Customer API endpoints."""

    @pytest_asyncio.fixture
    async def customer(self, test_db, vendor) -> dict:
        """Create a test customer."""
        customer_id = uuid.uuid4()
        tenant_id = uuid.uuid4()
        now = datetime.now(timezone.utc)

        # Create tenant first
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
                "name": "Test Customer Tenant",
                "type": "group",
                "status": "active",
                "created_at": now,
                "updated_at": now,
            },
        )

        # Create customer
        await test_db.execute(
            text(
                """
                INSERT INTO customers (id, vendor_id, tenant_id, contract_number,
                    licensed_users, licensed_authorities, billing_address_country, status, created_at, updated_at)
                VALUES (:id, :vendor_id, :tenant_id, :contract_number,
                    :licensed_users, :licensed_authorities, :billing_address_country, :status, :created_at, :updated_at)
                """
            ),
            {
                "id": customer_id,
                "vendor_id": uuid.UUID(vendor["id"]),
                "tenant_id": tenant_id,
                "contract_number": f"2024-TEST-{customer_id.hex[:6]}",
                "licensed_users": 50,
                "licensed_authorities": 5,
                "billing_address_country": "Deutschland",
                "status": "active",
                "created_at": now,
                "updated_at": now,
            },
        )
        await test_db.commit()

        return {
            "id": str(customer_id),
            "tenant_id": str(tenant_id),
            "vendor_id": vendor["id"],
            "contract_number": "2024-TEST-001",
            "licensed_users": 50,
            "licensed_authorities": 5,
        }

    @pytest.mark.asyncio
    async def test_customer_creates_tenant(
        self, client: AsyncClient, vendor_admin_headers: dict
    ):
        """AC-1.4.6: Customer-Erstellung erstellt Tenant automatisch."""
        response = await client.post(
            "/api/v1/customers",
            headers=vendor_admin_headers,
            json={
                "contract_number": f"2024-AUTO-{uuid.uuid4().hex[:6]}",
                "licensed_users": 50,
                "licensed_authorities": 5,
                "tenant_name": "Auto-Created Tenant",
                "tenant_type": "group",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["tenant_id"] is not None

    @pytest.mark.asyncio
    async def test_create_customer_with_licenses(
        self, client: AsyncClient, vendor_admin_headers: dict
    ):
        """AC-1.1.3: Customer mit Lizenzinfos kann erstellt werden."""
        response = await client.post(
            "/api/v1/customers",
            headers=vendor_admin_headers,
            json={
                "contract_number": f"2024-LIC-{uuid.uuid4().hex[:6]}",
                "licensed_users": 100,
                "licensed_authorities": 10,
                "tenant_name": "Licensed Customer",
                "tenant_type": "group",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["licensed_users"] == 100
        assert data["licensed_authorities"] == 10

    @pytest.mark.asyncio
    async def test_license_history_30_days(
        self, client: AsyncClient, vendor_admin_headers: dict, customer: dict, test_db
    ):
        """AC-1.4.7: Lizenz-Historie zeigt 30 Tage."""
        # Create some license usage records
        for i in range(5):
            usage_id = uuid.uuid4()
            usage_date = date.today()
            await test_db.execute(
                text(
                    """
                    INSERT INTO license_usages (id, customer_id, date, active_users,
                        active_authorities, created_at)
                    VALUES (:id, :customer_id, :date, :active_users,
                        :active_authorities, :created_at)
                    ON CONFLICT DO NOTHING
                    """
                ),
                {
                    "id": usage_id,
                    "customer_id": uuid.UUID(customer["id"]),
                    "date": usage_date,
                    "active_users": 40 + i,
                    "active_authorities": 3,
                    "created_at": datetime.now(timezone.utc),
                },
            )
        await test_db.commit()

        response = await client.get(
            f"/api/v1/customers/{customer['id']}/licenses",
            headers=vendor_admin_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "history" in data
        assert len(data["history"]) <= 30


class TestModuleDeploymentAPI:
    """Tests for Module Deployment API endpoints."""

    @pytest.mark.asyncio
    async def test_module_lifecycle(
        self, client: AsyncClient, vendor_developer_headers: dict, vendor_qa_headers: dict
    ):
        """AC-1.1.6: Module kann erstellt und released werden."""
        # Create module
        response = await client.post(
            "/api/v1/modules",
            headers=vendor_developer_headers,
            json={
                "name": "Lifecycle-Module",
                "version": "1.0.0",
                "description": "Test lifecycle",
            },
        )
        assert response.status_code == 201
        module = response.json()
        assert module["status"] == "development"

        # Release
        response = await client.post(
            f"/api/v1/modules/{module['id']}/release",
            headers=vendor_qa_headers,
        )
        assert response.status_code == 200
        released = response.json()
        assert released["status"] == "released"
        assert released["released_at"] is not None

    @pytest.mark.asyncio
    async def test_release_note_creation(
        self, client: AsyncClient, vendor_developer_headers: dict, vendor_qa_headers: dict
    ):
        """AC-1.1.8: ReleaseNote wird bei Release erstellt."""
        # Create module
        response = await client.post(
            "/api/v1/modules",
            headers=vendor_developer_headers,
            json={
                "name": "ReleaseNote-Module",
                "version": "1.0.0",
                "description": "Test release notes",
            },
        )
        module_id = response.json()["id"]

        # Create release note
        response = await client.post(
            f"/api/v1/modules/{module_id}/release-notes",
            headers=vendor_qa_headers,
            json={
                "version": "1.0.0",
                "title": "Initial Release",
                "changes": ["Feature A hinzugefügt", "Feature B hinzugefügt"],
                "breaking_changes": [],
            },
        )
        assert response.status_code == 201
        note = response.json()
        assert len(note["changes"]) == 2
        assert note["title"] == "Initial Release"
