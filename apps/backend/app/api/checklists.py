"""Checklist API Endpoints."""

from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.auth import get_current_user
from app.models.user import User
from app.models.audit_case import AuditCase, AuditCaseChecklist, ChecklistTemplate
from app.schemas.checklist import (
    ChecklistTemplateCreate,
    ChecklistTemplateUpdate,
    ChecklistTemplateResponse,
    ChecklistTemplateListResponse,
    ChecklistTemplateSummary,
    ChecklistCreateFromTemplate,
    ChecklistResponseUpdate,
    ChecklistInstanceResponse,
    ChecklistSummaryResponse,
    get_default_main_checklist,
    get_default_procurement_checklist,
)

router = APIRouter(prefix="/checklists", tags=["Checklists"])


# --- Template Endpoints ---


@router.get("/templates", response_model=ChecklistTemplateListResponse)
async def list_templates(
    checklist_type: Optional[str] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List checklist templates."""
    query = select(ChecklistTemplate).where(
        ChecklistTemplate.tenant_id == current_user.tenant_id,
        ChecklistTemplate.is_current == True,
    )

    if checklist_type:
        query = query.where(ChecklistTemplate.checklist_type == checklist_type)
    if status:
        query = query.where(ChecklistTemplate.status == status)
    if search:
        query = query.where(ChecklistTemplate.name.ilike(f"%{search}%"))

    query = query.order_by(ChecklistTemplate.name)

    result = await db.execute(query)
    templates = result.scalars().all()

    return ChecklistTemplateListResponse(
        items=[ChecklistTemplateResponse.model_validate(t) for t in templates],
        total=len(templates),
    )


@router.post("/templates", response_model=ChecklistTemplateResponse, status_code=201)
async def create_template(
    data: ChecklistTemplateCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new checklist template."""
    template = ChecklistTemplate(
        id=str(uuid4()),
        tenant_id=current_user.tenant_id,
        name=data.name,
        description=data.description,
        checklist_type=data.checklist_type,
        structure=data.structure,
        status="draft",
        version=1,
        is_current=True,
    )

    db.add(template)
    await db.commit()
    await db.refresh(template)

    return ChecklistTemplateResponse.model_validate(template)


@router.get("/templates/defaults")
async def get_default_templates(
    current_user: User = Depends(get_current_user),
):
    """Get default template structures."""
    return {
        "main": get_default_main_checklist(),
        "procurement": get_default_procurement_checklist(),
    }


@router.post(
    "/templates/create-defaults", response_model=list[ChecklistTemplateResponse]
)
async def create_default_templates(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create default templates for the tenant."""
    templates = []

    # Check existing templates
    existing = await db.execute(
        select(ChecklistTemplate)
        .where(ChecklistTemplate.tenant_id == current_user.tenant_id)
        .where(ChecklistTemplate.is_current == True)
    )
    existing_types = {t.checklist_type for t in existing.scalars().all()}

    # Main checklist
    if "main" not in existing_types:
        main_template = ChecklistTemplate(
            id=str(uuid4()),
            tenant_id=current_user.tenant_id,
            name="Hauptcheckliste Vorhabenprüfung",
            description="Standardcheckliste für die Prüfung von EU-Strukturfonds-Vorhaben",
            checklist_type="main",
            structure=get_default_main_checklist(),
            status="published",
            version=1,
            is_current=True,
        )
        db.add(main_template)
        templates.append(main_template)

    # Procurement checklist
    if "procurement" not in existing_types:
        procurement_template = ChecklistTemplate(
            id=str(uuid4()),
            tenant_id=current_user.tenant_id,
            name="Vergabeprüfung",
            description="Checkliste zur Prüfung der Einhaltung des Vergaberechts",
            checklist_type="procurement",
            structure=get_default_procurement_checklist(),
            status="published",
            version=1,
            is_current=True,
        )
        db.add(procurement_template)
        templates.append(procurement_template)

    if templates:
        await db.commit()
        for t in templates:
            await db.refresh(t)

    return [ChecklistTemplateResponse.model_validate(t) for t in templates]


@router.get("/templates/{template_id}", response_model=ChecklistTemplateResponse)
async def get_template(
    template_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific template."""
    result = await db.execute(
        select(ChecklistTemplate).where(
            ChecklistTemplate.id == template_id,
            ChecklistTemplate.tenant_id == current_user.tenant_id,
        )
    )
    template = result.scalar_one_or_none()

    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    return ChecklistTemplateResponse.model_validate(template)


@router.patch("/templates/{template_id}", response_model=ChecklistTemplateResponse)
async def update_template(
    template_id: str,
    data: ChecklistTemplateUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a template."""
    result = await db.execute(
        select(ChecklistTemplate).where(
            ChecklistTemplate.id == template_id,
            ChecklistTemplate.tenant_id == current_user.tenant_id,
        )
    )
    template = result.scalar_one_or_none()

    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(template, field, value)

    await db.commit()
    await db.refresh(template)

    return ChecklistTemplateResponse.model_validate(template)


@router.delete("/templates/{template_id}", status_code=204)
async def delete_template(
    template_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a template (archive it)."""
    result = await db.execute(
        select(ChecklistTemplate).where(
            ChecklistTemplate.id == template_id,
            ChecklistTemplate.tenant_id == current_user.tenant_id,
        )
    )
    template = result.scalar_one_or_none()

    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    # Check if template is in use
    usage_count = await db.scalar(
        select(func.count()).where(
            AuditCaseChecklist.checklist_template_id == template_id
        )
    )

    if usage_count and usage_count > 0:
        # Archive instead of delete
        template.status = "archived"
        template.is_current = False
        await db.commit()
    else:
        await db.delete(template)
        await db.commit()


# --- Audit Case Checklist Endpoints ---


@router.get("/audit-case/{case_id}", response_model=list[ChecklistSummaryResponse])
async def list_case_checklists(
    case_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List checklists for an audit case."""
    # Verify access
    case_result = await db.execute(
        select(AuditCase).where(
            AuditCase.id == case_id,
            AuditCase.tenant_id == current_user.tenant_id,
        )
    )
    if not case_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Audit case not found")

    query = (
        select(AuditCaseChecklist, ChecklistTemplate.name)
        .outerjoin(
            ChecklistTemplate,
            AuditCaseChecklist.checklist_template_id == ChecklistTemplate.id,
        )
        .where(AuditCaseChecklist.audit_case_id == case_id)
        .order_by(AuditCaseChecklist.created_at)
    )

    result = await db.execute(query)
    rows = result.all()

    checklists = []
    for checklist, template_name in rows:
        summary = ChecklistSummaryResponse.model_validate(checklist)
        summary.template_name = template_name
        checklists.append(summary)

    return checklists


@router.post(
    "/audit-case/{case_id}", response_model=ChecklistInstanceResponse, status_code=201
)
async def add_checklist_to_case(
    case_id: str,
    data: ChecklistCreateFromTemplate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Add a checklist to an audit case from a template."""
    # Verify access to case
    case_result = await db.execute(
        select(AuditCase).where(
            AuditCase.id == case_id,
            AuditCase.tenant_id == current_user.tenant_id,
        )
    )
    audit_case = case_result.scalar_one_or_none()
    if not audit_case:
        raise HTTPException(status_code=404, detail="Audit case not found")

    # Get template
    template_result = await db.execute(
        select(ChecklistTemplate).where(
            ChecklistTemplate.id == data.template_id,
            ChecklistTemplate.tenant_id == current_user.tenant_id,
        )
    )
    template = template_result.scalar_one_or_none()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    # Count questions in template
    total_questions = 0
    structure = template.structure or {}
    for section in structure.get("sections", []):
        for question in section.get("questions", []):
            if question.get("type") != "section":
                total_questions += 1

    # Create checklist instance
    checklist = AuditCaseChecklist(
        id=str(uuid4()),
        audit_case_id=case_id,
        checklist_template_id=template.id,
        checklist_type=data.checklist_type or template.checklist_type,
        status="not_started",
        progress=0,
        total_questions=total_questions,
        answered_questions=0,
        responses={},
    )

    db.add(checklist)
    await db.commit()
    await db.refresh(checklist)

    response = ChecklistInstanceResponse.model_validate(checklist)
    response.template_name = template.name
    response.structure = template.structure

    return response


@router.get(
    "/audit-case/{case_id}/{checklist_id}", response_model=ChecklistInstanceResponse
)
async def get_case_checklist(
    case_id: str,
    checklist_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific checklist with template structure."""
    query = (
        select(AuditCaseChecklist, ChecklistTemplate)
        .outerjoin(
            ChecklistTemplate,
            AuditCaseChecklist.checklist_template_id == ChecklistTemplate.id,
        )
        .where(
            AuditCaseChecklist.id == checklist_id,
            AuditCaseChecklist.audit_case_id == case_id,
        )
    )

    result = await db.execute(query)
    row = result.first()

    if not row:
        raise HTTPException(status_code=404, detail="Checklist not found")

    checklist, template = row

    response = ChecklistInstanceResponse.model_validate(checklist)
    if template:
        response.template_name = template.name
        response.structure = template.structure

    return response


@router.patch(
    "/audit-case/{case_id}/{checklist_id}", response_model=ChecklistInstanceResponse
)
async def update_case_checklist(
    case_id: str,
    checklist_id: str,
    data: ChecklistResponseUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update checklist responses."""
    query = (
        select(AuditCaseChecklist, ChecklistTemplate)
        .outerjoin(
            ChecklistTemplate,
            AuditCaseChecklist.checklist_template_id == ChecklistTemplate.id,
        )
        .where(
            AuditCaseChecklist.id == checklist_id,
            AuditCaseChecklist.audit_case_id == case_id,
        )
    )

    result = await db.execute(query)
    row = result.first()

    if not row:
        raise HTTPException(status_code=404, detail="Checklist not found")

    checklist, template = row

    # Merge responses
    if data.responses:
        current_responses = checklist.responses or {}
        for question_id, value in data.responses.items():
            current_responses[question_id] = {
                "value": value,
                "answered_at": datetime.now(timezone.utc).isoformat(),
                "answered_by": current_user.id,
            }
        checklist.responses = current_responses

        # Update progress
        checklist.answered_questions = len(current_responses)
        if checklist.total_questions > 0:
            checklist.progress = int(
                (checklist.answered_questions / checklist.total_questions) * 100
            )

        # Update status
        if checklist.status == "not_started":
            checklist.status = "in_progress"

    # Notes
    if data.notes:
        current_responses = checklist.responses or {}
        for question_id, note in data.notes.items():
            if question_id in current_responses:
                current_responses[question_id]["note"] = note
            else:
                current_responses[question_id] = {"note": note}
        checklist.responses = current_responses

    # Status
    if data.status:
        checklist.status = data.status
        if data.status == "completed":
            checklist.completed_by = current_user.id
            checklist.completed_at = datetime.now(timezone.utc)
            checklist.progress = 100

    await db.commit()
    await db.refresh(checklist)

    response = ChecklistInstanceResponse.model_validate(checklist)
    if template:
        response.template_name = template.name
        response.structure = template.structure

    return response


@router.delete("/audit-case/{case_id}/{checklist_id}", status_code=204)
async def delete_case_checklist(
    case_id: str,
    checklist_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a checklist from an audit case."""
    result = await db.execute(
        select(AuditCaseChecklist).where(
            AuditCaseChecklist.id == checklist_id,
            AuditCaseChecklist.audit_case_id == case_id,
        )
    )
    checklist = result.scalar_one_or_none()

    if not checklist:
        raise HTTPException(status_code=404, detail="Checklist not found")

    await db.delete(checklist)
    await db.commit()
