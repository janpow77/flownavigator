Erstelle den API-Endpoint "$ARGUMENTS" für das Development-Modul.

**Datei:** `apps/backend/app/api/development.py`

**Schritte:**
1. Prüfe existierende Endpoints als Referenz:
   - `apps/backend/app/api/modules.py`
   - `apps/backend/app/api/document_box.py`
2. Erstelle den Endpoint mit:
   - Korrektem HTTP-Verb (GET/POST/PUT/DELETE)
   - Pydantic Request/Response Schemas in `app/schemas/development.py`
   - Authentifizierung via `get_current_user`
   - Tenant-Filterung
   - Audit-Logging
3. Registriere in `apps/backend/app/api/__init__.py` falls nötig
4. Erstelle Test in `apps/backend/tests/api/test_development.py`

**Pattern:**
```python
@router.post("/sessions", response_model=SessionResponse)
async def create_session(
    data: SessionCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> SessionResponse:
    service = SessionService(db)
    session = await service.create_session(data, user.tenant_id)
    return session
```
