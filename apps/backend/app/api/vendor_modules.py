"""Vendor Modules API endpoints for Layer 0."""

from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.vendor import VendorUser
from app.models.customer import Customer
from app.models.module import (
    Module,
    ModuleStatus,
    ModuleDeployment,
    DeploymentStatus,
    ReleaseNote,
)
from app.api.vendor import (
    get_current_vendor_user,
    require_vendor_admin,
    require_vendor_developer,
    require_vendor_qa,
)
from app.schemas.module import (
    ModuleCreate,
    ModuleUpdate,
    ModuleResponse,
    ModuleListResponse,
    ModuleDeploymentResponse,
    ModuleDeploymentListResponse,
    ReleaseNoteCreate,
    ReleaseNoteResponse,
    ReleaseNoteListResponse,
    ModuleWithDeploymentsResponse,
)

router = APIRouter()


# Module CRUD
@router.get("", response_model=ModuleListResponse)
async def list_modules(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status_filter: Optional[ModuleStatus] = Query(None, alias="status"),
    current_user: VendorUser = Depends(get_current_vendor_user),
    db: AsyncSession = Depends(get_db),
) -> ModuleListResponse:
    """List all modules."""
    query = select(Module)

    if status_filter:
        query = query.where(Module.status == status_filter)

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    # Get modules with pagination
    query = query.offset(skip).limit(limit).order_by(Module.created_at.desc())
    result = await db.execute(query)
    modules = result.scalars().all()

    return ModuleListResponse(
        modules=[ModuleResponse.model_validate(m) for m in modules],
        total=total,
    )


@router.post("", response_model=ModuleResponse, status_code=status.HTTP_201_CREATED)
async def create_module(
    data: ModuleCreate,
    current_user: VendorUser = Depends(require_vendor_developer),
    db: AsyncSession = Depends(get_db),
) -> ModuleResponse:
    """Create a new module (vendor_developer only)."""
    module = Module(
        id=str(uuid4()),
        name=data.name,
        version=data.version,
        description=data.description,
        status=ModuleStatus.development,
        developed_by=current_user.id,
        dependencies=data.dependencies,
        min_system_version=data.min_system_version,
        feature_flags=data.feature_flags,
    )

    db.add(module)
    await db.commit()
    await db.refresh(module)

    return ModuleResponse.model_validate(module)


@router.get("/{module_id}", response_model=ModuleWithDeploymentsResponse)
async def get_module(
    module_id: str,
    current_user: VendorUser = Depends(get_current_vendor_user),
    db: AsyncSession = Depends(get_db),
) -> ModuleWithDeploymentsResponse:
    """Get module details with deployments."""
    result = await db.execute(
        select(Module)
        .options(selectinload(Module.deployments), selectinload(Module.release_notes))
        .where(Module.id == module_id)
    )
    module = result.scalar_one_or_none()

    if not module:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Modul nicht gefunden",
        )

    return ModuleWithDeploymentsResponse(
        **ModuleResponse.model_validate(module).model_dump(),
        deployments=[
            ModuleDeploymentResponse.model_validate(d) for d in module.deployments
        ],
        release_notes=[
            ReleaseNoteResponse.model_validate(r) for r in module.release_notes
        ],
    )


@router.put("/{module_id}", response_model=ModuleResponse)
async def update_module(
    module_id: str,
    data: ModuleUpdate,
    current_user: VendorUser = Depends(require_vendor_developer),
    db: AsyncSession = Depends(get_db),
) -> ModuleResponse:
    """Update module (vendor_developer only)."""
    result = await db.execute(select(Module).where(Module.id == module_id))
    module = result.scalar_one_or_none()

    if not module:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Modul nicht gefunden",
        )

    # Cannot update released/deprecated modules except status change
    if module.status in [ModuleStatus.released, ModuleStatus.deprecated]:
        if data.status is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Released/Deprecated Module können nur den Status ändern",
            )

    update_data = data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(module, field, value)

    await db.commit()
    await db.refresh(module)

    return ModuleResponse.model_validate(module)


# Module Release
@router.post("/{module_id}/release", response_model=ModuleResponse)
async def release_module(
    module_id: str,
    release_note: Optional[ReleaseNoteCreate] = None,
    current_user: VendorUser = Depends(require_vendor_qa),
    db: AsyncSession = Depends(get_db),
) -> ModuleResponse:
    """Release a module (vendor_qa only)."""
    result = await db.execute(select(Module).where(Module.id == module_id))
    module = result.scalar_one_or_none()

    if not module:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Modul nicht gefunden",
        )

    if module.status == ModuleStatus.released:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Modul ist bereits released",
        )

    if module.status == ModuleStatus.deprecated:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Deprecated Module können nicht released werden",
        )

    # Update module status
    module.status = ModuleStatus.released
    module.released_at = datetime.now(timezone.utc)

    # Create release note if provided
    if release_note:
        note = ReleaseNote(
            id=str(uuid4()),
            module_id=module.id,
            version=release_note.version or module.version,
            title=release_note.title,
            changes=release_note.changes,
            breaking_changes=release_note.breaking_changes,
            published_at=datetime.now(timezone.utc),
        )
        db.add(note)

    await db.commit()
    await db.refresh(module)

    return ModuleResponse.model_validate(module)


# Module Deployments
@router.get("/{module_id}/deployments", response_model=ModuleDeploymentListResponse)
async def list_module_deployments(
    module_id: str,
    current_user: VendorUser = Depends(get_current_vendor_user),
    db: AsyncSession = Depends(get_db),
) -> ModuleDeploymentListResponse:
    """List all deployments for a module."""
    result = await db.execute(select(Module).where(Module.id == module_id))
    if not result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Modul nicht gefunden",
        )

    result = await db.execute(
        select(ModuleDeployment)
        .where(ModuleDeployment.module_id == module_id)
        .order_by(ModuleDeployment.created_at.desc())
    )
    deployments = result.scalars().all()

    return ModuleDeploymentListResponse(
        deployments=[ModuleDeploymentResponse.model_validate(d) for d in deployments],
        total=len(deployments),
    )


@router.post(
    "/{module_id}/deploy/{customer_id}", response_model=ModuleDeploymentResponse
)
async def deploy_module(
    module_id: str,
    customer_id: str,
    current_user: VendorUser = Depends(require_vendor_admin),
    db: AsyncSession = Depends(get_db),
) -> ModuleDeploymentResponse:
    """Deploy a module to a customer (vendor_admin only)."""
    # Check module exists and is released
    result = await db.execute(select(Module).where(Module.id == module_id))
    module = result.scalar_one_or_none()

    if not module:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Modul nicht gefunden",
        )

    if module.status != ModuleStatus.released:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nur released Module können deployed werden",
        )

    # Check customer exists and belongs to vendor
    result = await db.execute(
        select(Customer).where(
            Customer.id == customer_id,
            Customer.vendor_id == current_user.vendor_id,
        )
    )
    customer = result.scalar_one_or_none()

    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Kunde nicht gefunden",
        )

    # Check for existing deployment
    result = await db.execute(
        select(ModuleDeployment).where(
            ModuleDeployment.module_id == module_id,
            ModuleDeployment.customer_id == customer_id,
            ModuleDeployment.status.in_(
                [
                    DeploymentStatus.pending,
                    DeploymentStatus.deploying,
                    DeploymentStatus.deployed,
                ]
            ),
        )
    )
    existing = result.scalar_one_or_none()

    previous_version = None
    if existing:
        if existing.status == DeploymentStatus.deployed:
            previous_version = existing.deployed_version
            existing.status = DeploymentStatus.rolled_back
        elif existing.status in [DeploymentStatus.pending, DeploymentStatus.deploying]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Deployment läuft bereits",
            )

    # Create new deployment
    deployment = ModuleDeployment(
        id=str(uuid4()),
        module_id=module_id,
        customer_id=customer_id,
        status=DeploymentStatus.pending,
        deployed_version=module.version,
        previous_version=previous_version,
        deployed_by=current_user.id,
    )

    db.add(deployment)

    # Simulate deployment (in real scenario, this would be async)
    deployment.status = DeploymentStatus.deployed
    deployment.deployed_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(deployment)

    return ModuleDeploymentResponse.model_validate(deployment)


@router.post(
    "/{module_id}/rollback/{customer_id}", response_model=ModuleDeploymentResponse
)
async def rollback_module(
    module_id: str,
    customer_id: str,
    current_user: VendorUser = Depends(require_vendor_admin),
    db: AsyncSession = Depends(get_db),
) -> ModuleDeploymentResponse:
    """Rollback a module deployment (vendor_admin only)."""
    # Find current deployment
    result = await db.execute(
        select(ModuleDeployment).where(
            ModuleDeployment.module_id == module_id,
            ModuleDeployment.customer_id == customer_id,
            ModuleDeployment.status == DeploymentStatus.deployed,
        )
    )
    deployment = result.scalar_one_or_none()

    if not deployment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Kein aktives Deployment gefunden",
        )

    if not deployment.previous_version:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Keine vorherige Version für Rollback vorhanden",
        )

    deployment.status = DeploymentStatus.rolled_back

    await db.commit()
    await db.refresh(deployment)

    return ModuleDeploymentResponse.model_validate(deployment)


# Release Notes
@router.get("/{module_id}/release-notes", response_model=ReleaseNoteListResponse)
async def list_release_notes(
    module_id: str,
    current_user: VendorUser = Depends(get_current_vendor_user),
    db: AsyncSession = Depends(get_db),
) -> ReleaseNoteListResponse:
    """List all release notes for a module."""
    result = await db.execute(select(Module).where(Module.id == module_id))
    if not result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Modul nicht gefunden",
        )

    result = await db.execute(
        select(ReleaseNote)
        .where(ReleaseNote.module_id == module_id)
        .order_by(ReleaseNote.published_at.desc())
    )
    notes = result.scalars().all()

    return ReleaseNoteListResponse(
        release_notes=[ReleaseNoteResponse.model_validate(n) for n in notes],
        total=len(notes),
    )


@router.post(
    "/{module_id}/release-notes",
    response_model=ReleaseNoteResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_release_note(
    module_id: str,
    data: ReleaseNoteCreate,
    current_user: VendorUser = Depends(require_vendor_qa),
    db: AsyncSession = Depends(get_db),
) -> ReleaseNoteResponse:
    """Create a release note for a module (vendor_qa only)."""
    result = await db.execute(select(Module).where(Module.id == module_id))
    module = result.scalar_one_or_none()

    if not module:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Modul nicht gefunden",
        )

    note = ReleaseNote(
        id=str(uuid4()),
        module_id=module_id,
        version=data.version,
        title=data.title,
        changes=data.changes,
        breaking_changes=data.breaking_changes,
        published_at=datetime.now(timezone.utc),
    )

    db.add(note)
    await db.commit()
    await db.refresh(note)

    return ReleaseNoteResponse.model_validate(note)
