Erstelle das SQLAlchemy Model "$ARGUMENTS" für das Development-Modul.

**Pfad:** `apps/backend/app/models/development.py`

**Schritte:**
1. Lies das Konzept in `docs/05_KONZEPT_DEVELOPMENT_MODUL.md`
2. Prüfe existierende Models als Referenz:
   - `apps/backend/app/models/tenant.py`
   - `apps/backend/app/models/user.py`
3. Erstelle das Model mit:
   - SQLAlchemy 2.0 Style (Mapped, mapped_column)
   - UUID als Primary Key
   - Timestamps (created_at, updated_at)
   - Tenant-Beziehung
   - Typ-Annotationen
4. Erstelle Alembic Migration:
   ```bash
   alembic revision --autogenerate -m "add $ARGUMENTS"
   alembic upgrade head
   ```

**Pattern:**
```python
from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.base import TimestampMixin

class MyModel(Base, TimestampMixin):
    __tablename__ = "my_models"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"))
    name: Mapped[str] = mapped_column(String(255))
```
