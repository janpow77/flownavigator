"""Add History tables for Workflow-Historisierung.

Revision ID: 009_add_history
Revises: 008_add_profiles
Create Date: 2025-01-01

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '009'
down_revision: Union[str, None] = '008'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create event_type enum
    event_type_enum = postgresql.ENUM(
        'installed', 'updated', 'uninstalled', 'configured', 'error', 'started', 'completed',
        name='event_type',
        create_type=False
    )
    event_type_enum.create(op.get_bind(), checkfirst=True)

    # Create message_role enum
    message_role_enum = postgresql.ENUM(
        'user', 'assistant', 'system',
        name='message_role',
        create_type=False
    )
    message_role_enum.create(op.get_bind(), checkfirst=True)

    # Create feedback_type enum
    feedback_type_enum = postgresql.ENUM(
        'helpful', 'not_helpful', 'partially_helpful', 'incorrect',
        name='feedback_type',
        create_type=False
    )
    feedback_type_enum.create(op.get_bind(), checkfirst=True)

    # Create module_events table (AC-7.1.1)
    op.create_table(
        'module_events',
        sa.Column('id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('module_id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('customer_id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('event_type', event_type_enum, nullable=False),
        sa.Column('version', sa.String(20), nullable=True),
        sa.Column('previous_version', sa.String(20), nullable=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column('details', postgresql.JSON(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['module_id'], ['modules.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_module_events_module_id', 'module_events', ['module_id'])
    op.create_index('ix_module_events_customer_id', 'module_events', ['customer_id'])
    op.create_index('ix_module_events_created_at', 'module_events', ['created_at'])

    # Create llm_conversations table (AC-7.1.2)
    op.create_table(
        'llm_conversations',
        sa.Column('id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column('context_type', sa.String(50), nullable=False),
        sa.Column('context_id', postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column('title', sa.String(255), nullable=True),
        sa.Column('model_used', sa.String(100), nullable=True),
        sa.Column('total_tokens', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_llm_conversations_tenant_id', 'llm_conversations', ['tenant_id'])
    op.create_index('ix_llm_conversations_user_id', 'llm_conversations', ['user_id'])
    op.create_index('ix_llm_conversations_context_type', 'llm_conversations', ['context_type'])

    # Create llm_messages table
    op.create_table(
        'llm_messages',
        sa.Column('id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('role', message_role_enum, nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('tokens', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('extra_data', postgresql.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['conversation_id'], ['llm_conversations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_llm_messages_conversation_id', 'llm_messages', ['conversation_id'])

    # Create llm_feedbacks table (AC-7.1.3)
    op.create_table(
        'llm_feedbacks',
        sa.Column('id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('message_id', postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column('feedback_type', feedback_type_enum, nullable=False),
        sa.Column('comment', sa.Text(), nullable=True),
        sa.Column('rating', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['conversation_id'], ['llm_conversations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['message_id'], ['llm_messages.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_llm_feedbacks_conversation_id', 'llm_feedbacks', ['conversation_id'])


def downgrade() -> None:
    op.drop_table('llm_feedbacks')
    op.drop_table('llm_messages')
    op.drop_table('llm_conversations')
    op.drop_table('module_events')
    op.execute('DROP TYPE IF EXISTS feedback_type')
    op.execute('DROP TYPE IF EXISTS message_role')
    op.execute('DROP TYPE IF EXISTS event_type')
