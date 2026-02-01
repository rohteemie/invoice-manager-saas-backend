"""
Test suite for permission checks in user management.
Validates:
- Owner role cannot be changed via API
- Self-deletion prevention
- Owner-to-owner deletion prevention
- Appropriate 403 errors for unauthorized operations
"""


def test_cannot_change_owner_role_to_other_role(client, auth_headers, test_user, db_session):
    """Test that owner role cannot be changed to another role via API."""
    # Try to change owner role to admin
    response = client.put(
        f"/api/v1/users/{test_user.id}",
        headers=auth_headers,
        json={
            "role": "admin"
        }
    )
    assert response.status_code == 403
    assert "owner role cannot be changed" in response.json()["message"].lower()

    # Verify role was not changed
    db_session.refresh(test_user)
    assert test_user.role.value == "owner"


def test_cannot_change_user_role_to_owner(client, auth_headers, test_admin, db_session):
    """Test that a user's role cannot be changed to owner via API."""
    # Try to change admin role to owner
    response = client.put(
        f"/api/v1/users/{test_admin.id}",
        headers=auth_headers,
        json={
            "role": "owner"
        }
    )
    assert response.status_code == 403
    assert "cannot assign owner role" in response.json()["message"].lower()

    # Verify role was not changed
    db_session.refresh(test_admin)
    assert test_admin.role.value == "admin"


def test_cannot_change_owner_role_as_admin(client, admin_auth_headers, test_user, db_session):
    """Test that admin cannot change owner's role (admin cannot access user update endpoint)."""
    response = client.put(
        f"/api/v1/users/{test_user.id}",
        headers=admin_auth_headers,
        json={
            "role": "manager"
        }
    )
    assert response.status_code == 403
    assert "insufficient" in response.json()["message"].lower()

    # Verify role was not changed
    db_session.refresh(test_user)
    assert test_user.role.value == "owner"


def test_owner_cannot_delete_another_owner(client, auth_headers, db_session, test_tenant):
    """Test that an owner cannot delete another owner."""
    from app.models.user import User, UserRole
    from app.core.security import get_password_hash

    # Create another owner in the same tenant
    second_owner = User(
        email="owner2@testcompany.com",
        full_name="Second Owner",
        hashed_password=get_password_hash("TestPass123!"),
        role=UserRole.OWNER,
        tenant_id=test_tenant.id,
        is_active=True,
        is_verified=True
    )
    db_session.add(second_owner)
    db_session.commit()
    db_session.refresh(second_owner)

    # Try to delete the second owner
    response = client.delete(
        f"/api/v1/users/{second_owner.id}",
        headers=auth_headers
    )
    assert response.status_code == 403
    assert "cannot delete another owner" in response.json()["message"].lower()

    # Verify second owner was not deleted
    db_session.refresh(second_owner)
    assert second_owner.is_active is True


def test_owner_can_delete_non_owner_users(client, auth_headers, test_admin, db_session):
    """Test that owner can still delete non-owner users."""
    response = client.delete(
        f"/api/v1/users/{test_admin.id}",
        headers=auth_headers
    )
    assert response.status_code == 200
    assert "deactivated" in response.json()["message"].lower()

    # Verify user was deactivated
    db_session.refresh(test_admin)
    assert test_admin.is_active is False


def test_owner_can_update_non_owner_roles(client, auth_headers, test_manager, db_session):
    """Test that owner can update non-owner roles (except to owner)."""
    response = client.put(
        f"/api/v1/users/{test_manager.id}",
        headers=auth_headers,
        json={
            "role": "admin"
        }
    )
    assert response.status_code == 200

    # Verify role was changed
    db_session.refresh(test_manager)
    assert test_manager.role.value == "admin"


def test_admin_cannot_update_users(client, admin_auth_headers, test_manager, db_session):
    """Test that admin cannot update non-owner roles (only owners can)."""
    response = client.put(
        f"/api/v1/users/{test_manager.id}",
        headers=admin_auth_headers,
        json={
            "role": "attendant"
        }
    )
    assert response.status_code == 403
    assert "insufficient" in response.json()["message"].lower()

    # Verify role was not changed
    db_session.refresh(test_manager)
    assert test_manager.role.value == "manager"


def test_admin_cannot_assign_owner_role(client, admin_auth_headers, test_attendant, db_session):
    """Test that admin cannot assign owner role to any user (admin cannot access user update endpoint)."""
    response = client.put(
        f"/api/v1/users/{test_attendant.id}",
        headers=admin_auth_headers,
        json={
            "role": "owner"
        }
    )
    assert response.status_code == 403
    assert "insufficient" in response.json()["message"].lower()

    # Verify role was not changed
    db_session.refresh(test_attendant)
    assert test_attendant.role.value == "attendant"


def test_self_deletion_prevention(client, auth_headers, test_user):
    """Test that users cannot delete themselves (already tested but included for completeness)."""
    response = client.delete(
        f"/api/v1/users/{test_user.id}",
        headers=auth_headers
    )
    assert response.status_code == 400
    assert "cannot delete your own account" in response.json()["message"].lower()


def test_manager_cannot_update_roles_forbidden(client, manager_auth_headers, test_attendant):
    """Test that manager gets proper 403 error when trying to update users."""
    response = client.put(
        f"/api/v1/users/{test_attendant.id}",
        headers=manager_auth_headers,
        json={
            "role": "admin"
        }
    )
    assert response.status_code == 403
    assert "insufficient" in response.json()["message"].lower()


def test_attendant_cannot_update_roles_forbidden(client, attendant_auth_headers, test_manager):
    """Test that attendant gets proper 403 error when trying to update users."""
    response = client.put(
        f"/api/v1/users/{test_manager.id}",
        headers=attendant_auth_headers,
        json={
            "role": "admin"
        }
    )
    assert response.status_code == 403
    assert "insufficient" in response.json()["message"].lower()
