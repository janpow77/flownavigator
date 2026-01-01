# Feature implementieren

Implementiere Feature $ARGUMENTS basierend auf der Dokumentation.

## Anweisungen

1. Lies zuerst `docs/07_UMSETZUNG_MIT_CLAUDE_CLI.md` und finde das entsprechende Feature
2. Lies auch `docs/LAYER-STRUKTUR.md` für Architektur-Details
3. Implementiere Schritt für Schritt:
   - Backend-Modelle (SQLAlchemy)
   - Alembic-Migration erstellen
   - API-Endpoints (FastAPI)
   - Pydantic-Schemas
   - Frontend-Komponenten (Vue 3)
   - Pinia-Store
4. Schreibe Tests gemäß Akzeptanzkriterien (AC-x.x.x)
5. Führe Tests aus und behebe Fehler

## Features

- **1**: Layer 0 - Vendor & Development Module
- **2**: Layer 1 - Koordinierungsstelle
- **3**: Layer 2 - Prüfbehörden
- **4**: Layer-Dashboard
- **5**: UI Enhancements (Shimmer, Microinteractions, ViewSwitcher)
- **6**: Modul-Distribution
- **7**: Workflow-Historisierung

## Beispiel

`/implement-feature 1` - Implementiert Layer 0 (Vendor & Development Module)
