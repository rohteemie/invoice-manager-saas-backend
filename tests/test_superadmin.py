"""
Test suite for Super Admin functionality.
Validates:
- Super Admin access control
- Tenant management operations (suspend/reactivate)
- Cross-tenant user viewing
- Platform-wide audit log access
- Platform statistics
"""
import pytest

from app.models.user import UserRole


@pytest.fixture
def superadmin_user(db_session):
    """Create a super admin user for testing."""
    from app.models.user import User
    from app.core.security import get_password_hash

    superadmin = User(
        email="superadmin@platform.com",
        full_name="Super Admin",
        hashed_password=get_password_hash("TestPass123!"),
        role=UserRole.ATTENDANT,  # Role doesn't matter for superadmin
        tenant_id=None,  # Superadmins don't belong to any tenant
        is_superadmin=True,
        is_verified=True
    )
    db_session.add(superadmin)
    db_session.commit()
    db_session.refresh(superadmin)
    return superadmin


@pytest.fixture
def superadmin_auth_headers(client, superadmin_user):
    """Get auth headers for super admin."""
    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": "superadmin@platform.com",
            "password": "TestPass123!"
        }
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_superadmin_can_access_admin_endpoints(
    client, superadmin_auth_headers, test_tenant
):
    """Test that super admin can access admin endpoints."""
    response = client.get(
        "/api/v1/admin/tenants",
        headers=superadmin_auth_headers
    )
    assert response.status_code == 200
    data = response.json()

    # Check pagination structure
    assert "items" in data
    assert "total" in data
    assert isinstance(data["items"], list)


def test_non_superadmin_cannot_access_admin_endpoints(
    client, auth_headers
):
    """Test that non-superadmin users get 403 on admin endpoints."""
    response = client.get(
        "/api/v1/admin/tenants",
        headers=auth_headers
    )
    assert response.status_code == 403
    assert "super admin" in response.json()["message"].lower()


def test_owner_cannot_access_admin_endpoints(
    client, auth_headers
):
    """Test that even tenant owners cannot access admin endpoints."""
    response = client.get(
        "/api/v1/admin/users",
        headers=auth_headers
    )
    assert response.status_code == 403
    assert "super admin" in response.json()["message"].lower()


def test_superadmin_can_list_all_tenants(
    client, superadmin_auth_headers, test_tenant, second_tenant
):
    """Test that super admin can view all tenants."""
    response = client.get(
        "/api/v1/admin/tenants",
        headers=superadmin_auth_headers
    )
    assert response.status_code == 200
    data = response.json()

    # Check pagination structure
    assert "items" in data
    assert "total" in data
    assert "page" in data
    assert "size" in data

    assert len(data["items"]) >= 2
    tenant_ids = [t["id"] for t in data["items"]]
    assert test_tenant.id in tenant_ids
    assert second_tenant.id in tenant_ids


def test_superadmin_can_get_specific_tenant(
    client, superadmin_auth_headers, test_tenant
):
    """Test that super admin can get details of a specific tenant."""
    response = client.get(
        f"/api/v1/admin/tenants/{test_tenant.id}",
        headers=superadmin_auth_headers
    )
    assert response.status_code == 200
    tenant = response.json()
    assert tenant["id"] == test_tenant.id
    assert tenant["name"] == test_tenant.name


def test_superadmin_can_suspend_tenant(
    client, superadmin_auth_headers, test_tenant, db_session
):
    """Test that super admin can suspend a tenant."""
    # Ensure tenant is active
    assert test_tenant.is_active is True

    response = client.put(
        f"/api/v1/admin/tenants/{test_tenant.id}/suspend",
        headers=superadmin_auth_headers
    )
    assert response.status_code == 200
    assert "suspended" in response.json()["message"].lower()

    # Verify tenant is suspended in database
    db_session.refresh(test_tenant)
    assert test_tenant.is_active is False


def test_superadmin_can_reactivate_tenant(
    client, superadmin_auth_headers, test_tenant, db_session
):
    """Test that super admin can reactivate a suspended tenant."""
    # First suspend the tenant
    test_tenant.is_active = False
    db_session.commit()

    response = client.put(
        f"/api/v1/admin/tenants/{test_tenant.id}/reactivate",
        headers=superadmin_auth_headers
    )
    assert response.status_code == 200
    assert "reactivated" in response.json()["message"].lower()

    # Verify tenant is active in database
    db_session.refresh(test_tenant)
    assert test_tenant.is_active is True


def test_cannot_suspend_already_suspended_tenant(
    client, superadmin_auth_headers, test_tenant, db_session
):
    """Test that suspending an already suspended tenant returns error."""
    # First suspend the tenant
    test_tenant.is_active = False
    db_session.commit()

    response = client.put(
        f"/api/v1/admin/tenants/{test_tenant.id}/suspend",
        headers=superadmin_auth_headers
    )
    assert response.status_code == 400
    assert "already suspended" in response.json()["message"].lower()


def test_cannot_reactivate_already_active_tenant(
    client, superadmin_auth_headers, test_tenant
):
    """Test that reactivating an already active tenant returns error."""
    assert test_tenant.is_active is True

    response = client.put(
        f"/api/v1/admin/tenants/{test_tenant.id}/reactivate",
        headers=superadmin_auth_headers
    )
    assert response.status_code == 400
    assert "already active" in response.json()["message"].lower()


def test_suspend_nonexistent_tenant_returns_404(
    client, superadmin_auth_headers
):
    """Test that suspending a non-existent tenant returns 404."""
    response = client.put(
        "/api/v1/admin/tenants/nonexistent-id/suspend",
        headers=superadmin_auth_headers
    )
    assert response.status_code == 404


def test_superadmin_can_list_all_users(
    client, superadmin_auth_headers, test_user, test_admin, db_session
):
    """Test that super admin can view all users across tenants."""
    response = client.get(
        "/api/v1/admin/users",
        headers=superadmin_auth_headers
    )
    assert response.status_code == 200
    data = response.json()

    # Check pagination structure
    assert "items" in data
    assert "total" in data

    assert len(data["items"]) >= 2
    user_ids = [u["id"] for u in data["items"]]
    assert test_user.id in user_ids
    assert test_admin.id in user_ids


def test_superadmin_can_filter_users_by_tenant(
    client, superadmin_auth_headers, test_user, test_tenant, db_session
):
    """Test that super admin can filter users by tenant."""
    response = client.get(
        f"/api/v1/admin/users?tenant_id={test_tenant.id}",
        headers=superadmin_auth_headers
    )
    assert response.status_code == 200
    data = response.json()

    # Check pagination structure
    assert "items" in data

    # All users should belong to the specified tenant
    for user in data["items"]:
        if user["tenant_id"]:  # Skip superadmins
            assert user["tenant_id"] == test_tenant.id


def test_superadmin_can_filter_users_by_active_status(
    client, superadmin_auth_headers, test_user, db_session
):
    """Test that super admin can filter users by active status."""
    # Create an inactive user
    from app.models.user import User
    from app.core.security import get_password_hash

    inactive_user = User(
        email="inactive@test.com",
        full_name="Inactive User",
        hashed_password=get_password_hash("TestPass123!"),
        role=UserRole.ATTENDANT,
        tenant_id=test_user.tenant_id,
        is_active=False,
        is_verified=True
    )
    db_session.add(inactive_user)
    db_session.commit()

    # Filter for active users
    response = client.get(
        "/api/v1/admin/users?is_active=true",
        headers=superadmin_auth_headers
    )
    assert response.status_code == 200
    data = response.json()

    # Check pagination structure
    assert "items" in data
    for user in data["items"]:
        assert user["is_active"] is True

    # Filter for inactive users
    response = client.get(
        "/api/v1/admin/users?is_active=false",
        headers=superadmin_auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) >= 1
    assert any(u["email"] == "inactive@test.com" for u in data["items"])


def test_superadmin_can_filter_users_by_superadmin_status(
    client, superadmin_auth_headers, superadmin_user
):
    """Test that super admin can filter users by superadmin status."""
    response = client.get(
        "/api/v1/admin/users?is_superadmin=true",
        headers=superadmin_auth_headers
    )
    assert response.status_code == 200
    data = response.json()

    # Check pagination structure
    assert "items" in data
    assert len(data["items"]) >= 1
    assert any(u["email"] == "superadmin@platform.com" for u in data["items"])


def test_superadmin_can_view_platform_audit_logs(
    client, superadmin_auth_headers, test_user, db_session
):
    """Test that super admin can view platform-wide audit logs."""
    response = client.get(
        "/api/v1/admin/audit-logs",
        headers=superadmin_auth_headers
    )
    assert response.status_code == 200
    data = response.json()

    # Check pagination structure
    assert "items" in data
    assert "total" in data
    assert isinstance(data["items"], list)


def test_superadmin_can_filter_audit_logs_by_tenant(
    client, superadmin_auth_headers, test_tenant
):
    """Test that super admin can filter audit logs by tenant."""
    response = client.get(
        f"/api/v1/admin/audit-logs?tenant_id={test_tenant.id}",
        headers=superadmin_auth_headers
    )
    assert response.status_code == 200
    data = response.json()

    # Check pagination structure
    assert "items" in data

    # All logs should belong to the specified tenant
    for log in data["items"]:
        if log["tenant_id"]:
            assert log["tenant_id"] == test_tenant.id


def test_superadmin_can_filter_audit_logs_by_user(
    client, superadmin_auth_headers, test_user
):
    """Test that super admin can filter audit logs by user."""
    response = client.get(
        f"/api/v1/admin/audit-logs?user_id={test_user.id}",
        headers=superadmin_auth_headers
    )
    assert response.status_code == 200
    data = response.json()

    # Check pagination structure
    assert "items" in data

    # All logs should belong to the specified user
    for log in data["items"]:
        if log["user_id"]:
            assert log["user_id"] == test_user.id


def test_superadmin_can_view_platform_stats(
    client, superadmin_auth_headers, test_tenant, test_user, superadmin_user
):
    """Test that super admin can view platform statistics."""
    response = client.get(
        "/api/v1/admin/stats",
        headers=superadmin_auth_headers
    )
    assert response.status_code == 200
    stats = response.json()

    # Verify expected stats fields exist
    assert "total_tenants" in stats
    assert "active_tenants" in stats
    assert "suspended_tenants" in stats
    assert "total_users" in stats
    assert "active_users" in stats
    assert "inactive_users" in stats
    assert "superadmins_count" in stats

    # Verify counts are reasonable
    assert stats["total_tenants"] >= 1
    assert stats["total_users"] >= 2  # At least test_user and superadmin_user
    assert stats["superadmins_count"] >= 1


def test_superadmin_bypasses_tenant_role_checks(
    client, superadmin_auth_headers, test_user
):
    """Test that superadmin bypasses tenant-level role checks."""
    # Even though superadmin has ATTENDANT role, they should have
    # access to owner-level endpoints within tenants
    # This tests the role_checker update in deps.py

    # Try to access a user management endpoint (typically requires OWNER role)
    response = client.get(
        f"/api/v1/users/{test_user.id}",
        headers=superadmin_auth_headers
    )
    # Superadmin should be able to access this regardless of their role
    # Note: This test assumes users endpoint exists and requires authentication
    assert response.status_code in [200, 404]  # 404 if endpoint not found, but not 403


def test_pagination_on_tenant_list(
    client, superadmin_auth_headers, test_tenant, second_tenant
):
    """Test pagination works on tenant list endpoint."""
    response = client.get(
        "/api/v1/admin/tenants?skip=0&limit=1",
        headers=superadmin_auth_headers
    )
    assert response.status_code == 200
    data = response.json()

    # Check pagination metadata
    assert "items" in data
    assert "total" in data
    assert "page" in data
    assert "size" in data

    assert len(data["items"]) == 1
    assert data["size"] == 1
    assert data["page"] == 1


def test_pagination_on_user_list(
    client, superadmin_auth_headers, test_user, test_admin
):
    """Test pagination works on user list endpoint."""
    response = client.get(
        "/api/v1/admin/users?skip=0&limit=1",
        headers=superadmin_auth_headers
    )
    assert response.status_code == 200
    data = response.json()

    # Check pagination metadata
    assert "items" in data
    assert "total" in data

    assert len(data["items"]) == 1


def test_pagination_on_audit_log_list(
    client, superadmin_auth_headers
):
    """Test pagination works on audit log list endpoint."""
    response = client.get(
        "/api/v1/admin/audit-logs?skip=0&limit=10",
        headers=superadmin_auth_headers
    )
    assert response.status_code == 200
    data = response.json()

    # Check pagination structure
    assert "items" in data
    assert "total" in data
    assert isinstance(data["items"], list)
    assert len(data["items"]) <= 10


def test_superadmin_token_includes_is_superadmin_flag(
    client, superadmin_user
):
    """Test that JWT token for superadmin includes is_superadmin flag."""
    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": "superadmin@platform.com",
            "password": "TestPass123!"
        }
    )
    assert response.status_code == 200

    # Decode token to verify is_superadmin is included
    from app.core.security import decode_token
    token = response.json()["access_token"]
    payload = decode_token(token)

    assert payload is not None
    assert "is_superadmin" in payload
    assert payload["is_superadmin"] is True


def test_normal_user_token_has_is_superadmin_false(
    client, test_user
):
    """Test that JWT token for normal user has is_superadmin as false."""
    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": test_user.email,
            "password": "TestPass123!"
        }
    )
    assert response.status_code == 200

    # Decode token to verify is_superadmin is false
    from app.core.security import decode_token
    token = response.json()["access_token"]
    payload = decode_token(token)

    assert payload is not None
    assert "is_superadmin" in payload
    assert payload["is_superadmin"] is False


def test_can_register_superadmin(client, superadmin_auth_headers):
    """Test that an authenticated superadmin can register another superadmin."""
    response = client.post(
        "/api/v1/auth/register",
        headers=superadmin_auth_headers,
        json={
            "email": "newsuperadmin@platform.com",
            "full_name": "New Super Admin",
            "password": "TestPass123!",
            "role": "attendant",
            "tenant_id": None,
            "is_superadmin": True
        }
    )
    assert response.status_code == 201
    user = response.json()
    assert user["is_superadmin"] is True
    assert user["tenant_id"] is None


def test_cannot_register_user_without_tenant_if_not_superadmin(
    client, superadmin_auth_headers, test_tenant
):
    """Test that the register endpoint rejects non-superadmin creation."""
    response = client.post(
        "/api/v1/auth/register",
        headers=superadmin_auth_headers,
        json={
            "email": "notenantuser@test.com",
            "full_name": "No Tenant User",
            "password": "TestPass123!",
            "role": "attendant",
            "tenant_id": None,
            "is_superadmin": False
        }
    )
    # The endpoint is superadmin-creation-only; passing is_superadmin=False
    # must be rejected regardless of the caller's credentials.
    assert response.status_code == 400
    assert "superadmin" in response.json()["message"].lower()
