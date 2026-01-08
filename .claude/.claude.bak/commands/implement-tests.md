# Implementiere Tests

## WICHTIG: Autonome Ausführung

**Arbeite OHNE Rückfragen!** Führe alle Schritte selbstständig aus:
1. Lies die bestehenden Tests um den Stil zu verstehen
2. Erweitere conftest.py mit den neuen Fixtures
3. Implementiere alle Test-Dateien
4. Führe `pytest` aus und behebe fehlschlagende Tests
5. Erreiche mindestens 80% Coverage für neue Module
6. Führe `pytest --cov=app --cov-report=term-missing` aus
7. Committe und pushe erst wenn alle Tests grün sind

**Nach Abschluss aller Tests:**
Melde "Module Converter Implementation abgeschlossen!" und liste auf:
- Anzahl implementierter Models
- Anzahl API-Endpoints
- Anzahl Frontend-Komponenten
- Test-Coverage

**Keine Fragen stellen - einfach machen!**

---

## Aufgabe
Erstelle umfassende Tests für den Module Converter basierend auf der bestehenden Teststruktur.

## Test-Übersicht

```
tests/
├── test_llm_service.py         # LLM Provider Tests
├── test_module_service.py      # Module CRUD Tests
├── test_module_api.py          # API Endpoint Tests
├── test_staging_service.py     # Staging Pipeline Tests
├── test_github_service.py      # GitHub Integration Tests
└── conftest.py                 # Shared Fixtures
```

## Zu erstellende Test-Dateien

### 1. Fixtures (`backend/tests/conftest.py` - erweitern)
```python
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.module_template import ModuleTemplate, ModuleStatus
from app.models.konzern import Konzern
from app.models.llm_configuration import LLMConfiguration, LLMProvider

@pytest.fixture
async def sample_konzern(db: AsyncSession) -> Konzern:
    konzern = Konzern(
        name="Test Konzern",
        slug="test-konzern",
        is_active=True
    )
    db.add(konzern)
    await db.commit()
    await db.refresh(konzern)
    return konzern

@pytest.fixture
async def sample_module(db: AsyncSession, sample_user) -> ModuleTemplate:
    module = ModuleTemplate(
        name="Test Prüfschema",
        slug="test-pruefschema",
        description="Ein Testmodul",
        layer="rahmen",
        status=ModuleStatus.DRAFT,
        tree_structure={
            "nodes": [
                {
                    "id": "1",
                    "type": "HEADING",
                    "content": "Prüfbereich 1",
                    "children": [
                        {
                            "id": "2",
                            "type": "QUESTION",
                            "content": "Wurde X geprüft?",
                            "answer_type": "BOOLEAN"
                        }
                    ]
                }
            ]
        },
        created_by_id=sample_user.id
    )
    db.add(module)
    await db.commit()
    await db.refresh(module)
    return module

@pytest.fixture
async def sample_llm_config(db: AsyncSession) -> LLMConfiguration:
    config = LLMConfiguration(
        layer="rahmen",
        provider=LLMProvider.OLLAMA,
        endpoint_url="http://localhost:11434",
        model_name="llama3.2",
        is_active=True,
        priority=1
    )
    db.add(config)
    await db.commit()
    await db.refresh(config)
    return config

@pytest.fixture
def mock_llm_response():
    return {
        "nodes": [
            {
                "id": "gen-1",
                "type": "HEADING",
                "content": "Generierter Bereich",
                "children": []
            }
        ]
    }
```

### 2. LLM Service Tests (`backend/tests/test_llm_service.py`)
```python
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.services.llm.llm_service import LLMService
from app.services.llm.ollama_provider import OllamaProvider
from app.services.llm.claude_provider import ClaudeProvider
from app.services.llm.base import LLMResponse

class TestOllamaProvider:
    @pytest.mark.asyncio
    async def test_health_check_success(self):
        provider = OllamaProvider(endpoint_url="http://localhost:11434")

        with patch("httpx.AsyncClient.get") as mock_get:
            mock_get.return_value = MagicMock(status_code=200)
            result = await provider.health_check()
            assert result is True

    @pytest.mark.asyncio
    async def test_health_check_failure(self):
        provider = OllamaProvider(endpoint_url="http://invalid:11434")

        with patch("httpx.AsyncClient.get") as mock_get:
            mock_get.side_effect = Exception("Connection failed")
            result = await provider.health_check()
            assert result is False

    @pytest.mark.asyncio
    async def test_generate_success(self):
        provider = OllamaProvider()

        mock_response = {
            "response": '{"nodes": []}',
            "prompt_eval_count": 100,
            "eval_count": 50
        }

        with patch("httpx.AsyncClient.post") as mock_post:
            mock_post.return_value = MagicMock(
                json=lambda: mock_response
            )
            result = await provider.generate("Test prompt")

            assert isinstance(result, LLMResponse)
            assert result.content == '{"nodes": []}'
            assert result.tokens_input == 100
            assert result.tokens_output == 50
            assert result.provider == "ollama"


class TestClaudeProvider:
    @pytest.mark.asyncio
    async def test_generate_calculates_cost(self):
        with patch("anthropic.AsyncAnthropic") as mock_client:
            mock_response = MagicMock()
            mock_response.content = [MagicMock(text='{"nodes": []}')]
            mock_response.usage.input_tokens = 1000
            mock_response.usage.output_tokens = 500

            mock_client.return_value.messages.create = AsyncMock(
                return_value=mock_response
            )

            provider = ClaudeProvider(api_key="test-key")
            result = await provider.generate("Test prompt")

            assert result.tokens_input == 1000
            assert result.tokens_output == 500
            assert result.cost_eur > 0
            assert result.provider == "claude"


class TestLLMService:
    @pytest.mark.asyncio
    async def test_get_provider_chain_fallback(
        self, db: AsyncSession, sample_llm_config
    ):
        service = LLMService(db)

        with patch.object(OllamaProvider, "health_check", return_value=True):
            providers = await service.get_provider_chain("rahmen")
            assert len(providers) >= 1

    @pytest.mark.asyncio
    async def test_convert_catalog_uses_fallback(
        self, db: AsyncSession, sample_llm_config, mock_llm_response
    ):
        service = LLMService(db)

        with patch.object(
            OllamaProvider, "generate",
            return_value=LLMResponse(
                content=str(mock_llm_response),
                tokens_input=100,
                tokens_output=200,
                cost_eur=0,
                provider="ollama",
                model="llama3.2"
            )
        ):
            result = await service.convert_catalog(
                catalog_content="Test Katalog",
                context={"name": "Test"}
            )

            assert result.provider == "ollama"
            assert result.tokens_input == 100
```

### 3. Module Service Tests (`backend/tests/test_module_service.py`)
```python
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from io import BytesIO
from fastapi import UploadFile
from app.services.module_service import ModuleService
from app.models.module_template import ModuleStatus

class TestModuleService:
    @pytest.mark.asyncio
    async def test_create_module(self, db, sample_user):
        service = ModuleService(db)

        module = await service.create_module(
            name="Neues Modul",
            description="Beschreibung",
            layer="rahmen",
            user=sample_user
        )

        assert module.name == "Neues Modul"
        assert module.slug == "neues-modul"
        assert module.status == ModuleStatus.DRAFT

    @pytest.mark.asyncio
    async def test_create_version_increments_correctly(
        self, db, sample_module, sample_user
    ):
        service = ModuleService(db)

        # Patch Version 1.0.0
        sample_module.version_major = 1
        sample_module.version_minor = 0
        sample_module.version_patch = 0
        await db.commit()

        # Test Patch-Version
        new_module = await service.create_version(
            module_id=sample_module.id,
            version_type="patch",
            change_description="Bugfix",
            user=sample_user
        )
        assert new_module.version_major == 1
        assert new_module.version_minor == 0
        assert new_module.version_patch == 1

    @pytest.mark.asyncio
    async def test_create_version_minor(self, db, sample_module, sample_user):
        service = ModuleService(db)
        sample_module.version_major = 1
        sample_module.version_minor = 2
        sample_module.version_patch = 5
        await db.commit()

        new_module = await service.create_version(
            module_id=sample_module.id,
            version_type="minor",
            change_description="Neue Funktion",
            user=sample_user
        )

        assert new_module.version_major == 1
        assert new_module.version_minor == 3
        assert new_module.version_patch == 0

    @pytest.mark.asyncio
    async def test_create_version_major(self, db, sample_module, sample_user):
        service = ModuleService(db)
        sample_module.version_major = 2
        sample_module.version_minor = 5
        sample_module.version_patch = 3
        await db.commit()

        new_module = await service.create_version(
            module_id=sample_module.id,
            version_type="major",
            change_description="Breaking Change",
            user=sample_user
        )

        assert new_module.version_major == 3
        assert new_module.version_minor == 0
        assert new_module.version_patch == 0

    @pytest.mark.asyncio
    async def test_convert_catalog_integration(
        self, db, sample_user, sample_llm_config
    ):
        service = ModuleService(db)

        # Mock file
        file_content = b"Pruefpunkt 1\nPruefpunkt 2"
        mock_file = UploadFile(
            filename="katalog.txt",
            file=BytesIO(file_content)
        )

        with patch.object(service.llm_service, "convert_catalog") as mock_convert:
            mock_convert.return_value = MagicMock(
                content='{"nodes": []}',
                provider="ollama",
                tokens_input=100,
                tokens_output=50,
                cost_eur=0
            )

            result = await service.convert_catalog(
                file=mock_file,
                name="Test Modul",
                description=None,
                layer="rahmen",
                konzern_id=None,
                user=sample_user
            )

            assert result["status"] == "success"
            assert result["llm_provider_used"] == "ollama"
```

### 4. Staging Service Tests (`backend/tests/test_staging_service.py`)
```python
import pytest
from app.services.staging_service import StagingService, StagingTransition
from app.models.module_template import ModuleStatus

class TestStagingTransitions:
    def test_draft_can_promote_to_dev(self):
        transition = StagingTransition.TRANSITIONS[ModuleStatus.DRAFT]
        assert transition["next"] == ModuleStatus.DEV

    def test_prod_cannot_promote(self):
        transition = StagingTransition.TRANSITIONS[ModuleStatus.PROD]
        assert transition["next"] is None

    def test_reject_targets(self):
        assert StagingTransition.REJECT_TO[ModuleStatus.DEV] == ModuleStatus.DRAFT
        assert StagingTransition.REJECT_TO[ModuleStatus.TEST] == ModuleStatus.DEV


class TestStagingService:
    @pytest.mark.asyncio
    async def test_can_promote_from_draft(self, db, sample_module, sample_user):
        service = StagingService(db)
        sample_module.status = ModuleStatus.DRAFT
        await db.commit()

        can_promote, errors = await service.can_promote(sample_module, sample_user)
        assert can_promote is True
        assert len(errors) == 0

    @pytest.mark.asyncio
    async def test_cannot_promote_from_prod(self, db, sample_module, sample_user):
        service = StagingService(db)
        sample_module.status = ModuleStatus.PROD
        await db.commit()

        can_promote, errors = await service.can_promote(sample_module, sample_user)
        assert can_promote is False
        assert len(errors) > 0

    @pytest.mark.asyncio
    async def test_promote_updates_status(self, db, sample_module, sample_user):
        service = StagingService(db)
        sample_module.status = ModuleStatus.DRAFT
        await db.commit()

        result = await service.promote(
            module_id=sample_module.id,
            user=sample_user,
            comment="Test promotion"
        )

        assert result.status == ModuleStatus.DEV

    @pytest.mark.asyncio
    async def test_reject_returns_to_previous(self, db, sample_module, sample_user):
        service = StagingService(db)
        sample_module.status = ModuleStatus.TEST
        await db.commit()

        result = await service.reject(
            module_id=sample_module.id,
            user=sample_user,
            reason="Fehler gefunden"
        )

        assert result.status == ModuleStatus.DEV

    @pytest.mark.asyncio
    async def test_validation_catches_empty_nodes(self, db, sample_user):
        from app.models.module_template import ModuleTemplate

        module = ModuleTemplate(
            name="Invalid Module",
            slug="invalid",
            layer="rahmen",
            status=ModuleStatus.DRAFT,
            tree_structure={
                "nodes": [
                    {"id": "1", "type": "HEADING", "content": ""}  # Leer!
                ]
            },
            created_by_id=sample_user.id
        )
        db.add(module)
        await db.commit()

        service = StagingService(db)
        errors = await service._validate_module_structure(module)

        assert len(errors) > 0
        assert "Leerer Inhalt" in errors[0]
```

### 5. API Tests (`backend/tests/test_module_api.py`)
```python
import pytest
from httpx import AsyncClient

class TestModuleAPI:
    @pytest.mark.asyncio
    async def test_list_modules(self, client: AsyncClient, auth_headers):
        response = await client.get(
            "/api/v1/modules/",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data

    @pytest.mark.asyncio
    async def test_get_module(
        self, client: AsyncClient, auth_headers, sample_module
    ):
        response = await client.get(
            f"/api/v1/modules/{sample_module.id}",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == sample_module.name

    @pytest.mark.asyncio
    async def test_get_module_not_found(self, client: AsyncClient, auth_headers):
        response = await client.get(
            "/api/v1/modules/99999",
            headers=auth_headers
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_promote_module(
        self, client: AsyncClient, auth_headers, sample_module
    ):
        response = await client.post(
            f"/api/v1/modules/{sample_module.id}/promote",
            headers=auth_headers,
            json={"comment": "Ready for DEV"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "dev"

    @pytest.mark.asyncio
    async def test_create_version(
        self, client: AsyncClient, auth_headers, sample_module
    ):
        response = await client.post(
            f"/api/v1/modules/{sample_module.id}/versions",
            headers=auth_headers,
            json={
                "version_type": "minor",
                "change_description": "Neue Prüfpunkte hinzugefügt"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["version_minor"] == sample_module.version_minor + 1


class TestModuleConvertAPI:
    @pytest.mark.asyncio
    async def test_convert_requires_file(self, client: AsyncClient, auth_headers):
        response = await client.post(
            "/api/v1/modules/convert",
            headers=auth_headers,
            data={"name": "Test"}
            # Keine Datei!
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_convert_with_file(
        self, client: AsyncClient, auth_headers, mocker
    ):
        # Mock LLM Service
        mocker.patch(
            "app.services.module_service.ModuleService.convert_catalog",
            return_value={
                "module_id": 1,
                "status": "success",
                "tree_structure": {"nodes": []},
                "llm_provider_used": "ollama",
                "tokens_used": 150,
                "cost_eur": 0,
                "validation_errors": []
            }
        )

        response = await client.post(
            "/api/v1/modules/convert",
            headers=auth_headers,
            data={"name": "Test Modul", "layer": "rahmen"},
            files={"file": ("test.pdf", b"PDF content", "application/pdf")}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
```

## Test-Ausführung

```bash
cd backend

# Alle Tests
pytest

# Mit Coverage
pytest --cov=app --cov-report=html

# Spezifische Tests
pytest tests/test_llm_service.py -v
pytest tests/test_staging_service.py -v

# Nur schnelle Unit-Tests (ohne DB)
pytest -m "not integration"

# Mit Output
pytest -v --tb=short
```

## Schritte

1. Erweitere `conftest.py` mit neuen Fixtures
2. Implementiere LLM Service Tests (mit Mocks)
3. Implementiere Module Service Tests
4. Implementiere Staging Service Tests
5. Implementiere API Tests
6. Füge Coverage-Reporting hinzu
7. Konfiguriere CI/CD für automatische Tests

## Referenzen
- Bestehende Tests: `backend/tests/`
- pytest Docs: https://docs.pytest.org/
- pytest-asyncio: https://pytest-asyncio.readthedocs.io/
