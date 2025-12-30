"""Findings API Endpoints."""

from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.auth import get_current_user
from app.api.audit_logs import log_audit_event
from app.models.user import User
from app.models.audit_case import AuditCase, AuditCaseFinding
from app.schemas.audit_case import (
    FindingCreate,
    FindingUpdate,
    FindingResponse,
)

# Finding type labels for logging
FINDING_TYPE_LABELS = {
    "irregularity": "Unregelmäßigkeit",
    "deficiency": "Mangel",
    "recommendation": "Empfehlung",
    "observation": "Beobachtung",
}

router = APIRouter(prefix="/audit-cases/{case_id}/findings", tags=["Findings"])


# --- Helper Functions ---


async def get_audit_case_or_404(
    case_id: str,
    db: AsyncSession,
    user: User,
) -> AuditCase:
    """Get audit case or raise 404."""
    result = await db.execute(
        select(AuditCase).where(
            AuditCase.id == case_id,
            AuditCase.tenant_id == user.tenant_id,
        )
    )
    case = result.scalar_one_or_none()
    if not case:
        raise HTTPException(status_code=404, detail="Audit case not found")
    return case


async def get_finding_or_404(
    finding_id: str,
    case_id: str,
    db: AsyncSession,
) -> AuditCaseFinding:
    """Get finding or raise 404."""
    result = await db.execute(
        select(AuditCaseFinding).where(
            AuditCaseFinding.id == finding_id,
            AuditCaseFinding.audit_case_id == case_id,
        )
    )
    finding = result.scalar_one_or_none()
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")
    return finding


async def get_next_finding_number(case_id: str, db: AsyncSession) -> int:
    """Get next finding number for a case."""
    result = await db.execute(
        select(func.max(AuditCaseFinding.finding_number)).where(
            AuditCaseFinding.audit_case_id == case_id
        )
    )
    max_number = result.scalar()
    return (max_number or 0) + 1


# --- Endpoints ---


@router.get("")
async def list_findings(
    case_id: str,
    status: str | None = None,
    finding_type: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[FindingResponse]:
    """List findings for an audit case."""
    await get_audit_case_or_404(case_id, db, current_user)

    query = select(AuditCaseFinding).where(AuditCaseFinding.audit_case_id == case_id)

    if status:
        query = query.where(AuditCaseFinding.status == status)
    if finding_type:
        query = query.where(AuditCaseFinding.finding_type == finding_type)

    query = query.order_by(AuditCaseFinding.finding_number)

    result = await db.execute(query)
    findings = result.scalars().all()

    return [FindingResponse.model_validate(f) for f in findings]


@router.post("", status_code=201)
async def create_finding(
    case_id: str,
    data: FindingCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FindingResponse:
    """Create a new finding for an audit case."""
    case = await get_audit_case_or_404(case_id, db, current_user)

    # Get next finding number
    finding_number = await get_next_finding_number(case_id, db)

    finding = AuditCaseFinding(
        id=str(uuid4()),
        audit_case_id=case.id,
        finding_number=finding_number,
        finding_type=data.finding_type,
        error_category=data.error_category,
        title=data.title,
        description=data.description,
        financial_impact=data.financial_impact,
        is_systemic=data.is_systemic,
        status="draft",
        response_requested=data.response_requested,
        response_deadline=data.response_deadline,
    )

    db.add(finding)
    await db.flush()

    # Log the creation
    type_label = FINDING_TYPE_LABELS.get(data.finding_type, data.finding_type)
    await log_audit_event(
        db=db,
        tenant_id=current_user.tenant_id,
        entity_type="audit_case",
        entity_id=case_id,
        action="create",
        user=current_user,
        description=f"Feststellung #{finding_number} erstellt: {type_label} - {data.title}",
        request=request,
    )

    await db.commit()
    await db.refresh(finding)

    return FindingResponse.model_validate(finding)


@router.get("/{finding_id}")
async def get_finding(
    case_id: str,
    finding_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FindingResponse:
    """Get a specific finding."""
    await get_audit_case_or_404(case_id, db, current_user)
    finding = await get_finding_or_404(finding_id, case_id, db)
    return FindingResponse.model_validate(finding)


@router.patch("/{finding_id}")
async def update_finding(
    case_id: str,
    finding_id: str,
    data: FindingUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FindingResponse:
    """Update a finding."""
    await get_audit_case_or_404(case_id, db, current_user)
    finding = await get_finding_or_404(finding_id, case_id, db)

    update_data = data.model_dump(exclude_unset=True)

    # Handle response received timestamp
    if "response_received" in update_data and update_data["response_received"]:
        update_data["response_received_at"] = datetime.now(timezone.utc)

    # Track changes for logging
    changes = {}
    for key, value in update_data.items():
        old_value = getattr(finding, key)
        if old_value != value:
            changes[key] = {
                "old": str(old_value) if old_value else None,
                "new": str(value) if value else None,
            }
        setattr(finding, key, value)

    if changes:
        await log_audit_event(
            db=db,
            tenant_id=current_user.tenant_id,
            entity_type="audit_case",
            entity_id=case_id,
            action="update",
            user=current_user,
            changes=changes,
            description=f"Feststellung #{finding.finding_number} aktualisiert",
            request=request,
        )

    await db.commit()
    await db.refresh(finding)

    return FindingResponse.model_validate(finding)


@router.delete("/{finding_id}", status_code=204)
async def delete_finding(
    case_id: str,
    finding_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """Delete a finding."""
    await get_audit_case_or_404(case_id, db, current_user)
    finding = await get_finding_or_404(finding_id, case_id, db)

    # Only allow deleting draft findings
    if finding.status != "draft":
        raise HTTPException(
            status_code=400,
            detail="Only draft findings can be deleted",
        )

    finding_number = finding.finding_number
    finding_title = finding.title

    # Log the deletion
    await log_audit_event(
        db=db,
        tenant_id=current_user.tenant_id,
        entity_type="audit_case",
        entity_id=case_id,
        action="delete",
        user=current_user,
        description=f"Feststellung #{finding_number} gelöscht: {finding_title}",
        request=request,
    )

    await db.delete(finding)
    await db.commit()


# --- Bulk Operations ---


@router.post("/{finding_id}/confirm")
async def confirm_finding(
    case_id: str,
    finding_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FindingResponse:
    """Confirm a draft finding."""
    await get_audit_case_or_404(case_id, db, current_user)
    finding = await get_finding_or_404(finding_id, case_id, db)

    if finding.status != "draft":
        raise HTTPException(
            status_code=400,
            detail="Only draft findings can be confirmed",
        )

    finding.status = "confirmed"

    # Log the confirmation
    await log_audit_event(
        db=db,
        tenant_id=current_user.tenant_id,
        entity_type="audit_case",
        entity_id=case_id,
        action="confirm",
        user=current_user,
        field_name="status",
        old_value="draft",
        new_value="confirmed",
        description=f"Feststellung #{finding.finding_number} bestätigt: {finding.title}",
        request=request,
    )

    await db.commit()
    await db.refresh(finding)

    return FindingResponse.model_validate(finding)


@router.post("/{finding_id}/resolve")
async def resolve_finding(
    case_id: str,
    finding_id: str,
    request: Request,
    corrective_action: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FindingResponse:
    """Mark a finding as resolved."""
    await get_audit_case_or_404(case_id, db, current_user)
    finding = await get_finding_or_404(finding_id, case_id, db)

    old_status = finding.status
    if old_status not in ["confirmed", "disputed"]:
        raise HTTPException(
            status_code=400,
            detail="Only confirmed or disputed findings can be resolved",
        )

    finding.status = "resolved"
    if corrective_action:
        finding.corrective_action = corrective_action

    # Log the resolution
    await log_audit_event(
        db=db,
        tenant_id=current_user.tenant_id,
        entity_type="audit_case",
        entity_id=case_id,
        action="resolve",
        user=current_user,
        field_name="status",
        old_value=old_status,
        new_value="resolved",
        description=f"Feststellung #{finding.finding_number} behoben: {finding.title}",
        request=request,
    )

    await db.commit()
    await db.refresh(finding)

    return FindingResponse.model_validate(finding)


# --- Statistics ---


@router.get("/stats/summary")
async def get_findings_summary(
    case_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Get findings summary for an audit case."""
    await get_audit_case_or_404(case_id, db, current_user)

    # Total count
    total_result = await db.execute(
        select(func.count()).where(AuditCaseFinding.audit_case_id == case_id)
    )
    total = total_result.scalar() or 0

    # Count by status
    status_result = await db.execute(
        select(AuditCaseFinding.status, func.count())
        .where(AuditCaseFinding.audit_case_id == case_id)
        .group_by(AuditCaseFinding.status)
    )
    by_status = dict(status_result.all())

    # Count by type
    type_result = await db.execute(
        select(AuditCaseFinding.finding_type, func.count())
        .where(AuditCaseFinding.audit_case_id == case_id)
        .group_by(AuditCaseFinding.finding_type)
    )
    by_type = dict(type_result.all())

    # Total financial impact
    impact_result = await db.execute(
        select(func.sum(AuditCaseFinding.financial_impact)).where(
            AuditCaseFinding.audit_case_id == case_id
        )
    )
    total_financial_impact = impact_result.scalar() or 0

    return {
        "total": total,
        "by_status": by_status,
        "by_type": by_type,
        "total_financial_impact": float(total_financial_impact),
    }
