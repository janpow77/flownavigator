# Konzept: Development-Modul mit iterativem Workflow und Memory

## 0. Eigenständige Modul-Architektur

Das Development-Modul ist ein **vollständig eigenständiges Package** innerhalb der FlowAudit-Plattform. Es hat keine harten Abhängigkeiten zu anderen Fachmodulen und kann unabhängig deployed werden.

### 0.1 Package-Struktur (konsistent mit bestehendem System)

Das Development-Modul folgt **exakt dem gleichen Pattern** wie bestehende Module (Checklists, Documents, etc.):

```
packages/
├── core/
│   ├── common/                  # @flowaudit/common (vorhanden)
│   └── validation/              # @flowaudit/validation (vorhanden)
│
├── domain/
│   ├── checklists/              # @flowaudit/checklists (vorhanden)
│   ├── group-queries/           # @flowaudit/group-queries (vorhanden)
│   │
│   └── development/             # ◀ @flowaudit/development (NEU)
│       ├── package.json
│       ├── tsconfig.json
│       ├── tsup.config.ts
│       └── src/
│           └── index.ts         # Alle Exports (Types, Interfaces, Utils)
│
├── documents/
│   └── document-box/            # @flowaudit/document-box (vorhanden)
│
└── adapters/
    └── vue-adapter/             # @flowaudit/vue-adapter (vorhanden)


apps/backend/app/
├── api/
│   ├── __init__.py              # Zentrale Router-Registrierung
│   ├── auth.py                  # (vorhanden)
│   ├── checklists.py            # (vorhanden)
│   ├── document_box.py          # (vorhanden)
│   ├── modules.py               # (vorhanden)
│   │
│   └── development.py           # ◀ NEU: Router mit prefix="/development"
│
├── models/
│   ├── audit_case.py            # (vorhanden)
│   ├── module_converter.py      # (vorhanden)
│   │
│   └── development.py           # ◀ NEU: SQLAlchemy Models
│
├── schemas/
│   ├── checklist.py             # (vorhanden)
│   │
│   └── development.py           # ◀ NEU: Pydantic Schemas
│
└── services/
    ├── module_service.py        # (vorhanden)
    ├── github_service.py        # (vorhanden)
    │
    └── development/             # ◀ NEU: Development-Services
        ├── __init__.py
        ├── session_service.py
        ├── context_service.py
        ├── multi_llm_service.py
        ├── git_integration_service.py
        └── dependency_validator.py


apps/frontend/src/
├── views/
│   ├── AuditCasesView.vue       # (vorhanden)
│   ├── ModuleConverterView.vue  # (vorhanden)
│   │
│   └── DevelopmentView.vue      # ◀ NEU: Haupt-View
│
├── components/
│   ├── checklists/              # (vorhanden)
│   ├── documents/               # (vorhanden)
│   ├── module-converter/        # (vorhanden)
│   │
│   └── development/             # ◀ NEU: Development-Komponenten
│       ├── DevelopmentDashboard.vue
│       ├── SessionWizard.vue
│       ├── FeedbackLoop.vue
│       ├── ModuleFlowDiagram.vue
│       ├── FileUploader.vue
│       ├── IterationPanel.vue
│       ├── ProposalView.vue
│       └── UserProfileSettings.vue
│
├── api/
│   ├── checklists.ts            # (vorhanden)
│   ├── moduleConverter.ts       # (vorhanden)
│   │
│   └── development.ts           # ◀ NEU: API-Client
│
└── stores/
    ├── auth.ts                  # (vorhanden)
    ├── moduleConverter.ts       # (vorhanden)
    │
    └── development.ts           # ◀ NEU: Pinia Store
```

### 0.2 Abhängigkeiten

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                    DEVELOPMENT-MODUL ABHÄNGIGKEITEN                              │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │                     @flowaudit/development                               │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│                                    │                                             │
│                    ┌───────────────┼───────────────┐                            │
│                    ▼               ▼               ▼                            │
│            ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                   │
│            │  @flowaudit │  │  PostgreSQL │  │  LLM APIs   │                   │
│            │  /common    │  │  + pgvector │  │  (extern)   │                   │
│            └─────────────┘  └─────────────┘  └─────────────┘                   │
│                 ▲                  ▲               ▲                            │
│                 │                  │               │                            │
│            Shared Types      Vektordatenbank   GLM-4, Claude                   │
│            Utilities         (KEINE ChromaDB!)  Multi-Provider                  │
│                                                                                  │
│  ─────────────────────────────────────────────────────────────────────────────  │
│  KEINE Abhängigkeiten zu:                                                       │
│  ✗ @flowaudit/checklists                                                        │
│  ✗ @flowaudit/documents                                                         │
│  ✗ @flowaudit/group-queries                                                     │
│  ✗ Andere Fachmodule                                                            │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 0.3 Vektordatenbank: pgvector (KEINE ChromaDB)

Das Development-Modul nutzt **pgvector** als Vektordatenbank-Erweiterung für PostgreSQL. Dies vermeidet eine zusätzliche Infrastruktur-Komponente.

```sql
-- pgvector Extension aktivieren
CREATE EXTENSION IF NOT EXISTS vector;

-- Embeddings für semantische Suche
CREATE TABLE development_embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id),

    -- Referenz
    entity_type VARCHAR(50) NOT NULL,        -- 'iteration', 'feedback', 'file_chunk'
    entity_id UUID NOT NULL,

    -- Content
    content_text TEXT NOT NULL,

    -- Vector (1536 für OpenAI ada-002, 1024 für andere)
    embedding vector(1536),

    -- Metadata
    metadata JSONB DEFAULT '{}',

    created_at TIMESTAMP DEFAULT NOW()
);

-- Index für schnelle Similarity-Suche
CREATE INDEX idx_dev_embeddings_vector
    ON development_embeddings
    USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

-- Index für Entity-Lookup
CREATE INDEX idx_dev_embeddings_entity
    ON development_embeddings(entity_type, entity_id);
```

**Vorteile von pgvector gegenüber ChromaDB:**

| Aspekt | pgvector | ChromaDB |
|--------|----------|----------|
| **Infrastruktur** | Nutzt bestehende PostgreSQL | Separater Service nötig |
| **Transaktionen** | ACID-konform mit Rest der DB | Eigene Transaktionslogik |
| **Backup** | In DB-Backup enthalten | Separates Backup nötig |
| **Skalierung** | Mit PostgreSQL | Eigene Skalierung |
| **Latenz** | Direkt in DB-Queries | Netzwerk-Overhead |

### 0.4 Modul-Registrierung (konsistent mit bestehendem Pattern)

Die Integration folgt dem **bestehenden Pattern** aus `app/api/__init__.py`:

```python
# apps/backend/app/api/development.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.auth import get_current_user, require_roles
from app.schemas.development import (
    DevelopmentSessionCreate,
    DevelopmentSessionResponse,
    DevelopmentIterationCreate,
    # ...
)
from app.services.development import (
    SessionService,
    IterationService,
    ContextService,
)

router = APIRouter(prefix="/development", tags=["Development"])

# Rollenbasierter Zugriff für alle Endpoints
REQUIRED_ROLES = ["developer", "admin"]


@router.get("/sessions", response_model=list[DevelopmentSessionResponse])
async def list_sessions(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_roles(REQUIRED_ROLES)),
):
    """Liste aller Development-Sessions des Users."""
    service = SessionService(db)
    return await service.list_sessions(current_user.tenant_id, current_user.id)


@router.post("/sessions", response_model=DevelopmentSessionResponse)
async def create_session(
    data: DevelopmentSessionCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_roles(REQUIRED_ROLES)),
):
    """Neue Development-Session starten."""
    service = SessionService(db)
    return await service.create_session(data, current_user)

# ... weitere Endpoints
```

```python
# apps/backend/app/api/__init__.py (Ergänzung)

from app.api.development import router as development_router

# Bestehende Router...
router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
router.include_router(checklists_router, tags=["Checklists"])
# ...

# NEU: Development-Router
router.include_router(development_router, tags=["Development"])
```

```typescript
// apps/frontend/src/router/index.ts (Ergänzung)

import DevelopmentView from '@/views/DevelopmentView.vue'

const routes = [
  // ... bestehende Routen
  {
    path: '/',
    component: DefaultLayout,
    meta: { requiresAuth: true },
    children: [
      // ... bestehende Children
      {
        path: 'development',
        name: 'development',
        component: DevelopmentView,
        meta: { requiredRoles: ['developer', 'admin'] }  // Rollenprüfung
      }
    ]
  }
]
```

---

## 1. Übersicht

Das Development-Modul ist das zentrale Werkzeug zur Entwicklung neuer Module und Features. Es kombiniert:

- **Modul-Auswahl** mit Flussdiagramm-Visualisierung
- **Iterativen Feedback-Loop** zwischen Entwickler und LLM
- **Persistentes Memory** für Kontext über Sessions hinweg
- **Parallele Entwicklung und Testing**

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         DEVELOPMENT-MODUL WORKFLOW                               │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────────────────────┐   │
│  │ 1. MODUL     │───>│ 2. DATEIEN   │───>│ 3. AUFGABE BESCHREIBEN          │   │
│  │    AUSWÄHLEN │    │    HOCHLADEN │    │    (Was soll entwickelt werden?) │   │
│  └──────────────┘    └──────────────┘    └──────────────────────────────────┘   │
│         │                   │                           │                        │
│         ▼                   ▼                           ▼                        │
│  ┌──────────────┐    ┌──────────────┐    ╔══════════════════════════════════╗   │
│  │ Flussdiagramm│    │ Erläuterung  │    ║ 4. ITERATIVER FEEDBACK-LOOP     ║   │
│  │ zeigt        │    │ pro Datei    │    ║    ┌───────────────────────┐    ║   │
│  │ Position     │    │ eingeben     │    ║    │ LLM → Vorschlag       │    ║   │
│  └──────────────┘    └──────────────┘    ║    │      ↓                │    ║   │
│                                          ║    │ User → Feedback       │    ║   │
│                                          ║    │      ↓                │    ║   │
│                                          ║    │ LLM → Überarbeitung   │    ║   │
│                                          ║    │      ↓                │    ║   │
│                                          ║    │ Wiederholen...        │    ║   │
│                                          ║    └───────────────────────┘    ║   │
│                                          ╚══════════════════════════════════╝   │
│                                                         │                        │
│                                                         ▼                        │
│                                          ┌──────────────────────────────────┐   │
│                                          │ 5. FREIGABE                      │   │
│                                          │    User gibt Entwicklung frei    │   │
│                                          └──────────────────────────────────┘   │
│                                                         │                        │
│                                                         ▼                        │
│                                          ┌──────────────────────────────────┐   │
│                                          │ 6. ENTWICKLUNG + TESTING         │   │
│                                          │    (parallel)                    │   │
│                                          └──────────────────────────────────┘   │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 1.1 User-Profil & Globale Präferenzen

Bevor das Development-Modul arbeitet, werden **User-spezifische Präferenzen** geladen. Diese beeinflussen jeden LLM-Prompt.

### Datenmodell: User Profile

```sql
CREATE TABLE user_profile (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,

    -- Key-Value für flexible Präferenzen
    key VARCHAR(100) NOT NULL,
    value TEXT NOT NULL,
    value_type VARCHAR(20) DEFAULT 'string',  -- string, json, boolean, number

    -- Kategorisierung
    category VARCHAR(50),                      -- code_style, language, llm, ui

    last_updated TIMESTAMP DEFAULT NOW(),

    UNIQUE(user_id, key)
);

CREATE INDEX idx_user_profile ON user_profile(user_id, category);
```

### Beispiel-Präferenzen

| Key | Value | Kategorie | Beschreibung |
|-----|-------|-----------|--------------|
| `code_language` | `de` | code_style | Sprache für Code-Kommentare |
| `vba_comments_language` | `de` | code_style | Sprache für VBA-Kommentare |
| `error_handling_style` | `strukturierte Fehlerprozeduren auf Deutsch` | code_style | Fehlerbehandlungs-Stil |
| `naming_convention` | `camelCase` | code_style | Namenskonvention |
| `preferred_llm` | `anthropic` | llm | Bevorzugtes LLM |
| `max_tokens_per_request` | `8000` | llm | Token-Limit |
| `ui_language` | `de` | ui | UI-Sprache |
| `notification_on_completion` | `true` | ui | Benachrichtigung bei Fertigstellung |

### Integration in Context-Service

```python
class DevelopmentContextService:
    async def build_context(self, session_id: str, ...) -> str:
        # 1. IMMER ZUERST: User-Profil laden
        user_profile = await self._get_user_profile(session.created_by)

        # 2. User-Präferenzen als festen Block im Prompt
        profile_context = self._format_user_profile(user_profile)

        context_parts = [profile_context]  # Immer an erster Stelle!

        # ... Rest des Kontexts

    def _format_user_profile(self, profile: dict) -> str:
        return f"""
## Benutzer-Präferenzen (IMMER BEACHTEN!)

Diese Präferenzen MÜSSEN bei jeder Code-Generierung befolgt werden:

- **Code-Kommentare:** {profile.get('code_language', 'de')}
- **Namenskonvention:** {profile.get('naming_convention', 'camelCase')}
- **Fehlerbehandlung:** {profile.get('error_handling_style', 'Standard')}
- **VBA-Kommentare:** {profile.get('vba_comments_language', 'de')}

⚠️ Diese Präferenzen haben Vorrang vor allgemeinen Best Practices!
"""
```

### User-Profil in Benutzereinstellungen (UI)

Das User-Profil ist als **eigene Registerkarte** in den Benutzereinstellungen sichtbar, aber nur für Benutzer mit der Rolle `developer` oder `admin`.

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         BENUTZEREINSTELLUNGEN                                    │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  ┌──────────────┬──────────────┬──────────────┬──────────────┐                  │
│  │  Allgemein   │   Sicherheit │  Benachricht.│ ●Development │  ← Neue Tab     │
│  └──────────────┴──────────────┴──────────────┴──────────────┘                  │
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │ ENTWICKLER-PRÄFERENZEN                                                   │    │
│  ├─────────────────────────────────────────────────────────────────────────┤    │
│  │                                                                          │    │
│  │ Code-Stil                                                               │    │
│  │ ─────────────────────────────────────────────────────────────           │    │
│  │ Sprache für Code-Kommentare:    [Deutsch           ▾]                   │    │
│  │ Sprache für VBA-Kommentare:     [Deutsch           ▾]                   │    │
│  │ Namenskonvention:               [camelCase         ▾]                   │    │
│  │ Fehlerbehandlung:               [Strukturiert (DE) ▾]                   │    │
│  │                                                                          │    │
│  │ LLM-Einstellungen                                                       │    │
│  │ ─────────────────────────────────────────────────────────────           │    │
│  │ Bevorzugter Provider:           [Anthropic Claude  ▾]                   │    │
│  │ Max. Tokens pro Anfrage:        [8000              ]                    │    │
│  │ Kreativität (Temperature):      [0.7               ]                    │    │
│  │                                                                          │    │
│  │ Benachrichtigungen                                                      │    │
│  │ ─────────────────────────────────────────────────────────────           │    │
│  │ [✓] Bei Fertigstellung benachrichtigen                                  │    │
│  │ [✓] Bei Feedback-Anforderung benachrichtigen                            │    │
│  │ [ ] E-Mail bei Session-Abschluss                                        │    │
│  │                                                                          │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│                                                                                  │
│  [Speichern]  [Zurücksetzen]                                                    │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Rollenbasierter Zugriff

```python
# apps/frontend/src/components/development/UserProfileSettings.vue

# Die Registerkarte wird nur angezeigt wenn:
# 1. User hat Rolle "developer" ODER "admin"
# 2. Development-Modul ist für den Tenant aktiviert

def can_access_development_settings(user: User) -> bool:
    return (
        "developer" in user.roles or
        "admin" in user.roles
    )
```

### API-Endpoints für User-Profil

```
GET  /api/v1/development/profile              → Eigenes Profil abrufen
PUT  /api/v1/development/profile              → Eigenes Profil aktualisieren
GET  /api/v1/development/profile/defaults     → System-Defaults abrufen
POST /api/v1/development/profile/reset        → Auf Defaults zurücksetzen

# Nur für Admins:
GET  /api/v1/development/profiles             → Alle Profile (Admin)
GET  /api/v1/development/profiles/{user_id}   → Profil eines Users (Admin)
PUT  /api/v1/development/profiles/{user_id}   → Profil eines Users ändern (Admin)
```

### Admin-Benutzer Setup

Für die Ersteinrichtung wird der Benutzer `jan.riener` mit sämtlichen Rechten angelegt:

```sql
-- Admin-Benutzer anlegen (Passwort: admin123)
INSERT INTO users (
    id,
    email,
    username,
    password_hash,
    first_name,
    last_name,
    is_active,
    is_superuser,
    created_at
) VALUES (
    gen_random_uuid(),
    'jan.riener@flowaudit.de',
    'jan.riener',
    -- bcrypt hash für 'admin123'
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.qUoXdJqZc1hZmS',
    'Jan',
    'Riener',
    true,
    true,  -- Superuser = alle Rechte
    NOW()
);

-- Rollen zuweisen
INSERT INTO user_roles (user_id, role_name) VALUES
    ((SELECT id FROM users WHERE username = 'jan.riener'), 'admin'),
    ((SELECT id FROM users WHERE username = 'jan.riener'), 'developer'),
    ((SELECT id FROM users WHERE username = 'jan.riener'), 'auditor');

-- Initiale Präferenzen setzen
INSERT INTO user_profile (user_id, key, value, category) VALUES
    ((SELECT id FROM users WHERE username = 'jan.riener'), 'code_language', 'de', 'code_style'),
    ((SELECT id FROM users WHERE username = 'jan.riener'), 'vba_comments_language', 'de', 'code_style'),
    ((SELECT id FROM users WHERE username = 'jan.riener'), 'naming_convention', 'camelCase', 'code_style'),
    ((SELECT id FROM users WHERE username = 'jan.riener'), 'preferred_llm', 'anthropic', 'llm'),
    ((SELECT id FROM users WHERE username = 'jan.riener'), 'ui_language', 'de', 'ui');
```

### Rollen-Übersicht

| Rolle | Zugriff auf Development-Modul | User-Profil sichtbar |
|-------|-------------------------------|----------------------|
| `viewer` | ✗ Kein Zugriff | ✗ Tab nicht sichtbar |
| `auditor` | ✗ Kein Zugriff | ✗ Tab nicht sichtbar |
| `developer` | ✓ Voller Zugriff | ✓ Eigenes Profil |
| `admin` | ✓ Voller Zugriff + Admin-Funktionen | ✓ Alle Profile |

---

## 1.2 Konzern- & Organisations-Hierarchie

Das System unterstützt eine mehrstufige Hierarchie: **Konzern → Organisation → Mandant → Module**

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         HIERARCHIE-MODELL                                        │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  KONZERN (Group)                                                                │
│  └─ Behörde XY / Holding ABC                                                    │
│     │                                                                            │
│     ├─ ORGANISATION A (Gesellschaft A1)                                         │
│     │  ├─ Mandant: Produktion                                                   │
│     │  │  ├─ Module: Checklists v3.2, Documents v1.5                           │
│     │  │  └─ Eigene Parameter & Prüfregeln                                     │
│     │  │                                                                        │
│     │  └─ Mandant: Vertrieb                                                     │
│     │     ├─ Module: Checklists v3.0 (ältere Version!)                         │
│     │     └─ Andere Prüfregeln                                                 │
│     │                                                                            │
│     ├─ ORGANISATION B (Gesellschaft A2)                                         │
│     │  └─ Mandant: Zentral                                                      │
│     │     └─ Module: Nur Reports v1.0                                          │
│     │                                                                            │
│     └─ ORGANISATION C (Gesellschaft A3)                                         │
│        └─ ...                                                                    │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Datenmodell: Konzern-Struktur

```sql
-- Konzern (oberste Ebene)
CREATE TABLE groups (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    name VARCHAR(255) NOT NULL,
    display_name VARCHAR(255) NOT NULL,
    description TEXT,

    -- Konzern-weite Einstellungen
    default_settings JSONB DEFAULT '{}',
    allowed_modules JSONB DEFAULT '[]',      -- Welche Module darf der Konzern nutzen?

    -- Branding
    logo_url VARCHAR(500),
    primary_color VARCHAR(20),

    -- Status
    status VARCHAR(20) DEFAULT 'active',

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Organisation (Gesellschaft innerhalb des Konzerns)
CREATE TABLE organizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    group_id UUID REFERENCES groups(id) ON DELETE CASCADE,

    name VARCHAR(255) NOT NULL,
    display_name VARCHAR(255) NOT NULL,
    org_type VARCHAR(50),                    -- holding, subsidiary, branch, department

    -- Organisations-spezifische Einstellungen (überschreiben Konzern)
    settings_override JSONB DEFAULT '{}',
    allowed_modules JSONB DEFAULT '[]',      -- Kann einschränken, nicht erweitern

    -- Kontakt
    contact_email VARCHAR(255),

    status VARCHAR(20) DEFAULT 'active',

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(group_id, name)
);

-- Mandant (bestehende Tabelle erweitern)
ALTER TABLE tenants ADD COLUMN IF NOT EXISTS
    organization_id UUID REFERENCES organizations(id);

ALTER TABLE tenants ADD COLUMN IF NOT EXISTS
    settings_override JSONB DEFAULT '{}';   -- Überschreibt Org-Settings

-- Modul-Instanz pro Mandant (welche Version ist wo aktiv?)
CREATE TABLE tenant_module_instances (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    module_id UUID REFERENCES module_registry(id),

    -- Versionierung
    installed_version VARCHAR(20) NOT NULL,
    target_version VARCHAR(20),              -- Falls Update geplant

    -- Mandanten-spezifische Konfiguration
    config_override JSONB DEFAULT '{}',

    -- Status
    status VARCHAR(20) DEFAULT 'active',     -- active, disabled, updating

    installed_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(tenant_id, module_id)
);

CREATE INDEX idx_tenant_modules ON tenant_module_instances(tenant_id);
```

### Hierarchische Einstellungs-Vererbung

```python
def get_effective_settings(tenant_id: str) -> dict:
    """
    Ermittelt effektive Einstellungen durch Hierarchie-Vererbung.
    Priorität: Mandant > Organisation > Konzern > System-Default
    """
    tenant = get_tenant(tenant_id)
    org = get_organization(tenant.organization_id)
    group = get_group(org.group_id)

    # Basis: System-Defaults
    settings = SYSTEM_DEFAULTS.copy()

    # Konzern-Ebene
    settings.update(group.default_settings)

    # Organisations-Ebene (überschreibt Konzern)
    settings.update(org.settings_override)

    # Mandanten-Ebene (überschreibt Organisation)
    settings.update(tenant.settings_override)

    return settings
```

### Modul-Verfügbarkeit pro Ebene

```sql
-- View: Welche Module sind für einen Mandanten verfügbar?
CREATE VIEW v_tenant_available_modules AS
SELECT
    t.id AS tenant_id,
    m.id AS module_id,
    m.name AS module_name,
    m.current_version,
    tmi.installed_version,
    tmi.status AS install_status,
    CASE
        WHEN m.id = ANY(
            SELECT jsonb_array_elements_text(o.allowed_modules)::uuid
            FROM organizations o WHERE o.id = t.organization_id
        ) THEN true
        ELSE false
    END AS allowed_by_org,
    CASE
        WHEN m.id = ANY(
            SELECT jsonb_array_elements_text(g.allowed_modules)::uuid
            FROM groups g
            JOIN organizations o ON o.group_id = g.id
            WHERE o.id = t.organization_id
        ) THEN true
        ELSE false
    END AS allowed_by_group
FROM tenants t
CROSS JOIN module_registry m
LEFT JOIN tenant_module_instances tmi
    ON tmi.tenant_id = t.id AND tmi.module_id = m.id;
```

---

## 2. Phase 1: Modul-Auswahl

### 2.1 Zwei Modi

| Modus | Beschreibung | Ergebnis |
|-------|--------------|----------|
| **Bestehendes Modul** | Feature für existierendes Modul → Neue Version | `version: 1.2.0 → 1.3.0` |
| **Neues Modul** | Komplett neues Modul erstellen | Neuer Eintrag im Flussdiagramm |

### 2.2 Flussdiagramm der Module

Das Flussdiagramm zeigt alle Module und ihre Beziehungen. Der User wählt:
- Bei **bestehendem Modul**: Das Modul im Diagramm anklicken
- Bei **neuem Modul**: Position im Workflow festlegen (vor/nach welchem Modul?)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         MODULE WORKFLOW DIAGRAM                                  │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│    ┌────────────┐      ┌────────────┐      ┌────────────┐      ┌────────────┐   │
│    │  Common    │─────>│ Validation │─────>│ Checklists │─────>│ Group      │   │
│    │  v2.1.0    │      │  v1.4.0    │      │  v3.2.0    │      │ Queries    │   │
│    └────────────┘      └────────────┘      └────────────┘      │  v1.1.0    │   │
│          │                                       │              └────────────┘   │
│          │                                       │                    │          │
│          ▼                                       ▼                    ▼          │
│    ┌────────────┐                         ┌────────────┐      ┌────────────┐    │
│    │ Vue-Adapter│                         │ Document   │─────>│ Reports    │    │
│    │  v2.0.0    │                         │ Box v1.5.0 │      │  v1.0.0    │    │
│    └────────────┘                         └────────────┘      └────────────┘    │
│                                                                                  │
│    ─────────────────────────────────────────────────────────────────────────    │
│    Legende:                                                                      │
│    ┌────────────┐  Modul mit Version                                            │
│    │  [Name]    │  ───> Abhängigkeit                                            │
│    │  v[x.y.z]  │  ● Ausgewähltes Modul                                         │
│    └────────────┘                                                                │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 2.3 Datenmodell: Module Registry

```sql
CREATE TABLE module_registry (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id),

    -- Identifikation
    name VARCHAR(100) NOT NULL,              -- z.B. "checklists"
    display_name VARCHAR(255) NOT NULL,      -- z.B. "Checklisten-Modul"
    package_name VARCHAR(255) NOT NULL,      -- z.B. "@flowaudit/checklists"

    -- Version
    current_version VARCHAR(20) NOT NULL,    -- z.B. "3.2.0"

    -- Workflow-Position
    workflow_position INTEGER NOT NULL,      -- Reihenfolge im Fluss
    workflow_group VARCHAR(50),              -- z.B. "core", "domain", "reporting"

    -- Abhängigkeiten (als JSON Array von module_ids)
    dependencies JSONB DEFAULT '[]',
    dependents JSONB DEFAULT '[]',           -- Module die von diesem abhängen

    -- Status
    status VARCHAR(20) DEFAULT 'active',     -- active, deprecated, development

    -- Metadaten
    description TEXT,
    icon VARCHAR(50),                        -- Icon für Flussdiagramm
    color VARCHAR(20),                       -- Farbe für Flussdiagramm

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(tenant_id, name)
);

-- Versions-Historie
CREATE TABLE module_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    module_id UUID REFERENCES module_registry(id) ON DELETE CASCADE,

    version VARCHAR(20) NOT NULL,
    release_notes TEXT,
    changelog JSONB DEFAULT '[]',

    -- Entwicklungs-Referenz
    development_session_id UUID,             -- Verweis auf die Development-Session

    released_at TIMESTAMP,
    released_by VARCHAR(100),

    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## 3. Phase 2: Dateien hochladen mit Erläuterungen

### 3.1 Workflow

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         DATEI-UPLOAD MIT ERLÄUTERUNGEN                           │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │ Hochgeladene Dateien                                                     │    │
│  ├─────────────────────────────────────────────────────────────────────────┤    │
│  │                                                                          │    │
│  │  📄 anforderungen.xlsx                                          [✓]     │    │
│  │  ┌─────────────────────────────────────────────────────────────────┐    │    │
│  │  │ Erläuterung: Diese Excel enthält alle fachlichen Anforderungen │    │    │
│  │  │ für die neue Prüfungslogik. Spalte A = ID, Spalte B = Text...  │    │    │
│  │  └─────────────────────────────────────────────────────────────────┘    │    │
│  │                                                                          │    │
│  │  📄 current_implementation.py                                    [✓]     │    │
│  │  ┌─────────────────────────────────────────────────────────────────┐    │    │
│  │  │ Erläuterung: Aktuelle Implementierung des ChecklistAnalyzer.   │    │    │
│  │  │ Muss erweitert werden um die neuen Prüfregeln zu unterstützen. │    │    │
│  │  └─────────────────────────────────────────────────────────────────┘    │    │
│  │                                                                          │    │
│  │  📄 api_spec.yaml                                                [✓]     │    │
│  │  ┌─────────────────────────────────────────────────────────────────┐    │    │
│  │  │ Erläuterung: OpenAPI-Spec der externen API die angebunden      │    │    │
│  │  │ werden soll. Wichtig: Authentifizierung per Bearer Token.      │    │    │
│  │  └─────────────────────────────────────────────────────────────────┘    │    │
│  │                                                                          │    │
│  │  [+ Weitere Datei hochladen]                                            │    │
│  │                                                                          │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│                                                                                  │
│  [Weiter: Aufgabe beschreiben →]                                                │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Datenmodell: Dateien mit Erläuterungen

```sql
CREATE TABLE development_files (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES development_sessions(id) ON DELETE CASCADE,

    -- Datei-Info
    original_filename VARCHAR(500) NOT NULL,
    storage_path VARCHAR(1000) NOT NULL,
    mime_type VARCHAR(100),
    file_size_bytes BIGINT,
    checksum_sha256 VARCHAR(64),

    -- Erläuterung durch User
    user_annotation TEXT NOT NULL,           -- Pflichtfeld!
    annotation_language VARCHAR(10) DEFAULT 'de',

    -- Verarbeitung
    processing_status VARCHAR(20) DEFAULT 'pending',  -- pending, processing, completed, failed
    parsed_content TEXT,                     -- Extrahierter Text-Inhalt
    parsed_metadata JSONB DEFAULT '{}',      -- Zusätzliche Metadaten (Spalten, Struktur, etc.)

    -- Embedding für RAG
    embedding_status VARCHAR(20) DEFAULT 'pending',
    chunk_count INTEGER DEFAULT 0,

    uploaded_by VARCHAR(100),
    uploaded_at TIMESTAMP DEFAULT NOW()
);

-- Datei-Chunks für RAG
CREATE TABLE development_file_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    file_id UUID REFERENCES development_files(id) ON DELETE CASCADE,

    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    token_count INTEGER,

    -- Optional: Embedding Vector (wenn pgvector installiert)
    -- embedding vector(1536),

    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## 4. Phase 3: Aufgabe beschreiben

### 4.1 Aufgaben-Template

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         AUFGABE BESCHREIBEN                                      │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  Modul: @flowaudit/checklists (v3.2.0 → v3.3.0)                                 │
│  Position im Workflow: Nach "Validation", vor "Document Box"                    │
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │ Aufgabenbeschreibung                                                     │    │
│  ├─────────────────────────────────────────────────────────────────────────┤    │
│  │                                                                          │    │
│  │ Ich möchte eine neue Prüfungslogik implementieren, die:                 │    │
│  │                                                                          │    │
│  │ 1. Die Anforderungen aus anforderungen.xlsx automatisch einliest        │    │
│  │ 2. Für jede Anforderung eine Prüfregel erstellt                         │    │
│  │ 3. Die Prüfregeln gegen hochgeladene Dokumente validiert                │    │
│  │ 4. Einen Bericht mit Findings erstellt                                  │    │
│  │                                                                          │    │
│  │ Wichtig:                                                                 │    │
│  │ - Muss kompatibel sein mit der bestehenden ChecklistAnalyzer API        │    │
│  │ - Soll die externe API (siehe api_spec.yaml) für zusätzliche Daten      │    │
│  │   nutzen können                                                          │    │
│  │ - Performance: Max. 2 Sekunden pro Dokument                             │    │
│  │                                                                          │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│                                                                                  │
│  Kategorie: [Feature ▾]    Priorität: [Hoch ▾]                                  │
│                                                                                  │
│  [LLM-Analyse starten →]                                                        │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 4.2 Datenmodell: Development Session

```sql
CREATE TABLE development_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id),

    -- Modul-Referenz
    module_id UUID REFERENCES module_registry(id),
    is_new_module BOOLEAN DEFAULT FALSE,
    new_module_name VARCHAR(100),            -- Falls neues Modul

    -- Version
    base_version VARCHAR(20),                -- Ausgangs-Version (z.B. "3.2.0")
    target_version VARCHAR(20),              -- Ziel-Version (z.B. "3.3.0")

    -- Aufgabe
    task_title VARCHAR(500) NOT NULL,
    task_description TEXT NOT NULL,
    task_category VARCHAR(50),               -- feature, bugfix, refactoring, enhancement
    task_priority VARCHAR(20),               -- low, medium, high, critical

    -- Status
    status VARCHAR(30) DEFAULT 'draft',      -- draft, analyzing, feedback_loop, approved, developing, testing, completed
    current_iteration INTEGER DEFAULT 0,

    -- Timing
    started_at TIMESTAMP DEFAULT NOW(),
    approved_at TIMESTAMP,
    completed_at TIMESTAMP,

    -- User
    created_by VARCHAR(100),
    approved_by VARCHAR(100),

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Index für schnelle Suche
CREATE INDEX idx_dev_sessions_module ON development_sessions(module_id);
CREATE INDEX idx_dev_sessions_status ON development_sessions(status);
```

---

## 5. Phase 4: Iterativer Feedback-Loop

### 5.1 Der Kern des Systems

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         ITERATIVER FEEDBACK-LOOP                                 │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  Iteration #3                                                    [History ▾]    │
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │ LLM-VORSCHLAG                                                           │    │
│  ├─────────────────────────────────────────────────────────────────────────┤    │
│  │                                                                          │    │
│  │ ## Implementierungsplan v3                                              │    │
│  │                                                                          │    │
│  │ ### 1. Neue Komponenten                                                 │    │
│  │                                                                          │    │
│  │ **RequirementParser** (services/requirement_parser.py)                  │    │
│  │ - Liest XLSX mit openpyxl                                               │    │
│  │ - Validiert Spaltenstruktur (ID, Text, Kategorie)                       │    │
│  │ - Gibt List[Requirement] zurück                                         │    │
│  │                                                                          │    │
│  │ **RuleGenerator** (services/rule_generator.py)                          │    │
│  │ - Transformiert Requirement → PrüfRegel                                 │    │
│  │ - Nutzt LLM für komplexe Regel-Interpretation                          │    │
│  │ - Cacht generierte Regeln                                               │    │
│  │                                                                          │    │
│  │ **ExternalAPIClient** (clients/external_api.py)                         │    │
│  │ - Implementiert api_spec.yaml                                           │    │
│  │ - Bearer Token Auth                                                     │    │
│  │ - Rate Limiting (100 req/min)                                           │    │
│  │                                                                          │    │
│  │ ### 2. API-Endpunkte                                                    │    │
│  │ - POST /api/v1/checklists/{id}/import-requirements                     │    │
│  │ - POST /api/v1/checklists/{id}/validate-document                       │    │
│  │ - GET /api/v1/checklists/{id}/findings                                 │    │
│  │                                                                          │    │
│  │ ### 3. Datenbank-Änderungen                                             │    │
│  │ - Neue Tabelle: checklist_requirements                                  │    │
│  │ - Neue Tabelle: checklist_rules                                         │    │
│  │ - Neue Tabelle: validation_findings                                     │    │
│  │                                                                          │    │
│  │ [Vollständigen Plan anzeigen...]                                        │    │
│  │                                                                          │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │ IHR FEEDBACK                                                            │    │
│  ├─────────────────────────────────────────────────────────────────────────┤    │
│  │                                                                          │    │
│  │ Der Plan sieht gut aus! Aber:                                           │    │
│  │                                                                          │    │
│  │ 1. Der ExternalAPIClient sollte async sein für bessere Performance      │    │
│  │ 2. Bitte auch Fehlerbehandlung für ungültige XLSX-Dateien einplanen     │    │
│  │ 3. Die Findings sollten einen Schweregrad haben (info, warning, error)  │    │
│  │                                                                          │    │
│  │ Ansonsten kann ich so freigeben.                                        │    │
│  │                                                                          │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│                                                                                  │
│  [← Vorherige Iteration]  [Feedback senden]  [✓ Freigeben →]                   │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 5.2 Datenmodell: Iterationen

```sql
-- Vorschlags-Iterationen
CREATE TABLE development_iterations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES development_sessions(id) ON DELETE CASCADE,

    iteration_number INTEGER NOT NULL,

    -- LLM-Vorschlag
    proposal_type VARCHAR(50) NOT NULL,      -- analysis, implementation_plan, code_review
    proposal_content TEXT NOT NULL,          -- Markdown-formatierter Vorschlag
    proposal_structured JSONB DEFAULT '{}',  -- Strukturierte Daten (Komponenten, APIs, etc.)

    -- LLM-Metadaten
    llm_provider VARCHAR(50),
    llm_model VARCHAR(100),
    llm_tokens_used INTEGER DEFAULT 0,
    llm_latency_ms INTEGER,
    llm_prompt TEXT,                         -- Der verwendete Prompt (für Debugging)

    -- User-Feedback
    feedback_content TEXT,                   -- Freitext-Feedback
    feedback_rating INTEGER,                 -- 1-5 Sterne (optional)
    feedback_tags JSONB DEFAULT '[]',        -- ["zu_komplex", "fehler", "unvollständig"]
    feedback_at TIMESTAMP,
    feedback_by VARCHAR(100),

    -- Status
    status VARCHAR(20) DEFAULT 'pending',    -- pending, feedback_received, revised, approved

    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_iterations_session ON development_iterations(session_id, iteration_number);
```

### 5.3 Feedback-Tags (vordefiniert)

| Tag | Beschreibung | Auswirkung auf nächste Iteration |
|-----|--------------|-----------------------------------|
| `zu_komplex` | Lösung ist zu kompliziert | LLM soll vereinfachen |
| `zu_einfach` | Lösung deckt nicht alle Fälle ab | LLM soll Details hinzufügen |
| `fehler` | Technischer Fehler im Vorschlag | LLM soll korrigieren |
| `unvollständig` | Aspekte fehlen | LLM soll ergänzen |
| `performance` | Performance-Bedenken | LLM soll optimieren |
| `sicherheit` | Sicherheitsbedenken | LLM soll absichern |
| `inkompatibel` | Passt nicht zur Architektur | LLM soll anpassen |

---

## 6. Memory-System (LLM-Kontext)

### 6.1 Kernprinzip

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              MEMORY = KONTEXT                                    │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│   Jede LLM-Anfrage bekommt automatisch relevanten Kontext:                      │
│                                                                                  │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │ KONTEXT-AUFBAU                                                           │   │
│   ├─────────────────────────────────────────────────────────────────────────┤   │
│   │                                                                          │   │
│   │  1. MODUL-ARCHITEKTUR                                                   │   │
│   │     ├─ Aktuelle Struktur (Komponenten, APIs)                            │   │
│   │     ├─ Tech-Stack (FastAPI, Vue3, PostgreSQL)                           │   │
│   │     └─ Abhängigkeiten zu anderen Modulen                                │   │
│   │                                                                          │   │
│   │  2. HOCHGELADENE DATEIEN + ERLÄUTERUNGEN                                │   │
│   │     ├─ Datei-Inhalt (oder Zusammenfassung bei großen Dateien)           │   │
│   │     └─ User-Erläuterung pro Datei                                       │   │
│   │                                                                          │   │
│   │  3. VORHERIGE ITERATIONEN DIESER SESSION                                │   │
│   │     ├─ Alle bisherigen Vorschläge                                       │   │
│   │     └─ Alle Feedback-Kommentare (KRITISCH!)                             │   │
│   │                                                                          │   │
│   │  4. FRÜHERE KORREKTUREN (aus anderen Sessions)                          │   │
│   │     └─ "Bei ähnlichen Anfragen wurde X korrigiert zu Y"                 │   │
│   │                                                                          │   │
│   │  5. MODUL-HISTORY                                                       │   │
│   │     └─ Letzte Änderungen am Modul                                       │   │
│   │                                                                          │   │
│   └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 6.2 Datenmodell: Memory

```sql
-- Modul-Architektur (persistentes Wissen über Module)
CREATE TABLE module_architecture (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    module_id UUID REFERENCES module_registry(id) UNIQUE,

    -- Struktur
    description TEXT,
    directory_structure JSONB DEFAULT '{}',
    tech_stack JSONB DEFAULT '{}',           -- {backend: ["FastAPI"], frontend: ["Vue3"]}
    patterns JSONB DEFAULT '[]',             -- ["Service Layer", "Repository"]

    -- Komponenten
    components JSONB DEFAULT '[]',           -- [{name, type, file_path, description}]

    -- Schnittstellen
    api_endpoints JSONB DEFAULT '[]',        -- [{method, path, description}]
    events JSONB DEFAULT '[]',               -- Emittierte Events

    version VARCHAR(20),
    updated_at TIMESTAMP DEFAULT NOW(),
    updated_by VARCHAR(100)
);

-- Feedback-Memory (lernt aus Korrekturen)
CREATE TABLE feedback_memory (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id),
    module_id UUID REFERENCES module_registry(id),

    -- Original
    original_context TEXT,                   -- Worauf bezog sich das Feedback?
    original_response TEXT,                  -- Was war die ursprüngliche LLM-Antwort?

    -- Korrektur
    correction TEXT NOT NULL,                -- Was war falsch / was ist richtig?
    correction_type VARCHAR(50),             -- factual, architectural, performance, security

    -- Für semantische Suche
    context_embedding_key VARCHAR(255),      -- Für schnelle Suche

    -- Relevanz
    times_applied INTEGER DEFAULT 0,         -- Wie oft wurde diese Korrektur angewendet?
    last_applied_at TIMESTAMP,

    created_at TIMESTAMP DEFAULT NOW(),
    created_by VARCHAR(100)
);

CREATE INDEX idx_feedback_memory_module ON feedback_memory(module_id);

-- Session-Memory (Zusammenfassungen abgeschlossener Sessions)
CREATE TABLE session_memory (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES development_sessions(id) UNIQUE,
    module_id UUID REFERENCES module_registry(id),

    -- Zusammenfassung
    summary TEXT NOT NULL,                   -- LLM-generierte Zusammenfassung
    key_decisions JSONB DEFAULT '[]',        -- Wichtigste Entscheidungen
    lessons_learned JSONB DEFAULT '[]',      -- Was wurde gelernt?

    -- Für zukünftige Sessions
    reusable_patterns JSONB DEFAULT '[]',    -- Wiederverwendbare Muster
    warnings JSONB DEFAULT '[]',             -- Warnungen für zukünftige Entwicklung

    created_at TIMESTAMP DEFAULT NOW()
);
```

### 6.3 Kontext-Service Implementation

```python
# services/context_service.py

class DevelopmentContextService:
    """
    Baut den vollständigen Kontext für LLM-Anfragen auf.
    Nutzt das Memory-System für relevante historische Daten.
    """

    async def build_context(
        self,
        session_id: str,
        iteration_number: int,
        current_question: str | None = None
    ) -> str:
        """
        Baut vollständigen Kontext für die nächste LLM-Anfrage auf.
        """
        context_parts = []

        # 1. Session-Daten laden
        session = await self._get_session(session_id)
        module = await self._get_module(session.module_id)

        # 2. Modul-Architektur
        architecture = await self._get_architecture(session.module_id)
        if architecture:
            context_parts.append(self._format_architecture(architecture))

        # 3. Hochgeladene Dateien mit Erläuterungen
        files = await self._get_session_files(session_id)
        if files:
            context_parts.append(self._format_files(files))

        # 4. Aufgabenbeschreibung
        context_parts.append(f"""
## Aufgabe
{session.task_description}

Kategorie: {session.task_category}
Ziel-Version: {session.base_version} → {session.target_version}
""")

        # 5. Bisherige Iterationen dieser Session
        iterations = await self._get_iterations(session_id, limit=iteration_number)
        if iterations:
            context_parts.append(self._format_iterations(iterations))

        # 6. Relevante Korrekturen aus dem Memory
        if current_question:
            corrections = await self._get_relevant_corrections(
                module_id=session.module_id,
                query=current_question,
                limit=5
            )
            if corrections:
                context_parts.append(self._format_corrections(corrections))

        # 7. Letzte Modul-Änderungen
        recent_changes = await self._get_module_history(session.module_id, limit=5)
        if recent_changes:
            context_parts.append(self._format_history(recent_changes))

        return "\n\n---\n\n".join(context_parts)

    def _format_corrections(self, corrections: list) -> str:
        """Formatiert frühere Korrekturen als Warnung."""
        text = "## ⚠️ Frühere Korrekturen (UNBEDINGT BEACHTEN!)\n\n"
        for c in corrections:
            text += f"- **Kontext:** {c.original_context[:100]}...\n"
            text += f"  **Korrektur:** {c.correction}\n\n"
        return text

    def _format_iterations(self, iterations: list) -> str:
        """Formatiert bisherige Iterationen."""
        text = "## Bisherige Iterationen\n\n"
        for it in iterations:
            text += f"### Iteration {it.iteration_number}\n"
            text += f"**Vorschlag:** {it.proposal_content[:500]}...\n"
            if it.feedback_content:
                text += f"**Feedback:** {it.feedback_content}\n"
            text += "\n"
        return text
```

---

## 7. Phase 5: Freigabe

### 7.1 Freigabe-Workflow

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              FREIGABE                                            │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  Session: Neue Prüfungslogik für @flowaudit/checklists                          │
│  Status: Iteration #4 - Bereit zur Freigabe                                     │
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │ FINALER PLAN                                                             │    │
│  ├─────────────────────────────────────────────────────────────────────────┤    │
│  │                                                                          │    │
│  │ ✓ 3 neue Services (RequirementParser, RuleGenerator, ExternalAPIClient) │    │
│  │ ✓ 3 neue API-Endpunkte                                                  │    │
│  │ ✓ 3 neue Datenbank-Tabellen                                             │    │
│  │ ✓ Async-Implementierung für Performance                                 │    │
│  │ ✓ Fehlerbehandlung für XLSX                                             │    │
│  │ ✓ Schweregrade für Findings (info, warning, error)                      │    │
│  │                                                                          │    │
│  │ [Vollständigen Plan anzeigen]                                           │    │
│  │                                                                          │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │ CHECKLISTE VOR FREIGABE                                                  │    │
│  ├─────────────────────────────────────────────────────────────────────────┤    │
│  │                                                                          │    │
│  │ [✓] Ich habe den Implementierungsplan vollständig geprüft              │    │
│  │ [✓] Die Architektur passt zum bestehenden System                        │    │
│  │ [✓] Performance-Anforderungen wurden berücksichtigt                     │    │
│  │ [✓] Sicherheitsaspekte wurden geprüft                                   │    │
│  │ [ ] Ich möchte vor der Entwicklung benachrichtigt werden                │    │
│  │                                                                          │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│                                                                                  │
│  [← Zurück zum Feedback]              [✓ Entwicklung freigeben]                │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 7.2 Datenmodell: Freigabe

```sql
-- Erweiterung der development_sessions Tabelle
ALTER TABLE development_sessions ADD COLUMN IF NOT EXISTS
    approval_checklist JSONB DEFAULT '{}';   -- {plan_reviewed: true, architecture_ok: true, ...}

ALTER TABLE development_sessions ADD COLUMN IF NOT EXISTS
    final_plan_id UUID REFERENCES development_iterations(id);  -- Verweis auf finale Iteration
```

---

## 8. Phase 6: Entwicklung + Testing (parallel)

### 8.1 Parallele Ausführung

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         ENTWICKLUNG + TESTING                                    │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  Session: Neue Prüfungslogik                     Status: In Entwicklung (67%)  │
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │ ENTWICKLUNG                                          TESTING             │    │
│  ├────────────────────────────────────┬────────────────────────────────────┤    │
│  │                                    │                                     │    │
│  │ ✓ RequirementParser               │ ✓ test_requirement_parser.py       │    │
│  │   └─ services/requirement_parser.py│   └─ 12/12 Tests bestanden        │    │
│  │                                    │                                     │    │
│  │ ✓ RuleGenerator                   │ ✓ test_rule_generator.py           │    │
│  │   └─ services/rule_generator.py   │   └─ 8/8 Tests bestanden           │    │
│  │                                    │                                     │    │
│  │ ◐ ExternalAPIClient               │ ◌ test_external_api.py             │    │
│  │   └─ clients/external_api.py      │   └─ Wartet auf Implementation     │    │
│  │                                    │                                     │    │
│  │ ◌ API-Endpunkte                   │ ◌ test_api_endpoints.py            │    │
│  │   └─ api/checklists_v2.py         │   └─ Wartet auf Implementation     │    │
│  │                                    │                                     │    │
│  │ ◌ Datenbank-Migration             │ ◌ Migration-Test                    │    │
│  │   └─ migrations/007_*.py          │   └─ Wartet auf Migration          │    │
│  │                                    │                                     │    │
│  └────────────────────────────────────┴────────────────────────────────────┘    │
│                                                                                  │
│  Logs: [Development] [Testing] [Errors]                                         │
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │ > Generating ExternalAPIClient with async httpx...                       │    │
│  │ > Adding rate limiting decorator...                                      │    │
│  │ > Implementing Bearer token authentication...                            │    │
│  │ > _                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│                                                                                  │
│  [Pause]  [Abbrechen]  [Details anzeigen]                                       │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 8.2 Datenmodell: Entwicklungs-Tasks

```sql
CREATE TABLE development_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES development_sessions(id) ON DELETE CASCADE,

    -- Task-Definition
    task_name VARCHAR(255) NOT NULL,
    task_type VARCHAR(50) NOT NULL,          -- implementation, test, migration, documentation
    task_order INTEGER NOT NULL,             -- Reihenfolge

    -- Abhängigkeiten
    depends_on JSONB DEFAULT '[]',           -- Array von task_ids

    -- Ziel-Dateien
    target_files JSONB DEFAULT '[]',         -- [{path, action: "create"|"modify"}]

    -- Status
    status VARCHAR(20) DEFAULT 'pending',    -- pending, in_progress, completed, failed, skipped
    progress INTEGER DEFAULT 0,              -- 0-100

    -- Ergebnis
    output_files JSONB DEFAULT '[]',         -- Generierte Dateien
    output_log TEXT,
    error_message TEXT,

    -- Timing
    started_at TIMESTAMP,
    completed_at TIMESTAMP,

    -- LLM-Nutzung
    llm_tokens_used INTEGER DEFAULT 0,

    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_dev_tasks_session ON development_tasks(session_id, task_order);

-- Test-Ergebnisse
CREATE TABLE development_test_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id UUID REFERENCES development_tasks(id) ON DELETE CASCADE,

    test_file VARCHAR(500),
    test_name VARCHAR(255),

    status VARCHAR(20),                      -- passed, failed, skipped, error
    duration_ms INTEGER,
    error_message TEXT,
    stack_trace TEXT,

    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## 9. API-Endpunkte

### 9.1 Development Session API

```
# Module Registry
GET  /api/v1/modules                         → Liste aller Module
GET  /api/v1/modules/{id}                    → Modul-Details
GET  /api/v1/modules/{id}/architecture       → Modul-Architektur
GET  /api/v1/modules/workflow-diagram        → Flussdiagramm-Daten

# Development Sessions
POST /api/v1/development/sessions            → Neue Session starten
GET  /api/v1/development/sessions            → Alle Sessions
GET  /api/v1/development/sessions/{id}       → Session-Details
PUT  /api/v1/development/sessions/{id}       → Session aktualisieren

# Dateien
POST /api/v1/development/sessions/{id}/files → Datei hochladen
GET  /api/v1/development/sessions/{id}/files → Alle Dateien
PUT  /api/v1/development/sessions/{id}/files/{file_id} → Erläuterung ändern

# Iterationen / Feedback-Loop
POST /api/v1/development/sessions/{id}/analyze        → LLM-Analyse starten
GET  /api/v1/development/sessions/{id}/iterations     → Alle Iterationen
POST /api/v1/development/sessions/{id}/iterations/{n}/feedback → Feedback geben

# Freigabe
POST /api/v1/development/sessions/{id}/approve        → Entwicklung freigeben

# Entwicklung
POST /api/v1/development/sessions/{id}/start-development → Entwicklung starten
GET  /api/v1/development/sessions/{id}/tasks          → Task-Status
GET  /api/v1/development/sessions/{id}/tasks/{task_id}/logs → Task-Logs

# Memory
GET  /api/v1/development/memory/corrections           → Gespeicherte Korrekturen
GET  /api/v1/development/memory/sessions/{module_id}  → Session-Zusammenfassungen
```

---

## 10. Zusammenfassung

### 10.1 Der komplette Workflow

```
1. MODUL AUSWÄHLEN
   ├─ Bestehendes Modul → Version erhöhen
   └─ Neues Modul → Im Flussdiagramm positionieren

2. DATEIEN HOCHLADEN
   └─ Pro Datei: Erläuterung eingeben (Pflicht)

3. AUFGABE BESCHREIBEN
   └─ Was soll entwickelt werden?

4. ITERATIVER FEEDBACK-LOOP
   ┌─────────────────────────────────┐
   │ LLM analysiert + macht Vorschlag│
   │              ↓                  │
   │ User gibt Feedback              │
   │              ↓                  │
   │ LLM überarbeitet                │
   │              ↓                  │
   │ Wiederholen bis zufrieden       │
   └─────────────────────────────────┘

5. FREIGABE
   └─ User gibt Entwicklung frei

6. ENTWICKLUNG + TESTING
   └─ Parallel: Code generieren + Tests ausführen

7. ABSCHLUSS
   ├─ Memory aktualisieren (Learnings speichern)
   └─ Neue Modul-Version registrieren
```

### 10.2 Memory-Formel

```
MEMORY = Architektur + Dateien + Iterationen + Korrekturen + History

Bei jeder LLM-Anfrage:
- Architektur des Moduls laden
- Hochgeladene Dateien + Erläuterungen einbinden
- Bisherige Iterationen dieser Session
- Relevante Korrekturen aus früheren Sessions
- Letzte Änderungen am Modul
```

### 10.3 Implementierungs-Prioritäten

| Phase | Komponente | Aufwand | Wert |
|-------|------------|---------|------|
| **1** | Module Registry + Workflow-Diagram | 3 Tage | Hoch |
| **1** | Development Session + Datei-Upload | 3 Tage | Kritisch |
| **2** | Iterativer Feedback-Loop | 4 Tage | Kritisch |
| **2** | Context-Service (Memory) | 3 Tage | Kritisch |
| **3** | Freigabe-Workflow | 2 Tage | Mittel |
| **3** | Development + Testing Pipeline | 5 Tage | Hoch |
| **4** | Memory-Persistenz + Learnings | 3 Tage | Hoch |

---

## 11. Multi-LLM-Strategie (GLM + Anthropic)

### 11.1 Warum zwei LLMs?

| LLM | Stärken | Einsatz im Development-Modul |
|-----|---------|------------------------------|
| **GLM-4** | Schnell, günstig, gute Code-Analyse | Erste Analyse, Strukturierung, Validierung |
| **Anthropic Claude** | Präzise, kreativ, tiefes Verständnis | Detaillierte Vorschläge, Code-Generierung, Feedback-Verarbeitung |

### 11.2 Kombinationsmuster

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         MULTI-LLM WORKFLOW                                       │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  ┌────────────────────────────────────────────────────────────────────────────┐ │
│  │ MUSTER 1: PIPELINE (Sequentiell)                                           │ │
│  ├────────────────────────────────────────────────────────────────────────────┤ │
│  │                                                                             │ │
│  │  Dateien + Aufgabe                                                         │ │
│  │         │                                                                   │ │
│  │         ▼                                                                   │ │
│  │  ┌──────────────┐     ┌──────────────────────────────────┐                 │ │
│  │  │   GLM-4      │────>│        ANTHROPIC CLAUDE          │                 │ │
│  │  │              │     │                                  │                 │ │
│  │  │ • Dateien    │     │ • Nimmt GLM-Analyse als Input    │                 │ │
│  │  │   parsen     │     │ • Erstellt detaillierten Plan    │                 │ │
│  │  │ • Struktur   │     │ • Generiert Code                 │                 │ │
│  │  │   erkennen   │     │ • Verarbeitet Feedback           │                 │ │
│  │  │ • Zusammen-  │     │                                  │                 │ │
│  │  │   fassung    │     │                                  │                 │ │
│  │  └──────────────┘     └──────────────────────────────────┘                 │ │
│  │       (schnell,              (präzise, kreativ)                            │ │
│  │        günstig)                                                            │ │
│  │                                                                             │ │
│  └────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                  │
│  ┌────────────────────────────────────────────────────────────────────────────┐ │
│  │ MUSTER 2: PARALLEL (Vergleich)                                             │ │
│  ├────────────────────────────────────────────────────────────────────────────┤ │
│  │                                                                             │ │
│  │              Aufgabe                                                        │ │
│  │                │                                                            │ │
│  │         ┌──────┴──────┐                                                     │ │
│  │         ▼             ▼                                                     │ │
│  │  ┌──────────────┐  ┌──────────────┐                                        │ │
│  │  │   GLM-4      │  │   ANTHROPIC  │                                        │ │
│  │  │   Vorschlag  │  │   Vorschlag  │                                        │ │
│  │  └──────────────┘  └──────────────┘                                        │ │
│  │         │                 │                                                 │ │
│  │         └────────┬────────┘                                                 │ │
│  │                  ▼                                                          │ │
│  │         ┌──────────────┐                                                   │ │
│  │         │  VERGLEICH   │  → User wählt besseren Vorschlag                  │ │
│  │         │  + MERGE     │  → Oder: Kombinierter Vorschlag                   │ │
│  │         └──────────────┘                                                   │ │
│  │                                                                             │ │
│  └────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                  │
│  ┌────────────────────────────────────────────────────────────────────────────┐ │
│  │ MUSTER 3: SPEZIALISIERT (Task-basiert)                                     │ │
│  ├────────────────────────────────────────────────────────────────────────────┤ │
│  │                                                                             │ │
│  │  Task                         LLM                                          │ │
│  │  ────                         ───                                          │ │
│  │  Datei-Analyse                GLM-4        (schnell, strukturiert)         │ │
│  │  Code-Validierung             GLM-4        (regelbasiert)                  │ │
│  │  Implementierungsplan         ANTHROPIC    (kreativ, detailliert)          │ │
│  │  Code-Generierung             ANTHROPIC    (präzise, best practices)       │ │
│  │  Feedback-Verarbeitung        ANTHROPIC    (Verständnis, Nuancen)          │ │
│  │  Test-Generierung             ANTHROPIC    (Edge Cases, Coverage)          │ │
│  │  Dokumentation                GLM-4        (strukturiert, schnell)         │ │
│  │                                                                             │ │
│  └────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 11.3 Implementierung: Multi-LLM Service

```python
# services/multi_llm_service.py

from enum import Enum
from typing import AsyncIterator

class LLMRole(str, Enum):
    """Rollen für verschiedene LLM-Tasks."""
    ANALYZER = "analyzer"           # Schnelle Analyse, Strukturierung
    PLANNER = "planner"             # Detaillierte Planung
    CODER = "coder"                 # Code-Generierung
    REVIEWER = "reviewer"           # Code-Review, Validierung
    FEEDBACK_PROCESSOR = "feedback" # Feedback verarbeiten

class LLMConfig:
    """Konfiguration welches LLM für welche Rolle."""

    DEFAULT_ROUTING = {
        LLMRole.ANALYZER: "glm-4",
        LLMRole.PLANNER: "claude-3-opus",
        LLMRole.CODER: "claude-3-opus",
        LLMRole.REVIEWER: "glm-4",
        LLMRole.FEEDBACK_PROCESSOR: "claude-3-opus",
    }


class MultiLLMService:
    """
    Orchestriert mehrere LLMs für verschiedene Aufgaben.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.glm_client = GLMClient()
        self.anthropic_client = AnthropicClient()
        self.routing = LLMConfig.DEFAULT_ROUTING.copy()

    async def execute_pipeline(
        self,
        session_id: str,
        files: list[DevelopmentFile],
        task_description: str,
        context: str,
    ) -> PipelineResult:
        """
        Führt die GLM → Anthropic Pipeline aus.

        1. GLM-4: Schnelle Voranalyse
        2. Anthropic: Detaillierter Vorschlag basierend auf GLM-Analyse
        """
        # Phase 1: GLM-4 Analyse
        glm_analysis = await self._analyze_with_glm(files, task_description)

        # Phase 2: Anthropic Vorschlag mit GLM-Kontext
        enriched_context = f"""
{context}

## Voranalyse (GLM-4)
{glm_analysis.summary}

### Erkannte Struktur
{glm_analysis.structure}

### Identifizierte Komponenten
{glm_analysis.components}

### Mögliche Herausforderungen
{glm_analysis.challenges}
"""

        anthropic_proposal = await self._create_proposal_with_anthropic(
            enriched_context,
            task_description
        )

        return PipelineResult(
            glm_analysis=glm_analysis,
            proposal=anthropic_proposal,
            total_tokens={
                "glm": glm_analysis.tokens_used,
                "anthropic": anthropic_proposal.tokens_used,
            }
        )

    async def execute_parallel(
        self,
        context: str,
        task_description: str,
    ) -> ParallelResult:
        """
        Führt beide LLMs parallel aus und vergleicht Ergebnisse.
        """
        # Parallel ausführen
        glm_task = asyncio.create_task(
            self._create_proposal_with_glm(context, task_description)
        )
        anthropic_task = asyncio.create_task(
            self._create_proposal_with_anthropic(context, task_description)
        )

        glm_result, anthropic_result = await asyncio.gather(
            glm_task, anthropic_task
        )

        # Ergebnisse vergleichen und Unterschiede hervorheben
        comparison = self._compare_proposals(glm_result, anthropic_result)

        return ParallelResult(
            glm_proposal=glm_result,
            anthropic_proposal=anthropic_result,
            comparison=comparison,
        )

    async def process_feedback(
        self,
        iteration: DevelopmentIteration,
        feedback: str,
    ) -> str:
        """
        Verarbeitet User-Feedback immer mit Anthropic.
        (Besseres Verständnis von Nuancen und Kritik)
        """
        return await self.anthropic_client.complete(
            messages=[
                {"role": "system", "content": FEEDBACK_SYSTEM_PROMPT},
                {"role": "user", "content": f"""
Vorheriger Vorschlag:
{iteration.proposal_content}

User-Feedback:
{feedback}

Bitte überarbeite den Vorschlag basierend auf dem Feedback.
"""}
            ],
            temperature=0.7,
        )

    async def _analyze_with_glm(
        self,
        files: list[DevelopmentFile],
        task: str,
    ) -> GLMAnalysis:
        """Schnelle Strukturanalyse mit GLM-4."""
        file_contents = "\n\n".join([
            f"### {f.original_filename}\n{f.parsed_content}\n\nErläuterung: {f.user_annotation}"
            for f in files
        ])

        response = await self.glm_client.complete(
            messages=[
                {"role": "system", "content": GLM_ANALYZER_PROMPT},
                {"role": "user", "content": f"""
Analysiere folgende Dateien für die Aufgabe: {task}

{file_contents}
"""}
            ],
            temperature=0.3,  # Niedriger für konsistente Analyse
        )

        return GLMAnalysis.parse(response)
```

### 11.4 Datenmodell: Multi-LLM Tracking

```sql
-- Erweiterung der development_iterations Tabelle
ALTER TABLE development_iterations ADD COLUMN IF NOT EXISTS
    llm_chain JSONB DEFAULT '[]';
    -- Speichert die Kette der LLM-Aufrufe:
    -- [
    --   {provider: "glm", model: "glm-4", role: "analyzer", tokens: 1200, latency_ms: 450},
    --   {provider: "anthropic", model: "claude-3-opus", role: "planner", tokens: 3500, latency_ms: 2100}
    -- ]

-- LLM-Routing-Konfiguration pro Tenant
CREATE TABLE llm_routing_config (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id),

    -- Routing-Regeln
    routing_mode VARCHAR(20) DEFAULT 'pipeline',  -- pipeline, parallel, specialized
    role_assignments JSONB DEFAULT '{}',
    -- {
    --   "analyzer": {"provider": "glm", "model": "glm-4"},
    --   "planner": {"provider": "anthropic", "model": "claude-3-opus"},
    --   "coder": {"provider": "anthropic", "model": "claude-3-opus"},
    --   ...
    -- }

    -- Fallback
    fallback_provider VARCHAR(50) DEFAULT 'anthropic',
    fallback_model VARCHAR(100) DEFAULT 'claude-3-sonnet',

    -- Kosten-Limits
    max_tokens_per_iteration INTEGER DEFAULT 50000,
    prefer_cheaper BOOLEAN DEFAULT FALSE,

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### 11.5 Kosten-Optimierung

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         KOSTEN-ÜBERSICHT                                         │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  Typische Session mit 5 Iterationen:                                            │
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │ OHNE Multi-LLM (nur Anthropic)                                          │    │
│  ├─────────────────────────────────────────────────────────────────────────┤    │
│  │ 5 × Analyse + Vorschlag: ~25.000 Tokens × $15/1M = $0.375               │    │
│  │ 5 × Feedback-Verarbeitung: ~15.000 Tokens × $15/1M = $0.225             │    │
│  │ Code-Generierung: ~30.000 Tokens × $15/1M = $0.450                      │    │
│  │ ─────────────────────────────────────────────────────────────           │    │
│  │ GESAMT: ~$1.05 pro Session                                              │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │ MIT Multi-LLM (GLM + Anthropic)                                         │    │
│  ├─────────────────────────────────────────────────────────────────────────┤    │
│  │ 5 × GLM-4 Voranalyse: ~10.000 Tokens × $1/1M = $0.01                    │    │
│  │ 5 × Anthropic Vorschlag: ~15.000 Tokens × $15/1M = $0.225               │    │
│  │ 5 × Anthropic Feedback: ~15.000 Tokens × $15/1M = $0.225                │    │
│  │ Code-Generierung: ~30.000 Tokens × $15/1M = $0.450                      │    │
│  │ ─────────────────────────────────────────────────────────────           │    │
│  │ GESAMT: ~$0.91 pro Session (-13%)                                       │    │
│  │                                                                          │    │
│  │ + Bonus: GLM-Analyse ist 3x schneller → Bessere UX                      │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 11.6 UI: LLM-Auswahl und Transparenz

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         LLM-STATUS                                               │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  Iteration #3                                                                   │
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │ LLM-Kette                                                               │    │
│  ├─────────────────────────────────────────────────────────────────────────┤    │
│  │                                                                          │    │
│  │  1. ✓ GLM-4 (Voranalyse)         1.200 Tokens    0.45s    $0.001        │    │
│  │     └─ Struktur erkannt, 3 Komponenten identifiziert                    │    │
│  │                                                                          │    │
│  │  2. ✓ Claude Opus (Vorschlag)    3.500 Tokens    2.1s     $0.053        │    │
│  │     └─ Detaillierter Implementierungsplan erstellt                      │    │
│  │                                                                          │    │
│  │  Gesamt: 4.700 Tokens | 2.55s | $0.054                                  │    │
│  │                                                                          │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│                                                                                  │
│  [LLM-Einstellungen ändern]                                                     │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 12. Git-Integration (Versionskontrolle)

### 12.1 Das Problem: Code-Injection-Lücke

Ohne Git-Integration entstehen kritische Risiken:

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         OHNE GIT-INTEGRATION (GEFÄHRLICH!)                       │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  LLM generiert Code                                                             │
│        │                                                                         │
│        ▼                                                                         │
│  ┌──────────────────┐      ┌────────────────────────────────────────────┐       │
│  │ output_files     │─────>│ DATEISYSTEM                                │       │
│  │ (DB JSONB Blob)  │      │                                            │       │
│  └──────────────────┘      │ ⚠️ Überschreibt existierende Dateien!     │       │
│                            │ ⚠️ Keine Merge-Conflicts erkannt!          │       │
│                            │ ⚠️ Manuelle Arbeit geht verloren!          │       │
│                            │ ⚠️ Kein Rollback möglich!                  │       │
│                            └────────────────────────────────────────────┘       │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 12.2 Die Lösung: Session = Git-Branch

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         MIT GIT-INTEGRATION (SICHER!)                            │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  1. SESSION START                                                               │
│     │                                                                            │
│     ├─ git fetch origin main                                                    │
│     ├─ git checkout -b feature/dev-session-{session_id}                         │
│     └─ Session mit Branch verknüpfen                                           │
│                                                                                  │
│  2. ITERATIVER FEEDBACK-LOOP                                                    │
│     │                                                                            │
│     └─ Vorschläge werden NICHT ins Dateisystem geschrieben                      │
│        (bleiben in der Datenbank als Entwurf)                                   │
│                                                                                  │
│  3. FREIGABE                                                                    │
│     │                                                                            │
│     ├─ git pull origin main (aktuelle Änderungen holen)                         │
│     ├─ LLM generiert Code MIT Wissen über aktuelle Dateien                      │
│     ├─ Code wird in Branch geschrieben                                          │
│     ├─ git add . && git commit -m "feat(module): Beschreibung"                  │
│     └─ git push origin feature/dev-session-{session_id}                         │
│                                                                                  │
│  4. REVIEW                                                                      │
│     │                                                                            │
│     ├─ Pull Request erstellen                                                   │
│     ├─ Diff anzeigen (was wurde geändert?)                                      │
│     ├─ Conflict-Detection                                                       │
│     └─ Merge oder Reject                                                        │
│                                                                                  │
│  5. ROLLBACK (falls nötig)                                                      │
│     │                                                                            │
│     └─ git revert oder Branch löschen                                          │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 12.3 Datenmodell: Git-Verknüpfung

```sql
-- Erweiterung der development_sessions Tabelle
ALTER TABLE development_sessions ADD COLUMN IF NOT EXISTS
    git_branch VARCHAR(255);                 -- z.B. "feature/dev-session-abc123"

ALTER TABLE development_sessions ADD COLUMN IF NOT EXISTS
    git_base_commit VARCHAR(64);             -- Commit von dem gestartet wurde

ALTER TABLE development_sessions ADD COLUMN IF NOT EXISTS
    git_head_commit VARCHAR(64);             -- Aktueller HEAD nach Commits

ALTER TABLE development_sessions ADD COLUMN IF NOT EXISTS
    git_pr_url VARCHAR(500);                 -- URL zum Pull Request

ALTER TABLE development_sessions ADD COLUMN IF NOT EXISTS
    git_pr_status VARCHAR(20);               -- open, merged, closed

-- Git-Commit-Log pro Session
CREATE TABLE session_git_commits (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES development_sessions(id) ON DELETE CASCADE,

    commit_sha VARCHAR(64) NOT NULL,
    commit_message TEXT NOT NULL,
    files_changed JSONB DEFAULT '[]',        -- [{path, action: add|modify|delete}]

    committed_at TIMESTAMP DEFAULT NOW(),
    committed_by VARCHAR(100)
);

CREATE INDEX idx_session_commits ON session_git_commits(session_id);
```

### 12.4 Git-Service Implementation

```python
# services/git_integration_service.py

class GitIntegrationService:
    """
    Verwaltet Git-Operationen für Development Sessions.
    KRITISCH: Schützt vor Race Conditions und Datenverlust.
    """

    def __init__(self, repo_path: str):
        self.repo_path = repo_path
        self.repo = git.Repo(repo_path)

    async def start_session_branch(
        self,
        session_id: str,
        base_branch: str = "main"
    ) -> str:
        """
        Erstellt einen neuen Branch für die Development Session.
        """
        branch_name = f"feature/dev-session-{session_id[:12]}"

        # Aktuellen Stand holen
        self.repo.remotes.origin.fetch()

        # Von base_branch abzweigen
        base = self.repo.refs[f"origin/{base_branch}"]
        new_branch = self.repo.create_head(branch_name, base.commit)
        new_branch.checkout()

        return branch_name

    async def read_current_file_state(
        self,
        file_paths: list[str]
    ) -> dict[str, str]:
        """
        Liest den aktuellen Zustand von Dateien aus dem Repo.
        WICHTIG: LLM bekommt diesen Kontext um Konflikte zu vermeiden.
        """
        current_state = {}
        for path in file_paths:
            full_path = os.path.join(self.repo_path, path)
            if os.path.exists(full_path):
                with open(full_path, 'r') as f:
                    current_state[path] = f.read()
            else:
                current_state[path] = None  # Datei existiert nicht
        return current_state

    async def write_and_commit(
        self,
        session: DevelopmentSession,
        files: list[GeneratedFile],
        commit_message: str
    ) -> str:
        """
        Schreibt generierte Dateien und erstellt Commit.
        """
        # 1. Sicherstellen dass wir auf dem richtigen Branch sind
        self.repo.heads[session.git_branch].checkout()

        # 2. Pull um Race Conditions zu vermeiden
        self.repo.remotes.origin.pull()

        # 3. Dateien schreiben
        for file in files:
            full_path = os.path.join(self.repo_path, file.path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, 'w') as f:
                f.write(file.content)

        # 4. Git add & commit
        self.repo.index.add([f.path for f in files])
        commit = self.repo.index.commit(commit_message)

        return commit.hexsha

    async def create_pull_request(
        self,
        session: DevelopmentSession,
        title: str,
        body: str
    ) -> str:
        """
        Erstellt Pull Request via GitHub API.
        """
        # Push branch
        self.repo.remotes.origin.push(session.git_branch)

        # PR erstellen (via GitHub API)
        pr = await self.github_client.create_pull_request(
            head=session.git_branch,
            base="main",
            title=title,
            body=body
        )

        return pr.html_url

    async def detect_conflicts(
        self,
        session: DevelopmentSession
    ) -> list[str]:
        """
        Prüft ob der Branch Merge-Konflikte mit main hat.
        """
        # Fetch latest main
        self.repo.remotes.origin.fetch()

        # Check for conflicts
        try:
            self.repo.git.merge("origin/main", no_commit=True, no_ff=True)
            self.repo.git.merge("--abort")
            return []  # Keine Konflikte
        except git.GitCommandError as e:
            self.repo.git.merge("--abort")
            # Parse conflicting files from error
            return self._parse_conflict_files(str(e))
```

### 12.5 Integration mit Context-Service

```python
class DevelopmentContextService:
    async def build_context(self, session_id: str, ...) -> str:
        # ... bisheriger Code ...

        # NEU: Aktuellen Datei-Stand aus Git laden
        if session.git_branch:
            target_files = self._determine_target_files(session)
            current_file_state = await self.git_service.read_current_file_state(
                target_files
            )

            context_parts.append(self._format_current_files(current_file_state))

    def _format_current_files(self, files: dict[str, str]) -> str:
        text = "## Aktueller Datei-Stand (NICHT ÜBERSCHREIBEN OHNE GRUND!)\n\n"
        for path, content in files.items():
            if content:
                text += f"### {path}\n```\n{content[:2000]}...\n```\n\n"
            else:
                text += f"### {path}\n*Datei existiert nicht (wird neu erstellt)*\n\n"
        return text
```

---

## 13. Dependency-Validation (Abhängigkeits-Prüfung)

### 13.1 Das Problem: Halluzinierte Abhängigkeiten

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         PROBLEM: HALLUZINIERTE IMPORTS                           │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  LLM generiert:                                                                 │
│  ┌──────────────────────────────────────────────────────────────────────────┐   │
│  │ from super_fancy_lib import magic_function  # Existiert nicht!           │   │
│  │ import nonexistent_package                   # Nicht in requirements!    │   │
│  └──────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
│  Deployment:                                                                    │
│  ┌──────────────────────────────────────────────────────────────────────────┐   │
│  │ $ pip install -r requirements.txt                                        │   │
│  │ $ python app.py                                                           │   │
│  │ ModuleNotFoundError: No module named 'super_fancy_lib'  ❌                │   │
│  └──────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 13.2 Die Lösung: Rigorose Validierung

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         DEPENDENCY VALIDATION PIPELINE                           │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  LLM generiert Code                                                             │
│        │                                                                         │
│        ▼                                                                         │
│  ┌──────────────────────────────────────────────────────────────────────────┐   │
│  │ 1. IMPORT EXTRACTION                                                      │   │
│  │    AST-Parsing: Alle import/from statements extrahieren                  │   │
│  └──────────────────────────────────────────────────────────────────────────┘   │
│        │                                                                         │
│        ▼                                                                         │
│  ┌──────────────────────────────────────────────────────────────────────────┐   │
│  │ 2. CATEGORIZATION                                                         │   │
│  │    ├─ Standard Library (ok)                                              │   │
│  │    ├─ Local Imports (prüfen ob Datei existiert)                          │   │
│  │    └─ Third-Party (gegen package.json/requirements.txt prüfen)           │   │
│  └──────────────────────────────────────────────────────────────────────────┘   │
│        │                                                                         │
│        ▼                                                                         │
│  ┌──────────────────────────────────────────────────────────────────────────┐   │
│  │ 3. VALIDATION                                                             │   │
│  │    ├─ In requirements.txt/package.json?                                  │   │
│  │    ├─ Version kompatibel?                                                 │   │
│  │    └─ Existiert auf PyPI/npm?                                            │   │
│  └──────────────────────────────────────────────────────────────────────────┘   │
│        │                                                                         │
│        ▼                                                                         │
│  ┌──────────────────────────────────────────────────────────────────────────┐   │
│  │ 4. RESULT                                                                 │   │
│  │    ✓ Alle Abhängigkeiten validiert → Weiter                              │   │
│  │    ✗ Fehlende Abhängigkeiten → LLM um Korrektur bitten                   │   │
│  └──────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 13.3 Datenmodell: Dependency Tracking

```sql
-- Bekannte Abhängigkeiten pro Modul (Whitelist)
CREATE TABLE module_dependencies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    module_id UUID REFERENCES module_registry(id) ON DELETE CASCADE,

    -- Package-Info
    package_name VARCHAR(255) NOT NULL,
    package_type VARCHAR(20) NOT NULL,       -- python, npm, internal
    version_constraint VARCHAR(100),         -- z.B. ">=1.0.0,<2.0.0"

    -- Kategorisierung
    is_optional BOOLEAN DEFAULT FALSE,
    is_dev_only BOOLEAN DEFAULT FALSE,

    -- Warum wird es gebraucht?
    purpose TEXT,

    added_at TIMESTAMP DEFAULT NOW(),
    added_by VARCHAR(100),

    UNIQUE(module_id, package_name, package_type)
);

-- Validierungs-Ergebnisse
CREATE TABLE dependency_validations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES development_sessions(id) ON DELETE CASCADE,
    task_id UUID REFERENCES development_tasks(id),

    -- Ergebnis
    status VARCHAR(20) NOT NULL,             -- passed, failed, warning
    imports_found JSONB DEFAULT '[]',        -- Alle gefundenen Imports
    missing_packages JSONB DEFAULT '[]',     -- Fehlende Packages
    version_conflicts JSONB DEFAULT '[]',    -- Versions-Konflikte
    suggestions JSONB DEFAULT '[]',          -- Vorschläge zur Behebung

    validated_at TIMESTAMP DEFAULT NOW()
);
```

### 13.4 Dependency-Validator Implementation

```python
# services/dependency_validator.py

import ast
import sys
from importlib.metadata import distributions
import httpx

class DependencyValidator:
    """
    Validiert Abhängigkeiten in generiertem Code.
    """

    # Standard Library Module (Python 3.11+)
    STDLIB_MODULES = set(sys.stdlib_module_names)

    def __init__(self, project_root: str):
        self.project_root = project_root
        self.requirements = self._load_requirements()
        self.package_json = self._load_package_json()

    async def validate_python_code(
        self,
        code: str,
        file_path: str
    ) -> ValidationResult:
        """
        Validiert Python-Code auf fehlende Abhängigkeiten.
        """
        # 1. Imports extrahieren via AST
        imports = self._extract_python_imports(code)

        # 2. Kategorisieren
        categorized = self._categorize_imports(imports, file_path)

        # 3. Third-Party gegen requirements.txt prüfen
        missing = []
        for pkg in categorized['third_party']:
            if not self._is_in_requirements(pkg):
                # Prüfen ob Package auf PyPI existiert
                exists = await self._check_pypi(pkg)
                missing.append({
                    'package': pkg,
                    'exists_on_pypi': exists,
                    'suggestion': f"pip install {pkg}" if exists else "Package existiert nicht!"
                })

        # 4. Local Imports prüfen
        invalid_local = []
        for imp in categorized['local']:
            if not self._local_module_exists(imp, file_path):
                invalid_local.append({
                    'import': imp,
                    'suggestion': f"Modul {imp} muss erst erstellt werden"
                })

        return ValidationResult(
            status='failed' if missing or invalid_local else 'passed',
            missing_packages=missing,
            invalid_local_imports=invalid_local,
            all_imports=imports
        )

    def _extract_python_imports(self, code: str) -> list[str]:
        """Extrahiert alle Imports aus Python-Code via AST."""
        imports = []
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name.split('.')[0])
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.append(node.module.split('.')[0])
        except SyntaxError:
            pass  # Code hat Syntax-Fehler, separat behandeln
        return list(set(imports))

    def _categorize_imports(
        self,
        imports: list[str],
        file_path: str
    ) -> dict:
        """Kategorisiert Imports in stdlib, local, third-party."""
        result = {
            'stdlib': [],
            'local': [],
            'third_party': []
        }

        for imp in imports:
            if imp in self.STDLIB_MODULES:
                result['stdlib'].append(imp)
            elif self._is_local_import(imp, file_path):
                result['local'].append(imp)
            else:
                result['third_party'].append(imp)

        return result

    async def _check_pypi(self, package_name: str) -> bool:
        """Prüft ob Package auf PyPI existiert."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"https://pypi.org/pypi/{package_name}/json",
                    timeout=5.0
                )
                return response.status_code == 200
            except:
                return False

    def _is_in_requirements(self, package: str) -> bool:
        """Prüft ob Package in requirements.txt ist."""
        return package.lower() in [
            r.split('==')[0].split('>=')[0].split('<')[0].lower()
            for r in self.requirements
        ]
```

### 13.5 Integration in Development Pipeline

```python
class DevelopmentTaskExecutor:
    async def execute_task(self, task: DevelopmentTask) -> TaskResult:
        # ... Code generieren ...

        # NEU: Dependency-Validation
        for file in generated_files:
            if file.path.endswith('.py'):
                validation = await self.dep_validator.validate_python_code(
                    file.content,
                    file.path
                )

                if validation.status == 'failed':
                    # LLM um Korrektur bitten
                    correction_prompt = self._build_correction_prompt(
                        file,
                        validation
                    )
                    corrected = await self.llm_service.correct_code(
                        file.content,
                        correction_prompt
                    )
                    file.content = corrected

            elif file.path.endswith(('.ts', '.js', '.tsx', '.jsx')):
                validation = await self.dep_validator.validate_js_code(
                    file.content,
                    file.path
                )
                # ... analog ...

        return TaskResult(files=generated_files, validations=validations)
```

### 13.6 UI: Dependency-Warnings

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         DEPENDENCY VALIDATION                                    │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  ⚠️ Abhängigkeits-Probleme gefunden:                                            │
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │ ❌ Fehlende Packages                                                    │    │
│  ├─────────────────────────────────────────────────────────────────────────┤    │
│  │                                                                          │    │
│  │  1. pandas                                                              │    │
│  │     └─ Existiert auf PyPI: ✓                                            │    │
│  │     └─ Lösung: pip install pandas                                       │    │
│  │     └─ [Zu requirements.txt hinzufügen]                                 │    │
│  │                                                                          │    │
│  │  2. super_fancy_lib                                                     │    │
│  │     └─ Existiert auf PyPI: ✗                                            │    │
│  │     └─ ⚠️ Package existiert nicht! LLM hat halluziniert.               │    │
│  │     └─ [LLM um Korrektur bitten]                                        │    │
│  │                                                                          │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│                                                                                  │
│  [Alle beheben]  [Ignorieren (nicht empfohlen)]  [Abbrechen]                   │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 14. Kontinuierliche Architektur-Überwachung & Vector-Sync

**Kernprinzip:** Das Development-Modul muss jederzeit ein aktuelles Abbild der gesamten Codebasis in pgvector haben, um konsistente und architektur-konforme Vorschläge zu machen.

### 14.1 Architektur-Scanner Service

```python
# apps/backend/app/services/development/architecture_scanner.py

from typing import AsyncGenerator
import asyncio
from datetime import datetime, timedelta
from pathlib import Path

class ArchitectureScanner:
    """
    Kontinuierlicher Scanner, der die Codebasis überwacht
    und Änderungen in pgvector synchronisiert.
    """

    SCAN_INTERVAL_SECONDS = 300  # Alle 5 Minuten

    async def start_background_sync(self) -> None:
        """Startet den Background-Sync-Job."""
        while True:
            try:
                await self.full_sync_cycle()
            except Exception as e:
                logger.error(f"Sync cycle failed: {e}")
            await asyncio.sleep(self.SCAN_INTERVAL_SECONDS)

    async def full_sync_cycle(self) -> dict:
        """Führt einen vollständigen Sync-Zyklus durch."""
        stats = {
            "files_scanned": 0,
            "files_updated": 0,
            "embeddings_created": 0,
            "duration_ms": 0
        }

        start_time = datetime.now()

        # 1. Git-Status prüfen
        git_changes = await self.detect_git_changes()

        # 2. Datei-Hashes vergleichen
        changed_files = await self.find_changed_files(git_changes)

        # 3. Für geänderte Dateien: Embeddings neu erstellen
        for file_path in changed_files:
            await self.update_file_embeddings(file_path)
            stats["files_updated"] += 1

        # 4. Architektur-Metadaten extrahieren
        await self.update_architecture_metadata()

        # 5. Abhängigkeits-Graph aktualisieren
        await self.update_dependency_graph()

        stats["duration_ms"] = (datetime.now() - start_time).total_seconds() * 1000
        return stats

    async def detect_git_changes(self) -> list[str]:
        """Erkennt Änderungen seit letztem Sync via Git."""
        last_sync_commit = await self.get_last_sync_commit()
        result = await run_command(
            f"git diff --name-only {last_sync_commit} HEAD"
        )
        return result.stdout.strip().split('\n')

    async def update_file_embeddings(self, file_path: Path) -> None:
        """Aktualisiert Embeddings für eine einzelne Datei."""
        content = file_path.read_text()

        # Verschiedene Embedding-Typen
        embeddings_to_create = [
            # Gesamtdatei-Embedding
            {
                "entity_type": "file",
                "content": self.prepare_file_content(content),
            },
            # Funktions-Embeddings
            *self.extract_function_embeddings(content, file_path),
            # Klassen-Embeddings
            *self.extract_class_embeddings(content, file_path),
            # Import-Embeddings (für Abhängigkeits-Suche)
            *self.extract_import_embeddings(content, file_path),
        ]

        # Alte Embeddings löschen
        await self.delete_file_embeddings(file_path)

        # Neue Embeddings erstellen
        for emb in embeddings_to_create:
            vector = await self.create_embedding(emb["content"])
            await self.store_embedding(
                entity_type=emb["entity_type"],
                entity_id=str(file_path),
                content=emb["content"],
                embedding=vector,
                metadata=emb.get("metadata", {})
            )
```

### 14.2 Event-basierte Echtzeit-Updates

```python
# apps/backend/app/services/development/file_watcher.py

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class CodebaseWatcher(FileSystemEventHandler):
    """
    Überwacht das Dateisystem auf Änderungen und
    triggert sofortige Vector-Updates.
    """

    WATCH_PATTERNS = [
        "**/*.py", "**/*.ts", "**/*.tsx", "**/*.vue",
        "**/*.js", "**/*.jsx", "**/*.sql", "**/*.yaml"
    ]

    IGNORE_PATTERNS = [
        "**/node_modules/**", "**/__pycache__/**",
        "**/.git/**", "**/dist/**", "**/build/**"
    ]

    async def on_modified(self, event):
        if self.should_process(event.src_path):
            await self.queue_for_embedding(event.src_path)

    async def on_created(self, event):
        if self.should_process(event.src_path):
            await self.queue_for_embedding(event.src_path)

    async def on_deleted(self, event):
        if self.should_process(event.src_path):
            await self.remove_embeddings(event.src_path)
```

### 14.3 Architektur-Metadaten in pgvector

```sql
-- Erweiterung der Embedding-Tabelle für Architektur-Infos

-- Modul-Struktur-Embeddings
INSERT INTO development_embeddings (
    entity_type, entity_id, content_text, embedding, metadata
)
VALUES (
    'module_structure',
    'packages/domain/checklists',
    'Checklists module provides audit checklist management...',
    '[0.1, 0.2, ...]'::vector,
    '{
        "module_name": "@flowaudit/checklists",
        "module_type": "domain",
        "dependencies": ["@flowaudit/core", "@flowaudit/db"],
        "exports": ["ChecklistService", "ChecklistModel"],
        "file_count": 24,
        "loc": 3500
    }'::jsonb
);

-- API-Endpoint-Embeddings
INSERT INTO development_embeddings (
    entity_type, entity_id, content_text, embedding, metadata
)
VALUES (
    'api_endpoint',
    'POST /api/v1/checklists',
    'Creates a new audit checklist with items...',
    '[0.1, 0.2, ...]'::vector,
    '{
        "method": "POST",
        "path": "/api/v1/checklists",
        "request_schema": "ChecklistCreate",
        "response_schema": "ChecklistResponse",
        "auth_required": true,
        "roles": ["auditor", "admin"]
    }'::jsonb
);

-- Datenbank-Schema-Embeddings
INSERT INTO development_embeddings (
    entity_type, entity_id, content_text, embedding, metadata
)
VALUES (
    'db_table',
    'checklists',
    'Checklists table stores audit checklist definitions...',
    '[0.1, 0.2, ...]'::vector,
    '{
        "table_name": "checklists",
        "columns": ["id", "tenant_id", "name", "status"],
        "foreign_keys": [{"column": "tenant_id", "references": "tenants.id"}],
        "indexes": ["idx_checklists_tenant", "idx_checklists_status"]
    }'::jsonb
);
```

### 14.4 Konsistenz-Prüfung vor LLM-Vorschlägen

```python
# apps/backend/app/services/development/consistency_checker.py

class ConsistencyChecker:
    """
    Prüft LLM-Vorschläge gegen die aktuelle Architektur in pgvector.
    """

    async def validate_proposal(
        self,
        proposal: DevelopmentProposal
    ) -> ValidationResult:
        """Validiert einen LLM-Vorschlag gegen die Codebasis."""

        issues = []

        # 1. Datei-Pfade prüfen
        for file_change in proposal.file_changes:
            if not await self.is_valid_path(file_change.path):
                issues.append(ValidationIssue(
                    severity="error",
                    message=f"Path {file_change.path} does not match project structure",
                    suggestion=await self.suggest_correct_path(file_change.path)
                ))

        # 2. Import-Pfade prüfen
        for import_stmt in self.extract_imports(proposal):
            if not await self.is_valid_import(import_stmt):
                issues.append(ValidationIssue(
                    severity="error",
                    message=f"Import {import_stmt} does not exist",
                    suggestion=await self.find_similar_import(import_stmt)
                ))

        # 3. API-Konsistenz prüfen
        for api_change in proposal.api_changes:
            existing = await self.find_similar_endpoints(api_change)
            if existing and not self.is_consistent(api_change, existing):
                issues.append(ValidationIssue(
                    severity="warning",
                    message=f"API pattern inconsistent with existing endpoints",
                    existing_patterns=existing
                ))

        # 4. Namenskonventionen prüfen
        naming_issues = await self.check_naming_conventions(proposal)
        issues.extend(naming_issues)

        return ValidationResult(
            valid=len([i for i in issues if i.severity == "error"]) == 0,
            issues=issues
        )

    async def suggest_correct_path(self, invalid_path: str) -> str:
        """Findet den korrekten Pfad via Vector-Ähnlichkeitssuche."""

        # Suche ähnliche existierende Pfade in pgvector
        similar = await self.db.execute("""
            SELECT entity_id, 1 - (embedding <=> $1) as similarity
            FROM development_embeddings
            WHERE entity_type = 'file'
            ORDER BY embedding <=> $1
            LIMIT 5
        """, [self.embed(invalid_path)])

        return self.find_best_match(invalid_path, similar)
```

### 14.5 Sync-Status Dashboard

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  📊 ARCHITEKTUR-SYNC STATUS                                            [Admin] │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  Letzter Full-Sync: vor 2 Minuten                    Status: ✅ Aktuell         │
│  Nächster Scan: in 3 Minuten                                                    │
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │ EMBEDDING-STATISTIKEN                                                   │    │
│  │ ─────────────────────────────────────────────────────────────          │    │
│  │ Dateien indexiert:        1,247                                         │    │
│  │ Funktionen/Klassen:       8,934                                         │    │
│  │ API-Endpoints:             156                                          │    │
│  │ DB-Tabellen:                42                                          │    │
│  │ Module:                     12                                          │    │
│  │                                                                          │    │
│  │ Gesamt-Embeddings:       10,391                                         │    │
│  │ Vector-DB Größe:          124 MB                                        │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │ LETZTE ÄNDERUNGEN                                                       │    │
│  │ ─────────────────────────────────────────────────────────────          │    │
│  │ • apps/backend/app/api/checklists.py      vor 5 min    ✅ Synced       │    │
│  │ • apps/frontend/src/views/Dashboard.vue   vor 12 min   ✅ Synced       │    │
│  │ • packages/domain/core/src/utils.ts       vor 1 Std    ✅ Synced       │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│                                                                                  │
│  [🔄 Manueller Full-Sync]  [📋 Sync-Log anzeigen]  [⚙️ Einstellungen]          │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 15. Modul-Zuweisung an Konzerne & Abrechnung

**Kernkonzept:** Module können flexibel an Konzerne, Organisationen und Tenants zugewiesen werden. Diese Zuweisung dient sowohl der Zugriffskontrolle als auch der Grundlage für die Abrechnung.

### 15.1 Hierarchie-basierte Modul-Lizenzierung

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           MODUL-LIZENZ-HIERARCHIE                               │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  KONZERN-EBENE (Enterprise License)                                             │
│  ├── Lizenz für: @flowaudit/checklists (Premium)                               │
│  ├── Lizenz für: @flowaudit/development (Enterprise)                           │
│  ├── Max. Organisationen: 10                                                    │
│  └── Max. User gesamt: 500                                                      │
│       │                                                                          │
│       ├── ORGANISATION A                                                        │
│       │    ├── Erbt: @flowaudit/checklists                                     │
│       │    ├── Zusatz-Lizenz: @flowaudit/reporting                             │
│       │    └── Max. User: 100                                                   │
│       │         │                                                                │
│       │         ├── TENANT A1 (Nutzt: checklists, reporting)                   │
│       │         └── TENANT A2 (Nutzt: nur checklists)                          │
│       │                                                                          │
│       └── ORGANISATION B                                                        │
│            ├── Erbt: @flowaudit/checklists                                     │
│            ├── Kein reporting (nicht lizenziert)                               │
│            └── Max. User: 50                                                    │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 15.2 Datenmodell für Modul-Lizenzen

```python
# apps/backend/app/models/licensing.py

class ModuleLicense(TenantModel):
    """Lizenzierung von Modulen auf verschiedenen Ebenen."""

    __tablename__ = "module_licenses"

    # Lizenz-Geltungsbereich (nur eins davon gesetzt)
    konzern_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("konzerne.id", ondelete="CASCADE"),
        nullable=True
    )
    organization_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=True
    )
    tenant_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=True
    )

    # Modul-Informationen
    module_package_name: Mapped[str] = mapped_column(String(255), nullable=False)
    module_version: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Lizenz-Details
    license_type: Mapped[str] = mapped_column(
        Enum("trial", "basic", "professional", "enterprise"),
        default="basic",
        nullable=False
    )

    # Zeitliche Gültigkeit
    valid_from: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.now
    )
    valid_until: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True  # None = unbegrenzt
    )

    # Nutzungslimits
    max_users: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_api_calls_per_month: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Abrechnungs-Referenz
    billing_account_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    __table_args__ = (
        # Eindeutigkeit: Ein Modul pro Scope
        UniqueConstraint(
            'konzern_id', 'organization_id', 'tenant_id', 'module_package_name',
            name='uq_module_license_scope'
        ),
    )


class ModuleUsageLog(Base, TimestampMixin):
    """Protokollierung der Modul-Nutzung für Abrechnung."""

    __tablename__ = "module_usage_logs"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid4())
    )

    # Wer nutzt
    tenant_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False
    )
    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )

    # Was wird genutzt
    module_package_name: Mapped[str] = mapped_column(String(255), nullable=False)
    action_type: Mapped[str] = mapped_column(String(100), nullable=False)

    # Metriken für Abrechnung
    api_calls: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    tokens_used: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    compute_time_ms: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Abrechnungsperiode
    billing_period: Mapped[str] = mapped_column(String(7), nullable=False)  # "2024-01"

    # Zusätzliche Details
    metadata: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
```

### 15.3 Lizenz-Prüfung Service

```python
# apps/backend/app/services/licensing_service.py

class LicensingService:
    """Service zur Prüfung und Verwaltung von Modul-Lizenzen."""

    async def check_module_access(
        self,
        tenant_id: str,
        module_name: str,
        user_id: str | None = None
    ) -> LicenseCheckResult:
        """
        Prüft, ob ein Tenant Zugriff auf ein Modul hat.
        Berücksichtigt Vererbung von Konzern/Organisation.
        """

        # Hole Hierarchie-Pfad
        hierarchy = await self.get_tenant_hierarchy(tenant_id)
        # hierarchy = {"tenant": {...}, "organization": {...}, "konzern": {...}}

        # Prüfe Lizenzen von unten nach oben (Tenant → Org → Konzern)
        license = None

        # 1. Direkte Tenant-Lizenz?
        license = await self.find_license(
            module_name=module_name,
            tenant_id=tenant_id
        )

        # 2. Organisations-Lizenz?
        if not license and hierarchy.get("organization"):
            license = await self.find_license(
                module_name=module_name,
                organization_id=hierarchy["organization"]["id"]
            )

        # 3. Konzern-Lizenz?
        if not license and hierarchy.get("konzern"):
            license = await self.find_license(
                module_name=module_name,
                konzern_id=hierarchy["konzern"]["id"]
            )

        if not license:
            return LicenseCheckResult(
                allowed=False,
                reason="Keine gültige Lizenz gefunden"
            )

        # Prüfe Gültigkeit
        now = datetime.now(timezone.utc)
        if license.valid_until and license.valid_until < now:
            return LicenseCheckResult(
                allowed=False,
                reason="Lizenz abgelaufen",
                expired_at=license.valid_until
            )

        # Prüfe User-Limit
        if license.max_users:
            current_users = await self.count_module_users(tenant_id, module_name)
            if current_users >= license.max_users:
                return LicenseCheckResult(
                    allowed=False,
                    reason=f"Benutzer-Limit erreicht ({license.max_users})"
                )

        return LicenseCheckResult(
            allowed=True,
            license_type=license.license_type,
            valid_until=license.valid_until
        )

    async def log_usage(
        self,
        tenant_id: str,
        user_id: str,
        module_name: str,
        action: str,
        metrics: UsageMetrics
    ) -> None:
        """Protokolliert Modul-Nutzung für Abrechnung."""

        billing_period = datetime.now().strftime("%Y-%m")

        log = ModuleUsageLog(
            tenant_id=tenant_id,
            user_id=user_id,
            module_package_name=module_name,
            action_type=action,
            api_calls=metrics.api_calls,
            tokens_used=metrics.tokens_used,
            compute_time_ms=metrics.compute_time_ms,
            billing_period=billing_period
        )

        await self.db.add(log)
        await self.db.commit()
```

### 15.4 Abrechnungs-Aggregation

```python
# apps/backend/app/services/billing_service.py

class BillingService:
    """Aggregiert Nutzungsdaten für die Abrechnung."""

    async def generate_billing_report(
        self,
        konzern_id: str,
        period: str  # "2024-01"
    ) -> BillingReport:
        """Erstellt Abrechnungsbericht für einen Konzern."""

        # Alle Organisationen und Tenants unter diesem Konzern
        hierarchy = await self.get_full_hierarchy(konzern_id)

        report = BillingReport(
            konzern_id=konzern_id,
            period=period,
            organizations=[]
        )

        for org in hierarchy["organizations"]:
            org_usage = await self.aggregate_organization_usage(org["id"], period)

            org_report = OrganizationBillingReport(
                organization_id=org["id"],
                organization_name=org["name"],
                tenants=[],
                totals=UsageTotals()
            )

            for tenant in org["tenants"]:
                tenant_usage = await self.aggregate_tenant_usage(tenant["id"], period)
                org_report.tenants.append(tenant_usage)
                org_report.totals += tenant_usage.totals

            report.organizations.append(org_report)

        # Berechne Kosten basierend auf Nutzung
        report.calculated_costs = await self.calculate_costs(report)

        return report

    async def aggregate_tenant_usage(
        self,
        tenant_id: str,
        period: str
    ) -> TenantUsageReport:
        """Aggregiert Nutzung pro Tenant und Modul."""

        usage = await self.db.execute("""
            SELECT
                module_package_name,
                COUNT(*) as total_actions,
                SUM(api_calls) as total_api_calls,
                SUM(tokens_used) as total_tokens,
                SUM(compute_time_ms) as total_compute_ms,
                COUNT(DISTINCT user_id) as unique_users
            FROM module_usage_logs
            WHERE tenant_id = $1
              AND billing_period = $2
            GROUP BY module_package_name
        """, [tenant_id, period])

        return TenantUsageReport(
            tenant_id=tenant_id,
            modules=usage.fetchall()
        )
```

### 15.5 Admin-UI für Modul-Zuweisung

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  🏢 MODUL-ZUWEISUNG                                            [Konzern-Admin] │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  Konzern: Muster AG                                                             │
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │ LIZENZIERTE MODULE (Konzern-Ebene)                                      │    │
│  │ ─────────────────────────────────────────────────────────────          │    │
│  │                                                                          │    │
│  │ ☑️  @flowaudit/core              Enterprise  │ Unbegrenzt │ 500 User   │    │
│  │ ☑️  @flowaudit/checklists        Professional│ 31.12.2025 │ 500 User   │    │
│  │ ☑️  @flowaudit/development       Enterprise  │ Unbegrenzt │ 50 User    │    │
│  │ ☐  @flowaudit/reporting          ────────────│────────────│──────────   │    │
│  │ ☐  @flowaudit/documents          ────────────│────────────│──────────   │    │
│  │                                                                          │    │
│  │ [+ Modul hinzufügen]                                                    │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │ ORGANISATIONS-ÜBERSICHT                                                 │    │
│  │ ─────────────────────────────────────────────────────────────          │    │
│  │                                                                          │    │
│  │ ▼ Organisation: Muster GmbH Berlin                                      │    │
│  │   │ Zusatz-Module: @flowaudit/reporting (Professional, 100 User)       │    │
│  │   │                                                                      │    │
│  │   ├── Tenant: Muster Berlin Haupt                                       │    │
│  │   │   └─ Nutzt: core, checklists, reporting │ 45 User aktiv            │    │
│  │   │                                                                      │    │
│  │   └── Tenant: Muster Berlin Filiale                                     │    │
│  │       └─ Nutzt: core, checklists            │ 12 User aktiv            │    │
│  │                                                                          │    │
│  │ ▶ Organisation: Muster GmbH München                                     │    │
│  │   └─ Keine Zusatz-Module                                                │    │
│  │                                                                          │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │ NUTZUNGS-ÜBERSICHT (Aktueller Monat)                                   │    │
│  │ ─────────────────────────────────────────────────────────────          │    │
│  │                                                                          │    │
│  │ @flowaudit/checklists:     12,450 API-Calls │   892,000 Tokens         │    │
│  │ @flowaudit/development:     1,230 API-Calls │ 2,340,000 Tokens         │    │
│  │ @flowaudit/reporting:       3,200 API-Calls │   450,000 Tokens         │    │
│  │                                                                          │    │
│  │ [📊 Detaillierter Bericht]  [📥 Export CSV]                            │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 15.6 API-Endpoints für Lizenzierung

```
# Lizenz-Verwaltung (Admin)
GET  /api/v1/licenses                         → Alle Lizenzen auflisten
POST /api/v1/licenses                         → Neue Lizenz erstellen
GET  /api/v1/licenses/{id}                    → Lizenz-Details
PUT  /api/v1/licenses/{id}                    → Lizenz aktualisieren
DELETE /api/v1/licenses/{id}                  → Lizenz entfernen

# Zugriffsprüfung
GET  /api/v1/licenses/check/{module_name}     → Prüft Zugriff für aktuellen User/Tenant

# Nutzungsberichte
GET  /api/v1/billing/usage                    → Eigene Nutzung
GET  /api/v1/billing/usage/organization/{id}  → Organisations-Nutzung (Org-Admin)
GET  /api/v1/billing/usage/konzern/{id}       → Konzern-Nutzung (Konzern-Admin)
GET  /api/v1/billing/report/{period}          → Abrechnungsbericht für Periode
POST /api/v1/billing/export                   → Export als CSV/PDF
```

---

## 16. Erweiterungen für die Zukunft

1. **Semantische Suche im Memory** - pgvector für bessere Korrektur-Findung
2. **Auto-Dokumentation** - Generierung von CHANGELOG und Docs
3. **Multi-User Kollaboration** - Mehrere User an einer Session
4. **A/B-Testing** - Verschiedene Implementierungen vergleichen
5. **Rollback** - Auf frühere Versionen zurückrollen
6. **Weitere LLMs** - Mistral, Llama, DeepSeek als zusätzliche Optionen
7. **Adaptive Routing** - Automatische LLM-Auswahl basierend auf Task-Komplexität
8. **CI/CD-Integration** - Automatische Tests nach Merge
9. **Security Scanning** - Automatische Prüfung auf Sicherheitslücken
