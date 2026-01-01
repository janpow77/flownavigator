"""Dashboard schemas for Layer Dashboard."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel

from app.models.customer import CustomerStatus


class VendorSummary(BaseModel):
    """Vendor summary for dashboard."""

    id: str
    name: str
    total_customers: int
    total_licenses: int
    total_users: int
    active_modules: int


class AuthoritySummary(BaseModel):
    """Authority summary for dashboard drill-down."""

    id: str
    name: str
    user_count: int
    active_cases: int
    authority_head: Optional[str] = None
    status: str


class CustomerSummary(BaseModel):
    """Customer summary for dashboard."""

    id: str
    name: str
    tenant_id: str
    contract_number: str
    licensed_users: int
    active_users: int
    licensed_authorities: int
    active_authorities: int
    license_percent: float
    authority_percent: float
    authority_count: int
    status: CustomerStatus
    authorities: Optional[list[AuthoritySummary]] = None


class LayerDashboardResponse(BaseModel):
    """Response for layer dashboard."""

    vendor: Optional[VendorSummary] = None
    total_customers: int
    total_licenses: int
    total_users: int
    customers: list[CustomerSummary]


class CustomerDetailResponse(BaseModel):
    """Detailed customer view for dashboard."""

    customer: CustomerSummary
    authorities: list[AuthoritySummary]
    recent_activity: list[dict] = []
    license_trend: list[dict] = []


class AuthorityDetailResponse(BaseModel):
    """Detailed authority view for dashboard."""

    authority: AuthoritySummary
    users: list[dict] = []
    recent_cases: list[dict] = []
    active_checklists: int = 0
    pending_findings: int = 0
