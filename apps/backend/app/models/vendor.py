"""Vendor models for Layer 0."""

from datetime import datetime
from enum import Enum as PyEnum
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin


class VendorRole(str, PyEnum):
    """Vendor user roles."""

    vendor_admin = "vendor_admin"
    vendor_support = "vendor_support"
    vendor_developer = "vendor_developer"
    vendor_qa = "vendor_qa"


class Vendor(Base, TimestampMixin):
    """Vendor model - Software provider (e.g., FlowAudit GmbH)."""

    __tablename__ = "vendors"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid4()),
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    contact_email: Mapped[str] = mapped_column(String(255), nullable=False)
    billing_email: Mapped[str] = mapped_column(String(255), nullable=False)

    # Address
    address_street: Mapped[str | None] = mapped_column(String(255), nullable=True)
    address_city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    address_postal_code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    address_country: Mapped[str] = mapped_column(String(100), default="Deutschland")

    # Relationships
    users: Mapped[list["VendorUser"]] = relationship(
        "VendorUser",
        back_populates="vendor",
        cascade="all, delete-orphan",
    )
    customers: Mapped[list["Customer"]] = relationship(  # type: ignore
        "Customer",
        back_populates="vendor",
    )


class VendorUser(Base, TimestampMixin):
    """Vendor user model - Employees of the software vendor."""

    __tablename__ = "vendor_users"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid4()),
    )
    vendor_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("vendors.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[VendorRole] = mapped_column(
        Enum(VendorRole, name="vendor_role"),
        nullable=False,
    )
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    vendor: Mapped["Vendor"] = relationship(
        "Vendor",
        back_populates="users",
    )
    module_deployments: Mapped[list["ModuleDeployment"]] = relationship(  # type: ignore
        "ModuleDeployment",
        back_populates="deployed_by_user",
    )

    @property
    def full_name(self) -> str:
        """Get user's full name."""
        return f"{self.first_name} {self.last_name}"
