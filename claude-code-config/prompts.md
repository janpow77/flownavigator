# Claude Code Prompts für FlowAudit

> Wiederverwendbare Prompts für häufige Entwicklungsaufgaben

## Feature-Entwicklung

### Neues API-Feature

```
Erstelle einen neuen API Endpoint für [FEATURE].

Anforderungen:
- FastAPI Router in app/api/
- Service-Layer in app/services/
- Pydantic Schemas in app/schemas/
- SQLAlchemy Models falls nötig
- Unit Tests in tests/

Konventionen beachten:
- Async/await für alle DB-Operationen
- Type Hints für alle Funktionen
- Docstrings für öffentliche Funktionen
- Fehlerbehandlung mit HTTPException
```

### Neue Vue-Komponente

```
Erstelle eine Vue 3 Komponente für [KOMPONENTE].

Anforderungen:
- Composition API mit <script setup>
- TypeScript mit defineProps/defineEmits
- Tailwind CSS für Styling
- Light/Dark Mode Support
- Lokalisierung mit vue-i18n (DE/EN)

Struktur:
- components/[category]/[Name].vue
- Composable falls wiederverwendbare Logik: composables/use[Name].ts
```

### Neue Pinia Store

```
Erstelle einen Pinia Store für [MODUL].

Anforderungen:
- Setup Store Syntax (Composition API Style)
- TypeScript Typen für State
- Computed Properties für abgeleitete Daten
- Actions für API-Aufrufe und Mutationen
- Error Handling mit Notification Store

Struktur:
- stores/[name].ts
- Typen in types/[name].ts
```

## Datenbank

### Neue Migration

```
Erstelle eine Alembic Migration für:
[BESCHREIBUNG DER ÄNDERUNGEN]

Anforderungen:
- Reversible upgrade() und downgrade()
- Keine Breaking Changes in Production
- Indices für häufige Queries
- JSONB für flexible Datenstrukturen
```

### JSONB Schema

```
Entwerfe ein JSONB Schema für [DATENSTRUKTUR].

Anforderungen:
- TypeScript Interface
- SQLAlchemy Model mit JSONB Column
- Pydantic Schema für Validierung
- Beispieldaten
```

## Checklisten

### Neuer Checklisten-Typ

```
Erstelle einen neuen Checklisten-Typ: [TYP]

Anforderungen:
- ChecklistType Enum erweitern
- ChecklistReportConfig definieren (full/summary_only/findings_only/none)
- Template-Struktur
- Berichtsübernahme-Logik
```

### Textbaustein-Trigger

```
Erstelle Textbaustein-Trigger für [CHECKLISTE].

Anforderungen:
- TriggerCondition Interface
- Platzhalter-Definition
- Formatierte Ausgabe (bold, lists, tables)
- Beispiel-Textbausteine
```

## Reporting

### Neuer Berichtstyp

```
Erstelle einen neuen Berichtstyp: [TYP]

Anforderungen:
- ReportType Enum erweitern
- Template-Struktur (Word)
- Daten-Aggregation
- Formatierung (Überschriften, Tabellen, Aufzählungen)
- Inhaltsverzeichnis
```

### JKB-Abschnitt

```
Erweitere den Jahreskontrollbericht um: [ABSCHNITT]

Anforderungen:
- JKBSection Interface
- Daten-Extraktion aus Prüfungen
- Aggregation auf Konzernebene
- Formatierte Ausgabe
```

## Statistik

### Neue Auswertung

```
Implementiere die statistische Auswertung: [AUSWERTUNG]

Anforderungen:
- Berechnungslogik in @flowaudit/calculations
- Backend-Service für Datenabfrage
- Frontend-Visualisierung (Chart/Tabelle)
- Export-Funktion (Excel/CSV)
```

### Hochrechnungsmethode

```
Implementiere die Hochrechnungsmethode: [METHODE]

Anforderungen:
- ProjectionMethod Enum erweitern
- Berechnungslogik mit Dokumentation
- Konfidenzintervall-Berechnung
- Unit Tests mit Testdaten
```

## UI/UX

### Dark Mode Komponente

```
Stelle sicher, dass [KOMPONENTE] Dark Mode unterstützt.

Prüfpunkte:
- Tailwind dark: Klassen verwenden
- Design Tokens statt hardcoded Farben
- Kontrast-Verhältnis prüfen (WCAG AA)
- Hover/Focus States für beide Modi
```

### Responsive Design

```
Mache [KOMPONENTE] responsive.

Breakpoints:
- sm: 640px
- md: 768px
- lg: 1024px
- xl: 1280px

Anforderungen:
- Mobile-first Ansatz
- Tailwind Breakpoint-Klassen
- Keine horizontalen Scrollbars
- Touch-freundliche Targets (min. 44px)
```

## Testing

### Unit Tests

```
Schreibe Unit Tests für [MODUL].

Anforderungen:
- pytest für Backend
- Vitest für Frontend
- Mocking von Dependencies
- Edge Cases abdecken
- 80%+ Coverage
```

### Integration Tests

```
Schreibe Integration Tests für [FEATURE].

Backend (pytest):
- TestClient für API-Tests
- Fixtures für Testdaten
- Transaktions-Rollback nach jedem Test

Frontend (Cypress):
- E2E User Flows
- Intercepts für API-Mocking
- Visual Regression falls nötig
```

## Debugging

### Performance-Analyse

```
Analysiere die Performance von [BEREICH].

Backend:
- EXPLAIN ANALYZE für Queries
- Profiling mit cProfile
- N+1 Query Detection

Frontend:
- Vue DevTools Performance Tab
- Network Tab Analyse
- Bundle Size Check
```

### Fehler-Diagnose

```
Debugge den Fehler: [FEHLERBESCHREIBUNG]

Schritte:
1. Reproduzierbare Schritte identifizieren
2. Logs analysieren
3. Root Cause finden
4. Fix implementieren
5. Test schreiben um Regression zu verhindern
```

## Code Review

### Pre-Commit Checklist

```
Prüfe vor dem Commit:

Backend:
☐ Type Hints vollständig
☐ Docstrings für öffentliche Funktionen
☐ Tests geschrieben/aktualisiert
☐ Keine hardcoded Secrets
☐ Alembic Migration falls DB-Änderung

Frontend:
☐ TypeScript Typen vollständig
☐ Lokalisierung (DE/EN)
☐ Dark Mode Support
☐ Responsive Design
☐ Accessibility (aria-labels, keyboard nav)

Allgemein:
☐ Keine console.log/print Statements
☐ Keine TODO Kommentare ohne Issue
☐ Dokumentation aktualisiert
```

## Architektur

### Package-Entwurf

```
Entwerfe das npm Package @flowaudit/[NAME].

Anforderungen:
- Framework-agnostisch (kein Vue/React direkt)
- TypeScript mit striktem Mode
- Exports in index.ts
- README.md mit Beispielen
- Unit Tests
```

### Konzern-Feature

```
Implementiere [FEATURE] für die Konzernansicht.

Anforderungen:
- Mandantentrennung (tenant_id)
- Rollup/Aggregation über Töchter
- Berechtigungsprüfung (Konzern-Sicht erlaubt?)
- Performance für große Datenmengen
```
