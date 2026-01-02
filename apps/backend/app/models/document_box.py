"""Document Box models - Belegkasten."""

from datetime import datetime
from typing import TYPE_CHECKING  # noqa: F401

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import TenantModel


class DocumentBox(TenantModel):
    """Belegkasten für eine Vorhabenprüfung."""

    __tablename__ = "document_boxes"

    audit_case_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("audit_cases.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    ai_verification_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    ai_provider: Mapped[str | None] = mapped_column(
        Enum("flow_invoice", "custom", name="ai_provider"),
        nullable=True,
    )
    ai_last_run_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    ai_config: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)

    # Relationships
    audit_case: Mapped["AuditCase"] = relationship(  # type: ignore
        "AuditCase",
        back_populates="document_box",
    )
    documents: Mapped[list["BoxDocument"]] = relationship(
        "BoxDocument",
        back_populates="box",
        cascade="all, delete-orphan",
    )


class BoxDocument(TenantModel):
    """Beleg im Belegkasten."""

    __tablename__ = "box_documents"

    box_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("document_boxes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    expenditure_item_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        nullable=True,
    )

    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    storage_path: Mapped[str] = mapped_column(String(500), nullable=False)
    thumbnail_path: Mapped[str | None] = mapped_column(String(500), nullable=True)

    category: Mapped[str] = mapped_column(
        Enum(
            "belege",
            "bescheide",
            "korrespondenz",
            "vertraege",
            "nachweise",
            "sonstige",
            name="document_category",
        ),
        nullable=False,
        default="sonstige",
    )

    uploaded_by: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        nullable=False,
    )
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    # Manuelle Verifikation
    manual_status: Mapped[str | None] = mapped_column(
        Enum("pending", "verified", "rejected", "unclear", name="document_status"),
        nullable=True,
    )
    manual_verified_by: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        nullable=True,
    )
    manual_verified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    manual_remarks: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    manual_findings: Mapped[list | None] = mapped_column(JSONB, nullable=True)

    # KI-Verifikation
    ai_verification: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Zuordnung zu Beleg
    matched_expenditure: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Relationships
    box: Mapped["DocumentBox"] = relationship(
        "DocumentBox",
        back_populates="documents",
    )
