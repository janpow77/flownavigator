"""Vendor schemas for Layer 0."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field

from app.models.vendor import VendorRole


# Vendor Schemas
class VendorBase(BaseModel):
    """Base vendor schema."""

    name: str = Field(..., min_length=1, max_length=255)
    contact_email: EmailStr
    billing_email: EmailStr
    address_street: Optional[str] = None
    address_city: Optional[str] = None
    address_postal_code: Optional[str] = None
    address_country: str = "Deutschland"


class VendorCreate(VendorBase):
    """Schema for creating a vendor."""

    pass


class VendorUpdate(BaseModel):
    """Schema for updating a vendor."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    contact_email: Optional[EmailStr] = None
    billing_email: Optional[EmailStr] = None
    address_street: Optional[str] = None
    address_city: Optional[str] = None
    address_postal_code: Optional[str] = None
    address_country: Optional[str] = None


class VendorResponse(VendorBase):
    """Schema for vendor response."""

    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# VendorUser Schemas
class VendorUserBase(BaseModel):
    """Base vendor user schema."""

    email: EmailStr
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    role: VendorRole


class VendorUserCreate(VendorUserBase):
    """Schema for creating a vendor user."""

    password: str = Field(..., min_length=8)


class VendorUserUpdate(BaseModel):
    """Schema for updating a vendor user."""

    email: Optional[EmailStr] = None
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    role: Optional[VendorRole] = None
    is_active: Optional[bool] = None
    password: Optional[str] = Field(None, min_length=8)


class VendorUserResponse(BaseModel):
    """Schema for vendor user response."""

    id: str
    vendor_id: str
    email: str
    first_name: str
    last_name: str
    role: VendorRole
    is_active: bool
    last_login_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class VendorUserListResponse(BaseModel):
    """Schema for listing vendor users."""

    users: list[VendorUserResponse]
    total: int


# Vendor with users
class VendorWithUsersResponse(VendorResponse):
    """Vendor response with users."""

    users: list[VendorUserResponse] = []
