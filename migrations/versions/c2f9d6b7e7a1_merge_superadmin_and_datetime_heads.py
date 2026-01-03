"""merge superadmin and datetime heads

Revision ID: c2f9d6b7e7a1
Revises: add_utc_datetime_everywhere, 2174a8f4afdb
Create Date: 2026-01-03 00:00:00.000000

"""
from typing import Sequence, Tuple, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c2f9d6b7e7a1"
down_revision: Union[str, Tuple[str, ...], None] = ("add_utc_datetime_everywhere", "2174a8f4afdb")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Merge migration; no schema changes required.
    pass


def downgrade() -> None:
    # Downgrade to either side of the merge.
    pass
