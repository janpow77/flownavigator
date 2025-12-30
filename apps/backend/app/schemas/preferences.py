"""Preferences Pydantic Schemas"""

from typing import Optional, Literal
from pydantic import BaseModel, Field


class AppearancePreferences(BaseModel):
    theme: Literal["light", "dark", "system"] = "system"
    accentColor: Literal["blue", "purple", "green", "orange", "pink", "teal"] = "blue"
    fontSize: Literal["small", "medium", "large"] = "medium"
    reducedMotion: bool = False
    highContrast: bool = False


class NavigationPreferences(BaseModel):
    defaultView: Literal["tiles", "list", "tree", "radial", "minimal"] = "tiles"
    sidebarCollapsed: bool = False
    enableAnimations: bool = True
    enableHoverEffects: bool = True
    showModuleBadges: bool = True


class DashboardPreferences(BaseModel):
    startPage: str = "/dashboard"
    visibleWidgets: list[str] = Field(
        default_factory=lambda: ["active_audits", "appointments", "tasks", "activities"]
    )
    widgetOrder: list[str] = Field(
        default_factory=lambda: ["active_audits", "appointments", "tasks", "activities"]
    )
    compactMode: bool = False


class NotificationPreferences(BaseModel):
    enabled: bool = True
    sound: bool = False
    desktop: bool = True
    emailDigest: Literal["none", "daily", "weekly"] = "daily"


class LocalePreferences(BaseModel):
    language: Literal["de", "en"] = "de"
    dateFormat: str = "DD.MM.YYYY"
    timeFormat: Literal["12h", "24h"] = "24h"
    timezone: str = "Europe/Berlin"
    numberFormat: str = "de-DE"


class ShortcutPreferences(BaseModel):
    enabled: bool = True
    custom: dict[str, str] = Field(default_factory=dict)


class UserPreferencesSchema(BaseModel):
    id: Optional[str] = None
    userId: Optional[str] = None

    appearance: AppearancePreferences = Field(default_factory=AppearancePreferences)
    navigation: NavigationPreferences = Field(default_factory=NavigationPreferences)
    dashboard: DashboardPreferences = Field(default_factory=DashboardPreferences)
    modulePreferences: dict = Field(default_factory=dict)
    notifications: NotificationPreferences = Field(
        default_factory=NotificationPreferences
    )
    locale: LocalePreferences = Field(default_factory=LocalePreferences)
    shortcuts: ShortcutPreferences = Field(default_factory=ShortcutPreferences)

    updatedAt: Optional[str] = None

    class Config:
        from_attributes = True


class UserPreferencesUpdate(BaseModel):
    """Schema for updating preferences - all fields optional"""

    appearance: Optional[AppearancePreferences] = None
    navigation: Optional[NavigationPreferences] = None
    dashboard: Optional[DashboardPreferences] = None
    modulePreferences: Optional[dict] = None
    notifications: Optional[NotificationPreferences] = None
    locale: Optional[LocalePreferences] = None
    shortcuts: Optional[ShortcutPreferences] = None
