Führe die komplette Test-Suite systematisch aus und analysiere Ergebnisse.

**Argumente:** $ARGUMENTS (optional: `backend`, `frontend`, `coverage`, `quick`, oder Testdatei)

---

## Schritt 1: Tests ausführen

### Backend Tests (Docker)
```bash
docker compose exec backend python -m pytest tests/ -v --tb=short --cov=app --cov-report=term-missing
```

### Frontend Tests (falls vorhanden)
```bash
cd apps/frontend && pnpm test 2>/dev/null || echo "Keine Frontend-Tests konfiguriert"
```

---

## Schritt 2: Ergebnisse analysieren

Nach Testausführung:

1. **Zähle Ergebnisse:**
   - Passed Tests
   - Failed Tests
   - Skipped/XFail Tests

2. **Coverage prüfen:**
   - Gesamt-Coverage (Ziel: >60%)
   - Niedrigste Module identifizieren
   - Kritische ungetestete Pfade

3. **Bei Fehlern:**
   - Fehlerursache identifizieren
   - Betroffene Datei und Zeile
   - Mögliche Fixes vorschlagen

---

## Schritt 3: Report erstellen

Erstelle eine Zusammenfassung:

```
## Test Report

| Metrik | Wert |
|--------|------|
| Tests gesamt | X |
| Passed | X |
| Failed | X |
| XFail | X |
| Coverage | X% |

### Coverage nach Bereich
- Models: X%
- Schemas: X%
- API: X%
- Services: X%

### Probleme
- [Liste aller Fehler mit Datei:Zeile]

### Empfehlungen
- [Vorschläge für mehr Coverage]
```

---

## Verfügbare Testdateien

| Datei | Beschreibung | Tests |
|-------|--------------|-------|
| `test_api.py` | Basis API Tests | ~10 |
| `test_audit_cases_api.py` | Audit Cases CRUD | 29 |
| `test_checklists_api.py` | Checklisten API | 24 |
| `test_dashboard_api.py` | Dashboard Widgets | 24 |
| `test_history_api.py` | History/Timeline | 28 |
| `test_modules_api.py` | Module Converter | 36 |
| `test_profiles_api.py` | Profile Management | 25 |
| `test_vendor.py` | Vendor/Customer | 40 |

**Gesamt: 216+ Tests**

---

## Quick Commands

```bash
# Alle Tests
docker compose exec backend python -m pytest tests/ -v

# Nur ein Testfile
docker compose exec backend python -m pytest tests/test_modules_api.py -v

# Mit Coverage
docker compose exec backend python -m pytest tests/ --cov=app --cov-report=html

# Nur Failed Tests wiederholen
docker compose exec backend python -m pytest tests/ --lf -v

# Schneller Durchlauf (ohne Coverage)
docker compose exec backend python -m pytest tests/ -q
```
