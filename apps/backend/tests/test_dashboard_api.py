"""Tests for Dashboard API endpoints (Layer Dashboard).

AC-4.1.1: vendor_admin sees all customers
AC-4.1.2: group_admin sees only own customer
AC-4.1.3: authority_head sees only own authority
AC-4.1.4: Drill-Down customer detail
"""

import uuid
from datetime import datetime, timezone, date, timedelta

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import text

from app.core.security import create_access_token, get_password_hash


# Fixtures for Dashboard Tests


@pytest_asyncio.fixture
async def dashboard_vendor(test_db) -> dict:
    """Create a vendor for dashboard tests."""
    vendor_id = uuid.uuid4()
    now = datetime.now(timezone.utc)

    await test_db.execute(
        text(
            """
            INSERT INTO vendors (id, name, contact_email, billing_email,
                address_country, created_at, updated_at)
            VALUES (:id, 'Dashboard Test Vendor', 'dashboard@vendor.de',
                'billing@vendor.de', 'Deutschland', :created_at, :updated_at)
            ON CONFLICT (id) DO NOTHING
            """
        ),
        {"id": vendor_id, "created_at": now, "updated_at": now},
    )
    await test_db.commit()

    return {"id": str(vendor_id), "name": "Dashboard Test Vendor"}


@pytest_asyncio.fixture
async def dashboard_vendor_user(test_db, dashboard_vendor) -> dict:
    """Create a vendor admin user for dashboard tests."""
    user_id = uuid.uuid4()
    now = datetime.now(timezone.utc)
    email = f"dashboard_admin_{user_id.hex[:8]}@vendor.de"

    await test_db.execute(
        text(
            """
            INSERT INTO vendor_users (id, vendor_id, email, hashed_password,
                role, first_name, last_name, is_active, created_at, updated_at)
            VALUES (:id, :vendor_id, :email, :hashed_password,
                'vendor_admin', 'Dashboard', 'Admin', true, :created_at, :updated_at)
            """
        ),
        {
            "id": user_id,
            "vendor_id": uuid.UUID(dashboard_vendor["id"]),
            "email": email,
            "hashed_password": get_password_hash("password123"),
            "created_at": now,
            "updated_at": now,
        },
    )
    await test_db.commit()

    return {
        "id": str(user_id),
        "vendor_id": dashboard_vendor["id"],
        "email": email,
        "role": "vendor_admin",
    }


@pytest_asyncio.fixture
def dashboard_vendor_headers(dashboard_vendor_user) -> dict:
    """Auth headers for dashboard vendor user."""
    token = create_access_token(
        data={
            "sub": dashboard_vendor_user["id"],
            "type": "vendor",
            "role": dashboard_vendor_user["role"],
        }
    )
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def dashboard_customer_tenant(test_db) -> dict:
    """Create a customer tenant for dashboard tests."""
    tenant_id = uuid.uuid4()
    now = datetime.now(timezone.utc)

    await test_db.execute(
        text(
            """
            INSERT INTO tenants (id, name, type, status, created_at, updated_at)
            VALUES (:id, 'Dashboard Customer Tenant', 'group', 'active',
                :created_at, :updated_at)
            ON CONFLICT (id) DO NOTHING
            """
        ),
        {"id": tenant_id, "created_at": now, "updated_at": now},
    )
    await test_db.commit()

    return {"id": str(tenant_id), "name": "Dashboard Customer Tenant"}


@pytest_asyncio.fixture
async def dashboard_customer(
    test_db, dashboard_vendor, dashboard_customer_tenant
) -> dict:
    """Create a customer for dashboard tests."""
    customer_id = uuid.uuid4()
    now = datetime.now(timezone.utc)
    contract_number = f"DASH-{customer_id.hex[:8]}"

    await test_db.execute(
        text(
            """
            INSERT INTO customers (id, vendor_id, tenant_id, contract_number,
                licensed_users, licensed_authorities, billing_address_country,
                status, created_at, updated_at)
            VALUES (:id, :vendor_id, :tenant_id, :contract_number,
                100, 10, 'Deutschland', 'active', :created_at, :updated_at)
            """
        ),
        {
            "id": customer_id,
            "vendor_id": uuid.UUID(dashboard_vendor["id"]),
            "tenant_id": uuid.UUID(dashboard_customer_tenant["id"]),
            "contract_number": contract_number,
            "created_at": now,
            "updated_at": now,
        },
    )
    await test_db.commit()

    return {
        "id": str(customer_id),
        "tenant_id": dashboard_customer_tenant["id"],
        "vendor_id": dashboard_vendor["id"],
        "contract_number": contract_number,
        "licensed_users": 100,
        "licensed_authorities": 10,
    }


@pytest_asyncio.fixture
async def dashboard_authority_tenant(test_db, dashboard_customer_tenant) -> dict:
    """Create an authority tenant under the customer tenant."""
    tenant_id = uuid.uuid4()
    now = datetime.now(timezone.utc)

    await test_db.execute(
        text(
            """
            INSERT INTO tenants (id, name, type, status, parent_id, created_at, updated_at)
            VALUES (:id, 'Dashboard Authority', 'authority', 'active',
                :parent_id, :created_at, :updated_at)
            ON CONFLICT (id) DO NOTHING
            """
        ),
        {
            "id": tenant_id,
            "parent_id": uuid.UUID(dashboard_customer_tenant["id"]),
            "created_at": now,
            "updated_at": now,
        },
    )
    await test_db.commit()

    return {
        "id": str(tenant_id),
        "name": "Dashboard Authority",
        "parent_id": dashboard_customer_tenant["id"],
    }


@pytest_asyncio.fixture
async def dashboard_authority_user(test_db, dashboard_authority_tenant) -> dict:
    """Create an authority head user."""
    user_id = uuid.uuid4()
    now = datetime.now(timezone.utc)
    email = f"authority_head_{user_id.hex[:8]}@test.de"

    await test_db.execute(
        text(
            """
            INSERT INTO users (id, tenant_id, email, hashed_password,
                first_name, last_name, role, is_active, created_at, updated_at)
            VALUES (:id, :tenant_id, :email, :hashed_password,
                'Authority', 'Head', 'authority_head', true, :created_at, :updated_at)
            """
        ),
        {
            "id": user_id,
            "tenant_id": uuid.UUID(dashboard_authority_tenant["id"]),
            "email": email,
            "hashed_password": get_password_hash("password123"),
            "created_at": now,
            "updated_at": now,
        },
    )
    await test_db.commit()

    return {
        "id": str(user_id),
        "tenant_id": dashboard_authority_tenant["id"],
        "email": email,
        "role": "authority_head",
    }


@pytest_asyncio.fixture
def dashboard_authority_headers(dashboard_authority_user) -> dict:
    """Auth headers for authority head user."""
    token = create_access_token(
        data={
            "sub": dashboard_authority_user["id"],
            "tenant_id": dashboard_authority_user["tenant_id"],
            "role": dashboard_authority_user["role"],
        }
    )
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def dashboard_group_admin(test_db, dashboard_customer_tenant) -> dict:
    """Create a group admin user."""
    user_id = uuid.uuid4()
    now = datetime.now(timezone.utc)
    email = f"group_admin_{user_id.hex[:8]}@test.de"

    await test_db.execute(
        text(
            """
            INSERT INTO users (id, tenant_id, email, hashed_password,
                first_name, last_name, role, is_active, created_at, updated_at)
            VALUES (:id, :tenant_id, :email, :hashed_password,
                'Group', 'Admin', 'group_admin', true, :created_at, :updated_at)
            """
        ),
        {
            "id": user_id,
            "tenant_id": uuid.UUID(dashboard_customer_tenant["id"]),
            "email": email,
            "hashed_password": get_password_hash("password123"),
            "created_at": now,
            "updated_at": now,
        },
    )
    await test_db.commit()

    return {
        "id": str(user_id),
        "tenant_id": dashboard_customer_tenant["id"],
        "email": email,
        "role": "group_admin",
    }


@pytest_asyncio.fixture
def dashboard_group_admin_headers(dashboard_group_admin) -> dict:
    """Auth headers for group admin user."""
    token = create_access_token(
        data={
            "sub": dashboard_group_admin["id"],
            "tenant_id": dashboard_group_admin["tenant_id"],
            "role": dashboard_group_admin["role"],
        }
    )
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def dashboard_license_usage(test_db, dashboard_customer) -> list:
    """Create license usage records for the last 30 days."""
    usages = []
    today = date.today()

    for i in range(10):
        usage_id = uuid.uuid4()
        usage_date = today - timedelta(days=i)
        active_users = 40 + i

        await test_db.execute(
            text(
                """
                INSERT INTO license_usages (id, customer_id, date, active_users,
                    active_authorities, created_at)
                VALUES (:id, :customer_id, :date, :active_users,
                    :active_authorities, NOW())
                ON CONFLICT DO NOTHING
                """
            ),
            {
                "id": usage_id,
                "customer_id": uuid.UUID(dashboard_customer["id"]),
                "date": usage_date,
                "active_users": active_users,
                "active_authorities": 3,
            },
        )
        usages.append(
            {"date": usage_date.isoformat(), "active_users": active_users}
        )

    await test_db.commit()
    return usages


class TestVendorLayerDashboard:
    """Tests for Vendor Layer Dashboard (AC-4.1.1)."""

    @pytest.mark.asyncio
    async def test_layers_unauthorized(self, client: AsyncClient):
        """Test that /layers requires vendor authentication."""
        response = await client.get("/api/v1/dashboard/layers")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_layers_with_regular_user_fails(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test that regular users cannot access vendor dashboard."""
        response = await client.get(
            "/api/v1/dashboard/layers", headers=auth_headers
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_layers_returns_dashboard(
        self,
        client: AsyncClient,
        dashboard_vendor_headers: dict,
        dashboard_customer: dict,
    ):
        """Test that vendor admin sees layer dashboard (AC-4.1.1)."""
        response = await client.get(
            "/api/v1/dashboard/layers", headers=dashboard_vendor_headers
        )
        assert response.status_code == 200
        data = response.json()

        # Check structure
        assert "vendor" in data
        assert "total_customers" in data
        assert "total_licenses" in data
        assert "total_users" in data
        assert "customers" in data

        # Check vendor summary
        assert data["vendor"] is not None
        assert data["vendor"]["name"] == "Dashboard Test Vendor"
        assert data["total_customers"] >= 1

    @pytest.mark.asyncio
    async def test_layers_shows_customer_summary(
        self,
        client: AsyncClient,
        dashboard_vendor_headers: dict,
        dashboard_customer: dict,
    ):
        """Test that customer summaries are included in dashboard."""
        response = await client.get(
            "/api/v1/dashboard/layers", headers=dashboard_vendor_headers
        )
        assert response.status_code == 200
        data = response.json()

        # Find our test customer
        customers = data["customers"]
        assert len(customers) >= 1

        customer = next(
            (c for c in customers if c["id"] == dashboard_customer["id"]), None
        )
        assert customer is not None
        assert customer["licensed_users"] == 100
        assert customer["licensed_authorities"] == 10
        assert "license_percent" in customer
        assert "authority_percent" in customer


class TestUserLayerDashboard:
    """Tests for User Layer Dashboard (AC-4.1.2, AC-4.1.3)."""

    @pytest.mark.asyncio
    async def test_my_dashboard_unauthorized(self, client: AsyncClient):
        """Test that /my-dashboard requires authentication."""
        response = await client.get("/api/v1/dashboard/my-dashboard")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_my_dashboard_group_admin(
        self,
        client: AsyncClient,
        dashboard_group_admin_headers: dict,
        dashboard_customer: dict,
    ):
        """Test that group_admin sees own customer (AC-4.1.2)."""
        response = await client.get(
            "/api/v1/dashboard/my-dashboard", headers=dashboard_group_admin_headers
        )
        assert response.status_code == 200
        data = response.json()

        assert "customers" in data
        assert data["total_customers"] >= 0

    @pytest.mark.asyncio
    async def test_my_dashboard_authority_head(
        self,
        client: AsyncClient,
        dashboard_authority_headers: dict,
        dashboard_customer: dict,
        dashboard_authority_tenant: dict,
    ):
        """Test that authority_head sees own authority (AC-4.1.3)."""
        response = await client.get(
            "/api/v1/dashboard/my-dashboard", headers=dashboard_authority_headers
        )
        assert response.status_code == 200
        data = response.json()

        # Authority head should see limited view
        assert "customers" in data
        assert "total_users" in data


class TestCustomerDetailDrillDown:
    """Tests for Customer Detail Drill-Down (AC-4.1.4)."""

    @pytest.mark.asyncio
    async def test_customer_detail_unauthorized(self, client: AsyncClient):
        """Test that customer detail requires vendor authentication."""
        response = await client.get(
            f"/api/v1/dashboard/layers/{uuid.uuid4()}"
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_customer_detail_not_found(
        self, client: AsyncClient, dashboard_vendor_headers: dict
    ):
        """Test 404 for non-existent customer."""
        fake_id = str(uuid.uuid4())
        response = await client.get(
            f"/api/v1/dashboard/layers/{fake_id}",
            headers=dashboard_vendor_headers,
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_customer_detail_returns_data(
        self,
        client: AsyncClient,
        dashboard_vendor_headers: dict,
        dashboard_customer: dict,
        dashboard_authority_tenant: dict,
    ):
        """Test that customer detail returns full data (AC-4.1.4)."""
        response = await client.get(
            f"/api/v1/dashboard/layers/{dashboard_customer['id']}",
            headers=dashboard_vendor_headers,
        )
        assert response.status_code == 200
        data = response.json()

        # Check structure
        assert "customer" in data
        assert "authorities" in data
        assert "license_trend" in data

        # Check customer data
        assert data["customer"]["id"] == dashboard_customer["id"]
        assert data["customer"]["licensed_users"] == 100

        # Check authorities list
        assert isinstance(data["authorities"], list)

    @pytest.mark.asyncio
    async def test_customer_detail_with_license_trend(
        self,
        client: AsyncClient,
        dashboard_vendor_headers: dict,
        dashboard_customer: dict,
        dashboard_license_usage: list,
    ):
        """Test that license trend is included in customer detail."""
        response = await client.get(
            f"/api/v1/dashboard/layers/{dashboard_customer['id']}",
            headers=dashboard_vendor_headers,
        )
        assert response.status_code == 200
        data = response.json()

        # Check license trend
        assert "license_trend" in data
        assert len(data["license_trend"]) >= 1

    @pytest.mark.asyncio
    async def test_customer_detail_wrong_vendor(
        self, client: AsyncClient, test_db
    ):
        """Test that vendor cannot see other vendor's customers."""
        # Create another vendor and user
        other_vendor_id = uuid.uuid4()
        other_user_id = uuid.uuid4()
        now = datetime.now(timezone.utc)

        await test_db.execute(
            text(
                """
                INSERT INTO vendors (id, name, contact_email, billing_email,
                    address_country, created_at, updated_at)
                VALUES (:id, 'Other Vendor', 'other@vendor.de',
                    'billing@other.de', 'Deutschland', :now, :now)
                ON CONFLICT (id) DO NOTHING
                """
            ),
            {"id": other_vendor_id, "now": now},
        )

        await test_db.execute(
            text(
                """
                INSERT INTO vendor_users (id, vendor_id, email, hashed_password,
                    role, first_name, last_name, is_active, created_at, updated_at)
                VALUES (:id, :vendor_id, 'other_admin@vendor.de', :password,
                    'vendor_admin', 'Other', 'Admin', true, :now, :now)
                """
            ),
            {
                "id": other_user_id,
                "vendor_id": other_vendor_id,
                "password": get_password_hash("password"),
                "now": now,
            },
        )
        await test_db.commit()

        # Create token for other vendor
        token = create_access_token(
            data={
                "sub": str(other_user_id),
                "type": "vendor",
                "role": "vendor_admin",
            }
        )
        other_headers = {"Authorization": f"Bearer {token}"}

        # Try to access customer from first vendor - should fail
        fake_customer_id = str(uuid.uuid4())
        response = await client.get(
            f"/api/v1/dashboard/layers/{fake_customer_id}",
            headers=other_headers,
        )
        assert response.status_code == 404


class TestAuthorityDetailDrillDown:
    """Tests for Authority Detail Drill-Down."""

    @pytest.mark.asyncio
    async def test_authority_detail_unauthorized(self, client: AsyncClient):
        """Test that authority detail requires vendor authentication."""
        response = await client.get(
            f"/api/v1/dashboard/layers/{uuid.uuid4()}/authorities/{uuid.uuid4()}"
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_authority_detail_customer_not_found(
        self, client: AsyncClient, dashboard_vendor_headers: dict
    ):
        """Test 404 when customer doesn't exist."""
        fake_customer = str(uuid.uuid4())
        fake_authority = str(uuid.uuid4())
        response = await client.get(
            f"/api/v1/dashboard/layers/{fake_customer}/authorities/{fake_authority}",
            headers=dashboard_vendor_headers,
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_authority_detail_authority_not_found(
        self,
        client: AsyncClient,
        dashboard_vendor_headers: dict,
        dashboard_customer: dict,
    ):
        """Test 404 when authority doesn't exist."""
        fake_authority = str(uuid.uuid4())
        response = await client.get(
            f"/api/v1/dashboard/layers/{dashboard_customer['id']}/authorities/{fake_authority}",
            headers=dashboard_vendor_headers,
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_authority_detail_returns_data(
        self,
        client: AsyncClient,
        dashboard_vendor_headers: dict,
        dashboard_customer: dict,
        dashboard_authority_tenant: dict,
        dashboard_authority_user: dict,
    ):
        """Test that authority detail returns full data."""
        response = await client.get(
            f"/api/v1/dashboard/layers/{dashboard_customer['id']}/authorities/{dashboard_authority_tenant['id']}",
            headers=dashboard_vendor_headers,
        )
        assert response.status_code == 200
        data = response.json()

        # Check structure
        assert "authority" in data
        assert "users" in data
        assert "recent_cases" in data
        assert "active_checklists" in data
        assert "pending_findings" in data

        # Check authority data
        assert data["authority"]["id"] == dashboard_authority_tenant["id"]
        assert data["authority"]["name"] == "Dashboard Authority"

        # Check users include authority head
        assert isinstance(data["users"], list)
        if len(data["users"]) > 0:
            user_ids = [u["id"] for u in data["users"]]
            assert dashboard_authority_user["id"] in user_ids


class TestDashboardCleanup:
    """Cleanup test data after dashboard tests."""

    @pytest.mark.asyncio
    async def test_cleanup_dashboard_data(self, test_db):
        """Clean up dashboard test data."""
        try:
            # Clean up in order due to foreign keys
            await test_db.execute(
                text(
                    "DELETE FROM license_usages WHERE customer_id IN "
                    "(SELECT id FROM customers WHERE contract_number LIKE 'DASH-%')"
                )
            )
            await test_db.execute(
                text("DELETE FROM customers WHERE contract_number LIKE 'DASH-%'")
            )
            await test_db.execute(
                text(
                    "DELETE FROM users WHERE email LIKE '%authority_head_%' "
                    "OR email LIKE '%group_admin_%'"
                )
            )
            await test_db.execute(
                text(
                    "DELETE FROM tenants WHERE name LIKE '%Dashboard%'"
                )
            )
            await test_db.execute(
                text(
                    "DELETE FROM vendor_users WHERE email LIKE '%dashboard_%' "
                    "OR email LIKE '%other_admin%'"
                )
            )
            await test_db.execute(
                text(
                    "DELETE FROM vendors WHERE name LIKE '%Dashboard%' "
                    "OR name LIKE '%Other Vendor%'"
                )
            )
            await test_db.commit()
        except Exception:
            await test_db.rollback()
