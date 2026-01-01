"""Profile schemas for Layer 1 and Layer 2."""

from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, EmailStr, Field, field_validator
import re


def validate_hex_color(v: str) -> str:
    """Validate hex color format."""
    if not re.match(r'^#[0-9A-Fa-f]{6}$', v):
        raise ValueError('Color must be in hex format (e.g., #1e40af)')
    return v.lower()


# Coordination Body Profile Schemas
class CBProfileBase(BaseModel):
    """Base schema for Coordination Body Profile."""

    official_name: str = Field(..., min_length=1, max_length=255)
    short_name: Optional[str] = Field(None, max_length=50)
    street: Optional[str] = Field(None, max_length=255)
    postal_code: Optional[str] = Field(None, max_length=20)
    city: Optional[str] = Field(None, max_length=100)
    country: str = "Deutschland"
    phone: Optional[str] = Field(None, max_length=50)
    email: Optional[EmailStr] = None
    website: Optional[str] = Field(None, max_length=255)


class CBProfileCreate(CBProfileBase):
    """Schema for creating a Coordination Body Profile."""

    primary_color: str = Field(default="#1e40af")
    secondary_color: str = Field(default="#3b82f6")

    @field_validator('primary_color', 'secondary_color')
    @classmethod
    def validate_colors(cls, v: str) -> str:
        return validate_hex_color(v)


class CBProfileUpdate(BaseModel):
    """Schema for updating a Coordination Body Profile."""

    official_name: Optional[str] = Field(None, min_length=1, max_length=255)
    short_name: Optional[str] = Field(None, max_length=50)
    street: Optional[str] = Field(None, max_length=255)
    postal_code: Optional[str] = Field(None, max_length=20)
    city: Optional[str] = Field(None, max_length=100)
    country: Optional[str] = None
    phone: Optional[str] = Field(None, max_length=50)
    email: Optional[EmailStr] = None
    website: Optional[str] = Field(None, max_length=255)
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None

    @field_validator('primary_color', 'secondary_color')
    @classmethod
    def validate_colors(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            return validate_hex_color(v)
        return v


class CBProfileResponse(CBProfileBase):
    """Schema for Coordination Body Profile response."""

    id: str
    tenant_id: str
    logo_url: Optional[str] = None
    primary_color: str
    secondary_color: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Authority Profile Schemas
class AuthorityProfileBase(BaseModel):
    """Base schema for Authority Profile."""

    official_name: str = Field(..., min_length=1, max_length=255)
    short_name: Optional[str] = Field(None, max_length=50)
    authority_type: Optional[Literal[
        'audit_authority', 'certifying_authority', 'managing_authority', 'intermediate_body'
    ]] = None
    street: Optional[str] = Field(None, max_length=255)
    postal_code: Optional[str] = Field(None, max_length=20)
    city: Optional[str] = Field(None, max_length=100)
    country: str = "Deutschland"
    phone: Optional[str] = Field(None, max_length=50)
    email: Optional[EmailStr] = None
    website: Optional[str] = Field(None, max_length=255)


class AuthorityProfileCreate(AuthorityProfileBase):
    """Schema for creating an Authority Profile."""

    use_parent_branding: bool = True
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None

    @field_validator('primary_color', 'secondary_color')
    @classmethod
    def validate_colors(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            return validate_hex_color(v)
        return v


class AuthorityProfileUpdate(BaseModel):
    """Schema for updating an Authority Profile."""

    official_name: Optional[str] = Field(None, min_length=1, max_length=255)
    short_name: Optional[str] = Field(None, max_length=50)
    authority_type: Optional[Literal[
        'audit_authority', 'certifying_authority', 'managing_authority', 'intermediate_body'
    ]] = None
    street: Optional[str] = Field(None, max_length=255)
    postal_code: Optional[str] = Field(None, max_length=20)
    city: Optional[str] = Field(None, max_length=100)
    country: Optional[str] = None
    phone: Optional[str] = Field(None, max_length=50)
    email: Optional[EmailStr] = None
    website: Optional[str] = Field(None, max_length=255)
    use_parent_branding: Optional[bool] = None
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None

    @field_validator('primary_color', 'secondary_color')
    @classmethod
    def validate_colors(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            return validate_hex_color(v)
        return v


class AuthorityProfileResponse(AuthorityProfileBase):
    """Schema for Authority Profile response."""

    id: str
    tenant_id: str
    logo_url: Optional[str] = None
    use_parent_branding: bool
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AuthorityProfileWithBranding(AuthorityProfileResponse):
    """Authority Profile with effective branding."""

    effective_branding: dict
