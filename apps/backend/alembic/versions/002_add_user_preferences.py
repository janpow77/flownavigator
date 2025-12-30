"""Add user preferences table

Revision ID: 002
Revises: 001
Create Date: 2024-12-30

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "user_preferences",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("appearance", postgresql.JSON(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("navigation", postgresql.JSON(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("dashboard", postgresql.JSON(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("module_preferences", postgresql.JSON(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("notifications", postgresql.JSON(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("locale", postgresql.JSON(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("shortcuts", postgresql.JSON(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )
    op.create_index("ix_user_preferences_user_id", "user_preferences", ["user_id"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_user_preferences_user_id", table_name="user_preferences")
    op.drop_table("user_preferences")
