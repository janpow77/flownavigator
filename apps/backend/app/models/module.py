"""Module models for Layer 0 - Development and Deployment."""

from datetime import datetime, timezone
from enum import Enum as PyEnum
from uuid import uuid4

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin


class ModuleStatus(str, PyEnum):
    """Module development status."""

    development = "development"
    testing = "testing"
    released = "released"
    deprecated = "deprecated"


class DeploymentStatus(str, PyEnum):
    """Module deployment status."""

    pending = "pending"
    deploying = "deploying"
    deployed = "deployed"
    failed = "failed"
    rolled_back = "rolled_back"


class Module(Base, TimestampMixin):
    """Module model - Vendor-developed feature modules."""

    __tablename__ = "modules"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid4()),
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    version: Mapped[str] = mapped_column(String(20), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[ModuleStatus] = mapped_column(
        Enum(ModuleStatus, name="module_status"),
        default=ModuleStatus.development,
        nullable=False,
    )
    developed_by: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("vendor_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    released_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Module configuration
    dependencies: Mapped[list | None] = mapped_column(
        JSON,
        default=list,
        nullable=True,
    )
    min_system_version: Mapped[str | None] = mapped_column(String(20), nullable=True)
    feature_flags: Mapped[dict | None] = mapped_column(
        JSON,
        default=dict,
        nullable=True,
    )

    # Relationships
    developer: Mapped["VendorUser"] = relationship(  # type: ignore
        "VendorUser",
        foreign_keys=[developed_by],
    )
    deployments: Mapped[list["ModuleDeployment"]] = relationship(
        "ModuleDeployment",
        back_populates="module",
        cascade="all, delete-orphan",
    )
    release_notes: Mapped[list["ReleaseNote"]] = relationship(
        "ReleaseNote",
        back_populates="module",
        cascade="all, delete-orphan",
    )


class ModuleDeployment(Base):
    """Module deployment tracking per customer."""

    __tablename__ = "module_deployments"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid4()),
    )
    module_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("modules.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    customer_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("customers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[DeploymentStatus] = mapped_column(
        Enum(DeploymentStatus, name="deployment_status"),
        default=DeploymentStatus.pending,
        nullable=False,
    )
    deployed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    deployed_by: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("vendor_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    deployed_version: Mapped[str] = mapped_column(String(20), nullable=False)
    previous_version: Mapped[str | None] = mapped_column(String(20), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    module: Mapped["Module"] = relationship(
        "Module",
        back_populates="deployments",
    )
    customer: Mapped["Customer"] = relationship(  # type: ignore
        "Customer",
        back_populates="module_deployments",
    )
    deployed_by_user: Mapped["VendorUser"] = relationship(  # type: ignore
        "VendorUser",
        back_populates="module_deployments",
    )


class ReleaseNote(Base):
    """Release notes for module versions."""

    __tablename__ = "release_notes"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid4()),
    )
    module_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("modules.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    version: Mapped[str] = mapped_column(String(20), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    changes: Mapped[list | None] = mapped_column(
        JSON,
        default=list,
        nullable=True,
    )
    breaking_changes: Mapped[list | None] = mapped_column(
        JSON,
        default=list,
        nullable=True,
    )
    published_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    module: Mapped["Module"] = relationship(
        "Module",
        back_populates="release_notes",
    )
