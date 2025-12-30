"""Document Box schemas."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


# Category types
DocumentCategory = Literal[
    "belege",
    "bescheide",
    "korrespondenz",
    "vertraege",
    "nachweise",
    "sonstige",
]

DocumentStatus = Literal["pending", "verified", "rejected", "unclear"]


# --- Document Box ---


class DocumentBoxBase(BaseModel):
    """Base schema for document box."""

    ai_verification_enabled: bool = False


class DocumentBoxResponse(DocumentBoxBase):
    """Response schema for document box."""

    id: str
    audit_case_id: str
    documents_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# --- Box Document ---


class BoxDocumentBase(BaseModel):
    """Base schema for box document."""

    file_name: str = Field(..., min_length=1, max_length=255)
    category: DocumentCategory = "sonstige"


class BoxDocumentCreate(BoxDocumentBase):
    """Schema for creating a document (metadata only, file handled separately)."""

    pass


class BoxDocumentUpdate(BaseModel):
    """Schema for updating a document."""

    category: DocumentCategory | None = None
    manual_status: DocumentStatus | None = None
    manual_remarks: str | None = Field(None, max_length=1000)


class BoxDocumentResponse(BoxDocumentBase):
    """Response schema for box document."""

    id: str
    box_id: str
    file_size: int
    mime_type: str
    thumbnail_path: str | None = None

    uploaded_by: str
    uploaded_at: datetime

    manual_status: DocumentStatus | None = None
    manual_verified_by: str | None = None
    manual_verified_at: datetime | None = None
    manual_remarks: str | None = None

    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class BoxDocumentListResponse(BaseModel):
    """Paginated list response for documents."""

    items: list[BoxDocumentResponse]
    total: int
    page: int
    page_size: int
    pages: int


# --- Category Labels (German) ---


CATEGORY_LABELS: dict[str, str] = {
    "belege": "Belege",
    "bescheide": "Bescheide",
    "korrespondenz": "Korrespondenz",
    "vertraege": "Vertr\u00e4ge",
    "nachweise": "Nachweise",
    "sonstige": "Sonstige",
}

STATUS_LABELS: dict[str, str] = {
    "pending": "Ausstehend",
    "verified": "Verifiziert",
    "rejected": "Abgelehnt",
    "unclear": "Unklar",
}
