# Implementiere Module Converter API

## WICHTIG: Autonome Ausführung

**Arbeite OHNE Rückfragen!** Führe alle Schritte selbstständig aus:
1. Lies die bestehenden Dateien um den Kontext zu verstehen
2. Implementiere alle beschriebenen Komponenten vollständig
3. Behebe Fehler eigenständig (Imports, Typen, Abhängigkeiten)
4. Registriere neue Router in der App
5. Führe die Validierung am Ende durch
6. Wenn Tests fehlschlagen: Analysiere und behebe die Fehler
7. Committe und pushe erst wenn alles funktioniert
8. Fahre dann mit `/implement-github` fort

**Keine Fragen stellen - einfach machen!**

---

## Aufgabe
Erstelle die FastAPI Endpoints für den Module Converter basierend auf `docs/PLAN_MODULE_CONVERSION_ENVIRONMENT.md`.

## API Endpoints

### Module Templates CRUD
```
POST   /api/v1/modules/                    # Neues Modul erstellen
GET    /api/v1/modules/                    # Module auflisten (mit Filtern)
GET    /api/v1/modules/{id}                # Modul-Details
PUT    /api/v1/modules/{id}                # Modul aktualisieren
DELETE /api/v1/modules/{id}                # Modul löschen (soft-delete)
```

### Conversion Workflow
```
POST   /api/v1/modules/convert             # Katalog hochladen und konvertieren
POST   /api/v1/modules/{id}/validate       # Struktur validieren
GET    /api/v1/modules/{id}/preview        # Preview der Konvertierung
POST   /api/v1/modules/{id}/finalize       # Konvertierung abschließen
```

### Versioning
```
POST   /api/v1/modules/{id}/versions       # Neue Version erstellen
GET    /api/v1/modules/{id}/versions       # Versionshistorie
GET    /api/v1/modules/{id}/diff/{v1}/{v2} # Versionen vergleichen
```

### Staging Pipeline
```
POST   /api/v1/modules/{id}/promote        # In nächste Stage befördern
POST   /api/v1/modules/{id}/reject         # Zurückweisen
GET    /api/v1/modules/{id}/stage-history  # Stage-Verlauf
```

## Zu erstellende Dateien

### 1. Router (`backend/app/api/endpoints/modules.py`)
```python
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.module import (
    ModuleCreate, ModuleUpdate, ModuleResponse,
    ModuleListResponse, ConversionRequest, ConversionResponse,
    VersionCreate, StagePromoteRequest
)
from app.services.module_service import ModuleService

router = APIRouter(prefix="/modules", tags=["modules"])

@router.post("/", response_model=ModuleResponse)
async def create_module(
    module: ModuleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = ModuleService(db)
    return await service.create_module(module, current_user)

@router.get("/", response_model=ModuleListResponse)
async def list_modules(
    layer: Optional[str] = None,
    konzern_id: Optional[int] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = ModuleService(db)
    return await service.list_modules(
        layer=layer, konzern_id=konzern_id, status=status,
        search=search, skip=skip, limit=limit, user=current_user
    )

@router.post("/convert", response_model=ConversionResponse)
async def convert_catalog(
    file: UploadFile = File(...),
    name: str = Query(...),
    description: Optional[str] = None,
    layer: str = Query("rahmen"),
    konzern_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Konvertiert einen hochgeladenen Katalog (PDF, DOCX, XLSX) in ein Prüfschema.
    """
    service = ModuleService(db)
    return await service.convert_catalog(
        file=file,
        name=name,
        description=description,
        layer=layer,
        konzern_id=konzern_id,
        user=current_user
    )

@router.get("/{module_id}", response_model=ModuleResponse)
async def get_module(
    module_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = ModuleService(db)
    module = await service.get_module(module_id, current_user)
    if not module:
        raise HTTPException(status_code=404, detail="Modul nicht gefunden")
    return module

@router.post("/{module_id}/validate")
async def validate_module(
    module_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = ModuleService(db)
    return await service.validate_module(module_id, current_user)

@router.post("/{module_id}/versions", response_model=ModuleResponse)
async def create_version(
    module_id: int,
    version_data: VersionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Erstellt eine neue Version eines bestehenden Moduls.
    version_type: patch | minor | major
    """
    service = ModuleService(db)
    return await service.create_version(
        module_id=module_id,
        version_type=version_data.version_type,
        change_description=version_data.change_description,
        user=current_user
    )

@router.get("/{module_id}/diff/{version1}/{version2}")
async def compare_versions(
    module_id: int,
    version1: str,  # z.B. "1.0.0"
    version2: str,  # z.B. "1.1.0"
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = ModuleService(db)
    return await service.compare_versions(module_id, version1, version2, current_user)

@router.post("/{module_id}/promote")
async def promote_module(
    module_id: int,
    promote_data: StagePromoteRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Befördert Modul in nächste Stage: DRAFT → DEV → TEST → FREIGABE → PROD
    """
    service = ModuleService(db)
    return await service.promote_module(
        module_id=module_id,
        comment=promote_data.comment,
        user=current_user
    )

@router.post("/{module_id}/reject")
async def reject_module(
    module_id: int,
    reject_data: StagePromoteRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Weist Modul zurück zur vorherigen Stage.
    """
    service = ModuleService(db)
    return await service.reject_module(
        module_id=module_id,
        reason=reject_data.comment,
        user=current_user
    )
```

### 2. Schemas (`backend/app/schemas/module.py`)
```python
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class VersionType(str, Enum):
    PATCH = "patch"
    MINOR = "minor"
    MAJOR = "major"

class ModuleStatus(str, Enum):
    DRAFT = "draft"
    DEV = "dev"
    TEST = "test"
    FREIGABE = "freigabe"
    PROD = "prod"
    ARCHIVED = "archived"

class ModuleCreate(BaseModel):
    name: str = Field(..., min_length=3, max_length=255)
    description: Optional[str] = None
    layer: str = Field("rahmen", pattern="^(rahmen|konzern|orga)$")
    konzern_id: Optional[int] = None
    organization_id: Optional[int] = None

class ModuleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    tree_structure: Optional[Dict[str, Any]] = None

class ModuleResponse(BaseModel):
    id: int
    name: str
    slug: str
    description: Optional[str]
    version: str  # "1.2.3"
    layer: str
    konzern_id: Optional[int]
    organization_id: Optional[int]
    status: ModuleStatus
    tree_structure: Optional[Dict[str, Any]]
    github_branch: Optional[str]
    github_pr_url: Optional[str]
    created_by_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ModuleListResponse(BaseModel):
    items: List[ModuleResponse]
    total: int
    skip: int
    limit: int

class ConversionRequest(BaseModel):
    name: str
    description: Optional[str] = None
    layer: str = "rahmen"
    konzern_id: Optional[int] = None

class ConversionResponse(BaseModel):
    module_id: int
    status: str
    tree_structure: Dict[str, Any]
    llm_provider_used: str
    tokens_used: int
    cost_eur: float
    validation_errors: List[str] = []

class VersionCreate(BaseModel):
    version_type: VersionType
    change_description: str = Field(..., min_length=10)

class StagePromoteRequest(BaseModel):
    comment: Optional[str] = None
```

### 3. Service (`backend/app/services/module_service.py`)
```python
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from fastapi import UploadFile

from app.models.module_template import ModuleTemplate, ModuleStatus
from app.models.module_conversion_log import ModuleConversionLog, ConversionStep
from app.models.user import User
from app.services.llm.llm_service import LLMService
from app.services.file_parser import FileParserService
from app.services.github_service import GitHubService

class ModuleService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.llm_service = LLMService(db)
        self.file_parser = FileParserService()
        self.github_service = GitHubService()

    async def convert_catalog(
        self,
        file: UploadFile,
        name: str,
        description: Optional[str],
        layer: str,
        konzern_id: Optional[int],
        user: User
    ):
        # 1. Datei parsen
        content = await self.file_parser.parse(file)

        # 2. LLM-Konvertierung
        context = {"name": name, "description": description}
        llm_response = await self.llm_service.convert_catalog(
            catalog_content=content,
            context=context,
            layer=layer,
            konzern_id=konzern_id
        )

        # 3. Modul erstellen
        module = ModuleTemplate(
            name=name,
            slug=self._slugify(name),
            description=description,
            layer=layer,
            konzern_id=konzern_id,
            tree_structure=self._parse_llm_response(llm_response.content),
            status=ModuleStatus.DRAFT,
            created_by_id=user.id
        )
        self.db.add(module)
        await self.db.commit()

        # 4. Log erstellen
        log = ModuleConversionLog(
            module_template_id=module.id,
            step=ConversionStep.LLM_CONVERSION,
            status="completed",
            llm_provider_used=llm_response.provider,
            llm_tokens_input=llm_response.tokens_input,
            llm_tokens_output=llm_response.tokens_output,
            llm_cost_eur=llm_response.cost_eur,
            created_by_id=user.id
        )
        self.db.add(log)
        await self.db.commit()

        return {
            "module_id": module.id,
            "status": "success",
            "tree_structure": module.tree_structure,
            "llm_provider_used": llm_response.provider,
            "tokens_used": llm_response.tokens_input + llm_response.tokens_output,
            "cost_eur": llm_response.cost_eur,
            "validation_errors": []
        }

    async def create_version(
        self,
        module_id: int,
        version_type: str,
        change_description: str,
        user: User
    ):
        # Hole bestehendes Modul
        module = await self.db.get(ModuleTemplate, module_id)
        if not module:
            raise ValueError("Modul nicht gefunden")

        # Berechne neue Version
        major, minor, patch = module.version_major, module.version_minor, module.version_patch
        if version_type == "major":
            major += 1
            minor = 0
            patch = 0
        elif version_type == "minor":
            minor += 1
            patch = 0
        else:  # patch
            patch += 1

        # Erstelle neue Version als Kopie
        new_module = ModuleTemplate(
            name=module.name,
            slug=module.slug,
            description=change_description,
            version_major=major,
            version_minor=minor,
            version_patch=patch,
            layer=module.layer,
            konzern_id=module.konzern_id,
            organization_id=module.organization_id,
            tree_structure=module.tree_structure.copy(),
            status=ModuleStatus.DRAFT,
            parent_module_id=module.id,
            created_by_id=user.id
        )

        # GitHub Branch erstellen
        branch_name = f"feature/module-{module.slug}-v{major}.{minor}.{patch}"
        await self.github_service.create_branch(branch_name)
        new_module.github_branch = branch_name

        self.db.add(new_module)
        await self.db.commit()
        await self.db.refresh(new_module)

        return new_module

    async def promote_module(self, module_id: int, comment: str, user: User):
        module = await self.db.get(ModuleTemplate, module_id)
        if not module:
            raise ValueError("Modul nicht gefunden")

        # Stage-Übergang
        stage_order = [ModuleStatus.DRAFT, ModuleStatus.DEV, ModuleStatus.TEST,
                       ModuleStatus.FREIGABE, ModuleStatus.PROD]
        current_index = stage_order.index(module.status)

        if current_index >= len(stage_order) - 1:
            raise ValueError("Modul ist bereits in PROD")

        module.status = stage_order[current_index + 1]
        await self.db.commit()

        return {"status": module.status, "message": f"Modul zu {module.status.value} befördert"}
```

## Schritte

1. Erstelle Schemas in `backend/app/schemas/module.py`
2. Erstelle Service in `backend/app/services/module_service.py`
3. Erstelle Router in `backend/app/api/endpoints/modules.py`
4. Registriere Router in `backend/app/api/router.py`
5. Erstelle FileParserService für PDF/DOCX/XLSX
6. Schreibe Integration Tests

## Validierung
```bash
cd backend
pytest tests/test_module_api.py -v
# Dann manuell testen:
curl -X POST http://localhost:8000/api/v1/modules/convert \
  -F "file=@test.pdf" -F "name=Test Modul"
```

## Referenzen
- Planung: `docs/PLAN_MODULE_CONVERSION_ENVIRONMENT.md`
- Bestehende APIs: `backend/app/api/endpoints/`
