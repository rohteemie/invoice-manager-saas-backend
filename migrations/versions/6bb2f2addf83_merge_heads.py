"""merge heads

Revision ID: 6bb2f2addf83
Revises: add_multi_currency_tax, add_token_expiration
Create Date: 2025-11-10 16:05:17.562662

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6bb2f2addf83'
down_revision: Union[str, None] = ('add_multi_currency_tax', 'add_token_expiration')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
