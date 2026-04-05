"""
Test suite for Password Reset functionality.
Tests forgot password and reset password endpoints.
"""
import time
from datetime import datetime, timedelta, timezone
from app.models.user import User as UserModel
from app.core.security import generate_password_reset_token, verify_password


def test_forgot_password_existing_user(client, test_user):
    """Test forgot password with existing user email."""
    response = client.post(
        "/api/v1/auth/forgot-password",
        json={"email": test_user.email}
    )
    assert response.status_code == 200
    data = response.json()
    assert "password reset link will be sent" in data["message"].lower()
    assert data["email"] == test_user.email


def test_forgot_password_nonexistent_email(client):
    """Test forgot password with non-existent email (should still return success)."""
    response = client.post(
        "/api/v1/auth/forgot-password",
        json={"email": "nonexistent@example.com"}
    )
    # Should return 200 to prevent email enumeration
    assert response.status_code == 200
    data = response.json()
    assert "password reset link will be sent" in data["message"].lower()


def test_forgot_password_invalid_email(client):
    """Test forgot password with invalid email format."""
    response = client.post(
        "/api/v1/auth/forgot-password",
        json={"email": "not-an-email"}
    )
    # Email format validation rejects malformed addresses with 422.
    # This does not leak any user existence information.
    assert response.status_code == 422


def test_forgot_password_inactive_user(client, test_user, db_session):
    """Test forgot password with inactive user account."""
    # Deactivate user
    test_user.is_active = False
    db_session.commit()

    response = client.post(
        "/api/v1/auth/forgot-password",
        json={"email": test_user.email}
    )
    # Should still return success to prevent account enumeration
    assert response.status_code == 200

    # Reactivate user for other tests
    test_user.is_active = True
    db_session.commit()


def test_forgot_password_generates_token(client, test_user, db_session):
    """Test that forgot password generates and stores reset token."""
    response = client.post(
        "/api/v1/auth/forgot-password",
        json={"email": test_user.email}
    )
    assert response.status_code == 200

    # Refresh user from database
    db_session.refresh(test_user)

    # Check that reset token was generated and stored
    assert test_user.reset_password_token is not None
    assert len(test_user.reset_password_token) > 0
    assert test_user.reset_password_token_expires_at is not None
    assert test_user.reset_password_token_expires_at > datetime.now(timezone.utc)


def test_forgot_password_exposes_reset_link_in_test_mode(client, test_user):
    """Test that reset link is exposed in header for testing."""
    response = client.post(
        "/api/v1/auth/forgot-password",
        json={"email": test_user.email}
    )
    assert response.status_code == 200

    # In test mode, reset link should be in header
    assert "X-Reset-Link" in response.headers
    reset_link = response.headers["X-Reset-Link"]
    assert "reset-password" in reset_link
    assert "token=" in reset_link


def test_reset_password_with_valid_token(client, test_user, db_session):
    """Test successful password reset with valid token."""
    # Generate reset token
    reset_token, token_expires_at = generate_password_reset_token()
    test_user.reset_password_token = reset_token
    test_user.reset_password_token_expires_at = token_expires_at
    db_session.commit()

    new_password = "NewSecurePassword123@"

    response = client.post(
        "/api/v1/auth/reset-password",
        json={
            "token": reset_token,
            "new_password": new_password
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "successfully" in data["message"].lower()
    assert data["email"] == test_user.email

    # Refresh user from database
    db_session.refresh(test_user)

    # Verify password was updated
    assert verify_password(new_password, test_user.hashed_password)

    # Verify token was cleared
    assert test_user.reset_password_token is None
    assert test_user.reset_password_token_expires_at is None


def test_reset_password_with_invalid_token(client):
    """Test reset password with invalid token."""
    response = client.post(
        "/api/v1/auth/reset-password",
        json={
            "token": "invalid_token_12345",
            "new_password": "NewSecurePassword123@"
        }
    )
    assert response.status_code == 400
    assert "invalid or expired" in response.json()["message"].lower()


def test_reset_password_with_expired_token(client, test_user, db_session):
    """Test reset password with expired token."""
    # Generate expired token
    reset_token, _ = generate_password_reset_token()
    test_user.reset_password_token = reset_token
    # Set expiration to past (use UTC-aware datetime)
    test_user.reset_password_token_expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
    db_session.commit()

    response = client.post(
        "/api/v1/auth/reset-password",
        json={
            "token": reset_token,
            "new_password": "NewSecurePassword123@"
        }
    )
    assert response.status_code == 400
    assert "expired" in response.json()["message"].lower()

    # Verify token was cleared
    db_session.refresh(test_user)
    assert test_user.reset_password_token is None
    assert test_user.reset_password_token_expires_at is None


def test_reset_password_with_short_password(client, test_user, db_session):
    """Test reset password with password that's too short."""
    # Generate reset token
    reset_token, token_expires_at = generate_password_reset_token()
    test_user.reset_password_token = reset_token
    test_user.reset_password_token_expires_at = token_expires_at
    db_session.commit()

    response = client.post(
        "/api/v1/auth/reset-password",
        json={
            "token": reset_token,
            "new_password": "Short1"  # Less than 8 characters
        }
    )
    assert response.status_code == 422  # Validation error


def test_reset_password_inactive_user(client, test_user, db_session):
    """Test reset password with inactive user account."""
    # Generate reset token
    reset_token, token_expires_at = generate_password_reset_token()
    test_user.reset_password_token = reset_token
    test_user.reset_password_token_expires_at = token_expires_at

    # Deactivate user
    test_user.is_active = False
    db_session.commit()

    response = client.post(
        "/api/v1/auth/reset-password",
        json={
            "token": reset_token,
            "new_password": "NewSecurePassword123@"
        }
    )
    assert response.status_code == 403
    assert "inactive" in response.json()["message"].lower()

    # Reactivate user for other tests
    test_user.is_active = True
    db_session.commit()


def test_reset_password_can_login_with_new_password(client, test_user, db_session):
    """Test that user can login with new password after reset."""
    # Generate reset token
    reset_token, token_expires_at = generate_password_reset_token()
    test_user.reset_password_token = reset_token
    test_user.reset_password_token_expires_at = token_expires_at
    db_session.commit()

    new_password = "NewSecurePassword456@"

    # Reset password
    response = client.post(
        "/api/v1/auth/reset-password",
        json={
            "token": reset_token,
            "new_password": new_password
        }
    )
    assert response.status_code == 200

    # Try to login with new password
    login_response = client.post(
        "/api/v1/auth/login",
        data={
            "username": test_user.email,
            "password": new_password
        }
    )
    assert login_response.status_code == 200
    login_data = login_response.json()
    assert "access_token" in login_data
    assert "refresh_token" in login_data


def test_reset_password_cannot_login_with_old_password(client, test_user, db_session):
    """Test that user cannot login with old password after reset."""
    old_password = "TestPass123!"

    # Generate reset token
    reset_token, token_expires_at = generate_password_reset_token()
    test_user.reset_password_token = reset_token
    test_user.reset_password_token_expires_at = token_expires_at
    db_session.commit()

    new_password = "NewSecurePassword789@"

    # Reset password
    response = client.post(
        "/api/v1/auth/reset-password",
        json={
            "token": reset_token,
            "new_password": new_password
        }
    )
    assert response.status_code == 200

    # Try to login with old password (should fail)
    login_response = client.post(
        "/api/v1/auth/login",
        data={
            "username": test_user.email,
            "password": old_password
        }
    )
    assert login_response.status_code == 401


def test_reset_password_token_cannot_be_reused(client, test_user, db_session):
    """Test that reset token cannot be reused after successful reset."""
    # Generate reset token
    reset_token, token_expires_at = generate_password_reset_token()
    test_user.reset_password_token = reset_token
    test_user.reset_password_token_expires_at = token_expires_at
    db_session.commit()

    new_password = "NewSecurePassword999@"

    # First reset (should succeed)
    response = client.post(
        "/api/v1/auth/reset-password",
        json={
            "token": reset_token,
            "new_password": new_password
        }
    )
    assert response.status_code == 200

    # Try to use same token again (should fail)
    response2 = client.post(
        "/api/v1/auth/reset-password",
        json={
            "token": reset_token,
            "new_password": "AnotherPassword123@"
        }
    )
    assert response2.status_code == 400
    assert "invalid or expired" in response2.json()["message"].lower()


def test_password_reset_full_flow(client, test_user, db_session):
    """Test complete password reset flow from forgot to reset."""
    # Step 1: Request password reset
    forgot_response = client.post(
        "/api/v1/auth/forgot-password",
        json={"email": test_user.email}
    )
    assert forgot_response.status_code == 200

    # Extract reset link from header (test mode)
    assert "X-Reset-Link" in forgot_response.headers
    reset_link = forgot_response.headers["X-Reset-Link"]

    # Extract token from reset link
    token = reset_link.split("token=")[1]

    # Step 2: Reset password with token
    new_password = "CompleteFlowPassword123@"
    reset_response = client.post(
        "/api/v1/auth/reset-password",
        json={
            "token": token,
            "new_password": new_password
        }
    )
    assert reset_response.status_code == 200

    # Step 3: Login with new password
    login_response = client.post(
        "/api/v1/auth/login",
        data={
            "username": test_user.email,
            "password": new_password
        }
    )
    assert login_response.status_code == 200
    assert "access_token" in login_response.json()


def test_password_strength_validation(client, test_user, db_session):
    """Test password strength validation on reset."""
    # Generate reset token
    reset_token, token_expires_at = generate_password_reset_token()
    test_user.reset_password_token = reset_token
    test_user.reset_password_token_expires_at = token_expires_at
    db_session.commit()

    # Test various invalid passwords
    invalid_passwords = [
        "short",           # Too short
        "1234567",         # Too short, only numbers
        "",                # Empty
    ]

    for invalid_password in invalid_passwords:
        response = client.post(
            "/api/v1/auth/reset-password",
            json={
                "token": reset_token,
                "new_password": invalid_password
            }
        )
        assert response.status_code == 422  # Validation error
