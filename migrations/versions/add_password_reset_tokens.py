"""add password reset token fields to users

Revision ID: add_password_reset_tokens
Revises: add_token_expiration
Create Date: 2025-11-18 10:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_password_reset_tokens'
down_revision = 'add_token_expiration'
branch_labels = None
depends_on = None


def upgrade():
    # Add password reset token columns to users table
    op.add_column('users', sa.Column('reset_password_token', sa.String(length=255), nullable=True))
    op.add_column('users', sa.Column('reset_password_token_expires_at', sa.DateTime(), nullable=True))
    op.create_index(op.f('ix_users_reset_password_token'), 'users', ['reset_password_token'], unique=False)


def downgrade():
    # Remove password reset token columns and index
    op.drop_index(op.f('ix_users_reset_password_token'), table_name='users')
    op.drop_column('users', 'reset_password_token_expires_at')
    op.drop_column('users', 'reset_password_token')
