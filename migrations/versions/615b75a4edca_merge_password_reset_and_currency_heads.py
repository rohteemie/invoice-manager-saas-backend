"""merge password reset and currency heads

Revision ID: 615b75a4edca
Revises: add_password_reset_tokens, update_default_currency_ngn
Create Date: 2025-11-19 22:43:02.396233

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '615b75a4edca'
down_revision: Union[str, None] = ('add_password_reset_tokens', 'update_default_currency_ngn')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
