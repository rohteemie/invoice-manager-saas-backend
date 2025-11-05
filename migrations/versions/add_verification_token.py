"""add verification token to users

Revision ID: add_verification_token
Revises: 285ea17a7a31
Create Date: 2025-11-02 22:35:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_verification_token'
down_revision = '285ea17a7a31'
branch_labels = None
depends_on = None


def upgrade():
    # Add verification_token column to users table
    op.add_column('users', sa.Column('verification_token', sa.String(length=255), nullable=True))
    op.create_index(op.f('ix_users_verification_token'), 'users', ['verification_token'], unique=False)


def downgrade():
    # Remove verification_token column and index
    op.drop_index(op.f('ix_users_verification_token'), table_name='users')
    op.drop_column('users', 'verification_token')
