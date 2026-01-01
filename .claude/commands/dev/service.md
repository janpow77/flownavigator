Erstelle den Service "$ARGUMENTS" nach dem Development-Modul Konzept.

**Pfad:** `apps/backend/app/services/development/$ARGUMENTS.py`

**Schritte:**
1. Lies das Konzept in `docs/05_KONZEPT_DEVELOPMENT_MODUL.md`
2. Prüfe existierende Services als Referenz:
   - `apps/backend/app/services/module_service.py`
   - `apps/backend/app/services/llm/`
3. Erstelle den Service mit:
   - Typ-Annotationen (Python 3.12 Style)
   - Docstrings
   - Async/await wo nötig
   - Dependency Injection via __init__
4. Erstelle Tests in `apps/backend/tests/services/development/test_$ARGUMENTS.py`
5. Führe Tests aus: `pytest apps/backend/tests/services/development/ -v`

**Patterns:**
```python
from sqlalchemy.ext.asyncio import AsyncSession

class MyService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def do_something(self, param: str) -> Result:
        ...
```
