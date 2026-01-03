"""
Test suite for Tenant Isolation.
Tests that users can only access data from their own tenant.
Validates cross-tenant data isolation at the API level.
"""


def test_user_cannot_see_other_tenant_users(
    client,
    auth_headers,
    second_tenant_user
):
    """Test that users can only see users from their own tenant."""
    response = client.get(
        "/api/v1/users/",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()

    # Should not see second tenant's user
    emails = [u["email"] for u in data["items"]]
    assert "owner@secondcompany.com" not in emails


def test_user_cannot_access_other_tenant_user_by_id(
    client,
    auth_headers,
    second_tenant_user
):
    """Test that users cannot access other tenant's users by ID."""
    response = client.get(
        f"/api/v1/users/{second_tenant_user.id}",
        headers=auth_headers
    )
    assert response.status_code == 404
    assert "not found" in response.json()["message"].lower()


def test_user_cannot_update_other_tenant_user(
    client,
    auth_headers,
    second_tenant_user
):
    """Test that users cannot update users from other tenants."""
    response = client.put(
        f"/api/v1/users/{second_tenant_user.id}",
        headers=auth_headers,
        json={
            "full_name": "Malicious Update"
        }
    )
    assert response.status_code == 404


def test_user_cannot_delete_other_tenant_user(
    client,
    auth_headers,
    second_tenant_user
):
    """Test that users cannot delete users from other tenants."""
    response = client.delete(
        f"/api/v1/users/{second_tenant_user.id}",
        headers=auth_headers
    )
    assert response.status_code == 404


def test_second_tenant_cannot_see_first_tenant_users(
    client,
    second_tenant_auth_headers,
    test_user,
    test_admin
):
    """Test isolation from second tenant's perspective."""
    response = client.get(
        "/api/v1/users/",
        headers=second_tenant_auth_headers
    )
    assert response.status_code == 200
    data = response.json()

    # Should not see first tenant's users
    emails = [u["email"] for u in data["items"]]
    assert "owner@testcompany.com" not in emails
    assert "admin@testcompany.com" not in emails


def test_tokens_contain_correct_tenant_id(
    client,
    test_user,
    second_tenant_user
):
    """Test that JWT tokens contain the correct tenant_id."""
    from jose import jwt
    from app.core.config import settings

    # Login as first tenant user
    response1 = client.post(
        "/api/v1/auth/login",
        data={
            "username": test_user.email,
            "password": "TestPassword123"
        }
    )
    token1 = response1.json()["access_token"]
    payload1 = jwt.decode(token1, settings.SECRET_KEY, algorithms=["HS256"])

    # Login as second tenant user
    response2 = client.post(
        "/api/v1/auth/login",
        data={
            "username": second_tenant_user.email,
            "password": "TestPassword123"
        }
    )
    token2 = response2.json()["access_token"]
    payload2 = jwt.decode(token2, settings.SECRET_KEY, algorithms=["HS256"])

    # Tokens should have different tenant IDs
    assert payload1["tenant_id"] == test_user.tenant_id
    assert payload2["tenant_id"] == second_tenant_user.tenant_id
    assert payload1["tenant_id"] != payload2["tenant_id"]


def test_user_list_filtered_by_tenant(
    client,
    auth_headers,
    test_user,
    test_admin,
    test_manager,
    second_tenant_user,
    db_session
):
    """Test that user list is properly filtered by tenant."""
    response = client.get(
        "/api/v1/users/",
        headers=auth_headers
    )
    assert response.status_code == 200
    response_data = response.json()
    data = response_data["items"]

    # Count users in first tenant
    tenant_ids = [u["tenant_id"] for u in data]
    assert all(tid == test_user.tenant_id for tid in tenant_ids)

    # Verify second tenant user is not in the list
    user_ids = [u["id"] for u in data]
    assert second_tenant_user.id not in user_ids


def test_cross_tenant_user_access_via_auth_token(
    client,
    auth_headers,
    second_tenant_user
):
    """
    Test that even with valid auth token, users cannot access
    resources from other tenants.
    """
    # Try to get second tenant user with first tenant auth
    response = client.get(
        f"/api/v1/users/{second_tenant_user.id}",
        headers=auth_headers
    )
    assert response.status_code == 404

    # Try to update second tenant user
    response = client.put(
        f"/api/v1/users/{second_tenant_user.id}",
        headers=auth_headers,
        json={"full_name": "Cross Tenant Attack"}
    )
    assert response.status_code == 404

    # Try to delete second tenant user
    response = client.delete(
        f"/api/v1/users/{second_tenant_user.id}",
        headers=auth_headers
    )
    assert response.status_code == 404


def test_multiple_users_same_email_different_tenants(
    client,
    test_tenant,
    second_tenant,
    db_session
):
    """
    Test that the same email can exist in different tenants
    (as tenant_id + email should be unique, not just email).
    Note: Current implementation has global unique email constraint.
    This test documents the current behavior.
    """
    # Register user with same email in first tenant
    response1 = client.post(
        "/api/v1/auth/register",
        json={
            "email": "sameuser@example.com",
            "full_name": "User in Tenant 1",
            "password": "TestPassword123",
            "role": "attendant",
            "tenant_id": test_tenant.id
        }
    )
    assert response1.status_code == 201

    # Try to register user with same email in second tenant
    # This will fail in current implementation due to unique email constraint
    response2 = client.post(
        "/api/v1/auth/register",
        json={
            "email": "sameuser@example.com",
            "full_name": "User in Tenant 2",
            "password": "TestPassword123",
            "role": "attendant",
            "tenant_id": second_tenant.id
        }
    )
    # Current implementation: email must be globally unique
    assert response2.status_code == 400


def test_tenant_isolation_with_deactivated_user(
    client,
    test_tenant,
    second_tenant,
    auth_headers,
    db_session
):
    """
    Test that deactivated users in other tenants don't affect
    active users in current tenant.
    """
    from app.models.user import User as UserModel
    from app.core.security import get_password_hash

    # Create and deactivate user in second tenant
    inactive_second_tenant_user = UserModel(
        email="inactive@secondcompany.com",
        full_name="Inactive Second User",
        hashed_password=get_password_hash("TestPassword123"),
        role="attendant",
        tenant_id=second_tenant.id,
        is_active=False
    )
    db_session.add(inactive_second_tenant_user)
    db_session.commit()

    # First tenant should still work normally
    response = client.get(
        "/api/v1/users/me",
        headers=auth_headers
    )
    assert response.status_code == 200

    # List users - should not include deactivated user from other tenant
    response = client.get(
        "/api/v1/users/",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json(); emails = [u["email"] for u in data.get("items", data)]
    assert "inactive@secondcompany.com" not in emails


def test_registration_enforces_tenant_id(client, test_tenant):
    """Test that user registration requires tenant_id."""
    # Note: This would fail validation, but let's verify the behavior
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "notenant@example.com",
            "full_name": "No Tenant User",
            "password": "TestPassword123",
            "role": "attendant"
            # Missing tenant_id
        }
    )
    assert response.status_code == 400  # Bad request (tenant_id required for non-superadmin)


def test_user_from_tenant_a_manages_only_tenant_a_users(
    client,
    test_tenant,
    second_tenant,
    auth_headers,
    test_admin,
    db_session
):
    """
    Comprehensive test: Verify that admin from tenant A
    can only manage users in tenant A.
    """
    from app.models.user import User as UserModel
    from app.core.security import get_password_hash

    # Create additional user in second tenant
    second_admin = UserModel(
        email="admin@secondcompany.com",
        full_name="Second Admin",
        hashed_password=get_password_hash("TestPassword123"),
        role="admin",
        tenant_id=second_tenant.id,
        is_active=True
    )
    db_session.add(second_admin)
    db_session.commit()
    db_session.refresh(second_admin)

    # Admin from first tenant lists users
    response = client.get("/api/v1/users/", headers=auth_headers)
    assert response.status_code == 200
    user_data = response.json()
    emails = [u["email"] for u in user_data.get("items", user_data)]

    # Should see only first tenant users
    assert "admin@testcompany.com" in emails
    assert "admin@secondcompany.com" not in emails

    # Try to get second tenant admin - should fail
    response = client.get(
        f"/api/v1/users/{second_admin.id}",
        headers=auth_headers
    )
    assert response.status_code == 404

    # Try to update second tenant admin - should fail
    response = client.put(
        f"/api/v1/users/{second_admin.id}",
        headers=auth_headers,
        json={"full_name": "Hacked Name"}
    )
    assert response.status_code == 404

    # Try to delete second tenant admin - should fail
    response = client.delete(
        f"/api/v1/users/{second_admin.id}",
        headers=auth_headers
    )
    assert response.status_code == 404
