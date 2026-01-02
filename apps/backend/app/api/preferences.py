"""User Preferences API Endpoints"""

import uuid
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.api.auth import get_current_user
from app.models.user import User
from app.models.user_preferences import UserPreferences
from app.schemas.preferences import UserPreferencesSchema, UserPreferencesUpdate

router = APIRouter(prefix="/preferences", tags=["preferences"])


@router.get("", response_model=UserPreferencesSchema)
async def get_preferences(
    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    """Get current user's preferences"""
    result = await db.execute(
        select(UserPreferences).where(UserPreferences.user_id == current_user.id)
    )
    preferences = result.scalar_one_or_none()

    if not preferences:
        # Return defaults if no preferences exist
        defaults = UserPreferences.get_defaults()
        return UserPreferencesSchema(
            userId=current_user.id,
            appearance=defaults["appearance"],
            navigation=defaults["navigation"],
            dashboard=defaults["dashboard"],
            modulePreferences=defaults["module_preferences"],
            notifications=defaults["notifications"],
            locale=defaults["locale"],
            shortcuts=defaults["shortcuts"],
        )

    return UserPreferencesSchema(
        id=preferences.id,
        userId=preferences.user_id,
        appearance=preferences.appearance,
        navigation=preferences.navigation,
        dashboard=preferences.dashboard,
        modulePreferences=preferences.module_preferences,
        notifications=preferences.notifications,
        locale=preferences.locale,
        shortcuts=preferences.shortcuts,
        updatedAt=(
            preferences.updated_at.isoformat() if preferences.updated_at else None
        ),
    )


@router.put("", response_model=UserPreferencesSchema)
async def update_preferences(
    preferences_update: UserPreferencesUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update current user's preferences"""
    result = await db.execute(
        select(UserPreferences).where(UserPreferences.user_id == current_user.id)
    )
    preferences = result.scalar_one_or_none()

    if not preferences:
        # Create new preferences
        defaults = UserPreferences.get_defaults()
        preferences = UserPreferences(
            id=str(uuid.uuid4()),
            user_id=current_user.id,
            appearance=defaults["appearance"],
            navigation=defaults["navigation"],
            dashboard=defaults["dashboard"],
            module_preferences=defaults["module_preferences"],
            notifications=defaults["notifications"],
            locale=defaults["locale"],
            shortcuts=defaults["shortcuts"],
        )
        db.add(preferences)

    # Update provided fields
    update_data = preferences_update.model_dump(exclude_unset=True)

    if "appearance" in update_data and update_data["appearance"]:
        preferences.appearance = {**preferences.appearance, **update_data["appearance"]}

    if "navigation" in update_data and update_data["navigation"]:
        preferences.navigation = {**preferences.navigation, **update_data["navigation"]}

    if "dashboard" in update_data and update_data["dashboard"]:
        preferences.dashboard = {**preferences.dashboard, **update_data["dashboard"]}

    if "modulePreferences" in update_data and update_data["modulePreferences"]:
        preferences.module_preferences = {
            **preferences.module_preferences,
            **update_data["modulePreferences"],
        }

    if "notifications" in update_data and update_data["notifications"]:
        preferences.notifications = {
            **preferences.notifications,
            **update_data["notifications"],
        }

    if "locale" in update_data and update_data["locale"]:
        preferences.locale = {**preferences.locale, **update_data["locale"]}

    if "shortcuts" in update_data and update_data["shortcuts"]:
        preferences.shortcuts = {**preferences.shortcuts, **update_data["shortcuts"]}

    await db.commit()
    await db.refresh(preferences)

    return UserPreferencesSchema(
        id=preferences.id,
        userId=preferences.user_id,
        appearance=preferences.appearance,
        navigation=preferences.navigation,
        dashboard=preferences.dashboard,
        modulePreferences=preferences.module_preferences,
        notifications=preferences.notifications,
        locale=preferences.locale,
        shortcuts=preferences.shortcuts,
        updatedAt=(
            preferences.updated_at.isoformat() if preferences.updated_at else None
        ),
    )


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
async def reset_preferences(
    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    """Reset preferences to defaults"""
    result = await db.execute(
        select(UserPreferences).where(UserPreferences.user_id == current_user.id)
    )
    preferences = result.scalar_one_or_none()

    if preferences:
        await db.delete(preferences)
        await db.commit()

    return None
