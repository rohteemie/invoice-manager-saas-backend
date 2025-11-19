"""add tenant branding and contact info

Revision ID: add_tenant_branding
Revises: 615b75a4edca
Create Date: 2025-11-19 22:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_tenant_branding'
down_revision = '615b75a4edca'
branch_labels = None
depends_on = None


def upgrade():
    """Add logo_url and contact information fields to tenants table."""
    op.add_column('tenants', sa.Column('logo_url', sa.String(length=500), nullable=True))
    op.add_column('tenants', sa.Column('address', sa.Text(), nullable=True))
    op.add_column('tenants', sa.Column('phone', sa.String(length=20), nullable=True))
    op.add_column('tenants', sa.Column('email', sa.String(length=255), nullable=True))


def downgrade():
    """Remove logo_url and contact information fields from tenants table."""
    op.drop_column('tenants', 'email')
    op.drop_column('tenants', 'phone')
    op.drop_column('tenants', 'address')
    op.drop_column('tenants', 'logo_url')
