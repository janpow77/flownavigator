"""Tests for Modules API endpoints.

Tests for:
- Vendor Modules API (/api/v1/modules)
- Module Converter API (/api/modules)
"""

import uuid
from datetime import datetime, timezone

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import text

from app.core.security import create_access_token, get_password_hash


# ==============================================================================
# Fixtures for Vendor Module Tests
# ==============================================================================


@pytest_asyncio.fixture
async def module_vendor(test_db) -> dict:
    """Create a vendor for module tests."""
    vendor_id = uuid.uuid4()
    now = datetime.now(timezone.utc)

    await test_db.execute(
        text(
            """
            INSERT INTO vendors (id, name, contact_email, billing_email,
                address_country, created_at, updated_at)
            VALUES (:id, 'Module Test Vendor', 'modules@vendor.de',
                'billing@vendor.de', 'Deutschland', :created_at, :updated_at)
            ON CONFLICT (id) DO NOTHING
            """
        ),
        {"id": vendor_id, "created_at": now, "updated_at": now},
    )
    await test_db.commit()

    return {"id": str(vendor_id), "name": "Module Test Vendor"}


@pytest_asyncio.fixture
async def module_vendor_developer(test_db, module_vendor) -> dict:
    """Create a vendor developer for module tests."""
    user_id = uuid.uuid4()
    now = datetime.now(timezone.utc)
    email = f"dev_{user_id.hex[:8]}@vendor.de"

    await test_db.execute(
        text(
            """
            INSERT INTO vendor_users (id, vendor_id, email, hashed_password,
                role, first_name, last_name, is_active, created_at, updated_at)
            VALUES (:id, :vendor_id, :email, :hashed_password,
                'vendor_developer', 'Dev', 'User', true, :created_at, :updated_at)
            """
        ),
        {
            "id": user_id,
            "vendor_id": uuid.UUID(module_vendor["id"]),
            "email": email,
            "hashed_password": get_password_hash("password123"),
            "created_at": now,
            "updated_at": now,
        },
    )
    await test_db.commit()

    return {"id": str(user_id), "vendor_id": module_vendor["id"], "email": email}


@pytest_asyncio.fixture
async def module_vendor_qa(test_db, module_vendor) -> dict:
    """Create a vendor QA for module tests."""
    user_id = uuid.uuid4()
    now = datetime.now(timezone.utc)
    email = f"qa_{user_id.hex[:8]}@vendor.de"

    await test_db.execute(
        text(
            """
            INSERT INTO vendor_users (id, vendor_id, email, hashed_password,
                role, first_name, last_name, is_active, created_at, updated_at)
            VALUES (:id, :vendor_id, :email, :hashed_password,
                'vendor_qa', 'QA', 'User', true, :created_at, :updated_at)
            """
        ),
        {
            "id": user_id,
            "vendor_id": uuid.UUID(module_vendor["id"]),
            "email": email,
            "hashed_password": get_password_hash("password123"),
            "created_at": now,
            "updated_at": now,
        },
    )
    await test_db.commit()

    return {"id": str(user_id), "vendor_id": module_vendor["id"], "email": email}


@pytest_asyncio.fixture
async def module_vendor_admin(test_db, module_vendor) -> dict:
    """Create a vendor admin for module tests."""
    user_id = uuid.uuid4()
    now = datetime.now(timezone.utc)
    email = f"admin_{user_id.hex[:8]}@vendor.de"

    await test_db.execute(
        text(
            """
            INSERT INTO vendor_users (id, vendor_id, email, hashed_password,
                role, first_name, last_name, is_active, created_at, updated_at)
            VALUES (:id, :vendor_id, :email, :hashed_password,
                'vendor_admin', 'Admin', 'User', true, :created_at, :updated_at)
            """
        ),
        {
            "id": user_id,
            "vendor_id": uuid.UUID(module_vendor["id"]),
            "email": email,
            "hashed_password": get_password_hash("password123"),
            "created_at": now,
            "updated_at": now,
        },
    )
    await test_db.commit()

    return {"id": str(user_id), "vendor_id": module_vendor["id"], "email": email}


@pytest_asyncio.fixture
def dev_headers(module_vendor_developer) -> dict:
    """Auth headers for vendor developer."""
    token = create_access_token(
        data={
            "sub": module_vendor_developer["id"],
            "type": "vendor",
            "role": "vendor_developer",
        }
    )
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
def qa_headers(module_vendor_qa) -> dict:
    """Auth headers for vendor QA."""
    token = create_access_token(
        data={
            "sub": module_vendor_qa["id"],
            "type": "vendor",
            "role": "vendor_qa",
        }
    )
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
def admin_headers(module_vendor_admin) -> dict:
    """Auth headers for vendor admin."""
    token = create_access_token(
        data={
            "sub": module_vendor_admin["id"],
            "type": "vendor",
            "role": "vendor_admin",
        }
    )
    return {"Authorization": f"Bearer {token}"}


# ==============================================================================
# Vendor Modules API Tests
# ==============================================================================


class TestVendorModulesCRUD:
    """Tests for Vendor Modules CRUD."""

    @pytest.mark.asyncio
    async def test_list_modules_unauthorized(self, client: AsyncClient):
        """Test that listing modules requires vendor auth."""
        response = await client.get("/api/v1/modules")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_list_modules_empty(
        self, client: AsyncClient, dev_headers: dict
    ):
        """Test listing modules when none exist."""
        response = await client.get("/api/v1/modules", headers=dev_headers)
        assert response.status_code == 200
        data = response.json()
        assert "modules" in data
        assert "total" in data

    @pytest.mark.asyncio
    async def test_create_module(
        self, client: AsyncClient, dev_headers: dict
    ):
        """Test creating a module (developer role)."""
        module_data = {
            "name": "Test-Module-Create",
            "version": "1.0.0",
            "description": "Test module for creation",
        }

        response = await client.post(
            "/api/v1/modules",
            json=module_data,
            headers=dev_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == module_data["name"]
        assert data["version"] == module_data["version"]
        assert data["status"] == "development"

    @pytest.mark.asyncio
    async def test_get_module_not_found(
        self, client: AsyncClient, dev_headers: dict
    ):
        """Test getting non-existent module."""
        fake_id = str(uuid.uuid4())
        response = await client.get(
            f"/api/v1/modules/{fake_id}",
            headers=dev_headers,
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_module_by_id(
        self, client: AsyncClient, dev_headers: dict, test_db
    ):
        """Test getting a specific module."""
        module_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)

        await test_db.execute(
            text(
                """
                INSERT INTO modules (id, name, version, status, created_at, updated_at)
                VALUES (:id, 'Get Test Module', '1.0.0', 'development',
                    :created_at, :updated_at)
                """
            ),
            {"id": module_id, "created_at": now, "updated_at": now},
        )
        await test_db.commit()

        response = await client.get(
            f"/api/v1/modules/{module_id}",
            headers=dev_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == module_id
        assert data["name"] == "Get Test Module"

    @pytest.mark.asyncio
    async def test_update_module(
        self, client: AsyncClient, dev_headers: dict, test_db
    ):
        """Test updating a module."""
        module_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)

        await test_db.execute(
            text(
                """
                INSERT INTO modules (id, name, version, status, created_at, updated_at)
                VALUES (:id, 'Update Test Module', '1.0.0', 'development',
                    :created_at, :updated_at)
                """
            ),
            {"id": module_id, "created_at": now, "updated_at": now},
        )
        await test_db.commit()

        response = await client.put(
            f"/api/v1/modules/{module_id}",
            json={"description": "Updated description"},
            headers=dev_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["description"] == "Updated description"

    @pytest.mark.asyncio
    async def test_update_module_not_found(
        self, client: AsyncClient, dev_headers: dict
    ):
        """Test updating non-existent module."""
        fake_id = str(uuid.uuid4())
        response = await client.put(
            f"/api/v1/modules/{fake_id}",
            json={"description": "New description"},
            headers=dev_headers,
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_list_modules_with_filter(
        self, client: AsyncClient, dev_headers: dict, test_db
    ):
        """Test listing modules with status filter."""
        now = datetime.now(timezone.utc)

        # Create modules with different statuses
        for i, status in enumerate(["development", "released"]):
            await test_db.execute(
                text(
                    """
                    INSERT INTO modules (id, name, version, status, created_at, updated_at)
                    VALUES (:id, :name, '1.0.0', :status, :created_at, :updated_at)
                    """
                ),
                {
                    "id": str(uuid.uuid4()),
                    "name": f"Filter Test {status}",
                    "status": status,
                    "created_at": now,
                    "updated_at": now,
                },
            )
        await test_db.commit()

        response = await client.get(
            "/api/v1/modules?status=development",
            headers=dev_headers,
        )

        assert response.status_code == 200
        data = response.json()
        for module in data["modules"]:
            assert module["status"] == "development"


class TestModuleRelease:
    """Tests for module release functionality."""

    @pytest_asyncio.fixture
    async def dev_module(self, test_db) -> dict:
        """Create a development module."""
        module_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)

        await test_db.execute(
            text(
                """
                INSERT INTO modules (id, name, version, status, created_at, updated_at)
                VALUES (:id, 'Release Test Module', '1.0.0', 'development',
                    :created_at, :updated_at)
                """
            ),
            {"id": module_id, "created_at": now, "updated_at": now},
        )
        await test_db.commit()

        return {"id": module_id, "name": "Release Test Module"}

    @pytest.mark.asyncio
    async def test_release_module(
        self, client: AsyncClient, qa_headers: dict, dev_module: dict
    ):
        """Test releasing a module (QA role)."""
        response = await client.post(
            f"/api/v1/modules/{dev_module['id']}/release",
            headers=qa_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "released"
        assert data["released_at"] is not None

    @pytest.mark.asyncio
    async def test_release_module_not_found(
        self, client: AsyncClient, qa_headers: dict
    ):
        """Test releasing non-existent module."""
        fake_id = str(uuid.uuid4())
        response = await client.post(
            f"/api/v1/modules/{fake_id}/release",
            headers=qa_headers,
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_release_already_released(
        self, client: AsyncClient, qa_headers: dict, test_db
    ):
        """Test releasing an already released module."""
        module_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)

        await test_db.execute(
            text(
                """
                INSERT INTO modules (id, name, version, status, released_at,
                    created_at, updated_at)
                VALUES (:id, 'Already Released', '1.0.0', 'released', :now,
                    :created_at, :updated_at)
                """
            ),
            {"id": module_id, "now": now, "created_at": now, "updated_at": now},
        )
        await test_db.commit()

        response = await client.post(
            f"/api/v1/modules/{module_id}/release",
            headers=qa_headers,
        )

        assert response.status_code == 400


class TestModuleReleaseNotes:
    """Tests for module release notes."""

    @pytest_asyncio.fixture
    async def module_with_notes(self, test_db) -> dict:
        """Create a module with release notes."""
        module_id = str(uuid.uuid4())
        note_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)

        await test_db.execute(
            text(
                """
                INSERT INTO modules (id, name, version, status, created_at, updated_at)
                VALUES (:id, 'Notes Test Module', '1.0.0', 'released',
                    :created_at, :updated_at)
                """
            ),
            {"id": module_id, "created_at": now, "updated_at": now},
        )

        await test_db.execute(
            text(
                """
                INSERT INTO release_notes (id, module_id, version, title, changes,
                    published_at, created_at)
                VALUES (:id, :module_id, '1.0.0', 'Initial Release',
                    :changes, :published_at, :created_at)
                """
            ),
            {
                "id": note_id,
                "module_id": module_id,
                "changes": '["Feature A", "Feature B"]',
                "published_at": now,
                "created_at": now,
            },
        )
        await test_db.commit()

        return {"id": module_id, "note_id": note_id}

    @pytest.mark.asyncio
    async def test_list_release_notes(
        self, client: AsyncClient, qa_headers: dict, module_with_notes: dict
    ):
        """Test listing release notes for a module."""
        response = await client.get(
            f"/api/v1/modules/{module_with_notes['id']}/release-notes",
            headers=qa_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "release_notes" in data
        assert len(data["release_notes"]) >= 1

    @pytest.mark.asyncio
    async def test_create_release_note(
        self, client: AsyncClient, qa_headers: dict, module_with_notes: dict
    ):
        """Test creating a release note (QA role)."""
        response = await client.post(
            f"/api/v1/modules/{module_with_notes['id']}/release-notes",
            json={
                "version": "1.1.0",
                "title": "Minor Update",
                "changes": ["Bug fix", "Performance improvement"],
                "breaking_changes": [],
            },
            headers=qa_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["version"] == "1.1.0"
        assert data["title"] == "Minor Update"

    @pytest.mark.asyncio
    async def test_list_release_notes_module_not_found(
        self, client: AsyncClient, qa_headers: dict
    ):
        """Test listing notes for non-existent module."""
        fake_id = str(uuid.uuid4())
        response = await client.get(
            f"/api/v1/modules/{fake_id}/release-notes",
            headers=qa_headers,
        )
        assert response.status_code == 404


class TestModuleDeployment:
    """Tests for module deployment functionality."""

    @pytest_asyncio.fixture
    async def released_module(self, test_db) -> dict:
        """Create a released module for deployment."""
        module_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)

        await test_db.execute(
            text(
                """
                INSERT INTO modules (id, name, version, status, released_at,
                    created_at, updated_at)
                VALUES (:id, 'Deploy Test Module', '1.0.0', 'released', :now,
                    :created_at, :updated_at)
                """
            ),
            {"id": module_id, "now": now, "created_at": now, "updated_at": now},
        )
        await test_db.commit()

        return {"id": module_id, "name": "Deploy Test Module"}

    @pytest_asyncio.fixture
    async def deploy_customer(self, test_db, module_vendor) -> dict:
        """Create a customer for deployment tests."""
        customer_id = str(uuid.uuid4())
        tenant_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)

        # Create tenant
        await test_db.execute(
            text(
                """
                INSERT INTO tenants (id, name, type, status, created_at, updated_at)
                VALUES (:id, 'Deploy Test Tenant', 'group', 'active',
                    :created_at, :updated_at)
                ON CONFLICT (id) DO NOTHING
                """
            ),
            {"id": uuid.UUID(tenant_id), "created_at": now, "updated_at": now},
        )

        # Create customer
        await test_db.execute(
            text(
                """
                INSERT INTO customers (id, vendor_id, tenant_id, contract_number,
                    licensed_users, licensed_authorities, billing_address_country,
                    status, created_at, updated_at)
                VALUES (:id, :vendor_id, :tenant_id, :contract, 50, 5, 'Deutschland',
                    'active', :created_at, :updated_at)
                """
            ),
            {
                "id": uuid.UUID(customer_id),
                "vendor_id": uuid.UUID(module_vendor["id"]),
                "tenant_id": uuid.UUID(tenant_id),
                "contract": f"DEPLOY-{customer_id[:8]}",
                "created_at": now,
                "updated_at": now,
            },
        )
        await test_db.commit()

        return {"id": customer_id, "tenant_id": tenant_id}

    @pytest.mark.asyncio
    async def test_list_module_deployments(
        self, client: AsyncClient, admin_headers: dict, released_module: dict
    ):
        """Test listing deployments for a module."""
        response = await client.get(
            f"/api/v1/modules/{released_module['id']}/deployments",
            headers=admin_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "deployments" in data

    @pytest.mark.asyncio
    async def test_deploy_module(
        self,
        client: AsyncClient,
        admin_headers: dict,
        released_module: dict,
        deploy_customer: dict,
    ):
        """Test deploying a module to customer (admin role)."""
        response = await client.post(
            f"/api/v1/modules/{released_module['id']}/deploy/{deploy_customer['id']}",
            headers=admin_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "deployed"
        assert data["deployed_version"] == "1.0.0"

    @pytest.mark.asyncio
    async def test_deploy_module_not_released(
        self, client: AsyncClient, admin_headers: dict, deploy_customer: dict, test_db
    ):
        """Test that only released modules can be deployed."""
        module_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)

        await test_db.execute(
            text(
                """
                INSERT INTO modules (id, name, version, status, created_at, updated_at)
                VALUES (:id, 'Dev Module', '1.0.0', 'development',
                    :created_at, :updated_at)
                """
            ),
            {"id": module_id, "created_at": now, "updated_at": now},
        )
        await test_db.commit()

        response = await client.post(
            f"/api/v1/modules/{module_id}/deploy/{deploy_customer['id']}",
            headers=admin_headers,
        )

        assert response.status_code == 400


# ==============================================================================
# Module Converter API Tests
# ==============================================================================


class TestLLMConfigAPI:
    """Tests for LLM Configuration API."""

    @pytest.mark.asyncio
    async def test_list_llm_configs_unauthorized(self, client: AsyncClient):
        """Test that listing LLM configs requires auth."""
        response = await client.get("/api/modules/llm-config")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_list_llm_configs(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test listing LLM configurations."""
        response = await client.get(
            "/api/modules/llm-config",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data

    @pytest.mark.asyncio
    async def test_create_llm_config(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test creating an LLM configuration."""
        config_data = {
            "name": "Test LLM Config",
            "provider": "openai",
            "model_name": "gpt-4",
            "api_key": "sk-test-key-12345",
            "temperature": 0.7,
            "max_tokens": 4096,
        }

        response = await client.post(
            "/api/modules/llm-config",
            json=config_data,
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["message"] == "Configuration created"

    @pytest.mark.asyncio
    async def test_get_llm_config_not_found(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test getting non-existent LLM config."""
        fake_id = str(uuid.uuid4())
        response = await client.get(
            f"/api/modules/llm-config/{fake_id}",
            headers=auth_headers,
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_llm_config(
        self, client: AsyncClient, auth_headers: dict, test_db
    ):
        """Test getting a specific LLM config."""
        config_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)

        await test_db.execute(
            text(
                """
                INSERT INTO llm_configurations (id, name, provider, model_name,
                    api_key_encrypted, temperature, max_tokens, top_p, config,
                    is_active, is_default, priority, requests_per_minute,
                    tokens_per_minute, created_at, updated_at)
                VALUES (:id, 'Get Test Config', 'OPENAI', 'gpt-4',
                    'test-key', 0.7, 4096, 1.0, '{}', true, false, 100, 60,
                    100000, :created_at, :updated_at)
                """
            ),
            {"id": config_id, "created_at": now, "updated_at": now},
        )
        await test_db.commit()

        response = await client.get(
            f"/api/modules/llm-config/{config_id}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Get Test Config"

    @pytest.mark.asyncio
    async def test_update_llm_config(
        self, client: AsyncClient, auth_headers: dict, test_db
    ):
        """Test updating an LLM config."""
        config_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)

        await test_db.execute(
            text(
                """
                INSERT INTO llm_configurations (id, name, provider, model_name,
                    api_key_encrypted, temperature, max_tokens, top_p, config,
                    is_active, is_default, priority, requests_per_minute,
                    tokens_per_minute, created_at, updated_at)
                VALUES (:id, 'Update Test Config', 'OPENAI', 'gpt-4',
                    'test-key', 0.7, 4096, 1.0, '{}', true, false, 100, 60,
                    100000, :created_at, :updated_at)
                """
            ),
            {"id": config_id, "created_at": now, "updated_at": now},
        )
        await test_db.commit()

        response = await client.put(
            f"/api/modules/llm-config/{config_id}",
            json={"temperature": 0.5},
            headers=auth_headers,
        )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_delete_llm_config(
        self, client: AsyncClient, auth_headers: dict, test_db
    ):
        """Test deleting an LLM config."""
        config_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)

        await test_db.execute(
            text(
                """
                INSERT INTO llm_configurations (id, name, provider, model_name,
                    api_key_encrypted, temperature, max_tokens, top_p, config,
                    is_active, is_default, priority, requests_per_minute,
                    tokens_per_minute, created_at, updated_at)
                VALUES (:id, 'Delete Test Config', 'OPENAI', 'gpt-4',
                    'test-key', 0.7, 4096, 1.0, '{}', true, false, 100, 60,
                    100000, :created_at, :updated_at)
                """
            ),
            {"id": config_id, "created_at": now, "updated_at": now},
        )
        await test_db.commit()

        response = await client.delete(
            f"/api/modules/llm-config/{config_id}",
            headers=auth_headers,
        )

        assert response.status_code == 200


class TestModuleTemplatesAPI:
    """Tests for Module Templates API."""

    @pytest.mark.asyncio
    async def test_list_templates_unauthorized(self, client: AsyncClient):
        """Test that listing templates requires auth."""
        response = await client.get("/api/modules/module-templates")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_list_templates(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test listing module templates."""
        response = await client.get(
            "/api/modules/module-templates",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data

    @pytest.mark.asyncio
    async def test_create_template(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test creating a module template."""
        template_data = {
            "name": "test-template",
            "display_name": "Test Template",
            "description": "Test template for module conversion",
            "module_type": "core",
            "package_name": "com.test.module",
        }

        response = await client.post(
            "/api/modules/module-templates",
            json=template_data,
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "id" in data

    @pytest.mark.asyncio
    async def test_get_template_not_found(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test getting non-existent template."""
        fake_id = str(uuid.uuid4())
        response = await client.get(
            f"/api/modules/module-templates/{fake_id}",
            headers=auth_headers,
        )
        assert response.status_code == 404


class TestConversionsAPI:
    """Tests for Conversions API."""

    @pytest.mark.asyncio
    async def test_list_conversions_unauthorized(self, client: AsyncClient):
        """Test that listing conversions requires auth."""
        response = await client.get("/api/modules/conversions")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_list_conversions(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test listing conversions."""
        response = await client.get(
            "/api/modules/conversions",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data

    @pytest.mark.asyncio
    async def test_get_conversion_not_found(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test getting non-existent conversion."""
        fake_id = str(uuid.uuid4())
        response = await client.get(
            f"/api/modules/conversions/{fake_id}",
            headers=auth_headers,
        )
        assert response.status_code == 404


class TestGitHubIntegrationsAPI:
    """Tests for GitHub Integrations API."""

    @pytest.mark.asyncio
    async def test_list_github_integrations_unauthorized(self, client: AsyncClient):
        """Test that listing GitHub integrations requires auth."""
        response = await client.get("/api/modules/github-integrations")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_list_github_integrations(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test listing GitHub integrations."""
        response = await client.get(
            "/api/modules/github-integrations",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "items" in data

    @pytest.mark.asyncio
    async def test_create_github_integration(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test creating a GitHub integration."""
        integration_data = {
            "name": "Test Integration",
            "access_token": "ghp_test_token_12345",
            "default_owner": "test-org",
            "default_repo": "test-repo",
        }

        response = await client.post(
            "/api/modules/github-integrations",
            json=integration_data,
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "id" in data

    @pytest.mark.asyncio
    async def test_get_github_integration_not_found(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test getting non-existent GitHub integration."""
        fake_id = str(uuid.uuid4())
        response = await client.get(
            f"/api/modules/github-integrations/{fake_id}",
            headers=auth_headers,
        )
        assert response.status_code == 404


class TestModulesCleanup:
    """Cleanup test data after module tests."""

    @pytest.mark.asyncio
    async def test_cleanup_module_data(self, test_db):
        """Clean up test module data."""
        try:
            # Clean up release notes
            await test_db.execute(
                text(
                    "DELETE FROM release_notes WHERE title LIKE '%Test%' "
                    "OR title LIKE '%Update%'"
                )
            )
            # Clean up deployments
            await test_db.execute(
                text(
                    "DELETE FROM module_deployments WHERE module_id IN "
                    "(SELECT id FROM modules WHERE name LIKE '%Test%')"
                )
            )
            # Clean up modules
            await test_db.execute(
                text("DELETE FROM modules WHERE name LIKE '%Test%'")
            )
            # Clean up LLM configs
            await test_db.execute(
                text("DELETE FROM llm_configurations WHERE name LIKE '%Test%'")
            )
            # Clean up templates
            await test_db.execute(
                text("DELETE FROM module_templates WHERE name LIKE '%test%'")
            )
            # Clean up GitHub integrations
            await test_db.execute(
                text("DELETE FROM github_integrations WHERE name LIKE '%Test%'")
            )
            # Clean up vendor users
            await test_db.execute(
                text("DELETE FROM vendor_users WHERE email LIKE '%@vendor.de'")
            )
            # Clean up vendors
            await test_db.execute(
                text("DELETE FROM vendors WHERE name = 'Module Test Vendor'")
            )
            await test_db.commit()
        except Exception:
            await test_db.rollback()
