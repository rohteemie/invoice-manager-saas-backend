"""remove branch_id from invoices

Revision ID: remove_branch_id
Revises: add_business_reg_plan
Create Date: 2026-01-23 21:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'remove_branch_id'
down_revision = 'add_business_reg_plan'
branch_labels = None
depends_on = None


def upgrade():
    """Remove branch_id column from invoices table."""
    # Drop index first if it exists
    op.drop_index('ix_invoices_branch_id', table_name='invoices')

    # Drop branch_id column
    op.drop_column('invoices', 'branch_id')


def downgrade():
    """Restore branch_id column to invoices table."""
    # Add branch_id column back
    op.add_column(
        'invoices',
        sa.Column('branch_id', sa.String(length=60), nullable=True)
    )

    # Recreate index
    op.create_index(
        'ix_invoices_branch_id',
        'invoices',
        ['branch_id'],
        unique=False
    )
