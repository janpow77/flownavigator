"""Authentication service."""

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    create_access_token,
    get_password_hash,
    verify_password,
)
from app.models.user import User
from app.schemas.auth import UserCreate, UserResponse


class AuthService:
    """Authentication service."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_user_by_email(self, email: str) -> User | None:
        """Get user by email."""
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_user_by_id(self, user_id: str) -> User | None:
        """Get user by ID."""
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def create_user(self, data: UserCreate) -> User:
        """Create a new user."""
        user = User(
            email=data.email,
            hashed_password=get_password_hash(data.password),
            first_name=data.first_name,
            last_name=data.last_name,
            role=data.role,
            tenant_id=data.tenant_id,
        )
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)
        return user

    async def authenticate_user(
        self,
        email: str,
        password: str,
    ) -> User | None:
        """Authenticate user with email and password."""
        user = await self.get_user_by_email(email)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        if not user.is_active:
            return None

        # Update last login
        user.last_login_at = datetime.now(timezone.utc)
        await self.db.flush()

        return user

    def create_token_for_user(self, user: User) -> str:
        """Create JWT token for user."""
        return create_access_token(
            data={
                "sub": user.id,
                "tenant_id": user.tenant_id,
                "role": user.role,
            }
        )

    def user_to_response(self, user: User) -> UserResponse:
        """Convert user model to response schema."""
        return UserResponse(
            id=user.id,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            role=user.role,
            tenant_id=user.tenant_id,
            is_active=user.is_active,
            last_login_at=user.last_login_at,
            created_at=user.created_at,
        )
