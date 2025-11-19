"""add payment method enum and currency preference

Revision ID: add_payment_method_currency_pref
Revises: 6bb2f2addf83
Create Date: 2025-11-18 18:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_payment_method_currency_pref'
down_revision = '6bb2f2addf83'
branch_labels = None
depends_on = None


def upgrade():
    # Add currency_preference column to users table
    op.add_column('users', sa.Column('currency_preference', sa.String(length=3), nullable=False, server_default='NGN'))
    
    # Note: payment_method column already exists as String(50) in invoices table
    # In production, you would need to migrate existing data before enforcing enum
    # For now, the application layer will handle enum validation


def downgrade():
    # Remove currency_preference column from users table
    op.drop_column('users', 'currency_preference')
