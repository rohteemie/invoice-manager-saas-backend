"""Merge multiple heads

Revision ID: a124808cbe39
Revises: 673c70294531, remove_branch_id
Create Date: 2026-01-29 00:56:16.115007

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a124808cbe39'
down_revision: Union[str, None] = ('673c70294531', 'remove_branch_id')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
