"""Tests for the Module Converter feature."""

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import text
from unittest.mock import AsyncMock, patch, MagicMock
import uuid

from app.models.module_converter import (
    LLMProvider,
    ConversionStatus,
    ModuleType,
)
from app.services.llm.base import LLMResponse, LLMMessage, MessageRole
from app.services.github_service import GitHubService, Repository, Branch


# Note: The API uses dict responses, so tests use plain dicts for request/response


# =============================================================================
# LLM Configuration Tests
# =============================================================================


@pytest.mark.asyncio(loop_scope="session")
class TestLLMConfiguration:
    """Tests for LLM configuration endpoints."""

    @pytest_asyncio.fixture
    async def cleanup_llm_config(self, test_db):
        """Cleanup LLM configurations after test."""
        yield
        try:
            await test_db.execute(
                text("DELETE FROM llm_configurations WHERE name LIKE 'TEST-%'")
            )
            await test_db.commit()
        except Exception:
            await test_db.rollback()

    async def test_list_llm_configs_empty(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test listing LLM configs."""
        response = await client.get("/api/modules/llm-config", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert isinstance(data["items"], list)

    async def test_create_llm_config(
        self, client: AsyncClient, auth_headers: dict, cleanup_llm_config
    ):
        """Test creating an LLM configuration."""
        config_data = {
            "name": "TEST-OpenAI-Config",
            "provider": "openai",
            "model_name": "gpt-4-turbo",
            "api_key": "sk-test-key-12345",
            "temperature": 0.7,
            "max_tokens": 4096,
        }

        response = await client.post(
            "/api/modules/llm-config",
            headers=auth_headers,
            json=config_data,
        )

        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "message" in data

    async def test_create_llm_config_anthropic(
        self, client: AsyncClient, auth_headers: dict, cleanup_llm_config
    ):
        """Test creating an Anthropic LLM configuration."""
        config_data = {
            "name": "TEST-Anthropic-Config",
            "provider": "anthropic",
            "model_name": "claude-3-sonnet-20240229",
            "api_key": "sk-ant-test-key-12345",
        }

        response = await client.post(
            "/api/modules/llm-config",
            headers=auth_headers,
            json=config_data,
        )

        assert response.status_code == 200
        data = response.json()
        assert "id" in data

    async def test_get_llm_config(
        self, client: AsyncClient, auth_headers: dict, cleanup_llm_config
    ):
        """Test getting a specific LLM configuration."""
        # First create a config
        config_data = {
            "name": "TEST-Get-Config",
            "provider": "openai",
            "model_name": "gpt-4",
            "api_key": "sk-test-key",
        }

        create_response = await client.post(
            "/api/modules/llm-config",
            headers=auth_headers,
            json=config_data,
        )
        config_id = create_response.json()["id"]

        # Then get it
        response = await client.get(
            f"/api/modules/llm-config/{config_id}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == config_id
        assert data["name"] == config_data["name"]

    async def test_update_llm_config(
        self, client: AsyncClient, auth_headers: dict, cleanup_llm_config
    ):
        """Test updating an LLM configuration."""
        # Create config
        config_data = {
            "name": "TEST-Update-Config",
            "provider": "openai",
            "model_name": "gpt-3.5-turbo",
            "api_key": "sk-test-key",
        }

        create_response = await client.post(
            "/api/modules/llm-config",
            headers=auth_headers,
            json=config_data,
        )
        config_id = create_response.json()["id"]

        # Update it (uses PUT endpoint)
        update_data = {"model_name": "gpt-4-turbo", "temperature": 0.5}
        response = await client.put(
            f"/api/modules/llm-config/{config_id}",
            headers=auth_headers,
            json=update_data,
        )

        assert response.status_code == 200
        data = response.json()
        assert "message" in data

    async def test_delete_llm_config(
        self, client: AsyncClient, auth_headers: dict, cleanup_llm_config
    ):
        """Test deleting an LLM configuration."""
        # Create config
        config_data = {
            "name": "TEST-Delete-Config",
            "provider": "openai",
            "model_name": "gpt-4",
            "api_key": "sk-test-key",
        }

        create_response = await client.post(
            "/api/modules/llm-config",
            headers=auth_headers,
            json=config_data,
        )
        config_id = create_response.json()["id"]

        # Delete it
        response = await client.delete(
            f"/api/modules/llm-config/{config_id}",
            headers=auth_headers,
        )

        assert response.status_code == 200  # API returns 200 with message

        # Verify it's gone
        get_response = await client.get(
            f"/api/modules/llm-config/{config_id}",
            headers=auth_headers,
        )
        assert get_response.status_code == 404


# =============================================================================
# Module Template Tests
# =============================================================================


@pytest.mark.asyncio(loop_scope="session")
class TestModuleTemplate:
    """Tests for module template endpoints."""

    @pytest_asyncio.fixture
    async def cleanup_templates(self, test_db):
        """Cleanup templates after test."""
        yield
        try:
            await test_db.execute(
                text("DELETE FROM module_templates WHERE name LIKE 'TEST-%'")
            )
            await test_db.commit()
        except Exception:
            await test_db.rollback()

    async def test_list_templates(self, client: AsyncClient, auth_headers: dict):
        """Test listing module templates."""
        response = await client.get(
            "/api/modules/module-templates", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert isinstance(data["items"], list)

    async def test_create_template(
        self, client: AsyncClient, auth_headers: dict, cleanup_templates
    ):
        """Test creating a module template."""
        template_data = {
            "name": "TEST-Core-Template",
            "display_name": "Test Core Template",
            "description": "Template for converting core modules",
            "module_type": "core",
            "package_name": "test.core",
        }

        response = await client.post(
            "/api/modules/module-templates",
            headers=auth_headers,
            json=template_data,
        )

        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "message" in data

    async def test_create_template_domain(
        self, client: AsyncClient, auth_headers: dict, cleanup_templates
    ):
        """Test creating a domain template."""
        template_data = {
            "name": "TEST-Domain-Template",
            "display_name": "Test Domain Template",
            "description": "Template for domain modules",
            "module_type": "domain",
            "package_name": "test.domain",
        }

        response = await client.post(
            "/api/modules/module-templates",
            headers=auth_headers,
            json=template_data,
        )

        assert response.status_code == 200
        data = response.json()
        assert "id" in data

    async def test_get_template(
        self, client: AsyncClient, auth_headers: dict, cleanup_templates
    ):
        """Test getting a specific template."""
        # Create template
        template_data = {
            "name": "TEST-Get-Template",
            "display_name": "Test Get Template",
            "description": "Test",
            "module_type": "core",
            "package_name": "test.get",
        }

        create_response = await client.post(
            "/api/modules/module-templates",
            headers=auth_headers,
            json=template_data,
        )
        template_id = create_response.json()["id"]

        # Get it
        response = await client.get(
            f"/api/modules/module-templates/{template_id}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        assert response.json()["id"] == template_id


# =============================================================================
# GitHub Integration Tests
# =============================================================================


@pytest.mark.asyncio(loop_scope="session")
class TestGitHubIntegration:
    """Tests for GitHub integration endpoints."""

    @pytest_asyncio.fixture
    async def cleanup_github(self, test_db):
        """Cleanup GitHub integrations after test."""
        yield
        try:
            await test_db.execute(
                text("DELETE FROM github_integrations WHERE name LIKE 'TEST-%'")
            )
            await test_db.commit()
        except Exception:
            await test_db.rollback()

    async def test_list_github_integrations(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test listing GitHub integrations."""
        response = await client.get(
            "/api/modules/github-integrations", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert isinstance(data["items"], list)

    async def test_create_github_integration(
        self, client: AsyncClient, auth_headers: dict, cleanup_github
    ):
        """Test creating a GitHub integration."""
        integration_data = {
            "name": "TEST-GitHub-Integration",
            "default_owner": "test-owner",
            "default_repo": "test-repo",
            "access_token": "ghp_test_token_12345",
            "default_base_branch": "main",
        }

        response = await client.post(
            "/api/modules/github-integrations",
            headers=auth_headers,
            json=integration_data,
        )

        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "message" in data


# =============================================================================
# Conversion Tests
# =============================================================================


@pytest.mark.asyncio(loop_scope="session")
class TestModuleConversion:
    """Tests for module conversion endpoints."""

    @pytest_asyncio.fixture
    async def test_template(self, client: AsyncClient, auth_headers: dict, test_db):
        """Create a test template."""
        template_data = {
            "name": "TEST-Conversion-Template",
            "display_name": "Test Conversion Template",
            "description": "Template for conversion tests",
            "module_type": "core",
            "package_name": "test.conversion",
        }

        response = await client.post(
            "/api/modules/module-templates",
            headers=auth_headers,
            json=template_data,
        )
        template = response.json()
        yield template

        # Cleanup
        try:
            await test_db.execute(
                text("DELETE FROM module_templates WHERE id = :id"),
                {"id": template["id"]},
            )
            await test_db.commit()
        except Exception:
            await test_db.rollback()

    @pytest_asyncio.fixture
    async def test_llm_config(self, client: AsyncClient, auth_headers: dict, test_db):
        """Create a test LLM config."""
        config_data = {
            "name": "TEST-Conversion-LLM",
            "provider": "openai",
            "model_name": "gpt-4",
            "api_key": "sk-test-key",
        }

        response = await client.post(
            "/api/modules/llm-config",
            headers=auth_headers,
            json=config_data,
        )
        config = response.json()
        yield config

        # Cleanup
        try:
            await test_db.execute(
                text("DELETE FROM llm_configurations WHERE id = :id"),
                {"id": config["id"]},
            )
            await test_db.commit()
        except Exception:
            await test_db.rollback()

    @pytest_asyncio.fixture
    async def cleanup_conversions(self, test_db):
        """Cleanup conversions after test."""
        yield
        try:
            await test_db.execute(
                text(
                    "DELETE FROM conversion_steps WHERE conversion_id IN (SELECT id FROM module_conversion_logs WHERE metadata->>'test' = 'true')"
                )
            )
            await test_db.execute(
                text(
                    "DELETE FROM module_conversion_logs WHERE metadata->>'test' = 'true'"
                )
            )
            await test_db.commit()
        except Exception:
            await test_db.rollback()

    async def test_list_conversions(self, client: AsyncClient, auth_headers: dict):
        """Test listing conversions."""
        response = await client.get("/api/modules/conversions", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data

    @patch("app.services.module_service.LLMService")
    async def test_start_conversion(
        self,
        mock_llm_service_class,
        client: AsyncClient,
        auth_headers: dict,
        test_template: dict,
        test_llm_config: dict,
        cleanup_conversions,
    ):
        """Test starting a conversion."""
        # Mock LLM service
        mock_llm_instance = AsyncMock()
        mock_llm_instance.complete = AsyncMock(
            return_value=LLMResponse(
                content='{"items": ["Item 1", "Item 2"]}',
                model="gpt-4",
                provider="openai",
                prompt_tokens=100,
                completion_tokens=50,
                total_tokens=150,
                finish_reason="stop",
            )
        )
        mock_llm_service_class.return_value = mock_llm_instance

        conversion_data = {
            "template_id": test_template["id"],
            "llm_config_id": test_llm_config["id"],
            "source_content": "# Checklist\n- [ ] Item 1\n- [ ] Item 2",
            "metadata": {"test": "true"},
        }

        response = await client.post(
            "/api/modules/conversions",
            headers=auth_headers,
            json=conversion_data,
        )

        # The conversion starts as a background task, so we just check it was accepted
        assert response.status_code in [200, 202]
        if response.status_code == 200:
            data = response.json()
            assert "id" in data
            assert "status" in data
            assert data["status"] in ["pending", "processing", "completed"]
            assert data["message"] == "Conversion started"


# =============================================================================
# LLM Service Unit Tests
# =============================================================================


@pytest.mark.asyncio(loop_scope="session")
class TestLLMServiceUnit:
    """Unit tests for the LLM service."""

    async def test_llm_message_creation(self):
        """Test LLM message creation."""
        message = LLMMessage(role=MessageRole.USER, content="Hello, world!")
        assert message.role == MessageRole.USER
        assert message.content == "Hello, world!"

    async def test_llm_response_creation(self):
        """Test LLM response creation."""
        response = LLMResponse(
            content="Response text",
            model="gpt-4",
            provider="openai",
            prompt_tokens=10,
            completion_tokens=20,
            total_tokens=30,
            finish_reason="stop",
        )
        assert response.content == "Response text"
        assert response.model == "gpt-4"
        assert response.finish_reason == "stop"
        assert response.total_tokens == 30


# =============================================================================
# GitHub Service Unit Tests
# =============================================================================


@pytest.mark.asyncio(loop_scope="session")
class TestGitHubServiceUnit:
    """Unit tests for the GitHub service."""

    async def test_repository_dataclass(self):
        """Test Repository dataclass."""
        repo = Repository(
            name="test-repo",
            full_name="owner/test-repo",
            default_branch="main",
            private=False,
            url="https://api.github.com/repos/owner/test-repo",
            clone_url="https://github.com/owner/test-repo.git",
        )
        assert repo.name == "test-repo"
        assert repo.full_name == "owner/test-repo"
        assert repo.default_branch == "main"

    async def test_branch_dataclass(self):
        """Test Branch dataclass."""
        branch = Branch(
            name="feature-branch",
            sha="abc123def456",
            protected=False,
        )
        assert branch.name == "feature-branch"
        assert branch.sha == "abc123def456"
        assert branch.protected is False

    @patch("httpx.AsyncClient")
    async def test_github_service_validate_token(self, mock_client_class):
        """Test GitHub service token validation."""
        # Setup mock
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"login": "test-user"}
        mock_response.content = b'{"login": "test-user"}'
        mock_client.request = AsyncMock(return_value=mock_response)
        mock_client.is_closed = False

        service = GitHubService(access_token="ghp_test_token")
        service._client = mock_client

        result = await service.validate_token()
        assert result is True

    @patch("httpx.AsyncClient")
    async def test_github_service_invalid_token(self, mock_client_class):
        """Test GitHub service with invalid token."""
        # Setup mock
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.json.return_value = {"message": "Bad credentials"}
        mock_response.content = b'{"message": "Bad credentials"}'
        mock_client.request = AsyncMock(return_value=mock_response)
        mock_client.is_closed = False

        service = GitHubService(access_token="invalid_token")
        service._client = mock_client

        result = await service.validate_token()
        assert result is False


# =============================================================================
# Model Tests
# =============================================================================


@pytest.mark.asyncio(loop_scope="session")
class TestModels:
    """Tests for module converter models."""

    async def test_llm_provider_enum(self):
        """Test LLM provider enum values."""
        assert LLMProvider.OPENAI.value == "openai"
        assert LLMProvider.ANTHROPIC.value == "anthropic"
        assert LLMProvider.OLLAMA.value == "ollama"
        assert LLMProvider.AZURE_OPENAI.value == "azure_openai"
        assert LLMProvider.MISTRAL.value == "mistral"
        assert LLMProvider.CUSTOM.value == "custom"

    async def test_conversion_status_enum(self):
        """Test conversion status enum values."""
        assert ConversionStatus.PENDING.value == "pending"
        assert ConversionStatus.QUEUED.value == "queued"
        assert ConversionStatus.PROCESSING.value == "processing"
        assert ConversionStatus.VALIDATING.value == "validating"
        assert ConversionStatus.STAGING.value == "staging"
        assert ConversionStatus.COMPLETED.value == "completed"
        assert ConversionStatus.FAILED.value == "failed"
        assert ConversionStatus.CANCELLED.value == "cancelled"

    async def test_module_type_enum(self):
        """Test module type enum values."""
        assert ModuleType.CORE.value == "core"
        assert ModuleType.DOMAIN.value == "domain"
        assert ModuleType.REPORTING.value == "reporting"
        assert ModuleType.DOCUMENTS.value == "documents"
        assert ModuleType.ADAPTERS.value == "adapters"
        assert ModuleType.INTEGRATIONS.value == "integrations"
