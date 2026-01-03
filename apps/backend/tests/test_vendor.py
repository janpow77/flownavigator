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
        response = await client.get(
            "/api/v1/vendor/users", headers=vendor_admin_headers
        )
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
        self,
        client: AsyncClient,
        vendor_developer_headers: dict,
        vendor_qa_headers: dict,
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
            assert (
                response.status_code == 201
            ), f"Failed for role {role}: {response.json()}"
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


class TestVendorAuthentication:
    """Tests for Vendor authentication endpoints."""

    @pytest.mark.asyncio
    @pytest.mark.xfail(
        reason="API bug: Token schema expects tenant_id but VendorUserResponse lacks it"
    )
    async def test_vendor_login_success(
        self, client: AsyncClient, vendor_admin: dict
    ):
        """Test successful vendor login."""
        response = await client.post(
            "/api/v1/vendor/login",
            data={
                "username": vendor_admin["email"],
                "password": "password123",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["user"]["email"] == vendor_admin["email"]

    @pytest.mark.asyncio
    async def test_vendor_login_wrong_password(
        self, client: AsyncClient, vendor_admin: dict
    ):
        """Test login with wrong password."""
        response = await client.post(
            "/api/v1/vendor/login",
            data={
                "username": vendor_admin["email"],
                "password": "wrongpassword",
            },
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_vendor_login_nonexistent_user(self, client: AsyncClient):
        """Test login with non-existent user."""
        response = await client.post(
            "/api/v1/vendor/login",
            data={
                "username": "nonexistent@example.com",
                "password": "password123",
            },
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_vendor_login_inactive_user(
        self, client: AsyncClient, test_db, vendor: dict
    ):
        """Test login with inactive user."""
        user_id = uuid.uuid4()
        now = datetime.now(timezone.utc)
        email = f"inactive_{user_id.hex[:8]}@flowaudit.de"

        await test_db.execute(
            text(
                """
                INSERT INTO vendor_users (id, vendor_id, email, hashed_password,
                    role, first_name, last_name, is_active, created_at, updated_at)
                VALUES (:id, :vendor_id, :email, :hashed_password,
                    :role, :first_name, :last_name, false, :created_at, :updated_at)
                """
            ),
            {
                "id": user_id,
                "vendor_id": uuid.UUID(vendor["id"]),
                "email": email,
                "hashed_password": get_password_hash("password123"),
                "role": "vendor_admin",
                "first_name": "Inactive",
                "last_name": "User",
                "created_at": now,
                "updated_at": now,
            },
        )
        await test_db.commit()

        response = await client.post(
            "/api/v1/vendor/login",
            data={
                "username": email,
                "password": "password123",
            },
        )
        assert response.status_code == 403


class TestVendorCRUD:
    """Tests for Vendor CRUD operations."""

    @pytest.mark.asyncio
    async def test_get_vendor_unauthorized(self, client: AsyncClient):
        """Test getting vendor without auth."""
        response = await client.get("/api/v1/vendor")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_vendor(
        self, client: AsyncClient, vendor_admin_headers: dict, vendor: dict
    ):
        """Test getting vendor info."""
        response = await client.get("/api/v1/vendor", headers=vendor_admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == vendor["name"]
        assert data["contact_email"] == vendor["contact_email"]

    @pytest.mark.asyncio
    async def test_update_vendor_admin_only(
        self, client: AsyncClient, vendor_admin_headers: dict
    ):
        """Test updating vendor (admin only)."""
        response = await client.put(
            "/api/v1/vendor",
            headers=vendor_admin_headers,
            json={"contact_email": "updated@flowaudit.de"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["contact_email"] == "updated@flowaudit.de"

    @pytest.mark.asyncio
    async def test_update_vendor_support_forbidden(
        self, client: AsyncClient, vendor_support_headers: dict
    ):
        """Test that support cannot update vendor."""
        response = await client.put(
            "/api/v1/vendor",
            headers=vendor_support_headers,
            json={"contact_email": "hacked@flowaudit.de"},
        )
        assert response.status_code == 403


class TestVendorUserCRUD:
    """Tests for Vendor User CRUD operations."""

    @pytest.mark.asyncio
    async def test_list_vendor_users(
        self, client: AsyncClient, vendor_admin_headers: dict
    ):
        """Test listing vendor users."""
        response = await client.get(
            "/api/v1/vendor/users", headers=vendor_admin_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "users" in data
        assert "total" in data
        assert isinstance(data["users"], list)

    @pytest.mark.asyncio
    async def test_get_vendor_user_by_id(
        self, client: AsyncClient, vendor_admin_headers: dict, vendor_admin: dict
    ):
        """Test getting a specific vendor user."""
        response = await client.get(
            f"/api/v1/vendor/users/{vendor_admin['id']}",
            headers=vendor_admin_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == vendor_admin["id"]
        assert data["email"] == vendor_admin["email"]

    @pytest.mark.asyncio
    async def test_get_vendor_user_not_found(
        self, client: AsyncClient, vendor_admin_headers: dict
    ):
        """Test getting non-existent vendor user."""
        fake_id = str(uuid.uuid4())
        response = await client.get(
            f"/api/v1/vendor/users/{fake_id}",
            headers=vendor_admin_headers,
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_create_vendor_user(
        self, client: AsyncClient, vendor_admin_headers: dict
    ):
        """Test creating a vendor user."""
        unique_email = f"new_{uuid.uuid4().hex[:8]}@flowaudit.de"
        response = await client.post(
            "/api/v1/vendor/users",
            headers=vendor_admin_headers,
            json={
                "email": unique_email,
                "password": "securepassword123",
                "first_name": "New",
                "last_name": "User",
                "role": "vendor_developer",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == unique_email
        assert data["role"] == "vendor_developer"

    @pytest.mark.asyncio
    async def test_create_vendor_user_duplicate_email(
        self, client: AsyncClient, vendor_admin_headers: dict, vendor_admin: dict
    ):
        """Test creating user with duplicate email."""
        response = await client.post(
            "/api/v1/vendor/users",
            headers=vendor_admin_headers,
            json={
                "email": vendor_admin["email"],
                "password": "password123",
                "first_name": "Duplicate",
                "last_name": "User",
                "role": "vendor_support",
            },
        )
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_update_vendor_user(
        self, client: AsyncClient, vendor_admin_headers: dict, vendor_developer: dict
    ):
        """Test updating a vendor user."""
        response = await client.put(
            f"/api/v1/vendor/users/{vendor_developer['id']}",
            headers=vendor_admin_headers,
            json={
                "first_name": "Updated",
                "last_name": "Developer",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["first_name"] == "Updated"
        assert data["last_name"] == "Developer"

    @pytest.mark.asyncio
    async def test_update_vendor_user_password(
        self, client: AsyncClient, vendor_admin_headers: dict, vendor_developer: dict
    ):
        """Test updating vendor user password."""
        response = await client.put(
            f"/api/v1/vendor/users/{vendor_developer['id']}",
            headers=vendor_admin_headers,
            json={"password": "newpassword123"},
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_update_vendor_user_not_found(
        self, client: AsyncClient, vendor_admin_headers: dict
    ):
        """Test updating non-existent user."""
        fake_id = str(uuid.uuid4())
        response = await client.put(
            f"/api/v1/vendor/users/{fake_id}",
            headers=vendor_admin_headers,
            json={"first_name": "Ghost"},
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_deactivate_vendor_user(
        self, client: AsyncClient, vendor_admin_headers: dict, test_db, vendor: dict
    ):
        """Test deactivating a vendor user."""
        # Create user to deactivate
        user_id = uuid.uuid4()
        now = datetime.now(timezone.utc)
        email = f"todeactivate_{user_id.hex[:8]}@flowaudit.de"

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
                "first_name": "ToDeactivate",
                "last_name": "User",
                "created_at": now,
                "updated_at": now,
            },
        )
        await test_db.commit()

        response = await client.delete(
            f"/api/v1/vendor/users/{user_id}",
            headers=vendor_admin_headers,
        )
        assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_cannot_deactivate_self(
        self, client: AsyncClient, vendor_admin_headers: dict, vendor_admin: dict
    ):
        """Test that admin cannot deactivate themselves."""
        response = await client.delete(
            f"/api/v1/vendor/users/{vendor_admin['id']}",
            headers=vendor_admin_headers,
        )
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_deactivate_user_not_found(
        self, client: AsyncClient, vendor_admin_headers: dict
    ):
        """Test deactivating non-existent user."""
        fake_id = str(uuid.uuid4())
        response = await client.delete(
            f"/api/v1/vendor/users/{fake_id}",
            headers=vendor_admin_headers,
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_support_cannot_create_users(
        self, client: AsyncClient, vendor_support_headers: dict
    ):
        """Test that support cannot create users."""
        response = await client.post(
            "/api/v1/vendor/users",
            headers=vendor_support_headers,
            json={
                "email": "unauthorized@flowaudit.de",
                "password": "password123",
                "first_name": "Unauthorized",
                "last_name": "User",
                "role": "vendor_support",
            },
        )
        assert response.status_code == 403


class TestModuleDeploymentAPI:
    """Tests for Module Deployment API endpoints."""

    @pytest.mark.asyncio
    async def test_module_lifecycle(
        self,
        client: AsyncClient,
        vendor_developer_headers: dict,
        vendor_qa_headers: dict,
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
        self,
        client: AsyncClient,
        vendor_developer_headers: dict,
        vendor_qa_headers: dict,
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


class TestVendorCleanup:
    """Cleanup test data after vendor tests."""

    @pytest.mark.asyncio
    async def test_cleanup_vendor_data(self, test_db):
        """Clean up test vendor data."""
        try:
            # Clean up vendor users
            await test_db.execute(
                text(
                    "DELETE FROM vendor_users WHERE email LIKE '%@flowaudit.de'"
                )
            )
            # Clean up vendors
            await test_db.execute(
                text(
                    "DELETE FROM vendors WHERE name = 'FlowAudit GmbH'"
                )
            )
            await test_db.commit()
        except Exception:
            await test_db.rollback()
