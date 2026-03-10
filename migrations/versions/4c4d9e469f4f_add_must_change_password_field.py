"""add_must_change_password_field

Revision ID: 4c4d9e469f4f
Revises: 9afeff7530ac
Create Date: 2026-02-08 16:13:46.329995

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '4c4d9e469f4f'
down_revision: Union[str, None] = '9afeff7530ac'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add must_change_password field to users table
    op.add_column('users', sa.Column(
        'must_change_password', sa.Boolean(), nullable=False,
        server_default='0'
    ))
    op.create_index(
        op.f('ix_users_must_change_password'),
        'users', ['must_change_password'], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f('ix_users_must_change_password'), table_name='users')
    op.drop_column('users', 'must_change_password')
