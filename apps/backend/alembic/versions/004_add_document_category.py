"""Add document category to box_documents.

Revision ID: 004
Revises: 003
Create Date: 2025-12-30
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "004"
down_revision = "003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add category column to box_documents."""
    # Create the enum type
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'document_category') THEN
                CREATE TYPE document_category AS ENUM (
                    'belege',
                    'bescheide',
                    'korrespondenz',
                    'vertraege',
                    'nachweise',
                    'sonstige'
                );
            END IF;
        END
        $$;
    """
    )

    # Add the column with default value
    op.add_column(
        "box_documents",
        sa.Column(
            "category",
            postgresql.ENUM(
                "belege",
                "bescheide",
                "korrespondenz",
                "vertraege",
                "nachweise",
                "sonstige",
                name="document_category",
                create_type=False,
            ),
            nullable=False,
            server_default="sonstige",
        ),
    )

    # Create index for category filtering
    op.create_index(
        "ix_box_documents_category",
        "box_documents",
        ["category"],
    )


def downgrade() -> None:
    """Remove category column from box_documents."""
    op.drop_index("ix_box_documents_category", table_name="box_documents")
    op.drop_column("box_documents", "category")
    # Note: We don't drop the enum type to avoid issues with other tables using it
