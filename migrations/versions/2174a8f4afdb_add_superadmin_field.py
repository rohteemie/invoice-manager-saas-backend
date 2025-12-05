"""Add superadmin field and make tenant_id nullable

Revision ID: 2174a8f4afdb
Revises: add_audit_logs
Create Date: 2025-12-05 16:12:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2174a8f4afdb'
down_revision = 'add_audit_logs'
branch_labels = None
depends_on = None


def upgrade():
    # Add is_superadmin column to users table
    op.add_column('users', sa.Column('is_superadmin', sa.Boolean(),
                                     nullable=False, server_default='0'))

    # Create index on is_superadmin
    op.create_index('ix_users_is_superadmin', 'users', ['is_superadmin'])

    # For MySQL/PostgreSQL: Make tenant_id nullable
    # Note: SQLite doesn't support ALTER COLUMN, so tenant_id remains
    # constrained. For SQLite, superadmins should be created with a
    # placeholder tenant_id or migrate to MySQL/PostgreSQL for full support.
    bind = op.get_bind()
    if bind.dialect.name != 'sqlite':
        # For MySQL/PostgreSQL: Make tenant_id nullable
        op.alter_column('users', 'tenant_id',
                        existing_type=sa.String(60),
                        nullable=True)


def downgrade():
    # Remove index
    op.drop_index('ix_users_is_superadmin', table_name='users')

    # Remove is_superadmin column
    op.drop_column('users', 'is_superadmin')

    # Restore tenant_id to non-nullable
    bind = op.get_bind()
    if bind.dialect.name != 'sqlite':
        op.alter_column('users', 'tenant_id',
                        existing_type=sa.String(60),
                        nullable=False)
