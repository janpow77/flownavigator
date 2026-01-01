"""Customer schemas for Layer 0."""

from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field

from app.models.customer import CustomerStatus


# Customer Schemas
class CustomerBase(BaseModel):
    """Base customer schema."""

    contract_number: str = Field(..., min_length=1, max_length=50)
    licensed_users: int = Field(default=10, ge=1)
    licensed_authorities: int = Field(default=1, ge=1)


class CustomerCreate(CustomerBase):
    """Schema for creating a customer."""

    tenant_name: str = Field(..., min_length=1, max_length=255, description="Name for the tenant to create")
    tenant_type: str = Field(default="group", pattern="^(group|authority)$")
    contract_start: Optional[date] = None
    contract_end: Optional[date] = None
    billing_contact: Optional[str] = None
    billing_email: Optional[EmailStr] = None
    billing_address_street: Optional[str] = None
    billing_address_city: Optional[str] = None
    billing_address_postal_code: Optional[str] = None
    billing_address_country: str = "Deutschland"
    payment_method: Optional[str] = None
    status: CustomerStatus = CustomerStatus.active


class CustomerUpdate(BaseModel):
    """Schema for updating a customer."""

    contract_number: Optional[str] = Field(None, min_length=1, max_length=50)
    contract_start: Optional[date] = None
    contract_end: Optional[date] = None
    licensed_users: Optional[int] = Field(None, ge=1)
    licensed_authorities: Optional[int] = Field(None, ge=1)
    billing_contact: Optional[str] = None
    billing_email: Optional[EmailStr] = None
    billing_address_street: Optional[str] = None
    billing_address_city: Optional[str] = None
    billing_address_postal_code: Optional[str] = None
    billing_address_country: Optional[str] = None
    payment_method: Optional[str] = None
    status: Optional[CustomerStatus] = None


class CustomerResponse(BaseModel):
    """Schema for customer response."""

    id: str
    vendor_id: Optional[str]
    tenant_id: str
    contract_number: str
    contract_start: Optional[date]
    contract_end: Optional[date]
    licensed_users: int
    licensed_authorities: int
    billing_contact: Optional[str]
    billing_email: Optional[str]
    billing_address_street: Optional[str]
    billing_address_city: Optional[str]
    billing_address_postal_code: Optional[str]
    billing_address_country: str
    payment_method: Optional[str]
    status: CustomerStatus
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CustomerListResponse(BaseModel):
    """Schema for listing customers."""

    customers: list[CustomerResponse]
    total: int


# License Usage Schemas
class LicenseUsageResponse(BaseModel):
    """Schema for license usage response."""

    id: str
    customer_id: str
    date: date
    active_users: int
    active_authorities: int
    created_at: datetime

    class Config:
        from_attributes = True


class LicenseUsageCreate(BaseModel):
    """Schema for creating license usage record."""

    date: date
    active_users: int = Field(ge=0)
    active_authorities: int = Field(ge=0)


class LicenseHistoryResponse(BaseModel):
    """Schema for license usage history."""

    history: list[LicenseUsageResponse]
    licensed_users: int
    licensed_authorities: int
    current_user_percent: float
    current_authority_percent: float


class LicenseAdjustRequest(BaseModel):
    """Schema for adjusting licenses."""

    licensed_users: Optional[int] = Field(None, ge=1)
    licensed_authorities: Optional[int] = Field(None, ge=1)


# License Alert Schemas
class LicenseAlertResponse(BaseModel):
    """Schema for license alert response."""

    id: str
    customer_id: str
    alert_type: str
    message: str
    threshold_percent: int
    current_percent: int
    acknowledged: bool
    acknowledged_at: Optional[datetime]
    acknowledged_by: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class LicenseAlertAcknowledge(BaseModel):
    """Schema for acknowledging a license alert."""

    acknowledged: bool = True


# Customer with license info
class CustomerWithLicensesResponse(CustomerResponse):
    """Customer response with license information."""

    license_usages: list[LicenseUsageResponse] = []
    license_alerts: list[LicenseAlertResponse] = []
    current_active_users: int = 0
    current_active_authorities: int = 0
    user_license_percent: float = 0.0
    authority_license_percent: float = 0.0
