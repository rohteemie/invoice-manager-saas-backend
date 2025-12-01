"""add timezone awareness to user datetime columns

Revision ID: add_user_datetime_timezone
Revises: add_tenant_branding
Create Date: 2025-12-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_user_datetime_timezone'
down_revision = 'add_tenant_branding'
branch_labels = None
depends_on = None


def upgrade():
    """Alter user datetime columns to be timezone-aware at the SQLAlchemy level.

    Note: MySQL's DATETIME type does not store timezone information. Setting
    `timezone=True` on SQLAlchemy DateTime is a schema-level indicator and is
    primarily effective for backends that support timezones (PostgreSQL).

    This migration will alter the column definitions to DATETIME(6) to
    ensure fractional-second precision and provide an explicit ALTER so Alembic
    records the change. Existing naive datetimes are assumed to be UTC.
    """
    # Use explicit MODIFY (MySQL) via raw SQL for precision; it's safe if the
    # columns already exist.
    conn = op.get_bind()
    dialect_name = conn.dialect.name
    if dialect_name.startswith('mysql'):
        op.execute("""
        ALTER TABLE `users`
        MODIFY COLUMN `verification_token_expires_at` DATETIME(6) NULL,
        MODIFY COLUMN `reset_password_token_expires_at` DATETIME(6) NULL;
        """)
    else:
        # For other DBs, use SQLAlchemy alteration
        op.alter_column('users', 'verification_token_expires_at', existing_type=sa.DateTime(), type_=sa.DateTime(timezone=True), existing_nullable=True)
        op.alter_column('users', 'reset_password_token_expires_at', existing_type=sa.DateTime(), type_=sa.DateTime(timezone=True), existing_nullable=True)


def downgrade():
    """Revert the column types back to naive DateTime where applicable."""
    conn = op.get_bind()
    dialect_name = conn.dialect.name
    if dialect_name.startswith('mysql'):
        op.execute("""
        ALTER TABLE `users`
        MODIFY COLUMN `verification_token_expires_at` DATETIME NULL,
        MODIFY COLUMN `reset_password_token_expires_at` DATETIME NULL;
        """)
    else:
        op.alter_column('users', 'verification_token_expires_at', existing_type=sa.DateTime(timezone=True), type_=sa.DateTime(), existing_nullable=True)
        op.alter_column('users', 'reset_password_token_expires_at', existing_type=sa.DateTime(timezone=True), type_=sa.DateTime(), existing_nullable=True)
