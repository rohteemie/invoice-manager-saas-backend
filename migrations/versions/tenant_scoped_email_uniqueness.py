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
from sqlalchemy.engine import reflection


# revision identifiers, used by Alembic.
revision = 'tenant_scoped_email'
down_revision = '673c70294531'
branch_labels = None
depends_on = None


def _get_existing_constraint_names(bind, table_name):
    """Return the set of unique constraint names on *table_name*."""
    insp = reflection.Inspector.from_engine(bind)
    return {
        uc['name']
        for uc in insp.get_unique_constraints(table_name)
        if uc.get('name')
    }


def _get_existing_index_names(bind, table_name):
    """Return the set of index names on *table_name*."""
    insp = reflection.Inspector.from_engine(bind)
    return {idx['name'] for idx in insp.get_indexes(table_name)}


def upgrade():
    """Remove global email unique constraint and add tenant-scoped one."""
    bind = op.get_bind()

    # Drop the non-unique index on email if it exists
    existing_indexes = _get_existing_index_names(bind, 'users')
    if 'ix_users_email' in existing_indexes:
        op.drop_index('ix_users_email', table_name='users')

    # Drop whichever global unique constraint on email exists
    existing_constraints = _get_existing_constraint_names(bind, 'users')
    for candidate in ('users_email_key', 'uq_users_email', 'uq_user_email'):
        if candidate in existing_constraints:
            op.drop_constraint(candidate, 'users', type_='unique')
            break  # Only one should exist; stop after the first match

    # Add composite unique constraint: (email, tenant_id)
    # Same email is allowed in different tenants but must be unique per tenant.
    if 'uq_user_email_tenant' not in existing_constraints:
        op.create_unique_constraint(
            'uq_user_email_tenant',
            'users',
            ['email', 'tenant_id']
        )


def downgrade():
    """Revert to global email uniqueness."""
    bind = op.get_bind()
    existing_constraints = _get_existing_constraint_names(bind, 'users')

    if 'uq_user_email_tenant' in existing_constraints:
        op.drop_constraint('uq_user_email_tenant', 'users', type_='unique')

    # Restore the global unique constraint on email.
    # This will fail if duplicate emails exist, requiring data cleanup first.
    if 'users_email_key' not in existing_constraints:
        op.create_unique_constraint('users_email_key', 'users', ['email'])
