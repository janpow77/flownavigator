# Architektur — flownavigator

_Automatisch generiert von graphify-kira aus dem Code-Graphen. Nicht von Hand editieren — wird beim nächsten Lauf überschrieben._

**Umfang:** 3087 Knoten, 5517 Kanten, 20 größere Module, 1 zirkuläre Abhängigkeiten.

## Modulkarte

- **Module Converter** (74): `module_converter.py`, `github_service.py`, `test_module_converter.py`
- **Conversion Tracking** (71): `modules.py`, `module_converter.py`, `module_service.py`
- **Conversation Management** (66): `modules.py`, `audit_case.py`
- **GitHub Integration** (64): `history.py`, `context_service.py`
- **Conversion Management** (62): `github_service.py`, `Exception`, `test_module_converter.py`
- **Checklist Management** (55): `checklists.py`, `audit_case.py`, `checklist.py`
- **Workflow Schemas** (52): `database.py`, `DeclarativeBase`, `audit_case.py`, `base.py`, `str`
- **TS Module Conversion** (51): `moduleConverter.ts`
- **Customer Management** (47): `vendor_modules.py`, `module_manager.py`, `customer.py`, `module.py`
- **Background Conversion** (47): `vendor.ts`
- **Vendor Modules API** (44): `test_audit_cases_api.py`, `test_profiles_api.py`
- **Access Control Tests** (43): `customers.py`, `customer.py`, `tenant.py`
- **Customer API** (43): `package.json`, `turbo.json`
- **Package Config** (42): `profiles.py`, `profile.py`
- **Document Box API** (41): `document_box.py`, `audit_case.py`
- **Profile API** (40): `App.vue`, `usePreferences.ts`, `index.ts`, `main.ts`, `preferences.ts`
- **User Preferences** (38): `auth.py`, `security.py`, `auth_service.py`
- **Frontend Dependencies** (38): `auth.py`, `vendor.py`, `security.py`
- **Vendor API** (38): `package.json`
- **Audit Log Schema** (35): `history.py`, `Enum`

## Zentrale Bausteine (God Nodes)

_Hohe Zentralität ist nicht automatisch ein Defekt (zentrale Stores/Modelle sind oft legitim). Konkrete Refactoring-Prioritäten siehe Optimierungs-Report._

- `Base (apps/backend/app/core/database.py)` — Grad 46 (ein 44/aus 2)
- `BaseModel` — Grad 95 (ein 95/aus 0)
- `User (apps/backend/app/models/user.py)` — Grad 102 (ein 99/aus 3)
- `TimestampMixin (apps/backend/app/models/base.py)` — Grad 41 (ein 40/aus 1)
- `AuditCase (apps/backend/app/models/audit_case.py)` — Grad 62 (ein 60/aus 2)
- `VendorUser (apps/backend/app/api/vendor.py)` — Grad 67 (ein 60/aus 7)
- `UUID (apps/backend/app/api/modules.py)` — Grad 66 (ein 57/aus 9)
- `AsyncClient (apps/backend/tests/test_customers_api.py)` — Grad 44 (ein 44/aus 0)
- `AsyncClient (apps/backend/tests/test_modules_api.py)` — Grad 35 (ein 35/aus 0)
- `AsyncClient (apps/backend/tests/test_findings_api.py)` — Grad 33 (ein 33/aus 0)

## Schnittstellen / Brücken (Betweenness)

- `UUID (apps/backend/app/api/modules.py)` — Betweenness 0.001
- `GitHubService (apps/backend/app/services/github_service.py)` — Betweenness 0.001
- `ModuleConverterService (apps/backend/app/services/module_service.py)` — Betweenness 0.001
- `VendorUser (apps/backend/app/api/vendor.py)` — Betweenness 0.000
- `AuthService (apps/backend/app/services/auth_service.py)` — Betweenness 0.000
- `Token (apps/backend/app/api/auth.py)` — Betweenness 0.000
- `Base (apps/backend/app/core/database.py)` — Betweenness 0.000
- `User (apps/backend/app/models/user.py)` — Betweenness 0.000
- `LLMProviderFactory (apps/backend/app/services/llm/factory.py)` — Betweenness 0.000
- `profiles.py (apps/backend/app/api/profiles.py)` — Betweenness 0.000

## Zirkuläre Abhängigkeiten

Es gibt **1** nicht-triviale Zyklen (starke Zusammenhangskomponenten) — Kandidaten zum Auflösen (Dependency-Inversion).

## Empfohlene Spezialisten

Passend zu Stack/Domäne dieses Projekts (Claude-Code-Agents/Skills):

`/deutsche-formulierung`, `@git-workflow`, `/auto-verify`, `@alembic-migrator`, `/db-migration-helper`, `@docker-proxy-debugger`, `/docker-debug`, `/cross-project-health`, `@e2e-browser-tester`, `/modern-gui-builder`, `/ux-completeness-check`, `/vue3-gui-builder`.

## Hinweis für Änderungen

Vor dem Ändern eines zentralen Bausteins die Abhängigen prüfen — am schnellsten über den **graphify-MCP** (globaler Graph): „Was hängt an `<datei>`?". Brücken-Knoten stabil halten.

