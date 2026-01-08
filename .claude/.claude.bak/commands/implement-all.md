# Module Converter - Komplette Implementation

## WICHTIG: Vollständig autonome Ausführung

**Arbeite KOMPLETT OHNE Rückfragen!** Dies ist der Master-Command für die gesamte Implementation.

### Anweisungen für Claude:

1. **Führe ALLE Schritte nacheinander aus** - ohne Pause, ohne Fragen
2. **Bei Fehlern**: Analysiere, behebe, weitermachen
3. **Bei fehlenden Infos**: Triff sinnvolle Entscheidungen basierend auf dem Kontext
4. **Committe nach jedem Modul** mit aussagekräftiger Message
5. **Stoppe nur** wenn ein kritischer Fehler nicht behebbar ist

---

## Ausführungsreihenfolge

Führe diese Commands nacheinander aus:

```
1. /implement-models       → Backend Models + Migrations
2. /implement-llm-service  → LLM Provider + Fallback
3. /implement-module-api   → API Endpoints
4. /implement-github       → GitHub Integration
5. /implement-wizard       → Frontend Wizard
6. /implement-staging      → Staging Pipeline
7. /implement-tests        → Test Suite
```

---

## Schnellstart (wenn du diesen Command ausführst)

Starte direkt mit der Implementation:

### Phase 1: Backend Foundation
```bash
# 1. Models erstellen
# Lies docs/PLAN_MODULE_CONVERSION_ENVIRONMENT.md für Kontext
# Erstelle: konzern.py, llm_configuration.py, module_template.py, module_conversion_log.py
# Dann: alembic revision --autogenerate -m "Add module converter models"
# Dann: alembic upgrade head
```

### Phase 2: Services
```bash
# 2. LLM Service
# Erstelle: backend/app/services/llm/ mit allen Providern
# 3. Module Service
# Erstelle: backend/app/services/module_service.py
# 4. GitHub Service
# Erstelle: backend/app/services/github_service.py
# 5. Staging Service
# Erstelle: backend/app/services/staging_service.py
```

### Phase 3: API
```bash
# 6. API Endpoints
# Erstelle: backend/app/api/endpoints/modules.py
# Erstelle: backend/app/api/endpoints/github.py
# Registriere in router.py
```

### Phase 4: Frontend
```bash
# 7. Wizard erstellen
# Erstelle: frontend/src/views/ModuleConverter/
# Alle 5 Steps implementieren
# Store und API Services erstellen
# Routes registrieren
```

### Phase 5: Tests & Finish
```bash
# 8. Tests schreiben
# Alle test_*.py Dateien
# pytest ausführen bis grün
```

---

## Erfolgskriterien

Bevor du "fertig" meldest, prüfe:

- [ ] `alembic upgrade head` läuft ohne Fehler
- [ ] `pytest` zeigt alle Tests grün
- [ ] `npm run build` im Frontend erfolgreich
- [ ] `npm run lint` ohne Fehler
- [ ] Alle Dateien committet und gepusht

---

## Bei Problemen

1. **Import-Fehler**: Prüfe `__init__.py` Dateien
2. **Type-Fehler**: Prüfe Pydantic Schemas
3. **DB-Fehler**: Prüfe Migrations und Model-Beziehungen
4. **Frontend-Fehler**: Prüfe Vue-Komponenten-Syntax und Imports

**Löse Probleme selbstständig - frag nicht nach!**

---

## Abschlussmeldung

Wenn alles fertig ist, gib aus:

```
╔════════════════════════════════════════════════════════════╗
║     MODULE CONVERTER - IMPLEMENTATION ABGESCHLOSSEN        ║
╠════════════════════════════════════════════════════════════╣
║                                                            ║
║  Backend Models:     X erstellt                            ║
║  API Endpoints:      X erstellt                            ║
║  Services:           X erstellt                            ║
║  Frontend Views:     X erstellt                            ║
║  Test Coverage:      XX%                                   ║
║                                                            ║
║  Commits:            X                                     ║
║  Branch:             claude/module-conversion-...          ║
║                                                            ║
╚════════════════════════════════════════════════════════════╝
```
