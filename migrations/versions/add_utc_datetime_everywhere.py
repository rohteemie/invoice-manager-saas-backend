"""Make datetime columns use UTC-aware handling in application

Revision ID: add_utc_datetime_everywhere
Revises: add_user_datetime_timezone
Create Date: 2025-12-01 00:10:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_utc_datetime_everywhere'
down_revision = 'add_user_datetime_timezone'
branch_labels = None
depends_on = None


def upgrade():
    """Alter DATETIME columns to DATETIME(6) to preserve precision and
    ensure consistent behavior across drivers. For MySQL, keep them as
    DATETIME(6) since MySQL doesn't store tzinfo; the application will
    interpret these as UTC via the TypeDecorator.
    """
    conn = op.get_bind()
    dialect = conn.dialect.name
    if dialect.startswith('mysql'):
        # Modify common model datetime columns to DATETIME(6)
        op.execute(
            "ALTER TABLE `users` MODIFY COLUMN `verification_token_expires_at` DATETIME(6) NULL, "
            "MODIFY COLUMN `reset_password_token_expires_at` DATETIME(6) NULL, "
            "MODIFY COLUMN `created_at` DATETIME(6) NOT NULL, "
            "MODIFY COLUMN `updated_at` DATETIME(6) NOT NULL"
        )

        op.execute(
            "ALTER TABLE `tenants` MODIFY COLUMN `created_at` DATETIME(6) NOT NULL, "
            "MODIFY COLUMN `updated_at` DATETIME(6) NOT NULL"
        )

        op.execute(
            "ALTER TABLE `invoices` MODIFY COLUMN `created_at` DATETIME(6) NOT NULL, "
            "MODIFY COLUMN `updated_at` DATETIME(6) NOT NULL"
        )

        op.execute(
            "ALTER TABLE `invoice_items` MODIFY COLUMN `created_at` DATETIME(6) NOT NULL, "
            "MODIFY COLUMN `updated_at` DATETIME(6) NOT NULL"
        )
    else:
        # For other DBs use SQLAlchemy alter_column
        tables = [
            ('users', 'verification_token_expires_at'),
            ('users', 'reset_password_token_expires_at'),
            ('users', 'created_at'),
            ('users', 'updated_at'),
            ('tenants', 'created_at'),
            ('tenants', 'updated_at'),
            ('invoices', 'created_at'),
            ('invoices', 'updated_at'),
            ('invoice_items', 'created_at'),
            ('invoice_items', 'updated_at'),
        ]
        for table, col in tables:
            try:
                op.alter_column(table, col, existing_type=sa.DateTime(), type_=sa.DateTime(timezone=True), existing_nullable=True)
            except Exception:
                # best-effort: some columns may not exist if schema differs
                pass


def downgrade():
    conn = op.get_bind()
    dialect = conn.dialect.name
    if dialect.startswith('mysql'):
        op.execute(
            "ALTER TABLE `users` MODIFY COLUMN `verification_token_expires_at` DATETIME NULL, "
            "MODIFY COLUMN `reset_password_token_expires_at` DATETIME NULL, "
            "MODIFY COLUMN `created_at` DATETIME NOT NULL, "
            "MODIFY COLUMN `updated_at` DATETIME NOT NULL"
        )

        op.execute(
            "ALTER TABLE `tenants` MODIFY COLUMN `created_at` DATETIME NOT NULL, "
            "MODIFY COLUMN `updated_at` DATETIME NOT NULL"
        )

        op.execute(
            "ALTER TABLE `invoices` MODIFY COLUMN `created_at` DATETIME NOT NULL, "
            "MODIFY COLUMN `updated_at` DATETIME NOT NULL"
        )

        op.execute(
            "ALTER TABLE `invoice_items` MODIFY COLUMN `created_at` DATETIME NOT NULL, "
            "MODIFY COLUMN `updated_at` DATETIME NOT NULL"
        )
    else:
        tables = [
            ('users', 'verification_token_expires_at'),
            ('users', 'reset_password_token_expires_at'),
            ('users', 'created_at'),
            ('users', 'updated_at'),
            ('tenants', 'created_at'),
            ('tenants', 'updated_at'),
            ('invoices', 'created_at'),
            ('invoices', 'updated_at'),
            ('invoice_items', 'created_at'),
            ('invoice_items', 'updated_at'),
        ]
        for table, col in tables:
            try:
                op.alter_column(table, col, existing_type=sa.DateTime(timezone=True), type_=sa.DateTime(), existing_nullable=True)
            except Exception:
                pass
