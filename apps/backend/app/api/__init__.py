"""API router configuration."""

from fastapi import APIRouter

from app.api.auth import router as auth_router
from app.api.health import router as health_router
from app.api.preferences import router as preferences_router

router = APIRouter()

router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
router.include_router(health_router, prefix="/health", tags=["Health"])
router.include_router(preferences_router, tags=["Preferences"])
