"""Add module converter tables

Revision ID: 006
Revises: 005
Create Date: 2025-12-31

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "006"
down_revision: Union[str, None] = "005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create enums
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'llm_provider') THEN
                CREATE TYPE llm_provider AS ENUM (
                    'openai', 'anthropic', 'azure_openai', 'ollama', 'mistral', 'custom'
                );
            END IF;
        END$$;
    """
    )

    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'conversion_status') THEN
                CREATE TYPE conversion_status AS ENUM (
                    'pending', 'queued', 'processing', 'validating',
                    'staging', 'completed', 'failed', 'cancelled'
                );
            END IF;
        END$$;
    """
    )

    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'module_type') THEN
                CREATE TYPE module_type AS ENUM (
                    'core', 'domain', 'reporting', 'documents', 'adapters', 'integrations'
                );
            END IF;
        END$$;
    """
    )

    # Create llm_configurations table
    op.create_table(
        "llm_configurations",
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "provider",
            postgresql.ENUM(
                "openai",
                "anthropic",
                "azure_openai",
                "ollama",
                "mistral",
                "custom",
                name="llm_provider",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("model_name", sa.String(255), nullable=False),
        sa.Column("api_endpoint", sa.String(512), nullable=True),
        sa.Column("api_key_encrypted", sa.Text(), nullable=True),
        sa.Column("temperature", sa.Float(), default=0.7, nullable=False),
        sa.Column("max_tokens", sa.Integer(), default=4096, nullable=False),
        sa.Column("top_p", sa.Float(), default=1.0, nullable=False),
        sa.Column(
            "config",
            postgresql.JSONB(astext_type=sa.Text()),
            default={},
            nullable=False,
        ),
        sa.Column("is_active", sa.Boolean(), default=True, nullable=False),
        sa.Column("is_default", sa.Boolean(), default=False, nullable=False),
        sa.Column("priority", sa.Integer(), default=100, nullable=False),
        sa.Column("requests_per_minute", sa.Integer(), default=60, nullable=False),
        sa.Column("tokens_per_minute", sa.Integer(), default=100000, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_llm_configurations_provider", "llm_configurations", ["provider"]
    )
    op.create_index(
        "ix_llm_configurations_is_active", "llm_configurations", ["is_active"]
    )
    op.create_index(
        "ix_llm_configurations_priority", "llm_configurations", ["priority"]
    )

    # Create module_templates table
    op.create_table(
        "module_templates",
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("display_name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("version", sa.String(50), default="1.0.0", nullable=False),
        sa.Column(
            "module_type",
            postgresql.ENUM(
                "core",
                "domain",
                "reporting",
                "documents",
                "adapters",
                "integrations",
                name="module_type",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("package_name", sa.String(255), nullable=False),
        sa.Column(
            "source_spec",
            postgresql.JSONB(astext_type=sa.Text()),
            default={},
            nullable=False,
        ),
        sa.Column(
            "target_spec",
            postgresql.JSONB(astext_type=sa.Text()),
            default={},
            nullable=False,
        ),
        sa.Column(
            "conversion_rules",
            postgresql.JSONB(astext_type=sa.Text()),
            default={},
            nullable=False,
        ),
        sa.Column("system_prompt", sa.Text(), nullable=True),
        sa.Column("conversion_prompt_template", sa.Text(), nullable=True),
        sa.Column(
            "validation_schema",
            postgresql.JSONB(astext_type=sa.Text()),
            default={},
            nullable=False,
        ),
        sa.Column(
            "include_patterns",
            postgresql.JSONB(astext_type=sa.Text()),
            default=[],
            nullable=False,
        ),
        sa.Column(
            "exclude_patterns",
            postgresql.JSONB(astext_type=sa.Text()),
            default=[],
            nullable=False,
        ),
        sa.Column("is_active", sa.Boolean(), default=True, nullable=False),
        sa.Column("is_public", sa.Boolean(), default=False, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_module_templates_tenant_id", "module_templates", ["tenant_id"])
    op.create_index(
        "ix_module_templates_module_type", "module_templates", ["module_type"]
    )
    op.create_index("ix_module_templates_is_active", "module_templates", ["is_active"])

    # Create github_integrations table
    op.create_table(
        "github_integrations",
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("github_app_id", sa.String(255), nullable=True),
        sa.Column("github_installation_id", sa.String(255), nullable=True),
        sa.Column("access_token_encrypted", sa.Text(), nullable=True),
        sa.Column("default_owner", sa.String(255), nullable=False),
        sa.Column("default_repo", sa.String(255), nullable=False),
        sa.Column(
            "default_base_branch", sa.String(255), default="main", nullable=False
        ),
        sa.Column(
            "pr_title_template",
            sa.String(512),
            default="[Module Converter] {module_name} - {action}",
            nullable=False,
        ),
        sa.Column("pr_body_template", sa.Text(), nullable=True),
        sa.Column("auto_merge", sa.Boolean(), default=False, nullable=False),
        sa.Column("require_review", sa.Boolean(), default=True, nullable=False),
        sa.Column(
            "branch_prefix", sa.String(100), default="module-converter/", nullable=False
        ),
        sa.Column(
            "default_labels",
            postgresql.JSONB(astext_type=sa.Text()),
            default=[],
            nullable=False,
        ),
        sa.Column(
            "default_reviewers",
            postgresql.JSONB(astext_type=sa.Text()),
            default=[],
            nullable=False,
        ),
        sa.Column("is_active", sa.Boolean(), default=True, nullable=False),
        sa.Column("last_validated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("validation_status", sa.String(50), nullable=True),
        sa.Column(
            "config",
            postgresql.JSONB(astext_type=sa.Text()),
            default={},
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_github_integrations_tenant_id", "github_integrations", ["tenant_id"]
    )
    op.create_index(
        "ix_github_integrations_is_active", "github_integrations", ["is_active"]
    )

    # Create module_conversion_logs table
    op.create_table(
        "module_conversion_logs",
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("job_id", sa.String(255), unique=True, nullable=False),
        sa.Column("template_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column(
            "llm_configuration_id", postgresql.UUID(as_uuid=False), nullable=True
        ),
        sa.Column("initiated_by", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column(
            "status",
            postgresql.ENUM(
                "pending",
                "queued",
                "processing",
                "validating",
                "staging",
                "completed",
                "failed",
                "cancelled",
                name="conversion_status",
                create_type=False,
            ),
            default="pending",
            nullable=False,
        ),
        sa.Column("progress", sa.Integer(), default=0, nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("source_type", sa.String(50), nullable=False),
        sa.Column("source_url", sa.String(1024), nullable=True),
        sa.Column("source_branch", sa.String(255), nullable=True),
        sa.Column("source_commit", sa.String(64), nullable=True),
        sa.Column(
            "input_data",
            postgresql.JSONB(astext_type=sa.Text()),
            default={},
            nullable=False,
        ),
        sa.Column(
            "output_data",
            postgresql.JSONB(astext_type=sa.Text()),
            default={},
            nullable=False,
        ),
        sa.Column("files_processed", sa.Integer(), default=0, nullable=False),
        sa.Column("files_converted", sa.Integer(), default=0, nullable=False),
        sa.Column("files_failed", sa.Integer(), default=0, nullable=False),
        sa.Column("tokens_used", sa.Integer(), default=0, nullable=False),
        sa.Column(
            "llm_requests",
            postgresql.JSONB(astext_type=sa.Text()),
            default=[],
            nullable=False,
        ),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column(
            "error_details", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
        sa.Column("staging_branch", sa.String(255), nullable=True),
        sa.Column("staging_pr_url", sa.String(1024), nullable=True),
        sa.Column("staging_pr_number", sa.Integer(), nullable=True),
        sa.Column(
            "result_artifacts",
            postgresql.JSONB(astext_type=sa.Text()),
            default=[],
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["template_id"], ["module_templates.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["llm_configuration_id"], ["llm_configurations.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(["initiated_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_module_conversion_logs_tenant_id", "module_conversion_logs", ["tenant_id"]
    )
    op.create_index(
        "ix_module_conversion_logs_job_id", "module_conversion_logs", ["job_id"]
    )
    op.create_index(
        "ix_module_conversion_logs_status", "module_conversion_logs", ["status"]
    )
    op.create_index(
        "ix_module_conversion_logs_template_id",
        "module_conversion_logs",
        ["template_id"],
    )
    op.create_index(
        "ix_module_conversion_logs_created_at", "module_conversion_logs", ["created_at"]
    )

    # Create conversion_steps table
    op.create_table(
        "conversion_steps",
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("conversion_log_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("step_number", sa.Integer(), nullable=False),
        sa.Column("step_name", sa.String(255), nullable=False),
        sa.Column("step_type", sa.String(50), nullable=False),
        sa.Column("status", sa.String(50), default="pending", nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column(
            "input_data",
            postgresql.JSONB(astext_type=sa.Text()),
            default={},
            nullable=False,
        ),
        sa.Column(
            "output_data",
            postgresql.JSONB(astext_type=sa.Text()),
            default={},
            nullable=False,
        ),
        sa.Column("llm_prompt", sa.Text(), nullable=True),
        sa.Column("llm_response", sa.Text(), nullable=True),
        sa.Column("llm_tokens", sa.Integer(), default=0, nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("retry_count", sa.Integer(), default=0, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["conversion_log_id"], ["module_conversion_logs.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_conversion_steps_conversion_log_id",
        "conversion_steps",
        ["conversion_log_id"],
    )
    op.create_index(
        "ix_conversion_steps_step_number", "conversion_steps", ["step_number"]
    )
    op.create_index("ix_conversion_steps_status", "conversion_steps", ["status"])


def downgrade() -> None:
    op.drop_table("conversion_steps")
    op.drop_table("module_conversion_logs")
    op.drop_table("github_integrations")
    op.drop_table("module_templates")
    op.drop_table("llm_configurations")
    op.execute("DROP TYPE IF EXISTS module_type")
    op.execute("DROP TYPE IF EXISTS conversion_status")
    op.execute("DROP TYPE IF EXISTS llm_provider")
