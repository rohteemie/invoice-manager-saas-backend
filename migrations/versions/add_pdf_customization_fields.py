"""add PDF customization fields to tenants

Revision ID: add_pdf_customization
Revises: add_tenant_branding
Create Date: 2026-01-04 17:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_pdf_customization'
down_revision = 'add_tenant_branding'
branch_labels = None
depends_on = None


def upgrade():
    """Add PDF customization fields to tenants table."""
    op.add_column(
        'tenants',
        sa.Column(
            'primary_color',
            sa.String(length=7),
            nullable=False,
            server_default='#2563eb'
        )
    )
    op.add_column(
        'tenants',
        sa.Column(
            'secondary_color',
            sa.String(length=7),
            nullable=False,
            server_default='#1e40af'
        )
    )
    op.add_column(
        'tenants',
        sa.Column('custom_footer', sa.Text(), nullable=True)
    )
    op.add_column(
        'tenants',
        sa.Column(
            'draft_watermark_enabled',
            sa.Boolean(),
            nullable=False,
            server_default='1'
        )
    )


def downgrade():
    """Remove PDF customization fields from tenants table."""
    op.drop_column('tenants', 'draft_watermark_enabled')
    op.drop_column('tenants', 'custom_footer')
    op.drop_column('tenants', 'secondary_color')
    op.drop_column('tenants', 'primary_color')
