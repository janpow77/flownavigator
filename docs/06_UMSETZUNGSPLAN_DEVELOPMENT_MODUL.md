# Umsetzungsplan: Development-Modul

> Detaillierter Plan zur Implementierung mit Claude Code CLI
> Basiert auf: `05_KONZEPT_DEVELOPMENT_MODUL.md`

---

## Übersicht der Phasen

| Phase | Beschreibung | Priorität | Abhängigkeiten |
|-------|--------------|-----------|----------------|
| **Phase 1** | Basis-Infrastruktur | KRITISCH | - |
| **Phase 2** | Datenmodelle & Migrationen | KRITISCH | Phase 1 |
| **Phase 3** | Backend-Services | HOCH | Phase 2 |
| **Phase 4** | API-Endpoints | HOCH | Phase 3 |
| **Phase 5** | Frontend-Grundlagen | HOCH | Phase 4 |
| **Phase 6** | LLM-Integration | HOCH | Phase 3 |
| **Phase 7** | Architektur-Sync & Vector | MITTEL | Phase 3 |
| **Phase 8** | i18n-Zentralisierung | MITTEL | Phase 4 |
| **Phase 9** | Admin-Dashboards | MITTEL | Phase 5 |
| **Phase 10** | Testing & Dokumentation | HOCH | Alle |

---

## Phase 1: Basis-Infrastruktur

### 1.1 pgvector Extension einrichten

**Anforderungen:**
- [ ] PostgreSQL muss pgvector Extension unterstützen
- [ ] Extension in der Datenbank aktivieren

**Schritte:**
```bash
# In der PostgreSQL-Datenbank ausführen
CREATE EXTENSION IF NOT EXISTS vector;
```

**Erfolgskriterium:** `SELECT * FROM pg_extension WHERE extname = 'vector';` gibt einen Eintrag zurück.

---

### 1.2 Modul-Package-Struktur erstellen

**Anforderungen:**
- [ ] pnpm workspace `@flowaudit/development` anlegen
- [ ] Ordnerstruktur nach bestehendem Muster

**Schritte:**

1. Package-Verzeichnis erstellen:
```
packages/domain/development/
├── src/
│   ├── index.ts
│   ├── types.ts
│   ├── schemas.ts
│   └── constants.ts
├── package.json
├── tsconfig.json
└── README.md
```

2. `packages/domain/development/package.json`:
```json
{
  "name": "@flowaudit/development",
  "version": "0.1.0",
  "type": "module",
  "main": "./src/index.ts",
  "types": "./src/index.ts",
  "dependencies": {
    "@flowaudit/core": "workspace:*"
  }
}
```

3. In Root `pnpm-workspace.yaml` sicherstellen:
```yaml
packages:
  - 'packages/domain/*'
```

**Erfolgskriterium:** `pnpm install` läuft ohne Fehler, `@flowaudit/development` ist verfügbar.

---

### 1.3 Backend-Modul-Struktur erstellen

**Anforderungen:**
- [ ] API-Router für development
- [ ] Service-Verzeichnis
- [ ] Model-Dateien

**Schritte:**

1. Dateien erstellen:
```
apps/backend/app/
├── api/
│   └── development.py          # NEU
├── models/
│   ├── development.py          # NEU
│   ├── i18n.py                 # NEU
│   └── licensing.py            # NEU
├── schemas/
│   └── development.py          # NEU
└── services/
    └── development/            # NEU
        ├── __init__.py
        ├── session_service.py
        ├── feedback_service.py
        ├── architecture_scanner.py
        ├── consistency_checker.py
        └── llm_orchestrator.py
```

2. Router in `apps/backend/app/api/__init__.py` registrieren:
```python
from app.api import development
router.include_router(development.router, prefix="/development", tags=["Development"])
```

**Erfolgskriterium:** Server startet ohne Importfehler.

---

## Phase 2: Datenmodelle & Migrationen

### 2.1 Development-Session Modelle

**Anforderungen:**
- [ ] `DevelopmentSession` Model
- [ ] `SessionFile` Model
- [ ] `SessionFeedback` Model
- [ ] `SessionProposal` Model

**Datei:** `apps/backend/app/models/development.py`

```python
# Vollständige Implementierung gemäß Konzept Sektion 2
# Enthält: DevelopmentSession, SessionFile, SessionFeedback, SessionProposal
```

**Erfolgskriterium:**
- `alembic revision --autogenerate -m "add development models"`
- `alembic upgrade head` ohne Fehler

---

### 2.2 pgvector Embedding-Tabelle

**Anforderungen:**
- [ ] `development_embeddings` Tabelle
- [ ] IVFFlat Index für schnelle Suche

**SQL-Migration:**
```sql
CREATE TABLE development_embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    entity_type VARCHAR(50) NOT NULL,
    entity_id UUID NOT NULL,
    content_text TEXT NOT NULL,
    embedding vector(1536),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_dev_embeddings_vector
    ON development_embeddings
    USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

CREATE INDEX idx_dev_embeddings_entity
    ON development_embeddings (entity_type, entity_id);
```

**Erfolgskriterium:** `SELECT * FROM development_embeddings LIMIT 1;` funktioniert.

---

### 2.3 Lizenzierungs-Modelle

**Anforderungen:**
- [ ] `ModuleLicense` Model
- [ ] `ModuleUsageLog` Model

**Datei:** `apps/backend/app/models/licensing.py`

**Erfolgskriterium:** Alembic-Migration erfolgreich.

---

### 2.4 i18n-Modelle

**Anforderungen:**
- [ ] `TranslationNamespace` Model
- [ ] `Translation` Model
- [ ] `TranslationEmbedding` Model

**Datei:** `apps/backend/app/models/i18n.py`

**Erfolgskriterium:** Alembic-Migration erfolgreich.

---

### 2.5 UI-Config-Modelle

**Anforderungen:**
- [ ] `UIComponent` Model
- [ ] `DesignToken` Model
- [ ] `UserUIPreference` Model

**Datei:** `apps/backend/app/models/ui_config.py`

**Erfolgskriterium:** Alembic-Migration erfolgreich.

---

### 2.6 Admin-User anlegen

**Anforderungen:**
- [ ] User `jan.riener` mit Passwort `admin123`
- [ ] Alle Rollen zuweisen

**SQL:**
```sql
INSERT INTO users (id, email, username, password_hash, first_name, last_name, is_active, is_superuser)
VALUES (
    gen_random_uuid(),
    'jan.riener@flowaudit.de',
    'jan.riener',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.qUoXdJqZc1hZmS', -- bcrypt hash für 'admin123'
    'Jan',
    'Riener',
    true,
    true
);

INSERT INTO user_roles (user_id, role_name)
SELECT id, role FROM users, unnest(ARRAY['admin', 'developer', 'auditor']) AS role
WHERE username = 'jan.riener';
```

**Erfolgskriterium:** Login mit `jan.riener` / `admin123` funktioniert.

---

## Phase 3: Backend-Services

### 3.1 Session-Service

**Datei:** `apps/backend/app/services/development/session_service.py`

**Anforderungen:**
- [ ] `create_session()`
- [ ] `get_session()`
- [ ] `list_sessions()`
- [ ] `update_session_status()`
- [ ] `add_file_to_session()`

**Erfolgskriterium:** Unit-Tests für alle Methoden grün.

---

### 3.2 Feedback-Service

**Datei:** `apps/backend/app/services/development/feedback_service.py`

**Anforderungen:**
- [ ] `submit_feedback()`
- [ ] `get_feedback_history()`
- [ ] `calculate_iteration_count()`

**Erfolgskriterium:** Feedback-Loop funktioniert (Test mit Mock-LLM).

---

### 3.3 Architecture-Scanner Service

**Datei:** `apps/backend/app/services/development/architecture_scanner.py`

**Anforderungen:**
- [ ] `scan_codebase()`
- [ ] `update_file_embeddings()`
- [ ] `detect_git_changes()`
- [ ] `start_background_sync()` (async background task)

**Erfolgskriterium:** Nach Scan sind Embeddings in `development_embeddings` vorhanden.

---

### 3.4 Consistency-Checker Service

**Datei:** `apps/backend/app/services/development/consistency_checker.py`

**Anforderungen:**
- [ ] `validate_proposal()`
- [ ] `check_file_paths()`
- [ ] `check_imports()`
- [ ] `suggest_corrections()`

**Erfolgskriterium:** Erkennt falsche Pfade wie `src/modules/` statt `src/components/`.

---

### 3.5 LLM-Orchestrator Service

**Datei:** `apps/backend/app/services/development/llm_orchestrator.py`

**Anforderungen:**
- [ ] `analyze_with_glm()` - Analyse-Phase mit GLM-4
- [ ] `generate_with_claude()` - Code-Generierung mit Anthropic
- [ ] `orchestrate_session()` - Vollständiger Workflow

**Erfolgskriterium:** Kann zwischen LLMs wechseln, Fallback funktioniert.

---

### 3.6 Licensing-Service

**Datei:** `apps/backend/app/services/licensing_service.py`

**Anforderungen:**
- [ ] `check_module_access()` mit Hierarchie-Prüfung
- [ ] `log_usage()`
- [ ] `get_tenant_hierarchy()`

**Erfolgskriterium:** Lizenz-Check berücksichtigt Konzern → Org → Tenant Vererbung.

---

### 3.7 i18n-Service

**Datei:** `apps/backend/app/services/i18n_service.py`

**Anforderungen:**
- [ ] `get_translations()`
- [ ] `search_translations()` mit pgvector
- [ ] `update_translation()`
- [ ] `import_from_json()` - Migration bestehender Dateien

**Erfolgskriterium:** Kann bestehende de.json/en.json in DB importieren.

---

### 3.8 UI-Config-Service

**Datei:** `apps/backend/app/services/ui_config_service.py`

**Anforderungen:**
- [ ] `get_user_config_with_defaults()`
- [ ] `sync_design_tokens_to_vector()`
- [ ] `sync_components_to_vector()`

**Erfolgskriterium:** User-Preferences werden korrekt gemerged.

---

## Phase 4: API-Endpoints

### 4.1 Development-Session Endpoints

**Datei:** `apps/backend/app/api/development.py`

**Endpoints:**
- [ ] `POST /api/v1/development/sessions` - Session erstellen
- [ ] `GET /api/v1/development/sessions` - Sessions auflisten
- [ ] `GET /api/v1/development/sessions/{id}` - Session-Details
- [ ] `PUT /api/v1/development/sessions/{id}` - Session aktualisieren
- [ ] `DELETE /api/v1/development/sessions/{id}` - Session löschen

**Erfolgskriterium:** Alle Endpoints via Swagger UI testbar.

---

### 4.2 File-Upload Endpoints

**Endpoints:**
- [ ] `POST /api/v1/development/sessions/{id}/files` - Datei hochladen
- [ ] `GET /api/v1/development/sessions/{id}/files` - Dateien auflisten
- [ ] `DELETE /api/v1/development/sessions/{id}/files/{file_id}` - Datei entfernen

**Erfolgskriterium:** Kann mehrere Dateien pro Session hochladen.

---

### 4.3 Feedback Endpoints

**Endpoints:**
- [ ] `POST /api/v1/development/sessions/{id}/feedback` - Feedback abgeben
- [ ] `GET /api/v1/development/sessions/{id}/feedback` - Feedback-Historie
- [ ] `POST /api/v1/development/sessions/{id}/approve` - Entwicklung freigeben

**Erfolgskriterium:** Iterativer Feedback-Loop funktioniert.

---

### 4.4 Proposal Endpoints

**Endpoints:**
- [ ] `GET /api/v1/development/sessions/{id}/proposal` - Aktueller Vorschlag
- [ ] `POST /api/v1/development/sessions/{id}/proposal/regenerate` - Neu generieren

**Erfolgskriterium:** LLM generiert Vorschläge basierend auf Feedback.

---

### 4.5 Architecture Endpoints

**Endpoints:**
- [ ] `GET /api/v1/development/architecture/status` - Sync-Status
- [ ] `POST /api/v1/development/architecture/sync` - Manueller Sync
- [ ] `GET /api/v1/development/architecture/search` - Semantische Suche

**Erfolgskriterium:** Kann nach Code-Elementen via Vector-Suche finden.

---

### 4.6 Licensing Endpoints

**Datei:** `apps/backend/app/api/licensing.py` (NEU)

**Endpoints:**
- [ ] `GET /api/v1/licenses` - Lizenzen auflisten
- [ ] `POST /api/v1/licenses` - Lizenz erstellen
- [ ] `GET /api/v1/licenses/check/{module}` - Zugriff prüfen
- [ ] `GET /api/v1/billing/usage` - Nutzung anzeigen

**Erfolgskriterium:** Lizenz-Check in Development-Endpoints integriert.

---

### 4.7 i18n Endpoints

**Datei:** `apps/backend/app/api/i18n.py` (NEU)

**Endpoints:**
- [ ] `GET /api/v1/i18n/{locale}` - Übersetzungen laden
- [ ] `POST /api/v1/i18n/search` - Semantische Suche
- [ ] `PUT /api/v1/i18n/translations/{key}` - Übersetzung ändern (Admin)
- [ ] `POST /api/v1/i18n/import` - JSON importieren (Admin)

**Erfolgskriterium:** Frontend kann Übersetzungen dynamisch laden.

---

### 4.8 UI-Config Endpoints

**Datei:** `apps/backend/app/api/ui_config.py` (NEU)

**Endpoints:**
- [ ] `GET /api/v1/ui/config` - User-Config abrufen
- [ ] `PUT /api/v1/ui/preferences` - Preferences speichern
- [ ] `GET /api/v1/ui/design-tokens` - Design-Tokens abrufen

**Erfolgskriterium:** Preferences werden zwischen Sessions persistiert.

---

## Phase 5: Frontend-Grundlagen

### 5.1 Development-Store (Pinia)

**Datei:** `apps/frontend/src/stores/development.ts`

**Anforderungen:**
- [ ] State für aktuelle Session
- [ ] State für Dateien, Feedback, Proposals
- [ ] Actions für alle API-Calls

**Erfolgskriterium:** Store reaktiv, DevTools zeigen State korrekt.

---

### 5.2 Development-API-Client

**Datei:** `apps/frontend/src/api/development.ts`

**Anforderungen:**
- [ ] Alle Development-Endpoints
- [ ] TypeScript-Typen aus `@flowaudit/development`

**Erfolgskriterium:** Typsichere API-Calls.

---

### 5.3 Development-View

**Datei:** `apps/frontend/src/views/DevelopmentView.vue`

**Anforderungen:**
- [ ] Session-Liste
- [ ] Session-Erstellung (Modul-Auswahl)
- [ ] Workflow-Visualisierung

**Erfolgskriterium:** Navigation zum Development-Bereich funktioniert.

---

### 5.4 Session-Detail-Komponenten

**Dateien:**
- [ ] `apps/frontend/src/components/development/SessionStepper.vue`
- [ ] `apps/frontend/src/components/development/FileUploader.vue`
- [ ] `apps/frontend/src/components/development/FeedbackPanel.vue`
- [ ] `apps/frontend/src/components/development/ProposalViewer.vue`
- [ ] `apps/frontend/src/components/development/DiffViewer.vue`

**Erfolgskriterium:** Vollständiger Workflow in UI durchspielbar.

---

### 5.5 User-Profile Einstellungen

**Datei:** `apps/frontend/src/components/development/UserProfileSettings.vue`

**Anforderungen:**
- [ ] Nur sichtbar für Rollen `developer` oder `admin`
- [ ] LLM-Präferenzen
- [ ] Benachrichtigungs-Einstellungen

**Erfolgskriterium:** Tab in Einstellungen erscheint nur für berechtigte User.

---

### 5.6 Router-Erweiterung

**Datei:** `apps/frontend/src/router/index.ts`

**Routen:**
```typescript
{
  path: '/development',
  component: () => import('@/views/DevelopmentView.vue'),
  meta: { requiresAuth: true, roles: ['developer', 'admin'] }
},
{
  path: '/development/session/:id',
  component: () => import('@/views/DevelopmentSessionView.vue'),
  meta: { requiresAuth: true, roles: ['developer', 'admin'] }
}
```

**Erfolgskriterium:** Routing mit Rollenprüfung funktioniert.

---

### 5.7 Zentrale i18n-Integration

**Datei:** `apps/frontend/src/composables/useCentralI18n.ts`

**Anforderungen:**
- [ ] Lädt Übersetzungen von API
- [ ] Fallback auf lokale JSON-Dateien
- [ ] Cache mit Background-Refresh

**Erfolgskriterium:** Sprachumschaltung lädt dynamisch vom Server.

---

## Phase 6: LLM-Integration

### 6.1 GLM-4 Adapter

**Datei:** `apps/backend/app/services/llm/glm_adapter.py`

**Anforderungen:**
- [ ] API-Anbindung an GLM-4
- [ ] Streaming-Support
- [ ] Error-Handling mit Retry

**Erfolgskriterium:** GLM-4 kann Analyse-Prompts verarbeiten.

---

### 6.2 Anthropic Claude Adapter

**Datei:** `apps/backend/app/services/llm/anthropic_adapter.py`

**Anforderungen:**
- [ ] API-Anbindung an Anthropic Claude
- [ ] Streaming-Support
- [ ] Error-Handling mit Retry

**Erfolgskriterium:** Claude kann Code-Generierung durchführen.

---

### 6.3 LLM-Router

**Datei:** `apps/backend/app/services/llm/router.py`

**Anforderungen:**
- [ ] Routing basierend auf Task-Typ
- [ ] Fallback-Kette bei Fehlern
- [ ] Rate-Limiting pro Provider

**Erfolgskriterium:** Automatischer Fallback funktioniert.

---

### 6.4 Prompt-Templates

**Datei:** `apps/backend/app/services/development/prompts.py`

**Anforderungen:**
- [ ] `ANALYSIS_PROMPT` - Für GLM-4 Analyse
- [ ] `GENERATION_PROMPT` - Für Claude Code-Gen
- [ ] `FEEDBACK_INCORPORATION_PROMPT` - Für Iteration
- [ ] `CONSISTENCY_CHECK_PROMPT` - Für Validierung

**Erfolgskriterium:** Prompts produzieren konsistente Ergebnisse.

---

## Phase 7: Architektur-Sync & Vector

### 7.1 File-Watcher Service

**Datei:** `apps/backend/app/services/development/file_watcher.py`

**Anforderungen:**
- [ ] Überwacht Dateisystem-Änderungen
- [ ] Ignoriert `node_modules`, `.git`, etc.
- [ ] Queued Updates für Embeddings

**Erfolgskriterium:** Dateiänderungen werden innerhalb 10s erkannt.

---

### 7.2 Embedding-Generator

**Datei:** `apps/backend/app/services/development/embedding_generator.py`

**Anforderungen:**
- [ ] Generiert Embeddings via OpenAI/lokales Modell
- [ ] Batch-Processing für Effizienz
- [ ] Caching für unveränderte Dateien

**Erfolgskriterium:** 1000 Dateien in < 5 Minuten indexiert.

---

### 7.3 Background-Sync-Job

**Anforderungen:**
- [ ] Läuft alle 5 Minuten
- [ ] Erkennt Git-Änderungen seit letztem Sync
- [ ] Aktualisiert nur geänderte Dateien

**Erfolgskriterium:** Sync-Job läuft stabil im Hintergrund.

---

### 7.4 Admin-Dashboard für Sync-Status

**Datei:** `apps/frontend/src/components/admin/ArchitectureSyncStatus.vue`

**Anforderungen:**
- [ ] Zeigt letzten Sync-Zeitpunkt
- [ ] Zeigt Anzahl indexierter Elemente
- [ ] Button für manuellen Sync

**Erfolgskriterium:** Admin kann Sync-Status einsehen und manuell triggern.

---

## Phase 8: i18n-Zentralisierung

### 8.1 Migration bestehender Übersetzungen

**Script:** `scripts/migrate_i18n.py`

**Anforderungen:**
- [ ] Liest `de.json` und `en.json`
- [ ] Erstellt Namespaces automatisch
- [ ] Importiert in `translations` Tabelle
- [ ] Generiert Embeddings

**Erfolgskriterium:** Alle bestehenden Keys sind in DB.

---

### 8.2 Admin-UI für Übersetzungen

**Datei:** `apps/frontend/src/views/admin/TranslationsView.vue`

**Anforderungen:**
- [ ] Namespace-Filter
- [ ] Suche (normal + semantisch)
- [ ] Inline-Editing
- [ ] Import/Export-Buttons

**Erfolgskriterium:** Admin kann Übersetzungen bearbeiten.

---

### 8.3 Fehlende Übersetzungen erkennen

**Anforderungen:**
- [ ] Warnung wenn `en` leer aber `de` vorhanden
- [ ] Report über fehlende Keys

**Erfolgskriterium:** Dashboard zeigt fehlende Übersetzungen.

---

## Phase 9: Admin-Dashboards

### 9.1 Konzern/Organisations-Übersicht

**Datei:** `apps/frontend/src/views/admin/HierarchyView.vue`

**Anforderungen:**
- [ ] Baumansicht: Konzern → Organisation → Tenant
- [ ] Modul-Lizenzen pro Ebene
- [ ] User-Zahlen

**Erfolgskriterium:** Admin kann Hierarchie visualisieren.

---

### 9.2 Modul-Zuweisung

**Datei:** `apps/frontend/src/views/admin/ModuleLicensesView.vue`

**Anforderungen:**
- [ ] Module an Konzerne zuweisen
- [ ] Lizenzen verwalten (Trial, Basic, Pro, Enterprise)
- [ ] Nutzungs-Limits setzen

**Erfolgskriterium:** Admin kann Lizenzen verwalten.

---

### 9.3 Billing/Nutzungs-Reports

**Datei:** `apps/frontend/src/views/admin/BillingView.vue`

**Anforderungen:**
- [ ] Nutzung pro Modul/Tenant
- [ ] Zeitraum-Filter
- [ ] Export als CSV

**Erfolgskriterium:** Abrechnungsdaten sind einsehbar.

---

### 9.4 Architektur-Monitor

**Datei:** `apps/frontend/src/views/admin/ArchitectureMonitorView.vue`

**Anforderungen:**
- [ ] Embedding-Statistiken
- [ ] Letzte Änderungen
- [ ] Sync-Log

**Erfolgskriterium:** Admin hat Überblick über Vector-DB.

---

## Phase 10: Testing & Dokumentation

### 10.1 Backend Unit-Tests

**Anforderungen:**
- [ ] Tests für alle Services
- [ ] Tests für alle API-Endpoints
- [ ] Mocked LLM-Responses

**Erfolgskriterium:** `pytest` mit > 80% Coverage.

---

### 10.2 Frontend Component-Tests

**Anforderungen:**
- [ ] Tests für kritische Komponenten
- [ ] Tests für Stores

**Erfolgskriterium:** `vitest` grün.

---

### 10.3 E2E-Tests

**Anforderungen:**
- [ ] Session-Erstellung bis Freigabe
- [ ] Feedback-Loop durchspielen
- [ ] Admin-Funktionen

**Erfolgskriterium:** Playwright-Tests grün.

---

### 10.4 API-Dokumentation

**Anforderungen:**
- [ ] OpenAPI-Spec vollständig
- [ ] Beispiel-Requests/-Responses

**Erfolgskriterium:** Swagger UI dokumentiert alle Endpoints.

---

### 10.5 README Updates

**Anforderungen:**
- [ ] Setup-Anleitung für Development-Modul
- [ ] Umgebungsvariablen dokumentiert
- [ ] LLM-API-Keys Konfiguration

**Erfolgskriterium:** Neuer Entwickler kann Setup in < 30 Min durchführen.

---

## Checkliste für Claude Code CLI

Jeder Task sollte mit folgendem Format bearbeitet werden:

```
## Task: [Name]

### Anforderungen
- [ ] Anforderung 1
- [ ] Anforderung 2

### Dateien
- `pfad/zur/datei1.py` - Beschreibung
- `pfad/zur/datei2.ts` - Beschreibung

### Erfolgskriterium
Wie wird geprüft, ob der Task erfolgreich ist?

### Abhängigkeiten
Welche anderen Tasks müssen vorher erledigt sein?
```

---

## Reihenfolge der Umsetzung

1. **Phase 1** komplett (Infrastruktur)
2. **Phase 2** komplett (Datenmodelle)
3. **Phase 3.1-3.5** (Core Services)
4. **Phase 4.1-4.4** (Core API)
5. **Phase 5.1-5.4** (Core Frontend)
6. **Phase 6** komplett (LLM-Integration)
7. **Phase 3.6-3.8** (Extended Services)
8. **Phase 4.5-4.8** (Extended API)
9. **Phase 5.5-5.7** (Extended Frontend)
10. **Phase 7** komplett (Architecture Sync)
11. **Phase 8** komplett (i18n)
12. **Phase 9** komplett (Admin Dashboards)
13. **Phase 10** komplett (Testing)

---

## Kritische Pfade

```
pgvector Setup → Embedding-Tabelle → Architecture Scanner → Consistency Checker
                                                              ↓
Session Model → Session Service → Session API → Frontend → LLM Integration
                                                              ↓
                                          Feedback Loop → Approval → Git Integration
```

---

## Geschätzte Komplexität

| Phase | Dateien | Geschätzte LOC |
|-------|---------|----------------|
| Phase 1 | 5-8 | ~200 |
| Phase 2 | 5-7 | ~500 |
| Phase 3 | 8-10 | ~1500 |
| Phase 4 | 4-6 | ~800 |
| Phase 5 | 10-15 | ~2000 |
| Phase 6 | 4-5 | ~600 |
| Phase 7 | 4-5 | ~700 |
| Phase 8 | 3-4 | ~400 |
| Phase 9 | 5-6 | ~1000 |
| Phase 10 | 10+ | ~1500 |

**Gesamt:** ~9200 LOC

---

*Dieser Plan ist ein lebendes Dokument und wird bei Bedarf aktualisiert.*
