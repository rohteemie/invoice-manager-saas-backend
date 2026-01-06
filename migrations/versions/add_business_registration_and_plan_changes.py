"""add business registration number and update plan type default

Revision ID: add_business_reg_plan
Revises: c2f9d6b7e7a1
Create Date: 2026-01-06 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_business_reg_plan'
down_revision = 'c2f9d6b7e7a1'
branch_labels = None
depends_on = None


def upgrade():
    """Add business_registration_number column and update plan_type default."""
    # Add business_registration_number column
    op.add_column(
        'tenants',
        sa.Column(
            'business_registration_number',
            sa.String(length=100),
            nullable=True
        )
    )
    
    # Create unique constraint for business_registration_number
    op.create_unique_constraint(
        'uq_tenants_business_registration_number',
        'tenants',
        ['business_registration_number']
    )
    
    # Update existing tenants to have 'Standard' plan_type instead of 'free'
    op.execute("UPDATE tenants SET plan_type = 'Standard' WHERE plan_type = 'free'")
    
    # Alter column default for plan_type
    op.alter_column(
        'tenants',
        'plan_type',
        server_default='Standard',
        existing_type=sa.String(length=20),
        existing_nullable=True
    )


def downgrade():
    """Remove business_registration_number column and revert plan_type default."""
    # Revert plan_type values
    op.execute("UPDATE tenants SET plan_type = 'free' WHERE plan_type = 'Standard'")
    
    # Revert column default for plan_type
    op.alter_column(
        'tenants',
        'plan_type',
        server_default='free',
        existing_type=sa.String(length=20),
        existing_nullable=True
    )
    
    # Drop unique constraint
    op.drop_constraint(
        'uq_tenants_business_registration_number',
        'tenants',
        type_='unique'
    )
    
    # Drop business_registration_number column
    op.drop_column('tenants', 'business_registration_number')
