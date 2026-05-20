"""
Test suite for Password Change on First Login functionality.
Tests must_change_password flag and force-change-password endpoint.
"""
import pytest
from app.models.user import User as UserModel, UserRole
from app.core.security import get_password_hash


@pytest.fixture
def user_must_change_password(db_session, test_tenant):
    """Create a test user who must change password."""
    user = UserModel(
        email="mustchange@testcompany.com",
        full_name="Must Change User",
        hashed_password=get_password_hash("TempPass123!"),
        role=UserRole.ATTENDANT,
        tenant_id=test_tenant.id,
        is_active=True,
        is_verified=True,
        must_change_password=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    yield user
    # Cleanup
    db_session.delete(user)
    db_session.commit()


def test_login_returns_requires_password_change(client, user_must_change_password):
    """Test that login returns requires_password_change flag when True."""
    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": user_must_change_password.email,
            "password": "TempPass123!"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "requires_password_change" in data
    assert data["requires_password_change"] is True


def test_login_returns_false_when_no_change_needed(client, test_user):
    """Test that login returns requires_password_change=False for normal users."""
    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": test_user.email,
            "password": "TestPass123!"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "requires_password_change" in data
    assert data["requires_password_change"] is False


def test_select_tenant_blocks_token_for_must_change_password_user(
    client, user_must_change_password, test_tenant
):
    """Test tenant selection blocks token issuance until password change."""
    response = client.post(
        "/api/v1/auth/select-tenant",
        json={
            "email": user_must_change_password.email,
            "password": "TempPass123!",
            "tenant_id": test_tenant.id
        }
    )

    assert response.status_code == 403
    assert "password change required" in response.json()["message"].lower()


def test_force_change_password_with_email_and_tenant(
    client,
    user_must_change_password,
    db_session
):
    """
    Test password change can complete without a token for tenant selection flow.
    """
    response = client.post(
        "/api/v1/auth/force-change-password",
        json={
            "email": user_must_change_password.email,
            "tenant_id": user_must_change_password.tenant_id,
            "current_password": "TempPass123!",
            "new_password": "TenantFlow456@"
        }
    )
    assert response.status_code == 200
    assert "success" in response.json()["message"].lower()

    db_session.refresh(user_must_change_password)
    assert user_must_change_password.must_change_password is False

    login_response = client.post(
        "/api/v1/auth/login",
        data={
            "username": user_must_change_password.email,
            "password": "TenantFlow456@"
        }
    )
    assert login_response.status_code == 200
    assert login_response.json()["requires_password_change"] is False


def test_force_change_password_success(client, user_must_change_password, db_session):
    """Test successful password change via force-change-password endpoint."""
    # First login to get token
    login_response = client.post(
        "/api/v1/auth/login",
        data={
            "username": user_must_change_password.email,
            "password": "TempPass123!"
        }
    )
    token = login_response.json()["access_token"]

    # Change password
    response = client.post(
        "/api/v1/auth/force-change-password",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "current_password": "TempPass123!",
            "new_password": "NewSecure456@"
        }
    )
    assert response.status_code == 200
    assert "success" in response.json()["message"].lower()

    # Verify flag is cleared
    db_session.refresh(user_must_change_password)
    assert user_must_change_password.must_change_password is False

    # Verify new password works
    login_response = client.post(
        "/api/v1/auth/login",
        data={
            "username": user_must_change_password.email,
            "password": "NewSecure456@"
        }
    )
    assert login_response.status_code == 200
    assert login_response.json()["requires_password_change"] is False


def test_force_change_password_wrong_current(client, user_must_change_password):
    """Test that wrong current password is rejected."""
    # First login to get token
    login_response = client.post(
        "/api/v1/auth/login",
        data={
            "username": user_must_change_password.email,
            "password": "TempPass123!"
        }
    )
    token = login_response.json()["access_token"]

    # Try with wrong current password
    response = client.post(
        "/api/v1/auth/force-change-password",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "current_password": "WrongPassword123!",
            "new_password": "NewSecure456@"
        }
    )
    assert response.status_code == 401
    assert "incorrect" in response.json()["message"].lower()


def test_force_change_password_credential_flow_wrong_current(
    client, user_must_change_password
):
    """Test credential flow uses generic auth error for wrong password."""
    response = client.post(
        "/api/v1/auth/force-change-password",
        json={
            "email": user_must_change_password.email,
            "tenant_id": user_must_change_password.tenant_id,
            "current_password": "WrongPassword123!",
            "new_password": "NewSecure456@"
        }
    )

    assert response.status_code == 401
    assert response.json()["message"] == "Incorrect email or password"


def test_force_change_password_same_as_current(client, user_must_change_password):
    """Test that new password cannot be same as current."""
    # First login to get token
    login_response = client.post(
        "/api/v1/auth/login",
        data={
            "username": user_must_change_password.email,
            "password": "TempPass123!"
        }
    )
    token = login_response.json()["access_token"]

    # Try to set same password
    response = client.post(
        "/api/v1/auth/force-change-password",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "current_password": "TempPass123!",
            "new_password": "TempPass123!"
        }
    )
    assert response.status_code == 400
    assert "different" in response.json()["message"].lower()


def test_force_change_password_no_auth(client):
    """Test that force-change-password requires authentication."""
    response = client.post(
        "/api/v1/auth/force-change-password",
        json={
            "current_password": "TempPass123!",
            "new_password": "NewSecure456@"
        }
    )
    assert response.status_code == 400
    assert "email and tenant_id are required" in response.json()[
        "message"
    ].lower()


def test_owner_created_user_has_must_change_flag(client, auth_headers, db_session):
    """Test that owner-created users have must_change_password=True."""
    # Owner creates a new user
    response = client.post(
        "/api/v1/users/",
        headers=auth_headers,
        json={
            "email": "newuser_flag_test@testcompany.com",
            "full_name": "New User Flag Test",
            "password": "TempPassword123@",
            "role": "attendant"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["must_change_password"] is True

    # Clean up - get the user and delete
    user = db_session.query(UserModel).filter(
        UserModel.email == "newuser_flag_test@testcompany.com"
    ).first()
    if user:
        db_session.delete(user)
        db_session.commit()
