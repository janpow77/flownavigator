"""Tenant model."""

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import DateTime, Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin


class Tenant(Base, TimestampMixin):
    """Tenant model - Konzern oder Prüfbehörde."""

    __tablename__ = "tenants"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid4()),
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[str] = mapped_column(
        Enum("group", "authority", name="tenant_type"),
        nullable=False,
    )
    parent_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("tenants.id", ondelete="SET NULL"),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        Enum("active", "suspended", "trial", name="tenant_status"),
        default="active",
        nullable=False,
    )

    # Relationships
    users: Mapped[list["User"]] = relationship(  # type: ignore
        "User",
        back_populates="tenant",
        cascade="all, delete-orphan",
    )
    children: Mapped[list["Tenant"]] = relationship(
        "Tenant",
        back_populates="parent",
        foreign_keys="[Tenant.parent_id]",
    )
    parent: Mapped["Tenant | None"] = relationship(
        "Tenant",
        back_populates="children",
        remote_side=[id],
        foreign_keys="[Tenant.parent_id]",
    )
    audit_cases: Mapped[list["AuditCase"]] = relationship(  # type: ignore
        "AuditCase",
        back_populates="tenant",
        cascade="all, delete-orphan",
    )
