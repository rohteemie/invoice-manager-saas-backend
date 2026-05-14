"""add_email_verified_to_auditaction

Revision ID: 6e7f8a9b0c1d
Revises: e3f1a2b4c5d6
Create Date: 2026-05-14 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '6e7f8a9b0c1d'
down_revision: Union[str, None] = 'e3f1a2b4c5d6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # PostgreSQL requires ALTER TYPE for enum extensions.
    bind = op.get_bind()
    if bind.dialect.name == 'postgresql':
        op.execute(
            "ALTER TYPE auditaction ADD VALUE IF NOT EXISTS 'email_verified'"
        )


def downgrade() -> None:
    # Enum value removal is not supported in-place for PostgreSQL.
    pass