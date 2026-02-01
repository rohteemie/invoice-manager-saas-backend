"""Ensure `currency_preference` column is removed from `users` table

Revision ID: ed3b9c7e8f1a
Revises: 673c70294531
Create Date: 2026-01-29 22:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = 'ed3b9c7e8f1a'
down_revision: Union[str, None] = '673c70294531'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _column_exists(conn, table_name: str, column_name: str) -> bool:
    """Return True if column exists in the current database schema."""
    sql = text(
        "SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS "
        "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = :table AND COLUMN_NAME = :column"
    )
    res = conn.execute(sql, {"table": table_name, "column": column_name}).fetchone()
    return res is not None


def upgrade() -> None:
    conn = op.get_bind()
    if _column_exists(conn, 'users', 'currency_preference'):
        # Drop the column if present (safe operation)
        op.drop_column('users', 'currency_preference')


def downgrade() -> None:
    conn = op.get_bind()
    if not _column_exists(conn, 'users', 'currency_preference'):
        # Recreate as nullable to avoid blocking inserts in downgrade
        op.add_column('users', sa.Column('currency_preference', sa.String(length=3), nullable=True))
