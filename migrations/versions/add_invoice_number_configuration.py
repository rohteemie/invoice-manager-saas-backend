"""add invoice number configuration

Revision ID: add_invoice_config
Revises: add_tenant_branding
Create Date: 2026-01-03 16:33:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_invoice_config'
down_revision = 'add_tenant_branding'
branch_labels = None
depends_on = None


def upgrade():
    """Add invoice number configuration fields to tenants table."""
    op.add_column('tenants', sa.Column('invoice_number_prefix', sa.String(length=20), nullable=False, server_default='INV'))
    op.add_column('tenants', sa.Column('invoice_number_format', sa.String(length=100), nullable=False, server_default='{prefix}-{date}-{sequence:04d}'))
    op.add_column('tenants', sa.Column('invoice_number_sequence', sa.Integer(), nullable=False, server_default='0'))


def downgrade():
    """Remove invoice number configuration fields from tenants table."""
    op.drop_column('tenants', 'invoice_number_sequence')
    op.drop_column('tenants', 'invoice_number_format')
    op.drop_column('tenants', 'invoice_number_prefix')
