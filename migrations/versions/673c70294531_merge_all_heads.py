"""merge_all_heads

Revision ID: 673c70294531
Revises: add_invoice_config, add_pdf_customization, c2f9d6b7e7a1
Create Date: 2026-01-04 19:56:00.251083

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '673c70294531'
down_revision: Union[str, None] = ('add_invoice_config', 'add_pdf_customization', 'c2f9d6b7e7a1')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
