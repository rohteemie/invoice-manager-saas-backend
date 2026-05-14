"""Add tenant-scoped invoice number uniqueness.

Revision ID: add_invoice_number_uniqueness
Revises: tenant_scoped_email
Create Date: 2026-05-13 16:04:35.657+00:00
"""
from alembic import op


# revision identifiers, used by Alembic.
revision = 'add_invoice_number_uniqueness'
down_revision = 'tenant_scoped_email'
branch_labels = None
depends_on = None


def upgrade():
    """Add unique constraint on (tenant_id, invoice_number)."""
    op.create_unique_constraint(
        'uq_invoice_tenant_invoice_number',
        'invoices',
        ['tenant_id', 'invoice_number']
    )


def downgrade():
    """Remove unique constraint on (tenant_id, invoice_number)."""
    op.drop_constraint(
        'uq_invoice_tenant_invoice_number',
        'invoices',
        type_='unique'
    )
