"""Audit Log API Endpoints."""

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, ConfigDict
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.auth import get_current_user
from app.models.user import User
from app.models.audit_case import AuditCase
from app.models.audit_log import AuditLog

router = APIRouter(prefix="/audit-cases/{case_id}/history", tags=["Audit History"])


# --- Schemas ---


class AuditLogResponse(BaseModel):
    """Schema for audit log response."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    entity_type: str
    entity_id: str
    action: str
    field_name: str | None = None
    old_value: str | None = None
    new_value: str | None = None
    changes: dict[str, Any] | None = None
    description: str | None = None
    user_id: str | None = None
    user_email: str | None = None
    user_name: str | None = None
    created_at: datetime


class AuditLogListResponse(BaseModel):
    """Schema for paginated audit log list."""

    items: list[AuditLogResponse]
    total: int
    page: int
    page_size: int
    pages: int


class AuditLogCreate(BaseModel):
    """Schema for creating an audit log entry."""

    action: str
    field_name: str | None = None
    old_value: str | None = None
    new_value: str | None = None
    changes: dict[str, Any] | None = None
    description: str | None = None


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


async def create_audit_log_entry(
    db: AsyncSession,
    tenant_id: str,
    entity_type: str,
    entity_id: str,
    action: str,
    user: User | None = None,
    field_name: str | None = None,
    old_value: str | None = None,
    new_value: str | None = None,
    changes: dict[str, Any] | None = None,
    description: str | None = None,
    request: Request | None = None,
) -> AuditLog:
    """Create an audit log entry."""
    log_entry = AuditLog(
        id=str(uuid4()),
        tenant_id=tenant_id,
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        field_name=field_name,
        old_value=old_value,
        new_value=new_value,
        changes=changes,
        description=description,
        user_id=user.id if user else None,
        user_email=user.email if user else None,
        user_name=f"{user.first_name} {user.last_name}" if user else None,
        ip_address=request.client.host if request and request.client else None,
        user_agent=request.headers.get("user-agent") if request else None,
    )
    db.add(log_entry)
    return log_entry


# --- Endpoints ---


@router.get("")
async def list_audit_logs(
    case_id: str,
    action: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AuditLogListResponse:
    """List audit logs for an audit case."""
    case = await get_audit_case_or_404(case_id, db, current_user)

    # Build query - include logs for the case and related entities
    query = select(AuditLog).where(
        AuditLog.tenant_id == current_user.tenant_id,
        AuditLog.entity_id == case.id,
    )

    if action:
        query = query.where(AuditLog.action == action)

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Paginate
    query = query.order_by(AuditLog.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    logs = result.scalars().all()

    pages = (total + page_size - 1) // page_size if total > 0 else 0

    return AuditLogListResponse(
        items=[AuditLogResponse.model_validate(log) for log in logs],
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


@router.post("", status_code=201)
async def add_comment(
    case_id: str,
    data: AuditLogCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AuditLogResponse:
    """Add a comment or manual log entry to an audit case."""
    case = await get_audit_case_or_404(case_id, db, current_user)

    # Only allow comment action via API
    if data.action != "comment":
        raise HTTPException(
            status_code=400,
            detail="Only 'comment' action is allowed via this endpoint",
        )

    log_entry = await create_audit_log_entry(
        db=db,
        tenant_id=current_user.tenant_id,
        entity_type="audit_case",
        entity_id=case.id,
        action=data.action,
        user=current_user,
        field_name=data.field_name,
        old_value=data.old_value,
        new_value=data.new_value,
        changes=data.changes,
        description=data.description,
        request=request,
    )

    await db.commit()
    await db.refresh(log_entry)

    return AuditLogResponse.model_validate(log_entry)


# --- Utility function for other modules ---


async def log_audit_event(
    db: AsyncSession,
    tenant_id: str,
    entity_type: str,
    entity_id: str,
    action: str,
    user: User | None = None,
    field_name: str | None = None,
    old_value: Any = None,
    new_value: Any = None,
    changes: dict[str, Any] | None = None,
    description: str | None = None,
    request: Request | None = None,
) -> None:
    """
    Utility function to log an audit event.
    Can be called from other API modules to track changes.
    """
    # Convert values to strings
    old_str = str(old_value) if old_value is not None else None
    new_str = str(new_value) if new_value is not None else None

    log_entry = AuditLog(
        id=str(uuid4()),
        tenant_id=tenant_id,
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        field_name=field_name,
        old_value=old_str,
        new_value=new_str,
        changes=changes,
        description=description,
        user_id=user.id if user else None,
        user_email=user.email if user else None,
        user_name=f"{user.first_name} {user.last_name}" if user else None,
        ip_address=request.client.host if request and request.client else None,
        user_agent=request.headers.get("user-agent") if request else None,
    )
    db.add(log_entry)
