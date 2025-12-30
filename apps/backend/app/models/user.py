"""User model."""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin


class User(Base, TimestampMixin):
    """User model."""

    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid4()),
    )
    tenant_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    role: Mapped[str] = mapped_column(
        Enum(
            "system_admin",
            "group_admin",
            "authority_head",
            "team_leader",
            "auditor",
            "viewer",
            name="user_role",
        ),
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    tenant: Mapped["Tenant"] = relationship(  # type: ignore
        "Tenant",
        back_populates="users",
    )
    preferences: Mapped["UserPreferences"] = relationship(  # type: ignore
        "UserPreferences",
        back_populates="user",
        uselist=False,
    )
    primary_audits: Mapped[list["AuditCase"]] = relationship(  # type: ignore
        "AuditCase",
        foreign_keys="[AuditCase.primary_auditor_id]",
        back_populates="primary_auditor",
    )
    secondary_audits: Mapped[list["AuditCase"]] = relationship(  # type: ignore
        "AuditCase",
        foreign_keys="[AuditCase.secondary_auditor_id]",
        back_populates="secondary_auditor",
    )
    led_audits: Mapped[list["AuditCase"]] = relationship(  # type: ignore
        "AuditCase",
        foreign_keys="[AuditCase.team_leader_id]",
        back_populates="team_leader",
    )

    @property
    def full_name(self) -> str:
        """Get user's full name."""
        return f"{self.first_name} {self.last_name}"
