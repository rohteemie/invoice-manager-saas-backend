"""Implement tenant-scoped email uniqueness for multi-tenancy support

Revision ID: tenant_scoped_email
Revises: 673c70294531
Create Date: 2026-04-03 14:00:00.000000

This migration:
1. Removes global unique constraint on email column
2. Removes global unique index on email column
3. Adds composite unique constraint on (email, tenant_id)
4. Allows same email to exist in different tenants
5. Ensures email is still unique within each tenant
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'tenant_scoped_email'
down_revision = '673c70294531'
branch_labels = None
depends_on = None


def upgrade():
    """Remove global email unique constraint and add tenant-scoped constraint."""
    # Drop the unique index on email (may have different names depending on DB)
    try:
        op.drop_index('ix_users_email', table_name='users')
    except Exception as e:
        print(f"Note: Could not drop ix_users_email index: {e}")
        pass

    # Drop unique constraint created by UniqueConstraint in initial migration
    # The constraint is typically named with pattern like users_email_key or uq_users_email
    try:
        # Try the default SQLAlchemy naming pattern
        op.drop_constraint('users_email_key', 'users', type_='unique')
    except Exception:
        try:
            # Try alternative naming
            op.drop_constraint('uq_users_email', 'users', type_='unique')
        except Exception:
            try:
                # Try another alternative
                op.drop_constraint('uq_user_email', 'users', type_='unique')
            except Exception as e:
                print(f"Note: Could not find and drop existing email constraint: {e}")
                pass

    # Create new composite unique constraint: (email, tenant_id)
    # This allows same email in different tenants but prevents duplicates within a tenant
    op.create_unique_constraint(
        'uq_user_email_tenant',
        'users',
        ['email', 'tenant_id']
    )


def downgrade():
    """Revert to global email uniqueness."""
    # Drop the composite constraint
    try:
        op.drop_constraint('uq_user_email_tenant', 'users', type_='unique')
    except Exception as e:
        print(f"Note: Could not drop composite constraint: {e}")
        pass

    # Restore the global unique constraint on email
    # This will fail if duplicate emails exist, requiring data cleanup first
    op.create_unique_constraint(
        'users_email_key',
        'users',
        ['email']
    )

