"""add multi-currency and tax support

Revision ID: add_multi_currency_tax
Revises: add_verification_token
Create Date: 2025-11-10 14:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import Numeric


# revision identifiers, used by Alembic.
revision = 'add_multi_currency_tax'
down_revision = 'add_verification_token'
branch_labels = None
depends_on = None


def upgrade():
    # Add currency support to invoices table
    op.add_column('invoices', sa.Column('currency', sa.String(length=3), nullable=False, server_default='USD'))
    op.create_index(op.f('ix_invoices_currency'), 'invoices', ['currency'], unique=False)
    
    # Add tax/currency configuration to tenants table
    op.add_column('tenants', sa.Column('default_currency', sa.String(length=3), nullable=False, server_default='USD'))
    op.add_column('tenants', sa.Column('tax_rate', Numeric(5, 2), nullable=True))
    op.add_column('tenants', sa.Column('tax_label', sa.String(length=50), nullable=True))


def downgrade():
    # Remove tenant tax/currency columns
    op.drop_column('tenants', 'tax_label')
    op.drop_column('tenants', 'tax_rate')
    op.drop_column('tenants', 'default_currency')
    
    # Remove invoice currency column and index
    op.drop_index(op.f('ix_invoices_currency'), table_name='invoices')
    op.drop_column('invoices', 'currency')
