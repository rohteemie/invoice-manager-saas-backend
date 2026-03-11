"""
Test suite for Authentication endpoints.
Tests user registration, login, token refresh, and JWT token handling.
"""
from jose import jwt
from app.core.config import settings


def test_register_superadmin_by_superadmin(client, superadmin_auth_headers):
    """Test that superadmin can create another superadmin."""
    response = client.post(
        "/api/v1/auth/register",
        headers=superadmin_auth_headers,
        json={
            "email": "newsuperadmin@platform.com",
            "full_name": "New Superadmin",
            "password": "SecurePassword123@",
            "role": "admin",
            "is_superadmin": True
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "newsuperadmin@platform.com"
    assert data["is_superadmin"] is True
    assert data["tenant_id"] is None


def test_register_requires_superadmin_auth(client, test_tenant):
    """Test that register endpoint requires superadmin authentication."""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "newuser@testcompany.com",
            "full_name": "New User",
            "password": "SecurePassword123@",
            "role": "manager",
            "tenant_id": test_tenant.id
        }
    )
    # Should fail because no auth provided
    assert response.status_code == 401


def test_register_non_superadmin_forbidden(
    client, superadmin_auth_headers, test_tenant
):
    """Test that /auth/register rejects non-superadmin user creation."""
    response = client.post(
        "/api/v1/auth/register",
        headers=superadmin_auth_headers,
        json={
            "email": "regularuser@testcompany.com",
            "full_name": "Regular User",
            "password": "SecurePassword123@",
            "role": "manager",
            "tenant_id": test_tenant.id,
            "is_superadmin": False
        }
    )
    assert response.status_code == 400
    assert "superadmin creation only" in response.json()["message"].lower()


def test_register_superadmin_with_tenant_rejected(
    client, superadmin_auth_headers, test_tenant
):
    """Test that superadmins cannot be associated with a tenant."""
    response = client.post(
        "/api/v1/auth/register",
        headers=superadmin_auth_headers,
        json={
            "email": "badsuperadmin@platform.com",
            "full_name": "Bad Superadmin",
            "password": "SecurePassword123@",
            "role": "admin",
            "tenant_id": test_tenant.id,
            "is_superadmin": True
        }
    )
    assert response.status_code == 400
    assert "cannot be associated" in response.json()["message"].lower()


def test_register_duplicate_email(client, test_user, superadmin_auth_headers):
    """Test that registering with duplicate email is rejected."""
    response = client.post(
        "/api/v1/auth/register",
        headers=superadmin_auth_headers,
        json={
            "email": test_user.email,
            "full_name": "Duplicate User",
            "password": "SecurePassword123@",
            "role": "attendant",
            "is_superadmin": True
        }
    )
    assert response.status_code == 400
    assert "already registered" in response.json()["message"].lower()


def test_register_invalid_email(client, superadmin_auth_headers):
    """Test that invalid email format is rejected."""
    response = client.post(
        "/api/v1/auth/register",
        headers=superadmin_auth_headers,
        json={
            "email": "not-an-email",
            "full_name": "Invalid Email",
            "password": "SecurePassword123@",
            "role": "admin",
            "is_superadmin": True
        }
    )
    assert response.status_code == 422  # Validation error


def test_register_short_password(client, superadmin_auth_headers):
    """Test that short passwords are rejected."""
    response = client.post(
        "/api/v1/auth/register",
        headers=superadmin_auth_headers,
        json={
            "email": "shortpw@platform.com",
            "full_name": "Short Password",
            "password": "Short1",  # Less than 8 characters
            "role": "admin",
            "is_superadmin": True
        }
    )
    assert response.status_code == 422  # Validation error


def test_login_success(client, test_user):
    """Test successful login."""
    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": test_user.email,
            "password": "TestPass123!"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"

    # Verify token contains correct user info
    payload = jwt.decode(
        data["access_token"],
        settings.SECRET_KEY,
        algorithms=["HS256"]
    )
    assert payload["sub"] == test_user.id
    assert payload["tenant_id"] == test_user.tenant_id
    assert payload["role"] == test_user.role.value


def test_login_incorrect_password(client, test_user):
    """Test login with incorrect password."""
    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": test_user.email,
            "password": "WrongPassword123!"
        }
    )
    assert response.status_code == 401
    assert "incorrect" in response.json()["message"].lower()


def test_login_nonexistent_user(client):
    """Test login with non-existent user."""
    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": "nonexistent@testcompany.com",
            "password": "TestPass123!"
        }
    )
    assert response.status_code == 401
    assert "incorrect" in response.json()["message"].lower()


def test_login_inactive_user(client, inactive_user):
    """Test that inactive users cannot login."""
    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": inactive_user.email,
            "password": "TestPass123!"
        }
    )
    # Should return 401 (not 403) to avoid account enumeration
    assert response.status_code == 401
    assert "incorrect" in response.json()["message"].lower()


def test_refresh_token_success(client, test_user):
    """Test successful token refresh."""
    # First, login to get tokens
    login_response = client.post(
        "/api/v1/auth/login",
        data={
            "username": test_user.email,
            "password": "TestPass123!"
        }
    )
    refresh_token = login_response.json()["refresh_token"]

    # Now refresh the token (using request body for security)
    response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"

    # Verify new token contains correct user info
    payload = jwt.decode(
        data["access_token"],
        settings.SECRET_KEY,
        algorithms=["HS256"]
    )
    assert payload["sub"] == test_user.id
    assert payload["tenant_id"] == test_user.tenant_id


def test_refresh_token_invalid(client):
    """Test refresh with invalid token."""
    response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": "invalid-token"}
    )
    assert response.status_code == 401
    assert "invalid" in response.json()["message"].lower()


def test_refresh_token_inactive_user(client, test_user, db_session):
    """Test that refresh fails for inactive users."""
    # First, login to get tokens
    login_response = client.post(
        "/api/v1/auth/login",
        data={
            "username": test_user.email,
            "password": "TestPass123!"
        }
    )
    refresh_token = login_response.json()["refresh_token"]

    # Deactivate the user
    test_user.is_active = False
    db_session.commit()

    # Try to refresh - should fail (using request body for security)
    response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token}
    )
    assert response.status_code == 401
    assert "inactive" in response.json()["message"].lower()


def test_password_is_hashed(client, superadmin_auth_headers, db_session):
    """Test that passwords are properly hashed in database."""
    from app.models.user import User as UserModel

    password = "TestPass123!"
    response = client.post(
        "/api/v1/auth/register",
        headers=superadmin_auth_headers,
        json={
            "email": "hashtest@platform.com",
            "full_name": "Hash Test",
            "password": password,
            "role": "admin",
            "is_superadmin": True
        }
    )
    assert response.status_code == 201

    # Check that password is hashed in database
    user = db_session.query(UserModel).filter(
        UserModel.email == "hashtest@platform.com"
    ).first()
    assert user.hashed_password != password
    assert user.hashed_password.startswith("$2b$")  # bcrypt hash


def test_access_token_expiration(client, test_user):
    """Test that access token contains expiration."""
    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": test_user.email,
            "password": "TestPass123!"
        }
    )
    token = response.json()["access_token"]

    payload = jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=["HS256"]
    )
    assert "exp" in payload
    assert payload["exp"] > 0


def test_different_users_different_tokens(client, test_user, test_admin):
    """Test that different users get different tokens."""
    response1 = client.post(
        "/api/v1/auth/login",
        data={
            "username": test_user.email,
            "password": "TestPass123!"
        }
    )
    token1 = response1.json()["access_token"]

    response2 = client.post(
        "/api/v1/auth/login",
        data={
            "username": test_admin.email,
            "password": "TestPass123!"
        }
    )
    token2 = response2.json()["access_token"]

    assert token1 != token2

    # Verify tokens contain different user IDs
    payload1 = jwt.decode(token1, settings.SECRET_KEY, algorithms=["HS256"])
    payload2 = jwt.decode(token2, settings.SECRET_KEY, algorithms=["HS256"])
    assert payload1["sub"] != payload2["sub"]
    assert payload1["role"] != payload2["role"]
