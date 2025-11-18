"""add payment method enum and currency preference

Revision ID: add_payment_method_currency_pref
Revises: add_multi_currency_tax
Create Date: 2025-11-18 12:58:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql, mysql, sqlite


# revision identifiers, used by Alembic.
revision = 'add_payment_method_currency_pref'
down_revision = 'add_multi_currency_tax'
branch_labels = None
depends_on = None


def upgrade():
    # Detect database type
    bind = op.get_bind()
    dialect_name = bind.dialect.name

    # Add currency_preference to users table
    # Use enum for PostgreSQL, string for others
    if dialect_name == 'postgresql':
        currency_enum = postgresql.ENUM(
            'NGN', 'USD', 'GBP', 'EUR',
            name='currency',
            create_type=False  # Type already exists from invoices table
        )
        op.add_column(
            'users',
            sa.Column(
                'currency_preference',
                currency_enum,
                nullable=False,
                server_default='USD'
            )
        )

        # Update payment_method column in invoices to use enum
        payment_method_enum = postgresql.ENUM(
            'transfer', 'cash', 'pos', 'cheque', 'card',
            'mobile_money', 'other',
            name='paymentmethod'
        )
        payment_method_enum.create(bind)

        # Alter payment_method column type
        op.execute("""
            ALTER TABLE invoices
            ALTER COLUMN payment_method TYPE paymentmethod
            USING payment_method::paymentmethod
        """)
    else:
        # For MySQL and SQLite, use string columns with constraints
        op.add_column(
            'users',
            sa.Column(
                'currency_preference',
                sa.String(length=3),
                nullable=False,
                server_default='USD'
            )
        )
        # payment_method is already a string column, no changes needed
        # but we can add a check constraint for validation
        if dialect_name == 'mysql':
            op.execute("""
                ALTER TABLE invoices
                ADD CONSTRAINT check_payment_method
                CHECK (payment_method IN (
                    'transfer', 'cash', 'pos', 'cheque', 'card',
                    'mobile_money', 'other'
                ))
            """)


def downgrade():
    # Detect database type
    bind = op.get_bind()
    dialect_name = bind.dialect.name

    if dialect_name == 'postgresql':
        # Revert payment_method to string
        op.execute("""
            ALTER TABLE invoices
            ALTER COLUMN payment_method TYPE VARCHAR(50)
        """)

        # Drop the payment method enum type
        op.execute("DROP TYPE IF EXISTS paymentmethod")

    elif dialect_name == 'mysql':
        # Remove check constraint
        op.execute("ALTER TABLE invoices DROP CHECK check_payment_method")

    # Drop currency_preference column
    op.drop_column('users', 'currency_preference')
