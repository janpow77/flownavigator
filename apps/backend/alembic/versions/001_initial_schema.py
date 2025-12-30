"""Initial schema with Tenant, User, GroupQuery, DocumentBox

Revision ID: 001
Revises:
Create Date: 2024-12-30

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enums
    op.execute("CREATE TYPE tenant_type AS ENUM ('group', 'authority')")
    op.execute("CREATE TYPE tenant_status AS ENUM ('active', 'suspended', 'trial')")
    op.execute(
        "CREATE TYPE user_role AS ENUM ("
        "'system_admin', 'group_admin', 'authority_head', "
        "'team_leader', 'auditor', 'viewer')"
    )
    op.execute(
        "CREATE TYPE group_query_category AS ENUM ("
        "'annual_report', 'quarterly_report', 'ad_hoc', "
        "'system_audit_summary', 'statistics')"
    )
    op.execute(
        "CREATE TYPE group_query_status AS ENUM ("
        "'draft', 'published', 'in_progress', 'evaluation', "
        "'completed', 'archived')"
    )
    op.execute(
        "CREATE TYPE assignment_status AS ENUM ("
        "'pending', 'in_progress', 'ready_for_review', "
        "'submitted', 'returned', 'accepted')"
    )
    op.execute(
        "CREATE TYPE verification_status AS ENUM ('pending', 'verified', 'rejected')"
    )
    op.execute("CREATE TYPE ai_provider AS ENUM ('flow_invoice', 'custom')")
    op.execute(
        "CREATE TYPE document_status AS ENUM "
        "('pending', 'verified', 'rejected', 'unclear')"
    )

    # Tenants
    op.create_table(
        "tenants",
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column(
            "type",
            postgresql.ENUM("group", "authority", name="tenant_type", create_type=False),
            nullable=False,
        ),
        sa.Column("parent_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column(
            "status",
            postgresql.ENUM(
                "active", "suspended", "trial", name="tenant_status", create_type=False
            ),
            nullable=False,
            server_default="active",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("id", name="pk_tenants"),
        sa.ForeignKeyConstraint(
            ["parent_id"],
            ["tenants.id"],
            name="fk_tenants_parent_id_tenants",
            ondelete="SET NULL",
        ),
    )

    # Users
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("first_name", sa.String(100), nullable=False),
        sa.Column("last_name", sa.String(100), nullable=False),
        sa.Column(
            "role",
            postgresql.ENUM(
                "system_admin",
                "group_admin",
                "authority_head",
                "team_leader",
                "auditor",
                "viewer",
                name="user_role",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("id", name="pk_users"),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenants.id"],
            name="fk_users_tenant_id_tenants",
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )
    op.create_index("ix_users_tenant_id", "users", ["tenant_id"])
    op.create_index("ix_users_email", "users", ["email"])

    # Group Queries
    op.create_table(
        "group_queries",
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "category",
            postgresql.ENUM(
                "annual_report",
                "quarterly_report",
                "ad_hoc",
                "system_audit_summary",
                "statistics",
                name="group_query_category",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("fiscal_year", sa.Integer(), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deadline", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "checklist_template_id", postgresql.UUID(as_uuid=False), nullable=False
        ),
        sa.Column("checklist_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("config", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column(
            "status",
            postgresql.ENUM(
                "draft",
                "published",
                "in_progress",
                "evaluation",
                "completed",
                "archived",
                name="group_query_status",
                create_type=False,
            ),
            nullable=False,
            server_default="draft",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("id", name="pk_group_queries"),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenants.id"],
            name="fk_group_queries_tenant_id_tenants",
            ondelete="CASCADE",
        ),
    )
    op.create_index("ix_group_queries_tenant_id", "group_queries", ["tenant_id"])
    op.create_index("ix_group_queries_status", "group_queries", ["status"])
    op.create_index("ix_group_queries_fiscal_year", "group_queries", ["fiscal_year"])

    # Group Query Assignments
    op.create_table(
        "group_query_assignments",
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("query_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("authority_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column(
            "status",
            postgresql.ENUM(
                "pending",
                "in_progress",
                "ready_for_review",
                "submitted",
                "returned",
                "accepted",
                name="assignment_status",
                create_type=False,
            ),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("progress", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("assigned_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("remarks", sa.Text(), nullable=True),
        sa.Column("internal_notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("id", name="pk_group_query_assignments"),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenants.id"],
            name="fk_group_query_assignments_tenant_id_tenants",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["query_id"],
            ["group_queries.id"],
            name="fk_group_query_assignments_query_id_group_queries",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["authority_id"],
            ["tenants.id"],
            name="fk_group_query_assignments_authority_id_tenants",
            ondelete="CASCADE",
        ),
    )
    op.create_index(
        "ix_group_query_assignments_tenant_id",
        "group_query_assignments",
        ["tenant_id"],
    )
    op.create_index(
        "ix_group_query_assignments_query_id",
        "group_query_assignments",
        ["query_id"],
    )
    op.create_index(
        "ix_group_query_assignments_authority_id",
        "group_query_assignments",
        ["authority_id"],
    )

    # Group Query Responses
    op.create_table(
        "group_query_responses",
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("assignment_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column(
            "checklist_data", postgresql.JSONB(), nullable=False, server_default="{}"
        ),
        sa.Column(
            "summary_data", postgresql.JSONB(), nullable=False, server_default="{}"
        ),
        sa.Column("current_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("versions", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("submitted_by", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("confirmation", postgresql.JSONB(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("id", name="pk_group_query_responses"),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenants.id"],
            name="fk_group_query_responses_tenant_id_tenants",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["assignment_id"],
            ["group_query_assignments.id"],
            name="fk_group_query_responses_assignment_id_group_query_assignments",
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint("assignment_id", name="uq_group_query_responses_assignment"),
    )
    op.create_index(
        "ix_group_query_responses_tenant_id",
        "group_query_responses",
        ["tenant_id"],
    )

    # Group Query Attachments
    op.create_table(
        "group_query_attachments",
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("assignment_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("requirement_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("file_name", sa.String(255), nullable=False),
        sa.Column("file_size", sa.Integer(), nullable=False),
        sa.Column("mime_type", sa.String(100), nullable=False),
        sa.Column("storage_path", sa.String(500), nullable=False),
        sa.Column("uploaded_by", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "verification_status",
            postgresql.ENUM(
                "pending",
                "verified",
                "rejected",
                name="verification_status",
                create_type=False,
            ),
            nullable=True,
        ),
        sa.Column("verified_by", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("id", name="pk_group_query_attachments"),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenants.id"],
            name="fk_group_query_attachments_tenant_id_tenants",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["assignment_id"],
            ["group_query_assignments.id"],
            name="fk_group_query_attachments_assignment_id_group_query_assignments",
            ondelete="CASCADE",
        ),
    )
    op.create_index(
        "ix_group_query_attachments_tenant_id",
        "group_query_attachments",
        ["tenant_id"],
    )
    op.create_index(
        "ix_group_query_attachments_assignment_id",
        "group_query_attachments",
        ["assignment_id"],
    )

    # Document Boxes
    op.create_table(
        "document_boxes",
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("audit_case_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column(
            "ai_verification_enabled",
            sa.Boolean(),
            nullable=False,
            server_default="false",
        ),
        sa.Column(
            "ai_provider",
            postgresql.ENUM(
                "flow_invoice", "custom", name="ai_provider", create_type=False
            ),
            nullable=True,
        ),
        sa.Column("ai_last_run_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ai_config", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("id", name="pk_document_boxes"),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenants.id"],
            name="fk_document_boxes_tenant_id_tenants",
            ondelete="CASCADE",
        ),
    )
    op.create_index("ix_document_boxes_tenant_id", "document_boxes", ["tenant_id"])
    op.create_index(
        "ix_document_boxes_audit_case_id", "document_boxes", ["audit_case_id"]
    )

    # Box Documents
    op.create_table(
        "box_documents",
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("box_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("expenditure_item_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("file_name", sa.String(255), nullable=False),
        sa.Column("file_size", sa.Integer(), nullable=False),
        sa.Column("mime_type", sa.String(100), nullable=False),
        sa.Column("storage_path", sa.String(500), nullable=False),
        sa.Column("thumbnail_path", sa.String(500), nullable=True),
        sa.Column("uploaded_by", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "manual_status",
            postgresql.ENUM(
                "pending",
                "verified",
                "rejected",
                "unclear",
                name="document_status",
                create_type=False,
            ),
            nullable=True,
        ),
        sa.Column("manual_verified_by", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("manual_verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("manual_remarks", sa.String(1000), nullable=True),
        sa.Column("manual_findings", postgresql.JSONB(), nullable=True),
        sa.Column("ai_verification", postgresql.JSONB(), nullable=True),
        sa.Column("matched_expenditure", postgresql.JSONB(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("id", name="pk_box_documents"),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenants.id"],
            name="fk_box_documents_tenant_id_tenants",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["box_id"],
            ["document_boxes.id"],
            name="fk_box_documents_box_id_document_boxes",
            ondelete="CASCADE",
        ),
    )
    op.create_index("ix_box_documents_tenant_id", "box_documents", ["tenant_id"])
    op.create_index("ix_box_documents_box_id", "box_documents", ["box_id"])


def downgrade() -> None:
    op.drop_table("box_documents")
    op.drop_table("document_boxes")
    op.drop_table("group_query_attachments")
    op.drop_table("group_query_responses")
    op.drop_table("group_query_assignments")
    op.drop_table("group_queries")
    op.drop_table("users")
    op.drop_table("tenants")

    op.execute("DROP TYPE document_status")
    op.execute("DROP TYPE ai_provider")
    op.execute("DROP TYPE verification_status")
    op.execute("DROP TYPE assignment_status")
    op.execute("DROP TYPE group_query_status")
    op.execute("DROP TYPE group_query_category")
    op.execute("DROP TYPE user_role")
    op.execute("DROP TYPE tenant_status")
    op.execute("DROP TYPE tenant_type")
