# FlowNavigator (FlowAudit Platform)

Modulare Prüfbehörden-Management-Plattform (EFRE-Audit). pnpm/Turborepo-Monorepo mit FastAPI-Backend, Vue-3-Frontend und mehrschichtiger Vendor → Customer (Coordination Body) Layer-Struktur (siehe `docs/LAYER-STRUKTUR.md`).

## Tech-Stack

- **Backend:** Python ≥3.11, FastAPI, SQLAlchemy 2.0 (async) + asyncpg, Alembic, Pydantic v2 / pydantic-settings, python-jose (JWT HS256), passlib/bcrypt, slowapi (Rate Limiting), structlog, httpx. ASGI via uvicorn.
- **Frontend:** Vue 3 (`<script setup>`), TypeScript, Vite 6, Pinia, vue-router, vue-i18n (de/en), Tailwind CSS 3, Headless UI / Heroicons.
- **Workspace-Pakete:** `@flowaudit/common`, `@flowaudit/validation`, `@flowaudit/checklists`, `@flowaudit/group-queries`, `@flowaudit/document-box`, `@flowaudit/vue-adapter` (gebaut mit tsup).
- **DB:** PostgreSQL 15.
- **LLM-Provider:** Anthropic, OpenAI, Ollama (Factory-Pattern, `app/services/llm/`).
- **Tooling:** Turborepo, pnpm 10, Prettier, ESLint, ruff/black/mypy/flake8 (Backend), pytest, Vitest.

### Ports

- Backend (uvicorn): `8000` im Container, gemappt auf Host `8001` (`/api/docs`, `/api/health`).
- Frontend (Vite): `5173` im Container, gemappt auf Host `3001`; Dev-Proxy `/api` → `http://localhost:8001`.
- PostgreSQL: Host `127.0.0.1:5436` → Container `5432` (DB/User/Pass: `flowaudit`/`flowaudit`/`dev_password`).

## Setup & Befehle

### Monorepo (Root, via Turborepo)

```bash
pnpm install            # Workspaces installieren (pnpm@10, node >=20)
pnpm build              # turbo run build (alle Pakete/Apps)
pnpm dev                # turbo run dev
pnpm lint               # turbo run lint
pnpm typecheck          # turbo run typecheck
pnpm test               # turbo run test
pnpm format             # prettier --write "**/*.{ts,tsx,vue,md,json}"
```

### Frontend (`apps/frontend`)

```bash
pnpm dev                # Vite Dev-Server (Port 5173)
pnpm build              # vue-tsc -b && vite build
pnpm typecheck          # vue-tsc --noEmit
pnpm test               # vitest
pnpm test:ci            # vitest run --coverage
pnpm lint               # eslint . --ext .vue,.ts,... --fix
```

### Backend (`apps/backend`)

```bash
# Abhängigkeiten (pip + pyproject; kein uv-Lockfile im Repo)
pip install -r requirements.txt          # bzw. pip install -e ".[dev]"
uvicorn app.main:app --reload --port 8000   # Dev-Server
alembic upgrade head                     # Migrationen anwenden (001..009)
pytest                                   # Tests (pytest.ini, asyncio_mode=auto)
ruff check . && black . && mypy app      # Lint/Format/Typecheck
```

`.env` wird aus `apps/backend/.env.example` abgeleitet (`DATABASE_URL`, `SECRET_KEY`, `DEBUG`, `API_PREFIX`, `CORS_ORIGINS`). Bei `DEBUG=false` ist ein sicherer `SECRET_KEY` Pflicht (sonst ValueError beim Start).

### Docker Compose

```bash
docker compose up -d    # db (5436), backend (8001), frontend (3001)
```

### Skripte (`scripts/`)

`backup.sh`, `restore.sh` (Postgres-Dumps → `backups/`), `startup-check.sh`, `setup-claude-cli.sh`.

## Struktur

```
apps/backend/          FastAPI-App
  app/main.py          Entrypoint (FastAPI, CORS, Rate-Limit, Logging, lifespan/init_db)
  app/api/             Router: auth, vendor, vendor_modules, customers, modules,
                       audit_cases, checklists, document_box, findings, history,
                       dashboard, profiles, preferences, audit_logs, health
  app/models/          SQLAlchemy-Modelle (Vendor, Customer/Tenant, User, Module,
                       ModuleConverter, AuditCase, DocumentBox, GroupQuery, ...)
  app/schemas/         Pydantic-Schemas
  app/services/        auth_service, github_service, module_service
                       (ModuleConverterService), llm/ (base, factory, anthropic/
                       openai/ollama provider, service)
  app/core/            config, database, security, logging, rate_limit,
                       context_service, module_manager
  alembic/             Migrationen 001_initial_schema .. 009_add_history
  tests/               pytest (*_api.py-Integrationstests + conftest)
apps/frontend/         Vue-3-App
  src/views/           Dashboard, AuditCases(+Detail), GroupQueries, ModuleConverter,
                       Settings, Login, vendor/VendorDashboard
  src/components/      module-converter/ (5-Step-Wizard), checklists/, documents/,
                       findings/, history/, vendor/, views/ (Tree/List/Tiles/Radial/Minimal)
  src/stores/          Pinia: auth, moduleConverter, vendor
  src/api/             Axios/Fetch-Clients je Domäne
packages/
  core/common, core/validation
  domain/checklists, domain/group-queries
  documents/document-box
  adapters/vue-adapter (Composables: useApi, useChecklist, useDocumentBox, ...)
docs/                  LAYER-STRUKTUR.md, EFRE-Methodik-PDFs/DOCX, DEPLOYMENT.md
graphify-out/          Codegraph (graph.json/html, manifest.json)
```

**Zentrale Module (Graph-Hubs):** `models/user`, `models/base` (BaseModel/TimestampMixin), `api/vendor` (VendorUser), `models/audit_case` (AuditCase), `core/database` (Base), `models/module` (ModuleStatus/DeploymentStatus), `services/github_service`, `api/moduleConverter`, `services/module_service` (ModuleConverterService), `models/customer`, `models/tenant`.

## Konventionen

- **Sprache:** Deutsche UI/Doku mit echten Umlauten (ä/ö/ü/ß); i18n de/en in `src/locales/`.
- **Frontend:** Prettier (`.prettierrc`): keine Semikolons, Single Quotes, 2 Spaces, `printWidth` 100, `trailingComma: es5`, LF. ESLint mit `--fix`. TS strict (`tsconfig.base.json`: `strict`, `noUnusedLocals/Parameters`, `noImplicitAny`). Import-Alias `@` → `src/`.
- **Backend:** black/ruff/flake8 `line-length = 88`, ruff-Regeln `E,F,I,N,W,UP`, mypy `strict` + pydantic-Plugin. pytest `asyncio_mode = auto`, Tests in `apps/backend/tests/` (`test_*.py`).
- **Tests:** Frontend Vitest (happy-dom), Backend pytest-asyncio (httpx AsyncClient in `*_api.py`).
- **DB-Migrationen:** Alembic, nummeriert/sequenziell (`001`..`009`).
