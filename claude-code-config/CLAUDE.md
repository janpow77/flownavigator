# CLAUDE.md - FlowAudit Platform

> Konfiguration für Claude Code CLI zur Entwicklung der FlowAudit Platform

## Projektübersicht

FlowAudit ist ein modulares Prüfbehörden-Management-System für EU-Strukturfonds mit:
- Vorhabenprüfungen, Systemprüfungen, Rechnungslegungsprüfungen
- Konzernstruktur mit hierarchischer Berichterstattung
- Automatisierte Berichterstellung mit Textbausteinen
- Statistische Auswertungen (Hochrechnung, Restfehlerquote)
- Jahreskontrollbericht (JKB) Generierung

## Technologie-Stack

### Backend
- **Framework**: Python 3.11 + FastAPI
- **ORM**: SQLAlchemy 2.0
- **Datenbank**: PostgreSQL 15 mit JSONB
- **Migrationen**: Alembic
- **Tests**: pytest

### Frontend
- **Framework**: Vue 3 + TypeScript
- **State**: Pinia
- **Styling**: Tailwind CSS
- **i18n**: vue-i18n (DE/EN)
- **Tests**: Vitest + Cypress

### Monorepo
- **Manager**: pnpm workspaces
- **Build**: Turborepo
- **Packages**: tsup

## Verzeichnisstruktur

```
flowaudit-platform/
├── packages/
│   ├── core/                     # Framework-agnostische Kernlogik
│   │   ├── common/               # Types, Utils, Konstanten
│   │   ├── validation/           # Validierungslogik
│   │   ├── calculations/         # Fehlerquoten, Hochrechnung
│   │   └── permissions/          # RBAC/ABAC
│   │
│   ├── domain/                   # Fachliche Module
│   │   ├── fiscal-year/
│   │   ├── master-data/
│   │   ├── operations/
│   │   ├── checklists/
│   │   ├── audit-cases/
│   │   ├── findings/
│   │   ├── system-audits/
│   │   ├── accounts/
│   │   ├── sampling/
│   │   └── population/
│   │
│   ├── reporting/
│   │   ├── report-engine/
│   │   ├── templates/
│   │   ├── text-modules/
│   │   ├── jkb/
│   │   └── analytics/
│   │
│   ├── documents/
│   │   ├── file-manager/
│   │   ├── word-export/
│   │   ├── excel-import/
│   │   └── flow-invoice/
│   │
│   └── adapters/
│       ├── vue-adapter/
│       └── api-client/
│
├── apps/
│   ├── backend/                  # FastAPI Backend
│   ├── audit-portal/             # Prüfer-Portal (Vue)
│   ├── admin-portal/             # Admin-Portal (Vue)
│   └── group-portal/             # Konzern-Portal (Vue)
│
└── docs/
```

## Entwicklungsbefehle

```bash
# Monorepo
pnpm install                      # Dependencies installieren
pnpm build                        # Alle Packages bauen
pnpm dev                          # Entwicklungsserver starten
pnpm test                         # Alle Tests ausführen
pnpm lint                         # Linting

# Backend
cd apps/backend
source venv/bin/activate
uvicorn app.main:app --reload     # Dev-Server
pytest                            # Tests
alembic upgrade head              # Migrationen

# Frontend (Audit-Portal)
cd apps/audit-portal
pnpm dev                          # Dev-Server (Port 5173)
pnpm build                        # Production Build
```

## Code-Konventionen

### TypeScript
- Strict mode aktiviert
- Explizite Typen für Funktionsparameter und Rückgabewerte
- Interfaces bevorzugt vor Type Aliases
- `readonly` für unveränderliche Properties

### Vue
- Composition API mit `<script setup>`
- Props mit defineProps und TypeScript
- Emits mit defineEmits
- Composables für wiederverwendbare Logik

### Python
- Type Hints für alle Funktionen
- Pydantic für Validierung
- async/await für I/O-Operationen
- Docstrings für öffentliche Funktionen

### Styling
- Tailwind CSS Utility Classes
- CSS Custom Properties für Theme
- Mobile-first Responsive Design
- Dark Mode Support

## Datenmodell-Hinweise

### Dynamische Felder
Vorhaben-Stammdaten und Beleglisten-Spalten werden über `FieldSchema` konfiguriert:
- Felder werden in der Administration definiert
- Daten werden als JSONB gespeichert
- Validierung erfolgt zur Laufzeit

### Prüfteam-Hierarchie
```
Prüfbehördenleiter (authority_head)
       ↑
Prüfteamleiter (team_leader)
       ↑
┌──────┴──────┐
1. Prüfer     2. Prüfer
(primary)     (secondary)
```

### Checklisten-Typen
| Typ | Beschreibung | Berichtsübernahme |
|-----|--------------|-------------------|
| main | Hauptcheckliste | Vollständig |
| procurement | Vergabeprüfung | Nur Ergebnistabelle |
| subsidy | Beihilfeprüfung | Nur Ergebnis |
| eligibility | Förderfähigkeit | Konfigurierbar |
| system | Systemprüfung | Vollständig |

### Bewertungskategorien (Systemprüfung)
- **Kategorie 1**: System funktioniert gut
- **Kategorie 2**: Verbesserungen nötig
- **Kategorie 3**: Erhebliche Mängel
- **Kategorie 4**: System funktioniert nicht

## UI/UX Richtlinien

### Design-Prinzipien
- **Modern & Clean**: Viel Weißraum, klare Typografie
- **NICHT wie SAP**: Keine überladenen Screens
- **Card-basiertes Layout**: Übersichtliche Karten
- **Intuitive Navigation**: Klare Hierarchie

### Farbschema
```typescript
// Primärfarbe
primary: '#3b82f6'

// Status
success: '#22c55e'
warning: '#f59e0b'
error: '#ef4444'

// Kategorien (Systemprüfung)
category1: '#22c55e' // Grün
category2: '#eab308' // Gelb
category3: '#f97316' // Orange
category4: '#ef4444' // Rot
```

### Komponenten-Bibliothek
- Design Tokens in `@flowaudit/ui`
- Basis-Komponenten in `@flowaudit/vue-adapter`
- Icons: Lucide Icons

## Wichtige Architektur-Entscheidungen

1. **Monorepo**: Gemeinsame Packages für alle Apps
2. **JSONB**: Flexible Datenstrukturen für Checklisten und Formulare
3. **Adapter-Pattern**: Framework-agnostische Kernlogik
4. **Textbausteine**: Regelbasierte Berichtsgenerierung
5. **Versioning**: Versionierung für Checklisten, Prüfungsfälle, Berichte

## Referenzen

- Architektur-Dokument: `/docs/SYSTEM_ARCHITECTURE_PLAN.md`
- API-Dokumentation: `/docs` (Swagger/ReDoc wenn Backend läuft)
- Komponenten-Übersicht: `/packages/adapters/vue-adapter/README.md`
