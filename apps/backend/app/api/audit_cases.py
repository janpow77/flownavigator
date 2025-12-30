"""Audit Cases API Endpoints."""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.api.auth import get_current_user
from app.api.audit_logs import log_audit_event
from app.models.user import User
from app.models.audit_case import AuditCase, AuditCaseChecklist, AuditCaseFinding
from app.schemas.audit_case import (
    AuditCaseCreate,
    AuditCaseUpdate,
    AuditCaseResponse,
    AuditCaseDetailResponse,
    AuditCaseListResponse,
    AuditCaseStatistics,
    AuditorInfo,
    FindingCreate,
    FindingUpdate,
    FindingResponse,
    ChecklistSummary,
    ChecklistResponse,
    ChecklistUpdate,
)

router = APIRouter(prefix="/audit-cases", tags=["Audit Cases"])


# --- Audit Cases CRUD ---


@router.get("", response_model=AuditCaseListResponse)
async def list_audit_cases(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    audit_type: Optional[str] = None,
    search: Optional[str] = None,
    fiscal_year_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List audit cases with pagination and filtering."""
    # Base query with tenant filter
    query = select(AuditCase).where(AuditCase.tenant_id == current_user.tenant_id)

    # Apply filters
    if status:
        query = query.where(AuditCase.status == status)
    if audit_type:
        query = query.where(AuditCase.audit_type == audit_type)
    if fiscal_year_id:
        query = query.where(AuditCase.fiscal_year_id == fiscal_year_id)
    if search:
        search_pattern = f"%{search}%"
        query = query.where(
            (AuditCase.case_number.ilike(search_pattern))
            | (AuditCase.project_name.ilike(search_pattern))
            | (AuditCase.beneficiary_name.ilike(search_pattern))
        )

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Calculate pages
    pages = (total + page_size - 1) // page_size if total > 0 else 1

    # Pagination
    offset = (page - 1) * page_size
    query = query.order_by(AuditCase.created_at.desc()).offset(offset).limit(page_size)

    result = await db.execute(query)
    items = result.scalars().all()

    return AuditCaseListResponse(
        items=[AuditCaseResponse.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


@router.post("", response_model=AuditCaseResponse, status_code=status.HTTP_201_CREATED)
async def create_audit_case(
    data: AuditCaseCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new audit case."""
    audit_case = AuditCase(
        tenant_id=current_user.tenant_id,
        **data.model_dump(),
    )
    db.add(audit_case)
    await db.flush()

    # Log the creation
    await log_audit_event(
        db=db,
        tenant_id=current_user.tenant_id,
        entity_type="audit_case",
        entity_id=audit_case.id,
        action="create",
        user=current_user,
        description=f"Prüfungsfall '{audit_case.case_number}' erstellt",
        request=request,
    )

    await db.commit()
    await db.refresh(audit_case)

    return AuditCaseResponse.model_validate(audit_case)


@router.get("/statistics", response_model=AuditCaseStatistics)
async def get_audit_statistics(
    fiscal_year_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get audit case statistics."""
    query = select(AuditCase).where(AuditCase.tenant_id == current_user.tenant_id)

    if fiscal_year_id:
        query = query.where(AuditCase.fiscal_year_id == fiscal_year_id)

    result = await db.execute(query)
    cases = result.scalars().all()

    # Calculate statistics
    by_status: dict[str, int] = {}
    by_result: dict[str, int] = {}
    by_type: dict[str, int] = {}
    total_audited = 0
    total_irregular = 0

    for case in cases:
        by_status[case.status] = by_status.get(case.status, 0) + 1
        if case.result:
            by_result[case.result] = by_result.get(case.result, 0) + 1
        by_type[case.audit_type] = by_type.get(case.audit_type, 0) + 1

        if case.audited_amount:
            total_audited += float(case.audited_amount)
        if case.irregular_amount:
            total_irregular += float(case.irregular_amount)

    error_rate = (total_irregular / total_audited * 100) if total_audited > 0 else 0

    return AuditCaseStatistics(
        total=len(cases),
        by_status=by_status,
        by_result=by_result,
        by_type=by_type,
        total_audited_amount=total_audited,
        total_irregular_amount=total_irregular,
        error_rate=round(error_rate, 2),
    )


@router.get("/{case_id}", response_model=AuditCaseDetailResponse)
async def get_audit_case(
    case_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get audit case details."""
    query = (
        select(AuditCase)
        .options(
            selectinload(AuditCase.primary_auditor),
            selectinload(AuditCase.secondary_auditor),
            selectinload(AuditCase.team_leader),
        )
        .where(
            AuditCase.id == case_id,
            AuditCase.tenant_id == current_user.tenant_id,
        )
    )
    result = await db.execute(query)
    audit_case = result.scalar_one_or_none()

    if not audit_case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audit case not found",
        )

    # Count related items
    checklists_count = (
        await db.scalar(
            select(func.count()).where(AuditCaseChecklist.audit_case_id == case_id)
        )
        or 0
    )

    findings_count = (
        await db.scalar(
            select(func.count()).where(AuditCaseFinding.audit_case_id == case_id)
        )
        or 0
    )

    response = AuditCaseDetailResponse.model_validate(audit_case)
    response.checklists_count = checklists_count
    response.findings_count = findings_count

    if audit_case.primary_auditor:
        response.primary_auditor = AuditorInfo.model_validate(
            audit_case.primary_auditor
        )
    if audit_case.secondary_auditor:
        response.secondary_auditor = AuditorInfo.model_validate(
            audit_case.secondary_auditor
        )
    if audit_case.team_leader:
        response.team_leader = AuditorInfo.model_validate(audit_case.team_leader)

    return response


@router.patch("/{case_id}", response_model=AuditCaseResponse)
async def update_audit_case(
    case_id: str,
    data: AuditCaseUpdate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update an audit case."""
    query = select(AuditCase).where(
        AuditCase.id == case_id,
        AuditCase.tenant_id == current_user.tenant_id,
    )
    result = await db.execute(query)
    audit_case = result.scalar_one_or_none()

    if not audit_case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audit case not found",
        )

    update_data = data.model_dump(exclude_unset=True)
    old_status = audit_case.status

    # Track changes for audit log
    changes = {}
    for field, value in update_data.items():
        old_value = getattr(audit_case, field)
        if old_value != value:
            changes[field] = {
                "old": str(old_value) if old_value else None,
                "new": str(value) if value else None,
            }
        setattr(audit_case, field, value)

    # Log status changes specifically
    if "status" in update_data and old_status != update_data["status"]:
        await log_audit_event(
            db=db,
            tenant_id=current_user.tenant_id,
            entity_type="audit_case",
            entity_id=audit_case.id,
            action="status_change",
            user=current_user,
            field_name="status",
            old_value=old_status,
            new_value=update_data["status"],
            description=f"Status geändert von '{old_status}' zu '{update_data['status']}'",
            request=request,
        )
    elif changes:
        # Log general updates
        await log_audit_event(
            db=db,
            tenant_id=current_user.tenant_id,
            entity_type="audit_case",
            entity_id=audit_case.id,
            action="update",
            user=current_user,
            changes=changes,
            description=f"Prüfungsfall aktualisiert ({len(changes)} Felder)",
            request=request,
        )

    await db.commit()
    await db.refresh(audit_case)

    return AuditCaseResponse.model_validate(audit_case)


@router.delete("/{case_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_audit_case(
    case_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete an audit case."""
    query = select(AuditCase).where(
        AuditCase.id == case_id,
        AuditCase.tenant_id == current_user.tenant_id,
    )
    result = await db.execute(query)
    audit_case = result.scalar_one_or_none()

    if not audit_case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audit case not found",
        )

    case_number = audit_case.case_number

    # Log the deletion before actually deleting
    await log_audit_event(
        db=db,
        tenant_id=current_user.tenant_id,
        entity_type="audit_case",
        entity_id=audit_case.id,
        action="delete",
        user=current_user,
        description=f"Prüfungsfall '{case_number}' gelöscht",
        request=request,
    )

    await db.delete(audit_case)
    await db.commit()


# --- Checklists ---


@router.get("/{case_id}/checklists", response_model=list[ChecklistSummary])
async def list_checklists(
    case_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List checklists for an audit case."""
    # Verify access
    case_query = select(AuditCase).where(
        AuditCase.id == case_id,
        AuditCase.tenant_id == current_user.tenant_id,
    )
    case_result = await db.execute(case_query)
    if not case_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Audit case not found")

    query = (
        select(AuditCaseChecklist)
        .where(AuditCaseChecklist.audit_case_id == case_id)
        .order_by(AuditCaseChecklist.created_at)
    )
    result = await db.execute(query)
    checklists = result.scalars().all()

    return [ChecklistSummary.model_validate(c) for c in checklists]


@router.get("/{case_id}/checklists/{checklist_id}", response_model=ChecklistResponse)
async def get_checklist(
    case_id: str,
    checklist_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a single checklist with responses."""
    query = select(AuditCaseChecklist).where(
        AuditCaseChecklist.id == checklist_id,
        AuditCaseChecklist.audit_case_id == case_id,
    )
    result = await db.execute(query)
    checklist = result.scalar_one_or_none()

    if not checklist:
        raise HTTPException(status_code=404, detail="Checklist not found")

    return ChecklistResponse.model_validate(checklist)


@router.patch("/{case_id}/checklists/{checklist_id}", response_model=ChecklistResponse)
async def update_checklist(
    case_id: str,
    checklist_id: str,
    data: ChecklistUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update checklist responses."""
    query = select(AuditCaseChecklist).where(
        AuditCaseChecklist.id == checklist_id,
        AuditCaseChecklist.audit_case_id == case_id,
    )
    result = await db.execute(query)
    checklist = result.scalar_one_or_none()

    if not checklist:
        raise HTTPException(status_code=404, detail="Checklist not found")

    # Merge responses
    if data.responses:
        checklist.responses = {**checklist.responses, **data.responses}
        checklist.answered_questions = len(checklist.responses)
        if checklist.total_questions > 0:
            checklist.progress = int(
                (checklist.answered_questions / checklist.total_questions) * 100
            )

    if data.status:
        checklist.status = data.status
        if data.status == "completed":
            checklist.completed_by = current_user.id
            from datetime import datetime, timezone

            checklist.completed_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(checklist)

    return ChecklistResponse.model_validate(checklist)
