"""add verification token expiration

Revision ID: add_token_expiration
Revises: add_verification_token
Create Date: 2025-11-03 21:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_token_expiration'
down_revision = 'add_verification_token'
branch_labels = None
depends_on = None


def upgrade():
    # Add verification_token_expires_at column to users table
    op.add_column('users', sa.Column('verification_token_expires_at', sa.DateTime(), nullable=True))


def downgrade():
    # Remove verification_token_expires_at column
    op.drop_column('users', 'verification_token_expires_at')
