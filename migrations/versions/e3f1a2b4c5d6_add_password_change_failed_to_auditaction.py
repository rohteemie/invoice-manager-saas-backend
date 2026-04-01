"""add_password_change_failed_to_auditaction

Revision ID: e3f1a2b4c5d6
Revises: 8ab1cc8b65d1
Create Date: 2026-04-01 15:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'e3f1a2b4c5d6'
down_revision: Union[str, None] = '8ab1cc8b65d1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add new enum values to auditaction type.
    # PostgreSQL requires ALTER TYPE to add new enum values.
    # For other databases (MySQL, SQLite) this is a no-op or handled inline.
    bind = op.get_bind()
    dialect = bind.dialect.name

    if dialect == 'postgresql':
        op.execute(
            "ALTER TYPE auditaction ADD VALUE IF NOT EXISTS "
            "'login_throttled'"
        )
        op.execute(
            "ALTER TYPE auditaction ADD VALUE IF NOT EXISTS "
            "'login_excessive_failures'"
        )
        op.execute(
            "ALTER TYPE auditaction ADD VALUE IF NOT EXISTS "
            "'password_change_failed'"
        )


def downgrade() -> None:
    # PostgreSQL does not support removing enum values directly.
    # A full type replacement would be needed; this is left as a no-op.
    pass
