Führe Tests aus für: $ARGUMENTS

**Mögliche Argumente:**
- `all` - Alle Tests
- `backend` - Nur Backend-Tests
- `frontend` - Nur Frontend-Tests
- `development` - Nur Development-Modul Tests
- `<dateiname>` - Spezifische Testdatei

**Befehle:**
```bash
# Backend
pytest apps/backend/tests/ -v --tb=short

# Frontend
cd apps/frontend && pnpm test

# Spezifisch
pytest $ARGUMENTS -v
```

**Bei Fehlern:**
1. Analysiere die Fehlermeldung
2. Finde die betroffene Datei
3. Schlage Fix vor
4. Frage ob Fix angewendet werden soll
