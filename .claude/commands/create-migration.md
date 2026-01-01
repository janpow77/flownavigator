# Alembic Migration erstellen

Erstelle eine neue Alembic-Migration für $ARGUMENTS.

## Anweisungen

1. Prüfe aktuelle Models in `apps/backend/app/models/`
2. Erstelle Migration mit beschreibendem Namen:
   ```bash
   cd apps/backend && alembic revision --autogenerate -m "$ARGUMENTS"
   ```
3. Prüfe die generierte Migration auf Korrektheit
4. Wende die Migration an:
   ```bash
   alembic upgrade head
   ```

## Beispiel

`/create-migration "add vendor and customer tables"` - Erstellt Migration für Vendor-Tabellen
