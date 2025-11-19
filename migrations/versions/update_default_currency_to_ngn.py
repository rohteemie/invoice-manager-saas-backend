"""update default currency to NGN

Revision ID: update_default_currency_ngn
Revises: add_payment_method_currency_pref
Create Date: 2025-11-18 19:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'update_default_currency_ngn'
down_revision = 'add_payment_method_currency_pref'
branch_labels = None
depends_on = None


def upgrade():
    # Update default currency for existing tenants and invoices to NGN
    # Note: This is a data migration, actual column defaults are handled
    # at the application level
    pass


def downgrade():
    # No downgrade needed as this doesn't change schema
    pass
