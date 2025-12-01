"""Add audit logs table

Revision ID: add_audit_logs
Revises: 
Create Date: 2025-12-01 22:05:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql


# revision identifiers, used by Alembic.
revision = 'add_audit_logs'
down_revision = '6bb2f2addf83'
branch_labels = None
depends_on = None


def upgrade():
    # Create audit_logs table
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.String(60), nullable=False, primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('user_id', sa.String(60), nullable=True),
        sa.Column('tenant_id', sa.String(60), nullable=True),
        sa.Column('action', sa.Enum(
            'LOGIN', 'LOGOUT', 'LOGIN_FAILED', 'TOKEN_REFRESH',
            'USER_CREATED', 'USER_UPDATED', 'USER_DELETED',
            'USER_ROLE_CHANGED', 'PASSWORD_CHANGED',
            'PASSWORD_RESET_REQUESTED', 'PASSWORD_RESET_COMPLETED',
            'TENANT_CREATED', 'TENANT_UPDATED', 'TENANT_DELETED',
            'INVOICE_CREATED', 'INVOICE_UPDATED', 'INVOICE_DELETED',
            'INVOICE_STATUS_CHANGED', 'DATA_EXPORTED',
            'INVOICE_PDF_GENERATED',
            name='auditaction'
        ), nullable=False),
        sa.Column('resource_type', sa.Enum(
            'USER', 'TENANT', 'INVOICE', 'INVOICE_ITEM', 'AUTH', 'EXPORT',
            name='resourcetype'
        ), nullable=False),
        sa.Column('resource_id', sa.String(60), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.String(500), nullable=True),
        sa.Column('changes', sa.Text, nullable=True),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('status', sa.String(20), nullable=False,
                  server_default='success'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes
    op.create_index('idx_audit_tenant_action', 'audit_logs',
                    ['tenant_id', 'action'])
    op.create_index('idx_audit_user_action', 'audit_logs',
                    ['user_id', 'action'])
    op.create_index('idx_audit_resource', 'audit_logs',
                    ['resource_type', 'resource_id'])
    op.create_index('idx_audit_created_at', 'audit_logs', ['created_at'])
    op.create_index('ix_audit_logs_user_id', 'audit_logs', ['user_id'])
    op.create_index('ix_audit_logs_tenant_id', 'audit_logs', ['tenant_id'])
    op.create_index('ix_audit_logs_action', 'audit_logs', ['action'])
    op.create_index('ix_audit_logs_resource_type', 'audit_logs',
                    ['resource_type'])
    op.create_index('ix_audit_logs_resource_id', 'audit_logs',
                    ['resource_id'])


def downgrade():
    # Drop indexes
    op.drop_index('ix_audit_logs_resource_id', 'audit_logs')
    op.drop_index('ix_audit_logs_resource_type', 'audit_logs')
    op.drop_index('ix_audit_logs_action', 'audit_logs')
    op.drop_index('ix_audit_logs_tenant_id', 'audit_logs')
    op.drop_index('ix_audit_logs_user_id', 'audit_logs')
    op.drop_index('idx_audit_created_at', 'audit_logs')
    op.drop_index('idx_audit_resource', 'audit_logs')
    op.drop_index('idx_audit_user_action', 'audit_logs')
    op.drop_index('idx_audit_tenant_action', 'audit_logs')

    # Drop table
    op.drop_table('audit_logs')

    # Drop enums (for PostgreSQL compatibility)
    sa.Enum(name='auditaction').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='resourcetype').drop(op.get_bind(), checkfirst=True)
