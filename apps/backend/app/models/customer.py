"""Customer models for Layer 0."""

from datetime import date, datetime, timezone
from enum import Enum as PyEnum
from uuid import uuid4

from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin


class CustomerStatus(str, PyEnum):
    """Customer status."""

    active = "active"
    suspended = "suspended"
    trial = "trial"
    terminated = "terminated"


class Customer(Base, TimestampMixin):
    """Customer model - Licensed organization (Coordination Body)."""

    __tablename__ = "customers"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid4()),
    )
    vendor_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("vendors.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    tenant_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    # Contract details
    contract_number: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False
    )
    contract_start: Mapped[date | None] = mapped_column(Date, nullable=True)
    contract_end: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Licensing
    licensed_users: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    licensed_authorities: Mapped[int] = mapped_column(
        Integer, default=1, nullable=False
    )

    # Billing
    billing_contact: Mapped[str | None] = mapped_column(String(255), nullable=True)
    billing_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    billing_address_street: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )
    billing_address_city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    billing_address_postal_code: Mapped[str | None] = mapped_column(
        String(20), nullable=True
    )
    billing_address_country: Mapped[str] = mapped_column(
        String(100), default="Deutschland"
    )
    payment_method: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Status
    status: Mapped[CustomerStatus] = mapped_column(
        Enum(CustomerStatus, name="customer_status"),
        default=CustomerStatus.active,
        nullable=False,
    )

    # Relationships
    vendor: Mapped["Vendor"] = relationship(  # type: ignore
        "Vendor",
        back_populates="customers",
    )
    tenant: Mapped["Tenant"] = relationship(  # type: ignore
        "Tenant",
        backref="customer",
    )
    license_usages: Mapped[list["LicenseUsage"]] = relationship(
        "LicenseUsage",
        back_populates="customer",
        cascade="all, delete-orphan",
    )
    license_alerts: Mapped[list["LicenseAlert"]] = relationship(
        "LicenseAlert",
        back_populates="customer",
        cascade="all, delete-orphan",
    )
    module_deployments: Mapped[list["ModuleDeployment"]] = relationship(  # type: ignore
        "ModuleDeployment",
        back_populates="customer",
    )


class LicenseUsage(Base):
    """Daily license usage tracking."""

    __tablename__ = "license_usages"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid4()),
    )
    customer_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("customers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    active_users: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    active_authorities: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    customer: Mapped["Customer"] = relationship(
        "Customer",
        back_populates="license_usages",
    )

    # Unique constraint on customer + date
    __table_args__ = ({"extend_existing": True},)


class LicenseAlert(Base):
    """License usage alerts."""

    __tablename__ = "license_alerts"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid4()),
    )
    customer_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("customers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    alert_type: Mapped[str] = mapped_column(
        Enum("warning", "critical", "exceeded", name="alert_type"),
        nullable=False,
    )
    message: Mapped[str] = mapped_column(Text, nullable=False)
    threshold_percent: Mapped[int] = mapped_column(Integer, nullable=False)
    current_percent: Mapped[int] = mapped_column(Integer, nullable=False)
    acknowledged: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    acknowledged_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    acknowledged_by: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("vendor_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    customer: Mapped["Customer"] = relationship(
        "Customer",
        back_populates="license_alerts",
    )
