"""Health check endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db

router = APIRouter()


@router.get("")
async def health_check(db: AsyncSession = Depends(get_db)) -> dict[str, str]:
    """Check API and database health."""
    try:
        await db.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception:
        db_status = "unhealthy"

    return {
        "api": "healthy",
        "database": db_status,
    }
