"""Group Query models - Konzern-Abfragen."""

from datetime import datetime
from typing import TYPE_CHECKING  # noqa: F401

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import TenantModel


class GroupQuery(TenantModel):
    """Konzern-Abfrage an Prüfbehörden."""

    __tablename__ = "group_queries"

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[str] = mapped_column(
        Enum(
            "annual_report",
            "quarterly_report",
            "ad_hoc",
            "system_audit_summary",
            "statistics",
            name="group_query_category",
        ),
        nullable=False,
    )
    fiscal_year: Mapped[int] = mapped_column(Integer, nullable=False)

    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    deadline: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    checklist_template_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        nullable=False,
    )
    checklist_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    config: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)

    status: Mapped[str] = mapped_column(
        Enum(
            "draft",
            "published",
            "in_progress",
            "evaluation",
            "completed",
            "archived",
            name="group_query_status",
        ),
        default="draft",
        nullable=False,
    )

    # Relationships
    assignments: Mapped[list["GroupQueryAssignment"]] = relationship(
        "GroupQueryAssignment",
        back_populates="query",
        cascade="all, delete-orphan",
    )


class GroupQueryAssignment(TenantModel):
    """Zuweisung einer Abfrage an eine Prüfbehörde."""

    __tablename__ = "group_query_assignments"

    query_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("group_queries.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    authority_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    status: Mapped[str] = mapped_column(
        Enum(
            "pending",
            "in_progress",
            "ready_for_review",
            "submitted",
            "returned",
            "accepted",
            name="assignment_status",
        ),
        default="pending",
        nullable=False,
    )
    progress: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    submitted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    remarks: Mapped[str | None] = mapped_column(Text, nullable=True)
    internal_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    query: Mapped["GroupQuery"] = relationship(
        "GroupQuery",
        back_populates="assignments",
    )
    response: Mapped["GroupQueryResponse | None"] = relationship(
        "GroupQueryResponse",
        back_populates="assignment",
        uselist=False,
    )
    attachments: Mapped[list["GroupQueryAttachment"]] = relationship(
        "GroupQueryAttachment",
        back_populates="assignment",
        cascade="all, delete-orphan",
    )


class GroupQueryResponse(TenantModel):
    """Antwort einer Prüfbehörde auf eine Konzern-Abfrage."""

    __tablename__ = "group_query_responses"

    assignment_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("group_query_assignments.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )

    checklist_data: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    summary_data: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)

    current_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    versions: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)

    submitted_by: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        nullable=False,
    )
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    confirmation: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Relationships
    assignment: Mapped["GroupQueryAssignment"] = relationship(
        "GroupQueryAssignment",
        back_populates="response",
    )


class GroupQueryAttachment(TenantModel):
    """Dateianhang zu einer Abfrage-Zuweisung."""

    __tablename__ = "group_query_attachments"

    assignment_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("group_query_assignments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    requirement_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        nullable=True,
    )

    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    storage_path: Mapped[str] = mapped_column(String(500), nullable=False)

    uploaded_by: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        nullable=False,
    )
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    verification_status: Mapped[str | None] = mapped_column(
        Enum("pending", "verified", "rejected", name="verification_status"),
        nullable=True,
    )
    verified_by: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        nullable=True,
    )
    verified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    assignment: Mapped["GroupQueryAssignment"] = relationship(
        "GroupQueryAssignment",
        back_populates="attachments",
    )
