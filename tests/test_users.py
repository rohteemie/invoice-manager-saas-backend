"""
Test suite for User Management endpoints.
Tests user retrieval, updates, role-based access control, and soft deletion.
"""
import pytest


def test_get_current_user(client, auth_headers):
    """Test getting current authenticated user info."""
    response = client.get(
        "/api/v1/users/me",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "owner@testcompany.com"
    assert data["full_name"] == "Test Owner"
    assert data["role"] == "owner"
    assert "hashed_password" not in data


def test_get_current_user_unauthorized(client):
    """Test that accessing /me without auth fails."""
    response = client.get("/api/v1/users/me")
    assert response.status_code == 401


def test_get_current_user_invalid_token(client):
    """Test that invalid token is rejected."""
    response = client.get(
        "/api/v1/users/me",
        headers={"Authorization": "Bearer invalid-token"}
    )
    assert response.status_code == 401


def test_list_users_as_admin(client, admin_auth_headers, test_user, test_admin):
    """Test that admin can list users in their tenant."""
    response = client.get(
        "/api/v1/users/",
        headers=admin_auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2  # At least test_user and test_admin
    emails = [u["email"] for u in data]
    assert "owner@testcompany.com" in emails
    assert "admin@testcompany.com" in emails


def test_list_users_as_owner(client, auth_headers):
    """Test that owner can list users."""
    response = client.get(
        "/api/v1/users/",
        headers=auth_headers
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_list_users_as_manager_forbidden(client, manager_auth_headers):
    """Test that manager cannot list users (requires Admin role)."""
    response = client.get(
        "/api/v1/users/",
        headers=manager_auth_headers
    )
    assert response.status_code == 403
    assert "insufficient" in response.json()["detail"].lower()


def test_list_users_as_attendant_forbidden(client, attendant_auth_headers):
    """Test that attendant cannot list users."""
    response = client.get(
        "/api/v1/users/",
        headers=attendant_auth_headers
    )
    assert response.status_code == 403


def test_list_users_pagination(client, auth_headers, test_admin, test_manager):
    """Test user list pagination."""
    response = client.get(
        "/api/v1/users/?skip=0&limit=1",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1


def test_get_user_by_id_as_admin(client, admin_auth_headers, test_user):
    """Test that admin can get user by ID."""
    response = client.get(
        f"/api/v1/users/{test_user.id}",
        headers=admin_auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == test_user.id
    assert data["email"] == test_user.email


def test_get_user_by_id_as_owner(client, auth_headers, test_admin):
    """Test that owner can get user by ID."""
    response = client.get(
        f"/api/v1/users/{test_admin.id}",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == test_admin.id


def test_get_user_by_id_as_manager_forbidden(client, manager_auth_headers, test_user):
    """Test that manager cannot get user by ID."""
    response = client.get(
        f"/api/v1/users/{test_user.id}",
        headers=manager_auth_headers
    )
    assert response.status_code == 403


def test_get_user_not_found(client, auth_headers):
    """Test getting non-existent user."""
    response = client.get(
        "/api/v1/users/nonexistent-id",
        headers=auth_headers
    )
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_update_user_as_admin(client, admin_auth_headers, test_attendant):
    """Test that admin can update user information."""
    response = client.put(
        f"/api/v1/users/{test_attendant.id}",
        headers=admin_auth_headers,
        json={
            "full_name": "Updated Attendant Name",
            "role": "manager"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["full_name"] == "Updated Attendant Name"
    assert data["role"] == "manager"


def test_update_user_as_owner(client, auth_headers, test_manager):
    """Test that owner can update user information."""
    response = client.put(
        f"/api/v1/users/{test_manager.id}",
        headers=auth_headers,
        json={
            "full_name": "Updated Manager Name"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["full_name"] == "Updated Manager Name"


def test_update_user_as_manager_forbidden(client, manager_auth_headers, test_attendant):
    """Test that manager cannot update users."""
    response = client.put(
        f"/api/v1/users/{test_attendant.id}",
        headers=manager_auth_headers,
        json={
            "full_name": "Should Not Update"
        }
    )
    assert response.status_code == 403


def test_update_user_verify_status(client, auth_headers, test_attendant):
    """Test updating user verification status."""
    response = client.put(
        f"/api/v1/users/{test_attendant.id}",
        headers=auth_headers,
        json={
            "is_verified": True
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["is_verified"] is True


def test_update_user_not_found(client, auth_headers):
    """Test updating non-existent user."""
    response = client.put(
        "/api/v1/users/nonexistent-id",
        headers=auth_headers,
        json={"full_name": "New Name"}
    )
    assert response.status_code == 404


def test_delete_user_as_owner(client, auth_headers, test_attendant, db_session):
    """Test that owner can soft delete users."""
    response = client.delete(
        f"/api/v1/users/{test_attendant.id}",
        headers=auth_headers
    )
    assert response.status_code == 200
    assert "deactivated" in response.json()["message"].lower()

    # Verify user is deactivated, not deleted
    db_session.refresh(test_attendant)
    assert test_attendant.is_active is False


def test_delete_user_as_admin_forbidden(client, admin_auth_headers, test_attendant):
    """Test that admin cannot delete users (requires Owner role)."""
    response = client.delete(
        f"/api/v1/users/{test_attendant.id}",
        headers=admin_auth_headers
    )
    assert response.status_code == 403
    assert "insufficient" in response.json()["detail"].lower()


def test_delete_user_as_manager_forbidden(client, manager_auth_headers, test_attendant):
    """Test that manager cannot delete users."""
    response = client.delete(
        f"/api/v1/users/{test_attendant.id}",
        headers=manager_auth_headers
    )
    assert response.status_code == 403


def test_delete_self_forbidden(client, auth_headers, test_user):
    """Test that user cannot delete their own account."""
    response = client.delete(
        f"/api/v1/users/{test_user.id}",
        headers=auth_headers
    )
    assert response.status_code == 400
    assert "cannot delete your own account" in response.json()["detail"].lower()


def test_delete_user_not_found(client, auth_headers):
    """Test deleting non-existent user."""
    response = client.delete(
        "/api/v1/users/nonexistent-id",
        headers=auth_headers
    )
    assert response.status_code == 404


def test_inactive_user_cannot_access_endpoints(client, inactive_user):
    """Test that deactivated users cannot access protected endpoints."""
    # Try to login
    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": inactive_user.email,
            "password": "TestPassword123"
        }
    )
    assert response.status_code == 403
    assert "inactive" in response.json()["detail"].lower()


def test_role_hierarchy_owner_highest(client, auth_headers, test_admin, test_manager, test_attendant):
    """Test that owner (highest role) can access all admin functions."""
    # Owner can list users
    response = client.get("/api/v1/users/", headers=auth_headers)
    assert response.status_code == 200

    # Owner can update users
    response = client.put(
        f"/api/v1/users/{test_admin.id}",
        headers=auth_headers,
        json={"full_name": "Updated by Owner"}
    )
    assert response.status_code == 200

    # Owner can delete users
    response = client.delete(
        f"/api/v1/users/{test_attendant.id}",
        headers=auth_headers
    )
    assert response.status_code == 200


def test_role_hierarchy_admin_can_manage_users(client, admin_auth_headers, test_manager):
    """Test that admin can manage users but not delete them."""
    # Admin can list users
    response = client.get("/api/v1/users/", headers=admin_auth_headers)
    assert response.status_code == 200

    # Admin can update users
    response = client.put(
        f"/api/v1/users/{test_manager.id}",
        headers=admin_auth_headers,
        json={"full_name": "Updated by Admin"}
    )
    assert response.status_code == 200

    # Admin cannot delete users
    response = client.delete(
        f"/api/v1/users/{test_manager.id}",
        headers=admin_auth_headers
    )
    assert response.status_code == 403
