"""Initial migration

Revision ID: 285ea17a7a31
Revises:
Create Date: 2025-10-08 14:49:40.355277

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '285ea17a7a31'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Create all tables from current SQLAlchemy models as the initial baseline.

    NOTE: This migration was intentionally created to serve as a baseline
    initial migration and will create all tables defined in the application's
    metadata. If you plan to apply subsequent auto-generated diffs on a clean
    database, this ensures the schema exists first and keeps downstream
    migrations' `down_revision` references intact.
    """
    bind = op.get_bind()
    # Import here to avoid import-time side effects when Alembic inspects files
    from app.models.general_model import Base

    Base.metadata.create_all(bind=bind)


def downgrade() -> None:
    """
    Drop all tables created by the initial baseline migration.

    WARNING: This will DROP ALL application tables. Use only in development
    or when you are certain you want to remove the schema.
    """
    bind = op.get_bind()
    from app.models.general_model import Base

    Base.metadata.drop_all(bind=bind)
