"""Add Profile tables for Layer 1 and Layer 2.

Revision ID: 008_add_profiles
Revises: 007_add_vendor_layer
Create Date: 2025-01-01

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '008'
down_revision: Union[str, None] = '007'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create authority_type enum
    authority_type_enum = postgresql.ENUM(
        'audit_authority', 'certifying_authority', 'managing_authority', 'intermediate_body',
        name='authority_type_enum',
        create_type=False
    )
    authority_type_enum.create(op.get_bind(), checkfirst=True)

    # Create coordination_body_profiles table
    op.create_table(
        'coordination_body_profiles',
        sa.Column('id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('official_name', sa.String(255), nullable=False),
        sa.Column('short_name', sa.String(50), nullable=True),
        sa.Column('street', sa.String(255), nullable=True),
        sa.Column('postal_code', sa.String(20), nullable=True),
        sa.Column('city', sa.String(100), nullable=True),
        sa.Column('country', sa.String(100), nullable=False, server_default='Deutschland'),
        sa.Column('phone', sa.String(50), nullable=True),
        sa.Column('email', sa.String(255), nullable=True),
        sa.Column('website', sa.String(255), nullable=True),
        sa.Column('logo_url', sa.String(512), nullable=True),
        sa.Column('primary_color', sa.String(7), nullable=False, server_default='#1e40af'),
        sa.Column('secondary_color', sa.String(7), nullable=False, server_default='#3b82f6'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tenant_id')
    )
    op.create_index('ix_coordination_body_profiles_tenant_id', 'coordination_body_profiles', ['tenant_id'])

    # Create authority_profiles table
    op.create_table(
        'authority_profiles',
        sa.Column('id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('official_name', sa.String(255), nullable=False),
        sa.Column('short_name', sa.String(50), nullable=True),
        sa.Column('authority_type', authority_type_enum, nullable=True),
        sa.Column('street', sa.String(255), nullable=True),
        sa.Column('postal_code', sa.String(20), nullable=True),
        sa.Column('city', sa.String(100), nullable=True),
        sa.Column('country', sa.String(100), nullable=False, server_default='Deutschland'),
        sa.Column('phone', sa.String(50), nullable=True),
        sa.Column('email', sa.String(255), nullable=True),
        sa.Column('website', sa.String(255), nullable=True),
        sa.Column('logo_url', sa.String(512), nullable=True),
        sa.Column('use_parent_branding', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('primary_color', sa.String(7), nullable=True),
        sa.Column('secondary_color', sa.String(7), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tenant_id')
    )
    op.create_index('ix_authority_profiles_tenant_id', 'authority_profiles', ['tenant_id'])


def downgrade() -> None:
    op.drop_table('authority_profiles')
    op.drop_table('coordination_body_profiles')
    op.execute('DROP TYPE IF EXISTS authority_type_enum')
