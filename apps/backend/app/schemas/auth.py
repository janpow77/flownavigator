"""Authentication schemas."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    """Schema for creating a new user."""

    email: EmailStr
    password: str
    first_name: str
    last_name: str
    role: Literal[
        "system_admin",
        "group_admin",
        "authority_head",
        "team_leader",
        "auditor",
        "viewer",
    ]
    tenant_id: str


class UserLogin(BaseModel):
    """Schema for user login."""

    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """Schema for user response."""

    id: str
    email: str
    first_name: str
    last_name: str
    role: str
    tenant_id: str
    is_active: bool
    last_login_at: datetime | None
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    """Schema for JWT token response."""

    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class TokenData(BaseModel):
    """Schema for token payload data."""

    user_id: str
    tenant_id: str
    role: str
