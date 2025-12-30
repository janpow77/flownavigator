"""Audit Case schemas."""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional, Any

from pydantic import BaseModel, Field, ConfigDict


# --- Enums as string literals ---

AuditCaseStatus = str  # draft, in_progress, review, completed, archived
AuditType = str  # operation, system, accounts
AuditResult = str  # no_findings, findings_minor, findings_major, irregularity


# --- Base Schemas ---

class AuditCaseBase(BaseModel):
    """Base schema for audit case."""

    case_number: str = Field(..., min_length=1, max_length=50)
    external_id: Optional[str] = Field(None, max_length=100)
    project_name: str = Field(..., min_length=1, max_length=500)
    beneficiary_name: str = Field(..., min_length=1, max_length=500)
    audit_type: AuditType = "operation"

    approved_amount: Optional[Decimal] = None
    audited_amount: Optional[Decimal] = None

    audit_start_date: Optional[date] = None
    audit_end_date: Optional[date] = None

    primary_auditor_id: Optional[str] = None
    secondary_auditor_id: Optional[str] = None
    team_leader_id: Optional[str] = None

    is_sample: bool = False
    custom_data: dict[str, Any] = Field(default_factory=dict)
    internal_notes: Optional[str] = None


class AuditCaseCreate(AuditCaseBase):
    """Schema for creating an audit case."""

    fiscal_year_id: Optional[str] = None


class AuditCaseUpdate(BaseModel):
    """Schema for updating an audit case."""

    case_number: Optional[str] = Field(None, min_length=1, max_length=50)
    external_id: Optional[str] = Field(None, max_length=100)
    project_name: Optional[str] = Field(None, min_length=1, max_length=500)
    beneficiary_name: Optional[str] = Field(None, min_length=1, max_length=500)
    audit_type: Optional[AuditType] = None

    approved_amount: Optional[Decimal] = None
    audited_amount: Optional[Decimal] = None
    irregular_amount: Optional[Decimal] = None

    status: Optional[AuditCaseStatus] = None
    result: Optional[AuditResult] = None

    audit_start_date: Optional[date] = None
    audit_end_date: Optional[date] = None

    primary_auditor_id: Optional[str] = None
    secondary_auditor_id: Optional[str] = None
    team_leader_id: Optional[str] = None
    fiscal_year_id: Optional[str] = None

    is_sample: Optional[bool] = None
    requires_follow_up: Optional[bool] = None
    custom_data: Optional[dict[str, Any]] = None
    internal_notes: Optional[str] = None


class AuditCaseResponse(AuditCaseBase):
    """Schema for audit case response."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    fiscal_year_id: Optional[str] = None

    status: AuditCaseStatus
    result: Optional[AuditResult] = None
    irregular_amount: Optional[Decimal] = None
    requires_follow_up: bool = False

    created_at: datetime
    updated_at: datetime


class AuditCaseListResponse(BaseModel):
    """Schema for paginated audit case list."""

    items: list[AuditCaseResponse]
    total: int
    page: int
    page_size: int
    pages: int


class AuditCaseSummary(BaseModel):
    """Summary schema for audit case (minimal fields)."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    case_number: str
    project_name: str
    beneficiary_name: str
    status: AuditCaseStatus
    result: Optional[AuditResult] = None
    audit_type: AuditType
    audited_amount: Optional[Decimal] = None
    irregular_amount: Optional[Decimal] = None


# --- Auditor Schemas ---

class AuditorInfo(BaseModel):
    """Minimal auditor info."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    first_name: str
    last_name: str
    email: str


class AuditCaseDetailResponse(AuditCaseResponse):
    """Detailed audit case response with relationships."""

    primary_auditor: Optional[AuditorInfo] = None
    secondary_auditor: Optional[AuditorInfo] = None
    team_leader: Optional[AuditorInfo] = None

    checklists_count: int = 0
    findings_count: int = 0
    documents_count: int = 0


# --- Finding Schemas ---

class FindingBase(BaseModel):
    """Base schema for finding."""

    finding_type: str  # irregularity, deficiency, recommendation, observation
    error_category: Optional[str] = None
    title: str = Field(..., min_length=1, max_length=500)
    description: str
    financial_impact: Optional[Decimal] = None
    is_systemic: bool = False

    response_requested: bool = False
    response_deadline: Optional[date] = None


class FindingCreate(FindingBase):
    """Schema for creating a finding."""
    pass


class FindingUpdate(BaseModel):
    """Schema for updating a finding."""

    finding_type: Optional[str] = None
    error_category: Optional[str] = None
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    description: Optional[str] = None
    financial_impact: Optional[Decimal] = None
    is_systemic: Optional[bool] = None
    status: Optional[str] = None

    response_requested: Optional[bool] = None
    response_deadline: Optional[date] = None
    response_received: Optional[str] = None

    final_assessment: Optional[str] = None
    corrective_action: Optional[str] = None


class FindingResponse(FindingBase):
    """Schema for finding response."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    audit_case_id: str
    finding_number: int
    status: str

    response_received: Optional[str] = None
    response_received_at: Optional[datetime] = None
    final_assessment: Optional[str] = None
    corrective_action: Optional[str] = None

    created_at: datetime
    updated_at: datetime


# --- Checklist Schemas ---

class ChecklistSummary(BaseModel):
    """Summary schema for checklist."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    checklist_type: str
    status: str
    progress: int
    total_questions: int
    answered_questions: int


class ChecklistResponse(BaseModel):
    """Full checklist response."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    audit_case_id: str
    checklist_template_id: Optional[str] = None
    checklist_type: str
    status: str
    progress: int
    total_questions: int
    answered_questions: int
    responses: dict[str, Any]
    completed_by: Optional[str] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class ChecklistUpdate(BaseModel):
    """Schema for updating checklist responses."""

    responses: dict[str, Any]
    status: Optional[str] = None


# --- Statistics ---

class AuditCaseStatistics(BaseModel):
    """Statistics for audit cases."""

    total: int = 0
    by_status: dict[str, int] = Field(default_factory=dict)
    by_result: dict[str, int] = Field(default_factory=dict)
    by_type: dict[str, int] = Field(default_factory=dict)

    total_audited_amount: Decimal = Decimal("0")
    total_irregular_amount: Decimal = Decimal("0")
    error_rate: float = 0.0
