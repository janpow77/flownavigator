# FlowNavigator - Claude CLI Projektkontext

## Projektübersicht

FlowNavigator ist ein Multi-Tenant Workflow-Management-System mit 3-Layer-Architektur:

- **Layer 0 (Vendor)**: Software-Anbieter, Lizenzverwaltung, Modul-Entwicklung
- **Layer 1 (Koordinierungsstelle)**: Konzern-Ebene, Template-Verwaltung, Mandanten
- **Layer 2 (Prüfbehörde)**: Einzelne Behörden mit eigenen Workflows

## Tech Stack

### Backend
- Python 3.11+
- FastAPI
- SQLAlchemy (async)
- PostgreSQL
- Alembic (Migrationen)
- pytest (Tests)

### Frontend
- Vue 3 (Composition API)
- TypeScript
- Pinia (State Management)
- Tailwind CSS
- Playwright (E2E Tests)

## Projektstruktur

```
flownavigator/
├── apps/
│   ├── backend/           # FastAPI Backend
│   │   ├── app/
│   │   │   ├── models/    # SQLAlchemy Models
│   │   │   ├── api/       # API Endpoints
│   │   │   ├── services/  # Business Logic
│   │   │   └── schemas/   # Pydantic Schemas
│   │   └── tests/         # pytest Tests
│   └── frontend/          # Vue 3 Frontend
│       ├── src/
│       │   ├── components/
│       │   ├── views/
│       │   ├── stores/    # Pinia Stores
│       │   └── composables/
│       └── tests/         # Playwright E2E
├── docs/                  # Dokumentation
└── CLAUDE.md              # Diese Datei
```

## Wichtige Dokumentation

Lies diese Dateien vor der Implementierung:

1. **`docs/07_UMSETZUNG_MIT_CLAUDE_CLI.md`** - Hauptimplementierungsplan mit:
   - Akzeptanzkriterien (AC-x.x.x Format)
   - Backend-Tests (Python/pytest)
   - E2E-Tests (TypeScript/Playwright)
   - Claude CLI Befehle

2. **`docs/LAYER-STRUKTUR.md`** - Detaillierte Architektur-Dokumentation

3. **`docs/02_IMPLEMENTATION_TASKS.md`** - Alle Implementierungsaufgaben

## Konventionen

### Backend
- Models in `app/models/` mit SQLAlchemy
- API-Routen in `app/api/v1/`
- Services für Business-Logik
- Schemas für Validierung (Pydantic)
- Tests mit `pytest` und `pytest-asyncio`

### Frontend
- Komponenten in PascalCase (`LayerDashboard.vue`)
- Composables mit `use` Prefix (`useLayerData.ts`)
- Stores in camelCase (`layerStore.ts`)
- E2E Tests mit Playwright

### Tests
- Akzeptanzkriterien als Test-Docstrings: `"""AC-1.1.1: Beschreibung"""`
- Backend: `apps/backend/tests/`
- Frontend: `apps/frontend/tests/e2e/`

## Befehle

```bash
# Backend Tests
cd apps/backend && pytest

# Frontend Tests
cd apps/frontend && npm run test:e2e

# Migrationen
cd apps/backend && alembic upgrade head
```

## Implementierungsreihenfolge

1. Layer 0: Vendor & Development Module
2. Layer 1: Koordinierungsstelle
3. Layer 2: Prüfbehörden
4. Layer-Dashboard
5. UI Enhancements
6. Modul-Distribution
7. Workflow-Historisierung

Siehe `/implement-feature` Command für Details.
