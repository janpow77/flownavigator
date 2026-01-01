"""Database models."""

from app.models.base import TenantModel, TimestampMixin
from app.models.tenant import Tenant
from app.models.user import User
from app.models.user_preferences import UserPreferences
from app.models.group_query import (
    GroupQuery,
    GroupQueryAssignment,
    GroupQueryResponse,
    GroupQueryAttachment,
)
from app.models.document_box import DocumentBox, BoxDocument
from app.models.audit_case import (
    AuditCase,
    AuditCaseChecklist,
    AuditCaseFinding,
    FiscalYear,
    ChecklistTemplate,
)
from app.models.audit_log import AuditLog
from app.models.module_converter import (
    LLMProvider,
    ConversionStatus,
    ModuleType,
    LLMConfiguration,
    ModuleTemplate,
    ModuleConversionLog,
    GitHubIntegration,
    ConversionStep,
)
# Layer 0: Vendor & Development
from app.models.vendor import Vendor, VendorUser, VendorRole
from app.models.customer import Customer, CustomerStatus, LicenseUsage, LicenseAlert
from app.models.module import Module, ModuleStatus, ModuleDeployment, DeploymentStatus, ReleaseNote
# Layer 1 & 2: Profiles
from app.models.profile import CoordinationBodyProfile, AuthorityProfile
# History (Feature 7)
from app.models.history import (
    ModuleEvent,
    LLMConversation,
    LLMMessage,
    LLMFeedback,
    EventType,
    FeedbackType,
)

__all__ = [
    "TenantModel",
    "TimestampMixin",
    "Tenant",
    "User",
    "UserPreferences",
    "GroupQuery",
    "GroupQueryAssignment",
    "GroupQueryResponse",
    "GroupQueryAttachment",
    "DocumentBox",
    "BoxDocument",
    "AuditCase",
    "AuditCaseChecklist",
    "AuditCaseFinding",
    "FiscalYear",
    "ChecklistTemplate",
    "AuditLog",
    # Module Converter
    "LLMProvider",
    "ConversionStatus",
    "ModuleType",
    "LLMConfiguration",
    "ModuleTemplate",
    "ModuleConversionLog",
    "GitHubIntegration",
    "ConversionStep",
    # Layer 0: Vendor & Development
    "Vendor",
    "VendorUser",
    "VendorRole",
    "Customer",
    "CustomerStatus",
    "LicenseUsage",
    "LicenseAlert",
    "Module",
    "ModuleStatus",
    "ModuleDeployment",
    "DeploymentStatus",
    "ReleaseNote",
    # Layer 1 & 2: Profiles
    "CoordinationBodyProfile",
    "AuthorityProfile",
    # History (Feature 7)
    "ModuleEvent",
    "LLMConversation",
    "LLMMessage",
    "LLMFeedback",
    "EventType",
    "FeedbackType",
]
