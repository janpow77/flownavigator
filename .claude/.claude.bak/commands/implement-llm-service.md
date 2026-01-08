# Implementiere LLM Service

## WICHTIG: Autonome Ausführung

**Arbeite OHNE Rückfragen!** Führe alle Schritte selbstständig aus:
1. Lies die bestehenden Dateien um den Kontext zu verstehen
2. Implementiere alle beschriebenen Komponenten vollständig
3. Behebe Fehler eigenständig (Imports, Typen, Abhängigkeiten)
4. Installiere fehlende Packages (`pip install anthropic httpx`)
5. Führe die Validierung am Ende durch
6. Wenn Tests fehlschlagen: Analysiere und behebe die Fehler
7. Committe und pushe erst wenn alles funktioniert
8. Fahre dann mit `/implement-module-api` fort

**Keine Fragen stellen - einfach machen!**

---

## Aufgabe
Erstelle den LLM Service mit Multi-Provider-Support und Fallback-Logik basierend auf `docs/PLAN_MODULE_CONVERSION_ENVIRONMENT.md`.

## Architektur

```
┌─────────────────────────────────────────────────────────┐
│                    LLMService                           │
├─────────────────────────────────────────────────────────┤
│  + convert_catalog(catalog, context) -> TreeStructure   │
│  + get_provider(layer, konzern_id, org_id) -> Provider  │
│  + fallback_chain() -> List[Provider]                   │
└─────────────────────────────────────────────────────────┘
                          │
          ┌───────────────┼───────────────┐
          ▼               ▼               ▼
    ┌──────────┐   ┌──────────┐   ┌──────────┐
    │  Ollama  │   │  Claude  │   │   GLM    │
    │ Provider │   │ Provider │   │ Provider │
    └──────────┘   └──────────┘   └──────────┘
```

## Zu erstellende Dateien

### 1. Provider Interface (`backend/app/services/llm/base.py`)
```python
from abc import ABC, abstractmethod
from typing import Optional
from pydantic import BaseModel

class LLMResponse(BaseModel):
    content: str
    tokens_input: int
    tokens_output: int
    cost_eur: Optional[float] = None
    provider: str
    model: str

class BaseLLMProvider(ABC):
    @abstractmethod
    async def generate(self, prompt: str, system_prompt: str = None) -> LLMResponse:
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        pass
```

### 2. Ollama Provider (`backend/app/services/llm/ollama_provider.py`)
```python
import httpx
from .base import BaseLLMProvider, LLMResponse

class OllamaProvider(BaseLLMProvider):
    def __init__(self, endpoint_url: str = "http://localhost:11434", model: str = "llama3.2"):
        self.endpoint_url = endpoint_url
        self.model = model

    async def generate(self, prompt: str, system_prompt: str = None) -> LLMResponse:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.endpoint_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "system": system_prompt or "",
                    "stream": False
                },
                timeout=120.0
            )
            data = response.json()
            return LLMResponse(
                content=data["response"],
                tokens_input=data.get("prompt_eval_count", 0),
                tokens_output=data.get("eval_count", 0),
                cost_eur=0.0,  # Ollama ist lokal/kostenlos
                provider="ollama",
                model=self.model
            )

    async def health_check(self) -> bool:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.endpoint_url}/api/tags", timeout=5.0)
                return response.status_code == 200
        except:
            return False
```

### 3. Claude Provider (`backend/app/services/llm/claude_provider.py`)
```python
import anthropic
from .base import BaseLLMProvider, LLMResponse

# Preise Stand 2024 (Opus 4)
CLAUDE_PRICES = {
    "claude-opus-4-20250514": {"input": 15.0, "output": 75.0},  # per 1M tokens
    "claude-sonnet-4-20250514": {"input": 3.0, "output": 15.0},
}

class ClaudeProvider(BaseLLMProvider):
    def __init__(self, api_key: str, model: str = "claude-opus-4-20250514"):
        self.client = anthropic.AsyncAnthropic(api_key=api_key)
        self.model = model

    async def generate(self, prompt: str, system_prompt: str = None) -> LLMResponse:
        response = await self.client.messages.create(
            model=self.model,
            max_tokens=8192,
            system=system_prompt or "Du bist ein Experte für Prüfschemata und Audit-Workflows.",
            messages=[{"role": "user", "content": prompt}]
        )

        tokens_in = response.usage.input_tokens
        tokens_out = response.usage.output_tokens
        prices = CLAUDE_PRICES.get(self.model, {"input": 15.0, "output": 75.0})
        cost = (tokens_in * prices["input"] + tokens_out * prices["output"]) / 1_000_000

        return LLMResponse(
            content=response.content[0].text,
            tokens_input=tokens_in,
            tokens_output=tokens_out,
            cost_eur=cost,
            provider="claude",
            model=self.model
        )

    async def health_check(self) -> bool:
        try:
            # Minimaler API-Call zum Testen
            await self.client.messages.create(
                model=self.model,
                max_tokens=10,
                messages=[{"role": "user", "content": "Hi"}]
            )
            return True
        except:
            return False
```

### 4. GLM Provider (`backend/app/services/llm/glm_provider.py`)
```python
import httpx
from .base import BaseLLMProvider, LLMResponse

class GLMProvider(BaseLLMProvider):
    def __init__(self, api_key: str, endpoint_url: str = "https://open.bigmodel.cn/api/paas/v4"):
        self.api_key = api_key
        self.endpoint_url = endpoint_url
        self.model = "glm-4"

    async def generate(self, prompt: str, system_prompt: str = None) -> LLMResponse:
        async with httpx.AsyncClient() as client:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            response = await client.post(
                f"{self.endpoint_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={"model": self.model, "messages": messages},
                timeout=120.0
            )
            data = response.json()

            usage = data.get("usage", {})
            return LLMResponse(
                content=data["choices"][0]["message"]["content"],
                tokens_input=usage.get("prompt_tokens", 0),
                tokens_output=usage.get("completion_tokens", 0),
                cost_eur=0.01,  # GLM Pricing anpassen
                provider="glm",
                model=self.model
            )

    async def health_check(self) -> bool:
        # Implementiere Health Check
        return True
```

### 5. LLM Service Orchestrator (`backend/app/services/llm/llm_service.py`)
```python
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.llm_configuration import LLMConfiguration, LLMProvider as LLMProviderEnum
from .base import BaseLLMProvider, LLMResponse
from .ollama_provider import OllamaProvider
from .claude_provider import ClaudeProvider
from .glm_provider import GLMProvider
from app.core.security import decrypt_api_key

class LLMService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_provider_chain(
        self,
        layer: str,
        konzern_id: Optional[int] = None,
        organization_id: Optional[int] = None
    ) -> List[BaseLLMProvider]:
        """
        Hole Provider-Chain mit Fallback:
        1. Prüfe Orga-Level (wenn organization_id)
        2. Prüfe Konzern-Level (wenn konzern_id)
        3. Prüfe Rahmen-Level (immer)
        """
        providers = []

        # Lookup-Chain durchlaufen
        lookups = []
        if organization_id:
            lookups.append(("orga", konzern_id, organization_id))
        if konzern_id:
            lookups.append(("konzern", konzern_id, None))
        lookups.append(("rahmen", None, None))

        for layer, k_id, o_id in lookups:
            query = select(LLMConfiguration).where(
                LLMConfiguration.layer == layer,
                LLMConfiguration.konzern_id == k_id,
                LLMConfiguration.organization_id == o_id,
                LLMConfiguration.is_active == True
            ).order_by(LLMConfiguration.priority)

            result = await self.db.execute(query)
            configs = result.scalars().all()

            for config in configs:
                provider = await self._create_provider(config)
                if provider and await provider.health_check():
                    providers.append(provider)

        return providers

    async def _create_provider(self, config: LLMConfiguration) -> Optional[BaseLLMProvider]:
        api_key = decrypt_api_key(config.api_key_encrypted) if config.api_key_encrypted else None

        if config.provider == LLMProviderEnum.OLLAMA:
            return OllamaProvider(
                endpoint_url=config.endpoint_url or "http://localhost:11434",
                model=config.model_name
            )
        elif config.provider == LLMProviderEnum.CLAUDE:
            if not api_key:
                return None
            return ClaudeProvider(api_key=api_key, model=config.model_name)
        elif config.provider == LLMProviderEnum.GLM:
            if not api_key:
                return None
            return GLMProvider(api_key=api_key, endpoint_url=config.endpoint_url)

        return None

    async def convert_catalog(
        self,
        catalog_content: str,
        context: dict,
        layer: str = "rahmen",
        konzern_id: Optional[int] = None,
        organization_id: Optional[int] = None
    ) -> LLMResponse:
        """Konvertiere Katalog zu Prüfschema mit Fallback-Chain"""

        providers = await self.get_provider_chain(layer, konzern_id, organization_id)

        if not providers:
            raise ValueError("Keine LLM-Provider verfügbar")

        system_prompt = self._get_conversion_system_prompt()
        user_prompt = self._get_conversion_user_prompt(catalog_content, context)

        last_error = None
        for provider in providers:
            try:
                return await provider.generate(user_prompt, system_prompt)
            except Exception as e:
                last_error = e
                continue

        raise last_error or ValueError("Alle Provider fehlgeschlagen")

    def _get_conversion_system_prompt(self) -> str:
        return """Du bist ein Experte für die Konvertierung von Prüfkatalogen in strukturierte Prüfschemata.

Deine Aufgabe:
1. Analysiere den gegebenen Katalog (PDF-Text, Word-Inhalt, etc.)
2. Extrahiere die Prüfpunkte und ihre Hierarchie
3. Erstelle ein strukturiertes JSON-Prüfschema

Das Output-Format ist:
{
  "nodes": [
    {
      "id": "uuid",
      "type": "HEADING|QUESTION|DECISION|HINT",
      "content": "...",
      "answer_type": "BOOLEAN|CURRENCY|DATE|CUSTOM_ENUM",
      "children": [...],
      "ja_branch": [...],  // nur bei DECISION
      "nein_branch": [...]  // nur bei DECISION
    }
  ]
}
"""

    def _get_conversion_user_prompt(self, catalog_content: str, context: dict) -> str:
        return f"""Konvertiere den folgenden Prüfkatalog in ein strukturiertes Prüfschema:

## Katalog-Inhalt:
{catalog_content}

## Kontext:
- Modul-Name: {context.get('name', 'Unbekannt')}
- Beschreibung: {context.get('description', '')}
- Zielgruppe: {context.get('target_audience', 'Interne Revision')}

## Anforderungen:
1. Behalte die Hierarchie des Katalogs bei
2. Verwende DECISION-Nodes für Ja/Nein-Entscheidungen
3. Füge HINT-Nodes für Erläuterungen hinzu
4. Erstelle sinnvolle IDs (UUIDs)

Antworte NUR mit dem JSON-Schema, keine Erklärungen.
"""
```

## Dependencies
Füge zu `backend/requirements.txt` hinzu:
```
anthropic>=0.18.0
httpx>=0.27.0
```

## Schritte

1. Erstelle Verzeichnis: `backend/app/services/llm/`
2. Erstelle `__init__.py` mit Exports
3. Implementiere Provider in der Reihenfolge: Ollama → Claude → GLM
4. Implementiere LLMService
5. Füge API-Key Verschlüsselung zu `backend/app/core/security.py` hinzu
6. Schreibe Unit-Tests für jeden Provider

## Validierung
```bash
cd backend
pytest tests/test_llm_service.py -v
```

## Referenzen
- Planung: `docs/PLAN_MODULE_CONVERSION_ENVIRONMENT.md` (Sektion 7: LLM-Integration)
