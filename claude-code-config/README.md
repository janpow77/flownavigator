# Claude Code Konfiguration für FlowAudit

Dieses Verzeichnis enthält alle Konfigurationsdateien für die Entwicklung der FlowAudit Platform mit Claude Code CLI.

## Dateien

| Datei | Beschreibung |
|-------|--------------|
| `CLAUDE.md` | Hauptkonfiguration mit Projektübersicht, Tech-Stack, Konventionen |
| `agents.md` | Spezialisierte Entwicklungs-Agents (Backend, Frontend, Reporting, etc.) |
| `prompts.md` | Wiederverwendbare Prompts für häufige Aufgaben |
| `AUDITOR_DASHBOARD.md` | Design-Spezifikation für das Prüfer-Dashboard |

## Schnellstart

### Claude Code CLI Setup

```bash
# Claude Code installieren
npm install -g @anthropic-ai/claude-code

# In Projektverzeichnis wechseln
cd /path/to/flowaudit-platform

# Claude Code starten
claude
```

### Basis-Nutzung

```bash
# Allgemeine Frage stellen
claude "Wo ist die Checklisten-Logik implementiert?"

# Feature implementieren
claude "Erstelle einen neuen API Endpoint für Prüfungsstatistiken"

# Bug fixen
claude "In der DashboardView wird die Anzahl der Prüfungen falsch berechnet"

# Code Review
claude "Überprüfe die letzte Änderung in tree_service.py"
```

### Mit Agents arbeiten

Die Agents in `agents.md` definieren spezialisierte Rollen:

- **@backend** - FastAPI, SQLAlchemy, Python
- **@frontend** - Vue 3, TypeScript, Tailwind
- **@checklists** - Prüflisten, Entscheidungsbäume
- **@reporting** - Berichte, Word-Export, Textbausteine
- **@statistics** - Stichproben, Hochrechnung
- **@system-audit** - Systemprüfungen, Kategorien 1-4
- **@api-client** - TypeScript API Client
- **@database** - PostgreSQL, Migrationen

```bash
# Agent-spezifische Aufgabe
claude "@backend Erstelle einen Service für die Fehlerquoten-Berechnung"

# Mehrere Agents kombinieren
claude "@statistics @frontend Implementiere eine Korrelationsanalyse-Visualisierung"
```

## Projekt-Struktur

```
flowaudit-platform/
├── packages/
│   ├── core/           # Framework-agnostische Kernlogik
│   ├── domain/         # Fachliche Module
│   ├── reporting/      # Berichtswesen
│   ├── documents/      # Dokumentenmanagement
│   └── adapters/       # Framework-Adapter
├── apps/
│   ├── backend/        # FastAPI Backend
│   ├── audit-portal/   # Prüfer-Portal (Vue)
│   ├── admin-portal/   # Admin-Portal (Vue)
│   └── group-portal/   # Konzern-Portal (Vue)
└── docs/
```

## Wichtige Konventionen

### TypeScript/Vue
- Composition API mit `<script setup>`
- Explizite Typen für Props und Emits
- Lokalisierung mit vue-i18n (DE/EN)
- Light/Dark Mode Support

### Python/FastAPI
- Type Hints für alle Funktionen
- Async/await für I/O
- Service-Layer Pattern
- Pydantic für Validierung

### Styling
- Tailwind CSS Utility Classes
- Design Tokens für Theme
- Mobile-first Responsive

### Datenbank
- JSONB für flexible Daten
- Alembic Migrationen (reversibel)
- Soft-Delete Pattern

## Häufige Aufgaben

### Neue Checkliste erstellen
1. ChecklistType in `packages/domain/checklists` erweitern
2. Template-Struktur definieren
3. Berichtsübernahme konfigurieren (full/summary_only/findings_only/none)
4. Frontend-Editor anpassen

### Neuen Berichtstyp hinzufügen
1. ReportType in `packages/reporting/report-engine` erweitern
2. Word-Template erstellen
3. Daten-Mapper implementieren
4. Textbausteine definieren

### Neue Statistik-Auswertung
1. Berechnungslogik in `packages/core/calculations`
2. Backend-Service für Datenabfrage
3. Frontend-Visualisierung
4. Export-Funktion

## Referenzen

- **Architektur-Plan**: `/docs/SYSTEM_ARCHITECTURE_PLAN.md`
- **API-Doku**: `http://localhost:8000/docs` (wenn Backend läuft)
- **Komponenten**: `/packages/adapters/vue-adapter/README.md`
