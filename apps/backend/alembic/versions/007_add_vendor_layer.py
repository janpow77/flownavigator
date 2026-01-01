"""Add Layer 0: Vendor, Customer, Module tables.

Revision ID: 007_add_vendor_layer
Revises: 006_add_module_converter
Create Date: 2025-01-01

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '007'
down_revision: Union[str, None] = '006'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create enums
    vendor_role_enum = postgresql.ENUM(
        'vendor_admin', 'vendor_support', 'vendor_developer', 'vendor_qa',
        name='vendor_role',
        create_type=False
    )
    vendor_role_enum.create(op.get_bind(), checkfirst=True)

    customer_status_enum = postgresql.ENUM(
        'active', 'suspended', 'trial', 'terminated',
        name='customer_status',
        create_type=False
    )
    customer_status_enum.create(op.get_bind(), checkfirst=True)

    alert_type_enum = postgresql.ENUM(
        'warning', 'critical', 'exceeded',
        name='alert_type',
        create_type=False
    )
    alert_type_enum.create(op.get_bind(), checkfirst=True)

    module_status_enum = postgresql.ENUM(
        'development', 'testing', 'released', 'deprecated',
        name='module_status',
        create_type=False
    )
    module_status_enum.create(op.get_bind(), checkfirst=True)

    deployment_status_enum = postgresql.ENUM(
        'pending', 'deploying', 'deployed', 'failed', 'rolled_back',
        name='deployment_status',
        create_type=False
    )
    deployment_status_enum.create(op.get_bind(), checkfirst=True)

    # Create vendors table
    op.create_table(
        'vendors',
        sa.Column('id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('contact_email', sa.String(255), nullable=False),
        sa.Column('billing_email', sa.String(255), nullable=False),
        sa.Column('address_street', sa.String(255), nullable=True),
        sa.Column('address_city', sa.String(100), nullable=True),
        sa.Column('address_postal_code', sa.String(20), nullable=True),
        sa.Column('address_country', sa.String(100), nullable=False, server_default='Deutschland'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id')
    )

    # Create vendor_users table
    op.create_table(
        'vendor_users',
        sa.Column('id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('vendor_id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('role', vendor_role_enum, nullable=False),
        sa.Column('first_name', sa.String(100), nullable=False),
        sa.Column('last_name', sa.String(100), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('last_login_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['vendor_id'], ['vendors.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )
    op.create_index('ix_vendor_users_vendor_id', 'vendor_users', ['vendor_id'])

    # Create customers table
    op.create_table(
        'customers',
        sa.Column('id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('vendor_id', postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('contract_number', sa.String(50), nullable=False),
        sa.Column('contract_start', sa.Date(), nullable=True),
        sa.Column('contract_end', sa.Date(), nullable=True),
        sa.Column('licensed_users', sa.Integer(), nullable=False, server_default='10'),
        sa.Column('licensed_authorities', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('billing_contact', sa.String(255), nullable=True),
        sa.Column('billing_email', sa.String(255), nullable=True),
        sa.Column('billing_address_street', sa.String(255), nullable=True),
        sa.Column('billing_address_city', sa.String(100), nullable=True),
        sa.Column('billing_address_postal_code', sa.String(20), nullable=True),
        sa.Column('billing_address_country', sa.String(100), nullable=False, server_default='Deutschland'),
        sa.Column('payment_method', sa.String(50), nullable=True),
        sa.Column('status', customer_status_enum, nullable=False, server_default='active'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['vendor_id'], ['vendors.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('contract_number'),
        sa.UniqueConstraint('tenant_id')
    )
    op.create_index('ix_customers_vendor_id', 'customers', ['vendor_id'])
    op.create_index('ix_customers_tenant_id', 'customers', ['tenant_id'])

    # Create license_usages table
    op.create_table(
        'license_usages',
        sa.Column('id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('customer_id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('active_users', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('active_authorities', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_license_usages_customer_id', 'license_usages', ['customer_id'])
    op.create_index('ix_license_usages_date', 'license_usages', ['date'])
    # Unique constraint for customer + date
    op.create_unique_constraint('uq_license_usages_customer_date', 'license_usages', ['customer_id', 'date'])

    # Create license_alerts table
    op.create_table(
        'license_alerts',
        sa.Column('id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('customer_id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('alert_type', alert_type_enum, nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('threshold_percent', sa.Integer(), nullable=False),
        sa.Column('current_percent', sa.Integer(), nullable=False),
        sa.Column('acknowledged', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('acknowledged_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('acknowledged_by', postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['acknowledged_by'], ['vendor_users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_license_alerts_customer_id', 'license_alerts', ['customer_id'])

    # Create modules table
    op.create_table(
        'modules',
        sa.Column('id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('version', sa.String(20), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', module_status_enum, nullable=False, server_default='development'),
        sa.Column('developed_by', postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column('released_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('dependencies', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('min_system_version', sa.String(20), nullable=True),
        sa.Column('feature_flags', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['developed_by'], ['vendor_users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create module_deployments table
    op.create_table(
        'module_deployments',
        sa.Column('id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('module_id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('customer_id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('status', deployment_status_enum, nullable=False, server_default='pending'),
        sa.Column('deployed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deployed_by', postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column('deployed_version', sa.String(20), nullable=False),
        sa.Column('previous_version', sa.String(20), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['module_id'], ['modules.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['deployed_by'], ['vendor_users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_module_deployments_module_id', 'module_deployments', ['module_id'])
    op.create_index('ix_module_deployments_customer_id', 'module_deployments', ['customer_id'])

    # Create release_notes table
    op.create_table(
        'release_notes',
        sa.Column('id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('module_id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('version', sa.String(20), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('changes', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('breaking_changes', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('published_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['module_id'], ['modules.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_release_notes_module_id', 'release_notes', ['module_id'])


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('release_notes')
    op.drop_table('module_deployments')
    op.drop_table('modules')
    op.drop_table('license_alerts')
    op.drop_table('license_usages')
    op.drop_table('customers')
    op.drop_table('vendor_users')
    op.drop_table('vendors')

    # Drop enums
    op.execute('DROP TYPE IF EXISTS deployment_status')
    op.execute('DROP TYPE IF EXISTS module_status')
    op.execute('DROP TYPE IF EXISTS alert_type')
    op.execute('DROP TYPE IF EXISTS customer_status')
    op.execute('DROP TYPE IF EXISTS vendor_role')
