"""Document Box API endpoints."""

import os
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import get_current_user
from app.api.audit_logs import log_audit_event
from app.core.config import settings
from app.core.database import get_db
from app.models.audit_case import AuditCase
from app.models.document_box import BoxDocument, DocumentBox
from app.models.user import User
from app.schemas.document_box import (
    BoxDocumentListResponse,
    BoxDocumentResponse,
    BoxDocumentUpdate,
    DocumentBoxResponse,
    DocumentCategory,
)

router = APIRouter(prefix="/audit-cases/{case_id}/documents", tags=["Document Box"])


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


async def get_or_create_document_box(
    case: AuditCase,
    db: AsyncSession,
    user: User,
) -> DocumentBox:
    """Get existing or create new document box for audit case."""
    result = await db.execute(
        select(DocumentBox).where(DocumentBox.audit_case_id == case.id)
    )
    box = result.scalar_one_or_none()

    if not box:
        box = DocumentBox(
            id=str(uuid4()),
            tenant_id=user.tenant_id,
            audit_case_id=case.id,
            ai_verification_enabled=False,
            ai_config={},
        )
        db.add(box)
        await db.flush()

    return box


async def get_document_or_404(
    doc_id: str,
    box: DocumentBox,
    db: AsyncSession,
) -> BoxDocument:
    """Get document or raise 404."""
    result = await db.execute(
        select(BoxDocument).where(
            BoxDocument.id == doc_id,
            BoxDocument.box_id == box.id,
        )
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc


def get_storage_path(tenant_id: str, case_id: str, doc_id: str, filename: str) -> Path:
    """Generate storage path for a document."""
    base_dir = Path(settings.upload_dir) / tenant_id / case_id / doc_id
    base_dir.mkdir(parents=True, exist_ok=True)
    return base_dir / filename


def validate_file(file: UploadFile) -> None:
    """Validate uploaded file."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required")

    if file.content_type and file.content_type not in settings.allowed_mime_types:
        raise HTTPException(
            status_code=400,
            detail=f"File type {file.content_type} is not allowed",
        )


# --- Endpoints ---


@router.get("")
async def list_documents(
    case_id: str,
    category: DocumentCategory | None = None,
    status: str | None = None,
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BoxDocumentListResponse:
    """List documents for an audit case."""
    case = await get_audit_case_or_404(case_id, db, current_user)

    # Get or create document box
    result = await db.execute(
        select(DocumentBox).where(DocumentBox.audit_case_id == case.id)
    )
    box = result.scalar_one_or_none()

    if not box:
        return BoxDocumentListResponse(
            items=[],
            total=0,
            page=page,
            page_size=page_size,
            pages=0,
        )

    # Build query
    query = select(BoxDocument).where(BoxDocument.box_id == box.id)

    if category:
        query = query.where(BoxDocument.category == category)
    if status:
        query = query.where(BoxDocument.manual_status == status)

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Paginate
    query = query.order_by(BoxDocument.uploaded_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    documents = result.scalars().all()

    pages = (total + page_size - 1) // page_size if total > 0 else 0

    return BoxDocumentListResponse(
        items=[BoxDocumentResponse.model_validate(doc) for doc in documents],
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


@router.post("", status_code=201)
async def upload_document(
    case_id: str,
    request: Request,
    file: UploadFile = File(...),
    category: DocumentCategory = Form(default="sonstige"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BoxDocumentResponse:
    """Upload a document to an audit case."""
    case = await get_audit_case_or_404(case_id, db, current_user)
    validate_file(file)

    # Get or create document box
    box = await get_or_create_document_box(case, db, current_user)

    # Generate document ID and storage path
    doc_id = str(uuid4())
    filename = file.filename or "unnamed"
    storage_path = get_storage_path(
        current_user.tenant_id,
        case_id,
        doc_id,
        filename,
    )

    # Read file content and get size
    content = await file.read()
    file_size = len(content)

    # Check file size
    if file_size > settings.max_upload_size:
        raise HTTPException(
            status_code=400,
            detail=f"File size exceeds maximum allowed size ({settings.max_upload_size // 1024 // 1024}MB)",
        )

    # Save file to disk
    try:
        with open(storage_path, "wb") as f:
            f.write(content)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save file: {str(e)}",
        )

    # Create document record
    document = BoxDocument(
        id=doc_id,
        tenant_id=current_user.tenant_id,
        box_id=box.id,
        file_name=filename,
        file_size=file_size,
        mime_type=file.content_type or "application/octet-stream",
        storage_path=str(storage_path),
        category=category,
        uploaded_by=current_user.id,
        uploaded_at=datetime.now(timezone.utc),
    )

    db.add(document)
    await db.flush()

    # Log the upload
    file_size_kb = file_size / 1024
    size_str = (
        f"{file_size_kb:.1f} KB"
        if file_size_kb < 1024
        else f"{file_size_kb/1024:.1f} MB"
    )
    await log_audit_event(
        db=db,
        tenant_id=current_user.tenant_id,
        entity_type="audit_case",
        entity_id=case_id,
        action="upload",
        user=current_user,
        description=f"Dokument hochgeladen: {filename} ({size_str})",
        request=request,
    )

    await db.commit()
    await db.refresh(document)

    return BoxDocumentResponse.model_validate(document)


@router.get("/{doc_id}")
async def get_document(
    case_id: str,
    doc_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BoxDocumentResponse:
    """Get document metadata."""
    case = await get_audit_case_or_404(case_id, db, current_user)

    result = await db.execute(
        select(DocumentBox).where(DocumentBox.audit_case_id == case.id)
    )
    box = result.scalar_one_or_none()
    if not box:
        raise HTTPException(status_code=404, detail="Document not found")

    document = await get_document_or_404(doc_id, box, db)
    return BoxDocumentResponse.model_validate(document)


@router.get("/{doc_id}/download")
async def download_document(
    case_id: str,
    doc_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FileResponse:
    """Download a document file."""
    case = await get_audit_case_or_404(case_id, db, current_user)

    result = await db.execute(
        select(DocumentBox).where(DocumentBox.audit_case_id == case.id)
    )
    box = result.scalar_one_or_none()
    if not box:
        raise HTTPException(status_code=404, detail="Document not found")

    document = await get_document_or_404(doc_id, box, db)

    if not os.path.exists(document.storage_path):
        raise HTTPException(status_code=404, detail="File not found on disk")

    return FileResponse(
        path=document.storage_path,
        filename=document.file_name,
        media_type=document.mime_type,
    )


@router.patch("/{doc_id}")
async def update_document(
    case_id: str,
    doc_id: str,
    data: BoxDocumentUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BoxDocumentResponse:
    """Update document metadata."""
    case = await get_audit_case_or_404(case_id, db, current_user)

    result = await db.execute(
        select(DocumentBox).where(DocumentBox.audit_case_id == case.id)
    )
    box = result.scalar_one_or_none()
    if not box:
        raise HTTPException(status_code=404, detail="Document not found")

    document = await get_document_or_404(doc_id, box, db)
    filename = document.file_name

    # Update fields
    update_data = data.model_dump(exclude_unset=True)
    old_status = document.manual_status

    # Handle manual verification status change
    if "manual_status" in update_data:
        update_data["manual_verified_by"] = current_user.id
        update_data["manual_verified_at"] = datetime.now(timezone.utc)

    for key, value in update_data.items():
        setattr(document, key, value)

    # Log verification status changes
    if "manual_status" in update_data and old_status != update_data["manual_status"]:
        status_labels = {
            "pending": "Ausstehend",
            "verified": "Verifiziert",
            "rejected": "Abgelehnt",
            "unclear": "Unklar",
        }
        new_status_label = status_labels.get(
            update_data["manual_status"], update_data["manual_status"]
        )
        await log_audit_event(
            db=db,
            tenant_id=current_user.tenant_id,
            entity_type="audit_case",
            entity_id=case_id,
            action="verify",
            user=current_user,
            field_name="manual_status",
            old_value=old_status,
            new_value=update_data["manual_status"],
            description=f"Dokument '{filename}' als '{new_status_label}' markiert",
            request=request,
        )

    await db.commit()
    await db.refresh(document)

    return BoxDocumentResponse.model_validate(document)


@router.delete("/{doc_id}", status_code=204)
async def delete_document(
    case_id: str,
    doc_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """Delete a document."""
    case = await get_audit_case_or_404(case_id, db, current_user)

    result = await db.execute(
        select(DocumentBox).where(DocumentBox.audit_case_id == case.id)
    )
    box = result.scalar_one_or_none()
    if not box:
        raise HTTPException(status_code=404, detail="Document not found")

    document = await get_document_or_404(doc_id, box, db)
    filename = document.file_name

    # Log the deletion before actually deleting
    await log_audit_event(
        db=db,
        tenant_id=current_user.tenant_id,
        entity_type="audit_case",
        entity_id=case_id,
        action="delete",
        user=current_user,
        description=f"Dokument gelöscht: {filename}",
        request=request,
    )

    # Delete file from disk
    storage_path = Path(document.storage_path)
    if storage_path.exists():
        storage_path.unlink()
        # Also remove the document directory if empty
        parent_dir = storage_path.parent
        if parent_dir.exists() and not any(parent_dir.iterdir()):
            parent_dir.rmdir()

    # Delete database record
    await db.delete(document)
    await db.commit()


# --- Document Box Info ---


@router.get("/box/info")
async def get_document_box_info(
    case_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DocumentBoxResponse:
    """Get document box information for an audit case."""
    case = await get_audit_case_or_404(case_id, db, current_user)

    result = await db.execute(
        select(DocumentBox).where(DocumentBox.audit_case_id == case.id)
    )
    box = result.scalar_one_or_none()

    if not box:
        # Return empty box info
        return DocumentBoxResponse(
            id="",
            audit_case_id=case.id,
            ai_verification_enabled=False,
            documents_count=0,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

    # Count documents
    count_result = await db.execute(
        select(func.count()).where(BoxDocument.box_id == box.id)
    )
    documents_count = count_result.scalar() or 0

    return DocumentBoxResponse(
        id=box.id,
        audit_case_id=case.id,
        ai_verification_enabled=box.ai_verification_enabled,
        documents_count=documents_count,
        created_at=box.created_at,
        updated_at=box.updated_at,
    )
