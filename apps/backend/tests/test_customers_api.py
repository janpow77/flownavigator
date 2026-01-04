"""Tests for Customers API endpoints (Layer 0).

Comprehensive tests for customer management, licensing, and alerts.
"""

import uuid
from datetime import date, datetime, timedelta, timezone

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import text

from app.core.security import create_access_token, get_password_hash


# ==============================================================================
# Fixtures
# ==============================================================================


@pytest_asyncio.fixture
async def customers_vendor(test_db) -> dict:
    """Create a test vendor for customers tests."""
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
            "name": "Customer Test Vendor",
            "contact_email": "contact@customertest.de",
            "billing_email": "billing@customertest.de",
            "address_city": "Frankfurt",
            "address_country": "Deutschland",
            "created_at": now,
            "updated_at": now,
        },
    )
    await test_db.commit()

    return {"id": str(vendor_id), "name": "Customer Test Vendor"}


@pytest_asyncio.fixture
async def customers_vendor_admin(test_db, customers_vendor) -> dict:
    """Create a vendor admin user for customers tests."""
    user_id = uuid.uuid4()
    now = datetime.now(timezone.utc)
    email = f"custadmin_{user_id.hex[:8]}@customertest.de"

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
            "vendor_id": uuid.UUID(customers_vendor["id"]),
            "email": email,
            "hashed_password": get_password_hash("password123"),
            "role": "vendor_admin",
            "first_name": "Customer",
            "last_name": "Admin",
            "created_at": now,
            "updated_at": now,
        },
    )
    await test_db.commit()

    return {
        "id": str(user_id),
        "vendor_id": customers_vendor["id"],
        "email": email,
        "role": "vendor_admin",
    }


@pytest_asyncio.fixture
async def customers_vendor_support(test_db, customers_vendor) -> dict:
    """Create a vendor support user for customers tests."""
    user_id = uuid.uuid4()
    now = datetime.now(timezone.utc)
    email = f"custsupport_{user_id.hex[:8]}@customertest.de"

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
            "vendor_id": uuid.UUID(customers_vendor["id"]),
            "email": email,
            "hashed_password": get_password_hash("password123"),
            "role": "vendor_support",
            "first_name": "Customer",
            "last_name": "Support",
            "created_at": now,
            "updated_at": now,
        },
    )
    await test_db.commit()

    return {
        "id": str(user_id),
        "vendor_id": customers_vendor["id"],
        "email": email,
        "role": "vendor_support",
    }


@pytest_asyncio.fixture
def customers_admin_headers(customers_vendor_admin) -> dict:
    """Auth headers for vendor admin."""
    token = create_access_token(
        data={
            "sub": customers_vendor_admin["id"],
            "type": "vendor",
            "role": customers_vendor_admin["role"],
        }
    )
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
def customers_support_headers(customers_vendor_support) -> dict:
    """Auth headers for vendor support."""
    token = create_access_token(
        data={
            "sub": customers_vendor_support["id"],
            "type": "vendor",
            "role": customers_vendor_support["role"],
        }
    )
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def test_customer(test_db, customers_vendor) -> dict:
    """Create a test customer with tenant."""
    customer_id = uuid.uuid4()
    tenant_id = uuid.uuid4()
    now = datetime.now(timezone.utc)
    contract_number = f"CUST-{customer_id.hex[:8]}"

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
                contract_start, contract_end, licensed_users, licensed_authorities,
                billing_contact, billing_email, billing_address_street,
                billing_address_city, billing_address_postal_code,
                billing_address_country, status, created_at, updated_at)
            VALUES (:id, :vendor_id, :tenant_id, :contract_number,
                :contract_start, :contract_end, :licensed_users, :licensed_authorities,
                :billing_contact, :billing_email, :billing_address_street,
                :billing_address_city, :billing_address_postal_code,
                :billing_address_country, :status, :created_at, :updated_at)
            """
        ),
        {
            "id": customer_id,
            "vendor_id": uuid.UUID(customers_vendor["id"]),
            "tenant_id": tenant_id,
            "contract_number": contract_number,
            "contract_start": date.today(),
            "contract_end": date.today() + timedelta(days=365),
            "licensed_users": 50,
            "licensed_authorities": 5,
            "billing_contact": "Max Mustermann",
            "billing_email": "billing@testcustomer.de",
            "billing_address_street": "Teststraße 123",
            "billing_address_city": "Berlin",
            "billing_address_postal_code": "10115",
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
        "vendor_id": customers_vendor["id"],
        "contract_number": contract_number,
        "licensed_users": 50,
        "licensed_authorities": 5,
    }


@pytest_asyncio.fixture
async def customer_with_usage(test_db, test_customer) -> dict:
    """Create customer with license usage data."""
    now = datetime.now(timezone.utc)
    today = date.today()

    # Create usage records for past 7 days
    for i in range(7):
        usage_id = uuid.uuid4()
        usage_date = today - timedelta(days=i)
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
                "customer_id": uuid.UUID(test_customer["id"]),
                "date": usage_date,
                "active_users": 35 + i,
                "active_authorities": 3,
                "created_at": now,
            },
        )
    await test_db.commit()

    return test_customer


@pytest_asyncio.fixture
async def customer_with_alerts(test_db, test_customer, customers_vendor_admin) -> dict:
    """Create customer with license alerts."""
    now = datetime.now(timezone.utc)

    # Create warning alert
    await test_db.execute(
        text(
            """
            INSERT INTO license_alerts (id, customer_id, alert_type, message,
                threshold_percent, current_percent, acknowledged, created_at)
            VALUES (:id, :customer_id, :alert_type, :message,
                :threshold_percent, :current_percent, :acknowledged, :created_at)
            """
        ),
        {
            "id": uuid.uuid4(),
            "customer_id": uuid.UUID(test_customer["id"]),
            "alert_type": "warning",
            "message": "Benutzerlizenzen bei 80% Auslastung",
            "threshold_percent": 80,
            "current_percent": 82,
            "acknowledged": False,
            "created_at": now,
        },
    )

    # Create acknowledged alert
    await test_db.execute(
        text(
            """
            INSERT INTO license_alerts (id, customer_id, alert_type, message,
                threshold_percent, current_percent, acknowledged, acknowledged_at,
                acknowledged_by, created_at)
            VALUES (:id, :customer_id, :alert_type, :message,
                :threshold_percent, :current_percent, :acknowledged, :acknowledged_at,
                :acknowledged_by, :created_at)
            """
        ),
        {
            "id": uuid.uuid4(),
            "customer_id": uuid.UUID(test_customer["id"]),
            "alert_type": "critical",
            "message": "Benutzerlizenzen bei 95% Auslastung",
            "threshold_percent": 95,
            "current_percent": 96,
            "acknowledged": True,
            "acknowledged_at": now,
            "acknowledged_by": uuid.UUID(customers_vendor_admin["id"]),
            "created_at": now - timedelta(hours=2),
        },
    )
    await test_db.commit()

    return test_customer


@pytest_asyncio.fixture
async def unacknowledged_alert(test_db, test_customer) -> dict:
    """Create an unacknowledged alert for testing."""
    alert_id = uuid.uuid4()
    now = datetime.now(timezone.utc)

    await test_db.execute(
        text(
            """
            INSERT INTO license_alerts (id, customer_id, alert_type, message,
                threshold_percent, current_percent, acknowledged, created_at)
            VALUES (:id, :customer_id, :alert_type, :message,
                :threshold_percent, :current_percent, :acknowledged, :created_at)
            """
        ),
        {
            "id": alert_id,
            "customer_id": uuid.UUID(test_customer["id"]),
            "alert_type": "exceeded",
            "message": "Benutzerlizenzlimit überschritten",
            "threshold_percent": 100,
            "current_percent": 110,
            "acknowledged": False,
            "created_at": now,
        },
    )
    await test_db.commit()

    return {"id": str(alert_id), "customer_id": test_customer["id"]}


@pytest_asyncio.fixture
async def customer_with_authorities(test_db, test_customer) -> dict:
    """Create customer with child authority tenants."""
    now = datetime.now(timezone.utc)

    # Create 3 authorities
    for i in range(3):
        auth_tenant_id = uuid.uuid4()
        await test_db.execute(
            text(
                """
                INSERT INTO tenants (id, name, type, status, parent_id, created_at, updated_at)
                VALUES (:id, :name, :type, :status, :parent_id, :created_at, :updated_at)
                ON CONFLICT (id) DO NOTHING
                """
            ),
            {
                "id": auth_tenant_id,
                "name": f"Test Authority {i + 1}",
                "type": "authority",
                "status": "active",
                "parent_id": uuid.UUID(test_customer["tenant_id"]),
                "created_at": now,
                "updated_at": now,
            },
        )
    await test_db.commit()

    return test_customer


# ==============================================================================
# Authentication Tests
# ==============================================================================


class TestCustomersAuthentication:
    """Tests for customers API authentication."""

    @pytest.mark.asyncio
    async def test_list_customers_unauthorized(self, client: AsyncClient):
        """Test that listing customers requires vendor authentication."""
        response = await client.get("/api/v1/customers")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_list_customers_regular_user_forbidden(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test that regular users cannot access customers API."""
        response = await client.get("/api/v1/customers", headers=auth_headers)
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_create_customer_unauthorized(self, client: AsyncClient):
        """Test that creating customer requires authentication."""
        response = await client.post(
            "/api/v1/customers",
            json={
                "contract_number": "TEST-001",
                "tenant_name": "Test",
                "licensed_users": 10,
            },
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_customer_unauthorized(
        self, client: AsyncClient, test_customer: dict
    ):
        """Test that getting customer requires authentication."""
        response = await client.get(f"/api/v1/customers/{test_customer['id']}")
        assert response.status_code == 401


# ==============================================================================
# List Customers Tests
# ==============================================================================


class TestListCustomers:
    """Tests for listing customers."""

    @pytest.mark.asyncio
    async def test_list_customers_empty(
        self,
        client: AsyncClient,
        customers_admin_headers: dict,
        customers_vendor: dict,
    ):
        """Test listing customers when none exist."""
        response = await client.get(
            "/api/v1/customers", headers=customers_admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "customers" in data
        assert "total" in data
        assert isinstance(data["customers"], list)

    @pytest.mark.asyncio
    async def test_list_customers_with_items(
        self,
        client: AsyncClient,
        customers_admin_headers: dict,
        test_customer: dict,
    ):
        """Test listing customers with existing items."""
        response = await client.get(
            "/api/v1/customers", headers=customers_admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        assert any(c["id"] == test_customer["id"] for c in data["customers"])

    @pytest.mark.asyncio
    async def test_list_customers_filter_by_status(
        self,
        client: AsyncClient,
        customers_admin_headers: dict,
        test_customer: dict,
    ):
        """Test filtering customers by status."""
        response = await client.get(
            "/api/v1/customers?status=active", headers=customers_admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        for customer in data["customers"]:
            assert customer["status"] == "active"

    @pytest.mark.asyncio
    async def test_list_customers_pagination(
        self,
        client: AsyncClient,
        customers_admin_headers: dict,
        test_customer: dict,
    ):
        """Test customers pagination."""
        response = await client.get(
            "/api/v1/customers?skip=0&limit=10", headers=customers_admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["customers"]) <= 10

    @pytest.mark.asyncio
    async def test_list_customers_support_access(
        self,
        client: AsyncClient,
        customers_support_headers: dict,
        test_customer: dict,
    ):
        """Test that support users can list customers (read access)."""
        response = await client.get(
            "/api/v1/customers", headers=customers_support_headers
        )

        assert response.status_code == 200


# ==============================================================================
# Create Customer Tests
# ==============================================================================


class TestCreateCustomer:
    """Tests for creating customers."""

    @pytest.mark.asyncio
    async def test_create_customer_success(
        self, client: AsyncClient, customers_admin_headers: dict
    ):
        """Test successful customer creation."""
        contract_number = f"NEW-{uuid.uuid4().hex[:8]}"
        customer_data = {
            "contract_number": contract_number,
            "tenant_name": "New Customer Tenant",
            "tenant_type": "group",
            "licensed_users": 100,
            "licensed_authorities": 10,
            "billing_contact": "Test Contact",
            "billing_email": "billing@newcustomer.de",
        }

        response = await client.post(
            "/api/v1/customers",
            json=customer_data,
            headers=customers_admin_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["contract_number"] == contract_number
        assert data["licensed_users"] == 100
        assert data["licensed_authorities"] == 10
        assert data["tenant_id"] is not None
        assert data["status"] == "active"

    @pytest.mark.asyncio
    async def test_create_customer_with_billing_info(
        self, client: AsyncClient, customers_admin_headers: dict
    ):
        """Test creating customer with full billing information."""
        customer_data = {
            "contract_number": f"BILL-{uuid.uuid4().hex[:8]}",
            "tenant_name": "Billing Customer",
            "licensed_users": 50,
            "billing_contact": "Hans Billing",
            "billing_email": "hans@billing.de",
            "billing_address_street": "Rechnungsstraße 1",
            "billing_address_city": "München",
            "billing_address_postal_code": "80331",
            "billing_address_country": "Deutschland",
            "payment_method": "invoice",
        }

        response = await client.post(
            "/api/v1/customers",
            json=customer_data,
            headers=customers_admin_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["billing_contact"] == "Hans Billing"
        assert data["billing_address_city"] == "München"

    @pytest.mark.asyncio
    async def test_create_customer_with_trial_status(
        self, client: AsyncClient, customers_admin_headers: dict
    ):
        """Test creating customer with trial status."""
        customer_data = {
            "contract_number": f"TRIAL-{uuid.uuid4().hex[:8]}",
            "tenant_name": "Trial Customer",
            "licensed_users": 5,
            "licensed_authorities": 1,
            "status": "trial",
        }

        response = await client.post(
            "/api/v1/customers",
            json=customer_data,
            headers=customers_admin_headers,
        )

        assert response.status_code == 201
        assert response.json()["status"] == "trial"

    @pytest.mark.asyncio
    async def test_create_customer_with_contract_dates(
        self, client: AsyncClient, customers_admin_headers: dict
    ):
        """Test creating customer with contract dates."""
        start_date = date.today().isoformat()
        end_date = (date.today() + timedelta(days=365)).isoformat()

        customer_data = {
            "contract_number": f"DATE-{uuid.uuid4().hex[:8]}",
            "tenant_name": "Dated Customer",
            "licensed_users": 20,
            "contract_start": start_date,
            "contract_end": end_date,
        }

        response = await client.post(
            "/api/v1/customers",
            json=customer_data,
            headers=customers_admin_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["contract_start"] == start_date
        assert data["contract_end"] == end_date

    @pytest.mark.asyncio
    async def test_create_customer_duplicate_contract_number(
        self,
        client: AsyncClient,
        customers_admin_headers: dict,
        test_customer: dict,
    ):
        """Test that duplicate contract numbers are rejected."""
        customer_data = {
            "contract_number": test_customer["contract_number"],
            "tenant_name": "Duplicate Customer",
            "licensed_users": 10,
        }

        response = await client.post(
            "/api/v1/customers",
            json=customer_data,
            headers=customers_admin_headers,
        )

        assert response.status_code == 400
        assert "Vertragsnummer" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_create_customer_support_forbidden(
        self, client: AsyncClient, customers_support_headers: dict
    ):
        """Test that support users cannot create customers."""
        customer_data = {
            "contract_number": f"FORBID-{uuid.uuid4().hex[:8]}",
            "tenant_name": "Forbidden Customer",
            "licensed_users": 10,
        }

        response = await client.post(
            "/api/v1/customers",
            json=customer_data,
            headers=customers_support_headers,
        )

        assert response.status_code == 403


# ==============================================================================
# Get Customer Tests
# ==============================================================================


class TestGetCustomer:
    """Tests for getting customer details."""

    @pytest.mark.asyncio
    async def test_get_customer_success(
        self,
        client: AsyncClient,
        customers_admin_headers: dict,
        test_customer: dict,
    ):
        """Test getting customer details."""
        response = await client.get(
            f"/api/v1/customers/{test_customer['id']}",
            headers=customers_admin_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_customer["id"]
        assert data["contract_number"] == test_customer["contract_number"]
        assert "license_usages" in data
        assert "license_alerts" in data

    @pytest.mark.asyncio
    async def test_get_customer_with_usage_data(
        self,
        client: AsyncClient,
        customers_admin_headers: dict,
        customer_with_usage: dict,
    ):
        """Test getting customer with license usage data."""
        response = await client.get(
            f"/api/v1/customers/{customer_with_usage['id']}",
            headers=customers_admin_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "current_active_users" in data
        assert "current_active_authorities" in data
        assert "user_license_percent" in data
        assert "authority_license_percent" in data

    @pytest.mark.asyncio
    async def test_get_customer_not_found(
        self, client: AsyncClient, customers_admin_headers: dict
    ):
        """Test getting non-existent customer."""
        fake_id = str(uuid.uuid4())
        response = await client.get(
            f"/api/v1/customers/{fake_id}",
            headers=customers_admin_headers,
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_customer_support_access(
        self,
        client: AsyncClient,
        customers_support_headers: dict,
        test_customer: dict,
    ):
        """Test that support users can view customer details."""
        response = await client.get(
            f"/api/v1/customers/{test_customer['id']}",
            headers=customers_support_headers,
        )

        assert response.status_code == 200


# ==============================================================================
# Update Customer Tests
# ==============================================================================


class TestUpdateCustomer:
    """Tests for updating customers."""

    @pytest.mark.asyncio
    async def test_update_customer_success(
        self,
        client: AsyncClient,
        customers_admin_headers: dict,
        test_customer: dict,
    ):
        """Test successful customer update."""
        response = await client.put(
            f"/api/v1/customers/{test_customer['id']}",
            json={
                "billing_contact": "Updated Contact",
                "billing_email": "updated@customer.de",
            },
            headers=customers_admin_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["billing_contact"] == "Updated Contact"
        assert data["billing_email"] == "updated@customer.de"

    @pytest.mark.asyncio
    async def test_update_customer_licensed_users(
        self,
        client: AsyncClient,
        customers_admin_headers: dict,
        test_customer: dict,
    ):
        """Test updating licensed users."""
        response = await client.put(
            f"/api/v1/customers/{test_customer['id']}",
            json={"licensed_users": 100},
            headers=customers_admin_headers,
        )

        assert response.status_code == 200
        assert response.json()["licensed_users"] == 100

    @pytest.mark.asyncio
    async def test_update_customer_status(
        self,
        client: AsyncClient,
        customers_admin_headers: dict,
        test_customer: dict,
    ):
        """Test updating customer status."""
        response = await client.put(
            f"/api/v1/customers/{test_customer['id']}",
            json={"status": "suspended"},
            headers=customers_admin_headers,
        )

        assert response.status_code == 200
        assert response.json()["status"] == "suspended"

    @pytest.mark.asyncio
    async def test_update_customer_contract_number(
        self,
        client: AsyncClient,
        customers_admin_headers: dict,
        test_customer: dict,
    ):
        """Test updating contract number."""
        new_contract = f"UPDATED-{uuid.uuid4().hex[:8]}"
        response = await client.put(
            f"/api/v1/customers/{test_customer['id']}",
            json={"contract_number": new_contract},
            headers=customers_admin_headers,
        )

        assert response.status_code == 200
        assert response.json()["contract_number"] == new_contract

    @pytest.mark.asyncio
    async def test_update_customer_not_found(
        self, client: AsyncClient, customers_admin_headers: dict
    ):
        """Test updating non-existent customer."""
        fake_id = str(uuid.uuid4())
        response = await client.put(
            f"/api/v1/customers/{fake_id}",
            json={"billing_contact": "Ghost"},
            headers=customers_admin_headers,
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_customer_support_forbidden(
        self,
        client: AsyncClient,
        customers_support_headers: dict,
        test_customer: dict,
    ):
        """Test that support users cannot update customers."""
        response = await client.put(
            f"/api/v1/customers/{test_customer['id']}",
            json={"billing_contact": "Forbidden Update"},
            headers=customers_support_headers,
        )

        assert response.status_code == 403


# ==============================================================================
# Terminate Customer Tests
# ==============================================================================


class TestTerminateCustomer:
    """Tests for terminating customers."""

    @pytest.mark.asyncio
    async def test_terminate_customer_success(
        self,
        client: AsyncClient,
        customers_admin_headers: dict,
        test_db,
        customers_vendor: dict,
    ):
        """Test successful customer termination."""
        # Create customer to terminate
        customer_id = uuid.uuid4()
        tenant_id = uuid.uuid4()
        now = datetime.now(timezone.utc)

        await test_db.execute(
            text(
                """
                INSERT INTO tenants (id, name, type, status, created_at, updated_at)
                VALUES (:id, 'Terminate Tenant', 'group', 'active', :now, :now)
                """
            ),
            {"id": tenant_id, "now": now},
        )
        await test_db.execute(
            text(
                """
                INSERT INTO customers (id, vendor_id, tenant_id, contract_number,
                    licensed_users, licensed_authorities, billing_address_country,
                    status, created_at, updated_at)
                VALUES (:id, :vendor_id, :tenant_id, :contract_number,
                    10, 1, 'Deutschland', 'active', :now, :now)
                """
            ),
            {
                "id": customer_id,
                "vendor_id": uuid.UUID(customers_vendor["id"]),
                "tenant_id": tenant_id,
                "contract_number": f"TERM-{customer_id.hex[:8]}",
                "now": now,
            },
        )
        await test_db.commit()

        response = await client.delete(
            f"/api/v1/customers/{customer_id}",
            headers=customers_admin_headers,
        )

        assert response.status_code == 204

        # Verify status changed to terminated
        check_response = await client.get(
            f"/api/v1/customers/{customer_id}",
            headers=customers_admin_headers,
        )
        assert check_response.json()["status"] == "terminated"

    @pytest.mark.asyncio
    async def test_terminate_customer_not_found(
        self, client: AsyncClient, customers_admin_headers: dict
    ):
        """Test terminating non-existent customer."""
        fake_id = str(uuid.uuid4())
        response = await client.delete(
            f"/api/v1/customers/{fake_id}",
            headers=customers_admin_headers,
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_terminate_customer_support_forbidden(
        self,
        client: AsyncClient,
        customers_support_headers: dict,
        test_customer: dict,
    ):
        """Test that support users cannot terminate customers."""
        response = await client.delete(
            f"/api/v1/customers/{test_customer['id']}",
            headers=customers_support_headers,
        )

        assert response.status_code == 403


# ==============================================================================
# License History Tests
# ==============================================================================


class TestLicenseHistory:
    """Tests for license history endpoints."""

    @pytest.mark.asyncio
    async def test_get_license_history_success(
        self,
        client: AsyncClient,
        customers_admin_headers: dict,
        customer_with_usage: dict,
    ):
        """Test getting license usage history."""
        response = await client.get(
            f"/api/v1/customers/{customer_with_usage['id']}/licenses",
            headers=customers_admin_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "history" in data
        assert "licensed_users" in data
        assert "licensed_authorities" in data
        assert "current_user_percent" in data
        assert "current_authority_percent" in data

    @pytest.mark.asyncio
    async def test_get_license_history_custom_days(
        self,
        client: AsyncClient,
        customers_admin_headers: dict,
        customer_with_usage: dict,
    ):
        """Test getting license history with custom days parameter."""
        response = await client.get(
            f"/api/v1/customers/{customer_with_usage['id']}/licenses?days=7",
            headers=customers_admin_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["history"]) <= 7

    @pytest.mark.asyncio
    async def test_get_license_history_not_found(
        self, client: AsyncClient, customers_admin_headers: dict
    ):
        """Test getting license history for non-existent customer."""
        fake_id = str(uuid.uuid4())
        response = await client.get(
            f"/api/v1/customers/{fake_id}/licenses",
            headers=customers_admin_headers,
        )

        assert response.status_code == 404


# ==============================================================================
# Adjust Licenses Tests
# ==============================================================================


class TestAdjustLicenses:
    """Tests for license adjustment endpoints."""

    @pytest.mark.asyncio
    async def test_adjust_licensed_users(
        self,
        client: AsyncClient,
        customers_admin_headers: dict,
        test_customer: dict,
    ):
        """Test adjusting licensed users."""
        response = await client.post(
            f"/api/v1/customers/{test_customer['id']}/licenses/adjust",
            json={"licensed_users": 75},
            headers=customers_admin_headers,
        )

        assert response.status_code == 200
        assert response.json()["licensed_users"] == 75

    @pytest.mark.asyncio
    async def test_adjust_licensed_authorities(
        self,
        client: AsyncClient,
        customers_admin_headers: dict,
        test_customer: dict,
    ):
        """Test adjusting licensed authorities."""
        response = await client.post(
            f"/api/v1/customers/{test_customer['id']}/licenses/adjust",
            json={"licensed_authorities": 10},
            headers=customers_admin_headers,
        )

        assert response.status_code == 200
        assert response.json()["licensed_authorities"] == 10

    @pytest.mark.asyncio
    async def test_adjust_both_licenses(
        self,
        client: AsyncClient,
        customers_admin_headers: dict,
        test_customer: dict,
    ):
        """Test adjusting both user and authority licenses."""
        response = await client.post(
            f"/api/v1/customers/{test_customer['id']}/licenses/adjust",
            json={"licensed_users": 200, "licensed_authorities": 20},
            headers=customers_admin_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["licensed_users"] == 200
        assert data["licensed_authorities"] == 20

    @pytest.mark.asyncio
    async def test_adjust_licenses_not_found(
        self, client: AsyncClient, customers_admin_headers: dict
    ):
        """Test adjusting licenses for non-existent customer."""
        fake_id = str(uuid.uuid4())
        response = await client.post(
            f"/api/v1/customers/{fake_id}/licenses/adjust",
            json={"licensed_users": 100},
            headers=customers_admin_headers,
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_adjust_licenses_support_forbidden(
        self,
        client: AsyncClient,
        customers_support_headers: dict,
        test_customer: dict,
    ):
        """Test that support users cannot adjust licenses."""
        response = await client.post(
            f"/api/v1/customers/{test_customer['id']}/licenses/adjust",
            json={"licensed_users": 100},
            headers=customers_support_headers,
        )

        assert response.status_code == 403


# ==============================================================================
# Authorities Tests
# ==============================================================================


class TestCustomerAuthorities:
    """Tests for customer authorities endpoints."""

    @pytest.mark.asyncio
    async def test_get_customer_authorities_success(
        self,
        client: AsyncClient,
        customers_admin_headers: dict,
        customer_with_authorities: dict,
    ):
        """Test getting customer authorities."""
        response = await client.get(
            f"/api/v1/customers/{customer_with_authorities['id']}/authorities",
            headers=customers_admin_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "authorities" in data
        assert "total" in data
        assert data["total"] == 3
        assert len(data["authorities"]) == 3

    @pytest.mark.asyncio
    async def test_get_customer_authorities_empty(
        self,
        client: AsyncClient,
        customers_admin_headers: dict,
        test_customer: dict,
    ):
        """Test getting authorities when none exist."""
        response = await client.get(
            f"/api/v1/customers/{test_customer['id']}/authorities",
            headers=customers_admin_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0

    @pytest.mark.asyncio
    async def test_get_customer_authorities_not_found(
        self, client: AsyncClient, customers_admin_headers: dict
    ):
        """Test getting authorities for non-existent customer."""
        fake_id = str(uuid.uuid4())
        response = await client.get(
            f"/api/v1/customers/{fake_id}/authorities",
            headers=customers_admin_headers,
        )

        assert response.status_code == 404


# ==============================================================================
# License Alerts Tests
# ==============================================================================


class TestLicenseAlerts:
    """Tests for license alerts endpoints."""

    @pytest.mark.asyncio
    async def test_get_license_alerts_success(
        self,
        client: AsyncClient,
        customers_admin_headers: dict,
        customer_with_alerts: dict,
    ):
        """Test getting license alerts."""
        response = await client.get(
            f"/api/v1/customers/{customer_with_alerts['id']}/alerts",
            headers=customers_admin_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # Only unacknowledged by default
        assert all(not a["acknowledged"] for a in data)

    @pytest.mark.asyncio
    async def test_get_license_alerts_include_acknowledged(
        self,
        client: AsyncClient,
        customers_admin_headers: dict,
        customer_with_alerts: dict,
    ):
        """Test getting all alerts including acknowledged."""
        response = await client.get(
            f"/api/v1/customers/{customer_with_alerts['id']}/alerts?include_acknowledged=true",
            headers=customers_admin_headers,
        )

        assert response.status_code == 200
        data = response.json()
        # Should include both acknowledged and unacknowledged
        acknowledged_count = sum(1 for a in data if a["acknowledged"])
        assert acknowledged_count >= 1

    @pytest.mark.asyncio
    async def test_get_license_alerts_not_found(
        self, client: AsyncClient, customers_admin_headers: dict
    ):
        """Test getting alerts for non-existent customer."""
        fake_id = str(uuid.uuid4())
        response = await client.get(
            f"/api/v1/customers/{fake_id}/alerts",
            headers=customers_admin_headers,
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_acknowledge_alert_success(
        self,
        client: AsyncClient,
        customers_admin_headers: dict,
        unacknowledged_alert: dict,
    ):
        """Test acknowledging a license alert."""
        response = await client.post(
            f"/api/v1/customers/{unacknowledged_alert['customer_id']}/alerts/{unacknowledged_alert['id']}/acknowledge",
            headers=customers_admin_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["acknowledged"] is True
        assert data["acknowledged_at"] is not None
        assert data["acknowledged_by"] is not None

    @pytest.mark.asyncio
    async def test_acknowledge_alert_not_found(
        self,
        client: AsyncClient,
        customers_admin_headers: dict,
        test_customer: dict,
    ):
        """Test acknowledging non-existent alert."""
        fake_alert_id = str(uuid.uuid4())
        response = await client.post(
            f"/api/v1/customers/{test_customer['id']}/alerts/{fake_alert_id}/acknowledge",
            headers=customers_admin_headers,
        )

        assert response.status_code == 404


# ==============================================================================
# Cleanup
# ==============================================================================


class TestCustomersCleanup:
    """Cleanup test data after customers tests."""

    @pytest.mark.asyncio
    async def test_cleanup_customers_data(self, test_db):
        """Clean up test customer data."""
        try:
            # Clean up license alerts
            await test_db.execute(
                text(
                    "DELETE FROM license_alerts WHERE message LIKE '%Benutzer%' "
                    "OR message LIKE '%Test%'"
                )
            )
            # Clean up license usages
            await test_db.execute(
                text(
                    "DELETE FROM license_usages WHERE customer_id IN "
                    "(SELECT id FROM customers WHERE contract_number LIKE 'CUST-%' "
                    "OR contract_number LIKE 'NEW-%' OR contract_number LIKE 'TERM-%')"
                )
            )
            # Clean up customers
            await test_db.execute(
                text(
                    "DELETE FROM customers WHERE contract_number LIKE 'CUST-%' "
                    "OR contract_number LIKE 'NEW-%' OR contract_number LIKE 'BILL-%' "
                    "OR contract_number LIKE 'TRIAL-%' OR contract_number LIKE 'DATE-%' "
                    "OR contract_number LIKE 'TERM-%' OR contract_number LIKE 'UPDATED-%'"
                )
            )
            # Clean up vendor users
            await test_db.execute(
                text(
                    "DELETE FROM vendor_users WHERE email LIKE '%@customertest.de'"
                )
            )
            # Clean up tenants
            await test_db.execute(
                text(
                    "DELETE FROM tenants WHERE name LIKE '%Test%Customer%' "
                    "OR name LIKE '%Authority%' OR name LIKE 'Terminate%' "
                    "OR name LIKE 'New Customer%' OR name LIKE 'Billing Customer%' "
                    "OR name LIKE 'Trial Customer%' OR name LIKE 'Dated Customer%'"
                )
            )
            # Clean up vendors
            await test_db.execute(
                text("DELETE FROM vendors WHERE name = 'Customer Test Vendor'")
            )
            await test_db.commit()
        except Exception:
            await test_db.rollback()
