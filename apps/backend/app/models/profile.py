"""Profile models for Layer 1 and Layer 2."""

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin


class CoordinationBodyProfile(Base, TimestampMixin):
    """Coordination Body Profile (Layer 1 - Konzern)."""

    __tablename__ = "coordination_body_profiles"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid4()),
    )
    tenant_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    # Organization details
    official_name: Mapped[str] = mapped_column(String(255), nullable=False)
    short_name: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Address
    street: Mapped[str | None] = mapped_column(String(255), nullable=True)
    postal_code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    country: Mapped[str] = mapped_column(String(100), default="Deutschland")

    # Contact
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    website: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Branding
    logo_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    primary_color: Mapped[str] = mapped_column(String(7), default="#1e40af")  # hex color
    secondary_color: Mapped[str] = mapped_column(String(7), default="#3b82f6")

    # Relationships
    tenant: Mapped["Tenant"] = relationship(  # type: ignore
        "Tenant",
        backref="coordination_body_profile",
    )


class AuthorityProfile(Base, TimestampMixin):
    """Authority Profile (Layer 2 - Prüfbehörde)."""

    __tablename__ = "authority_profiles"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid4()),
    )
    tenant_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    # Organization details
    official_name: Mapped[str] = mapped_column(String(255), nullable=False)
    short_name: Mapped[str | None] = mapped_column(String(50), nullable=True)
    authority_type: Mapped[str | None] = mapped_column(
        Enum(
            "audit_authority",
            "certifying_authority",
            "managing_authority",
            "intermediate_body",
            name="authority_type_enum",
        ),
        nullable=True,
    )

    # Address
    street: Mapped[str | None] = mapped_column(String(255), nullable=True)
    postal_code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    country: Mapped[str] = mapped_column(String(100), default="Deutschland")

    # Contact
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    website: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Branding
    logo_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    use_parent_branding: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    primary_color: Mapped[str | None] = mapped_column(String(7), nullable=True)
    secondary_color: Mapped[str | None] = mapped_column(String(7), nullable=True)

    # Relationships
    tenant: Mapped["Tenant"] = relationship(  # type: ignore
        "Tenant",
        backref="authority_profile",
    )

    def get_effective_branding(self) -> dict:
        """Get effective branding, falling back to parent if needed."""
        if not self.use_parent_branding:
            return {
                "logo_url": self.logo_url,
                "primary_color": self.primary_color,
                "secondary_color": self.secondary_color,
            }

        # Get parent profile if available
        if self.tenant and self.tenant.parent_id:
            parent_profile = (
                self.tenant.parent.coordination_body_profile
                if hasattr(self.tenant.parent, "coordination_body_profile")
                else None
            )
            if parent_profile:
                return {
                    "logo_url": parent_profile.logo_url,
                    "primary_color": parent_profile.primary_color,
                    "secondary_color": parent_profile.secondary_color,
                }

        return {
            "logo_url": self.logo_url,
            "primary_color": self.primary_color or "#1e40af",
            "secondary_color": self.secondary_color or "#3b82f6",
        }
