"""Module Converter Models.

Diese Models unterstützen die Konvertierung von Modulen zwischen verschiedenen
Formaten und die Verwaltung von LLM-Konfigurationen.
"""

from datetime import datetime, timezone
from enum import Enum as PyEnum
from typing import Any
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    Float,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin, TenantModel


class LLMProvider(str, PyEnum):
    """Supported LLM providers."""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    AZURE_OPENAI = "azure_openai"
    OLLAMA = "ollama"
    MISTRAL = "mistral"
    CUSTOM = "custom"


class ConversionStatus(str, PyEnum):
    """Status of a module conversion job."""

    PENDING = "pending"
    QUEUED = "queued"
    PROCESSING = "processing"
    VALIDATING = "validating"
    STAGING = "staging"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ModuleType(str, PyEnum):
    """Types of modules that can be converted."""

    CORE = "core"
    DOMAIN = "domain"
    REPORTING = "reporting"
    DOCUMENTS = "documents"
    ADAPTERS = "adapters"
    INTEGRATIONS = "integrations"


class LLMConfiguration(Base, TimestampMixin):
    """LLM Provider Configuration for Module Conversion.

    Stores configuration for different LLM providers including
    API keys, model settings, and fallback configuration.
    """

    __tablename__ = "llm_configurations"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid4()),
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Provider settings
    provider: Mapped[str] = mapped_column(
        Enum(LLMProvider),
        nullable=False,
    )
    model_name: Mapped[str] = mapped_column(String(255), nullable=False)
    api_endpoint: Mapped[str | None] = mapped_column(String(512), nullable=True)

    # Encrypted API key stored separately or via reference
    api_key_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Model parameters
    temperature: Mapped[float] = mapped_column(Float, default=0.7, nullable=False)
    max_tokens: Mapped[int] = mapped_column(Integer, default=4096, nullable=False)
    top_p: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)

    # Extended configuration as JSONB
    config: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        default=dict,
        nullable=False,
    )

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Priority for fallback (lower = higher priority)
    priority: Mapped[int] = mapped_column(Integer, default=100, nullable=False)

    # Rate limiting
    requests_per_minute: Mapped[int] = mapped_column(
        Integer, default=60, nullable=False
    )
    tokens_per_minute: Mapped[int] = mapped_column(
        Integer, default=100000, nullable=False
    )

    # Relationships
    conversion_logs: Mapped[list["ModuleConversionLog"]] = relationship(
        "ModuleConversionLog",
        back_populates="llm_configuration",
        foreign_keys="ModuleConversionLog.llm_configuration_id",
    )


class ModuleTemplate(TenantModel):
    """Template for module structure and conversion rules.

    Defines the structure, validation rules, and conversion specifications
    for a module type.
    """

    __tablename__ = "module_templates"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    version: Mapped[str] = mapped_column(String(50), default="1.0.0", nullable=False)

    # Module metadata
    module_type: Mapped[str] = mapped_column(
        Enum(ModuleType),
        nullable=False,
    )
    package_name: Mapped[str] = mapped_column(
        String(255), nullable=False
    )  # e.g., @flowaudit/checklists

    # Source and target specifications
    source_spec: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        default=dict,
        nullable=False,
    )
    target_spec: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        default=dict,
        nullable=False,
    )

    # Conversion rules and prompts
    conversion_rules: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        default=dict,
        nullable=False,
    )
    system_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    conversion_prompt_template: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Validation
    validation_schema: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        default=dict,
        nullable=False,
    )

    # File patterns
    include_patterns: Mapped[list[str]] = mapped_column(
        JSONB,
        default=list,
        nullable=False,
    )
    exclude_patterns: Mapped[list[str]] = mapped_column(
        JSONB,
        default=lambda: ["node_modules", ".git", "__pycache__", "*.pyc"],
        nullable=False,
    )

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_public: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    conversion_logs: Mapped[list["ModuleConversionLog"]] = relationship(
        "ModuleConversionLog",
        back_populates="template",
    )


class ModuleConversionLog(TenantModel):
    """Log of module conversion operations.

    Tracks the complete history of conversion attempts including
    status, progress, errors, and results.
    """

    __tablename__ = "module_conversion_logs"

    # Job identification
    job_id: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        default=lambda: f"conv-{uuid4().hex[:12]}",
    )

    # References
    template_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("module_templates.id", ondelete="SET NULL"),
        nullable=True,
    )
    llm_configuration_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("llm_configurations.id", ondelete="SET NULL"),
        nullable=True,
    )

    # User who initiated
    initiated_by: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Status tracking
    status: Mapped[str] = mapped_column(
        Enum(ConversionStatus),
        default=ConversionStatus.PENDING,
        nullable=False,
    )
    progress: Mapped[int] = mapped_column(Integer, default=0, nullable=False)  # 0-100

    # Timing
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Source information
    source_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # github, upload, url
    source_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    source_branch: Mapped[str | None] = mapped_column(String(255), nullable=True)
    source_commit: Mapped[str | None] = mapped_column(String(64), nullable=True)

    # Input/Output data
    input_data: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        default=dict,
        nullable=False,
    )
    output_data: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        default=dict,
        nullable=False,
    )

    # Statistics
    files_processed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    files_converted: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    files_failed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    tokens_used: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # LLM interactions
    llm_requests: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB,
        default=list,
        nullable=False,
    )

    # Error handling
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_details: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    # Staging/GitHub information
    staging_branch: Mapped[str | None] = mapped_column(String(255), nullable=True)
    staging_pr_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    staging_pr_number: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Result artifacts
    result_artifacts: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB,
        default=list,
        nullable=False,
    )

    # Relationships
    template: Mapped["ModuleTemplate | None"] = relationship(
        "ModuleTemplate",
        back_populates="conversion_logs",
    )
    llm_configuration: Mapped["LLMConfiguration | None"] = relationship(
        "LLMConfiguration",
        back_populates="conversion_logs",
        foreign_keys=[llm_configuration_id],
    )
    user: Mapped["User | None"] = relationship(  # type: ignore
        "User",
        foreign_keys=[initiated_by],
    )


class GitHubIntegration(Base, TimestampMixin):
    """GitHub integration configuration for staging and PR creation.

    Stores GitHub credentials and repository configuration for
    automated PR creation and code staging.
    """

    __tablename__ = "github_integrations"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid4()),
    )

    # Owner identification (could be tenant or system-wide)
    tenant_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=True,
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # GitHub connection
    github_app_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    github_installation_id: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )
    access_token_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Repository defaults
    default_owner: Mapped[str] = mapped_column(String(255), nullable=False)
    default_repo: Mapped[str] = mapped_column(String(255), nullable=False)
    default_base_branch: Mapped[str] = mapped_column(
        String(255), default="main", nullable=False
    )

    # PR configuration
    pr_title_template: Mapped[str] = mapped_column(
        String(512),
        default="[Module Converter] {module_name} - {action}",
        nullable=False,
    )
    pr_body_template: Mapped[str | None] = mapped_column(Text, nullable=True)
    auto_merge: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    require_review: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Branch naming
    branch_prefix: Mapped[str] = mapped_column(
        String(100),
        default="module-converter/",
        nullable=False,
    )

    # Labels and reviewers
    default_labels: Mapped[list[str]] = mapped_column(
        JSONB,
        default=lambda: ["module-converter", "automated"],
        nullable=False,
    )
    default_reviewers: Mapped[list[str]] = mapped_column(
        JSONB,
        default=list,
        nullable=False,
    )

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_validated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    validation_status: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Configuration
    config: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        default=dict,
        nullable=False,
    )


class ConversionStep(Base, TimestampMixin):
    """Individual step in a conversion process.

    Tracks granular progress for each step of the conversion pipeline.
    """

    __tablename__ = "conversion_steps"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid4()),
    )

    # Parent conversion
    conversion_log_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("module_conversion_logs.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Step information
    step_number: Mapped[int] = mapped_column(Integer, nullable=False)
    step_name: Mapped[str] = mapped_column(String(255), nullable=False)
    step_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # analyze, transform, validate, stage

    # Status
    status: Mapped[str] = mapped_column(
        String(50),
        default="pending",
        nullable=False,
    )

    # Timing
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Input/Output
    input_data: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        default=dict,
        nullable=False,
    )
    output_data: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        default=dict,
        nullable=False,
    )

    # LLM interaction for this step
    llm_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    llm_response: Mapped[str | None] = mapped_column(Text, nullable=True)
    llm_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Error information
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Relationship
    conversion_log: Mapped["ModuleConversionLog"] = relationship(
        "ModuleConversionLog",
        backref="steps",
    )
