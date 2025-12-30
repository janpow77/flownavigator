"""Add audit cases tables

Revision ID: 003
Revises: 002
Create Date: 2024-12-30

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create enums with DO block to check if they exist
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'audit_case_status') THEN
                CREATE TYPE audit_case_status AS ENUM ('draft', 'in_progress', 'review', 'completed', 'archived');
            END IF;
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'audit_type') THEN
                CREATE TYPE audit_type AS ENUM ('operation', 'system', 'accounts');
            END IF;
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'audit_result') THEN
                CREATE TYPE audit_result AS ENUM ('no_findings', 'findings_minor', 'findings_major', 'irregularity');
            END IF;
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'checklist_type') THEN
                CREATE TYPE checklist_type AS ENUM ('main', 'procurement', 'subsidy', 'eligibility', 'custom');
            END IF;
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'checklist_status') THEN
                CREATE TYPE checklist_status AS ENUM ('not_started', 'in_progress', 'completed');
            END IF;
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'finding_type') THEN
                CREATE TYPE finding_type AS ENUM ('irregularity', 'deficiency', 'recommendation', 'observation');
            END IF;
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'error_category') THEN
                CREATE TYPE error_category AS ENUM ('ineligible_expenditure', 'public_procurement', 'missing_documents', 'calculation_error', 'double_funding', 'other');
            END IF;
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'finding_status') THEN
                CREATE TYPE finding_status AS ENUM ('draft', 'confirmed', 'disputed', 'resolved', 'withdrawn');
            END IF;
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'fiscal_year_status') THEN
                CREATE TYPE fiscal_year_status AS ENUM ('planning', 'active', 'closing', 'closed');
            END IF;
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'template_checklist_type') THEN
                CREATE TYPE template_checklist_type AS ENUM ('main', 'procurement', 'subsidy', 'eligibility', 'system', 'custom');
            END IF;
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'template_status') THEN
                CREATE TYPE template_status AS ENUM ('draft', 'published', 'archived');
            END IF;
        END$$;
    """)

    # Create fiscal_years table
    op.create_table(
        "fiscal_years",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("status", postgresql.ENUM("planning", "active", "closing", "closed", name="fiscal_year_status", create_type=False), nullable=False, server_default="planning"),
        sa.Column("config", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("statistics", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_fiscal_years_tenant_id", "fiscal_years", ["tenant_id"])

    # Create checklist_templates table
    op.create_table(
        "checklist_templates",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("is_current", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("checklist_type", postgresql.ENUM("main", "procurement", "subsidy", "eligibility", "system", "custom", name="template_checklist_type", create_type=False), nullable=False, server_default="main"),
        sa.Column("structure", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("status", postgresql.ENUM("draft", "published", "archived", name="template_status", create_type=False), nullable=False, server_default="draft"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_checklist_templates_tenant_id", "checklist_templates", ["tenant_id"])

    # Create audit_cases table
    op.create_table(
        "audit_cases",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("fiscal_year_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("case_number", sa.String(50), nullable=False),
        sa.Column("external_id", sa.String(100), nullable=True),
        sa.Column("project_name", sa.String(500), nullable=False),
        sa.Column("beneficiary_name", sa.String(500), nullable=False),
        sa.Column("approved_amount", sa.Numeric(15, 2), nullable=True),
        sa.Column("audited_amount", sa.Numeric(15, 2), nullable=True),
        sa.Column("irregular_amount", sa.Numeric(15, 2), nullable=True),
        sa.Column("status", postgresql.ENUM("draft", "in_progress", "review", "completed", "archived", name="audit_case_status", create_type=False), nullable=False, server_default="draft"),
        sa.Column("audit_type", postgresql.ENUM("operation", "system", "accounts", name="audit_type", create_type=False), nullable=False, server_default="operation"),
        sa.Column("audit_start_date", sa.Date(), nullable=True),
        sa.Column("audit_end_date", sa.Date(), nullable=True),
        sa.Column("primary_auditor_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("secondary_auditor_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("team_leader_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("result", postgresql.ENUM("no_findings", "findings_minor", "findings_major", "irregularity", name="audit_result", create_type=False), nullable=True),
        sa.Column("custom_data", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("is_sample", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("requires_follow_up", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("internal_notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["fiscal_year_id"], ["fiscal_years.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["primary_auditor_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["secondary_auditor_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["team_leader_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_audit_cases_tenant_id", "audit_cases", ["tenant_id"])
    op.create_index("ix_audit_cases_fiscal_year_id", "audit_cases", ["fiscal_year_id"])
    op.create_index("ix_audit_cases_case_number", "audit_cases", ["case_number"])
    op.create_index("ix_audit_cases_status", "audit_cases", ["status"])

    # Create audit_case_checklists table
    op.create_table(
        "audit_case_checklists",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("audit_case_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("checklist_template_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("checklist_type", postgresql.ENUM("main", "procurement", "subsidy", "eligibility", "custom", name="checklist_type", create_type=False), nullable=False, server_default="main"),
        sa.Column("status", postgresql.ENUM("not_started", "in_progress", "completed", name="checklist_status", create_type=False), nullable=False, server_default="not_started"),
        sa.Column("progress", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_questions", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("answered_questions", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("responses", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("completed_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["audit_case_id"], ["audit_cases.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["checklist_template_id"], ["checklist_templates.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["completed_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_audit_case_checklists_audit_case_id", "audit_case_checklists", ["audit_case_id"])

    # Create audit_case_findings table
    op.create_table(
        "audit_case_findings",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("audit_case_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("finding_number", sa.Integer(), nullable=False),
        sa.Column("finding_type", postgresql.ENUM("irregularity", "deficiency", "recommendation", "observation", name="finding_type", create_type=False), nullable=False),
        sa.Column("error_category", postgresql.ENUM("ineligible_expenditure", "public_procurement", "missing_documents", "calculation_error", "double_funding", "other", name="error_category", create_type=False), nullable=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("financial_impact", sa.Numeric(15, 2), nullable=True),
        sa.Column("is_systemic", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("status", postgresql.ENUM("draft", "confirmed", "disputed", "resolved", "withdrawn", name="finding_status", create_type=False), nullable=False, server_default="draft"),
        sa.Column("response_requested", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("response_deadline", sa.Date(), nullable=True),
        sa.Column("response_received", sa.Text(), nullable=True),
        sa.Column("response_received_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("final_assessment", sa.Text(), nullable=True),
        sa.Column("corrective_action", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["audit_case_id"], ["audit_cases.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_audit_case_findings_audit_case_id", "audit_case_findings", ["audit_case_id"])

    # Update document_boxes to reference audit_cases
    op.create_foreign_key(
        "fk_document_boxes_audit_case_id",
        "document_boxes",
        "audit_cases",
        ["audit_case_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    # Remove foreign key from document_boxes
    op.drop_constraint("fk_document_boxes_audit_case_id", "document_boxes", type_="foreignkey")

    # Drop tables
    op.drop_index("ix_audit_case_findings_audit_case_id", table_name="audit_case_findings")
    op.drop_table("audit_case_findings")

    op.drop_index("ix_audit_case_checklists_audit_case_id", table_name="audit_case_checklists")
    op.drop_table("audit_case_checklists")

    op.drop_index("ix_audit_cases_status", table_name="audit_cases")
    op.drop_index("ix_audit_cases_case_number", table_name="audit_cases")
    op.drop_index("ix_audit_cases_fiscal_year_id", table_name="audit_cases")
    op.drop_index("ix_audit_cases_tenant_id", table_name="audit_cases")
    op.drop_table("audit_cases")

    op.drop_index("ix_checklist_templates_tenant_id", table_name="checklist_templates")
    op.drop_table("checklist_templates")

    op.drop_index("ix_fiscal_years_tenant_id", table_name="fiscal_years")
    op.drop_table("fiscal_years")

    # Drop enums
    op.execute("DROP TYPE IF EXISTS template_status")
    op.execute("DROP TYPE IF EXISTS template_checklist_type")
    op.execute("DROP TYPE IF EXISTS fiscal_year_status")
    op.execute("DROP TYPE IF EXISTS finding_status")
    op.execute("DROP TYPE IF EXISTS error_category")
    op.execute("DROP TYPE IF EXISTS finding_type")
    op.execute("DROP TYPE IF EXISTS checklist_status")
    op.execute("DROP TYPE IF EXISTS checklist_type")
    op.execute("DROP TYPE IF EXISTS audit_result")
    op.execute("DROP TYPE IF EXISTS audit_type")
    op.execute("DROP TYPE IF EXISTS audit_case_status")
