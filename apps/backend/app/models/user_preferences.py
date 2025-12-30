"""User Preferences Model"""
from uuid import uuid4

from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class UserPreferences(Base, TimestampMixin):
    """User preferences for UI customization"""

    __tablename__ = "user_preferences"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid4()),
    )
    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )

    # Appearance settings
    appearance: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    # Navigation settings
    navigation: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    # Dashboard settings
    dashboard: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    # Module-specific preferences
    module_preferences: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    # Notification settings
    notifications: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    # Locale settings
    locale: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    # Keyboard shortcuts
    shortcuts: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    # Relationship
    user = relationship("User", back_populates="preferences")

    @classmethod
    def get_defaults(cls) -> dict:
        """Return default preferences"""
        return {
            "appearance": {
                "theme": "system",
                "accentColor": "blue",
                "fontSize": "medium",
                "reducedMotion": False,
                "highContrast": False
            },
            "navigation": {
                "defaultView": "tiles",
                "sidebarCollapsed": False,
                "enableAnimations": True,
                "enableHoverEffects": True,
                "showModuleBadges": True
            },
            "dashboard": {
                "startPage": "/dashboard",
                "visibleWidgets": ["active_audits", "appointments", "tasks", "activities"],
                "widgetOrder": ["active_audits", "appointments", "tasks", "activities"],
                "compactMode": False
            },
            "module_preferences": {},
            "notifications": {
                "enabled": True,
                "sound": False,
                "desktop": True,
                "emailDigest": "daily"
            },
            "locale": {
                "language": "de",
                "dateFormat": "DD.MM.YYYY",
                "timeFormat": "24h",
                "timezone": "Europe/Berlin",
                "numberFormat": "de-DE"
            },
            "shortcuts": {
                "enabled": True,
                "custom": {}
            }
        }
