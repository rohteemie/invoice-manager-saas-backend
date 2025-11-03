"""
Test suite for Email Verification functionality.
Tests email verification token generation, verification, and edge cases.
"""
from datetime import datetime, timedelta
from jose import jwt
from app.core.config import settings
from app.core.security import create_email_verification_token, verify_email_verification_token


def test_send_verification_email_success(client, db_session, test_user):
    """Test sending verification email to an unverified user."""
    # First, mark user as unverified
    test_user.is_verified = False
    db_session.commit()

    response = client.post(
        f"/api/v1/auth/send-verification-email?email={test_user.email}"
    )
    assert response.status_code == 200
    data = response.json()
    assert "verification_token" in data
    assert "message" in data
    assert data["message"] == "Verification email sent"


def test_send_verification_email_already_verified(client, db_session, test_user):
    """Test that sending verification email to already verified user fails."""
    # Mark user as verified
    test_user.is_verified = True
    db_session.commit()

    response = client.post(
        f"/api/v1/auth/send-verification-email?email={test_user.email}"
    )
    assert response.status_code == 400
    assert "already verified" in response.json()["detail"].lower()


def test_send_verification_email_nonexistent_user(client):
    """Test that sending verification email to non-existent user fails."""
    response = client.post(
        "/api/v1/auth/send-verification-email?email=nonexistent@example.com"
    )
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_verify_email_success(client, db_session, test_user):
    """Test successful email verification."""
    # Ensure user is not verified
    test_user.is_verified = False
    db_session.commit()

    # Generate verification token
    token = create_email_verification_token(test_user.email)

    # Verify email
    response = client.post(
        f"/api/v1/auth/verify-email?token={token}"
    )
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Email verified successfully"
    assert data["email"] == test_user.email

    # Verify user is now marked as verified in database
    db_session.refresh(test_user)
    assert test_user.is_verified is True


def test_verify_email_already_verified(client, db_session, test_user):
    """Test verifying an already verified email."""
    # Mark user as verified
    test_user.is_verified = True
    db_session.commit()

    # Generate verification token
    token = create_email_verification_token(test_user.email)

    # Attempt to verify again
    response = client.post(
        f"/api/v1/auth/verify-email?token={token}"
    )
    assert response.status_code == 200
    assert "already verified" in response.json()["message"].lower()


def test_verify_email_invalid_token(client):
    """Test email verification with invalid token."""
    response = client.post(
        "/api/v1/auth/verify-email?token=invalid_token_xyz"
    )
    assert response.status_code == 400
    assert "invalid" in response.json()["detail"].lower()


def test_verify_email_expired_token(client):
    """Test email verification with expired token."""
    # Create a token with a past expiration time
    expire = datetime.utcnow() - timedelta(hours=1)  # Expired 1 hour ago
    to_encode = {
        "sub": "test@example.com",
        "type": "email_verification",
        "exp": expire
    }
    expired_token = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm="HS256"
    )

    response = client.post(
        f"/api/v1/auth/verify-email?token={expired_token}"
    )
    assert response.status_code == 400
    assert "invalid" in response.json()["detail"].lower()


def test_verify_email_wrong_token_type(client):
    """Test email verification with wrong token type."""
    expire = datetime.utcnow() + timedelta(hours=1)
    to_encode = {
        "sub": "test@example.com",
        "type": "wrong_type",  # Wrong type
        "exp": expire
    }
    wrong_token = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm="HS256"
    )

    response = client.post(
        f"/api/v1/auth/verify-email?token={wrong_token}"
    )
    assert response.status_code == 400
    assert "invalid" in response.json()["detail"].lower()


def test_email_verification_token_creation_and_verification():
    """Test creating and verifying email verification tokens."""
    test_email = "test@example.com"

    # Create token
    token = create_email_verification_token(test_email)
    assert token is not None
    assert isinstance(token, str)

    # Verify token
    email = verify_email_verification_token(token)
    assert email == test_email


def test_verify_email_for_nonexistent_user(client):
    """Test email verification for a user that doesn't exist."""
    # Create token for non-existent user
    token = create_email_verification_token("nonexistent@example.com")

    response = client.post(
        f"/api/v1/auth/verify-email?token={token}"
    )
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_full_email_verification_workflow(client, test_tenant):
    """Test complete email verification workflow from registration to verification."""
    # Step 1: Register a new user
    register_response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "newuser@example.com",
            "full_name": "New User",
            "password": "SecurePassword123",
            "role": "attendant",
            "tenant_id": test_tenant.id
        }
    )
    assert register_response.status_code == 201
    user_data = register_response.json()
    assert user_data["is_verified"] is False

    # Step 2: Request verification email
    verification_request = client.post(
        "/api/v1/auth/send-verification-email?email=newuser@example.com"
    )
    assert verification_request.status_code == 200
    verification_data = verification_request.json()
    token = verification_data["verification_token"]

    # Step 3: Verify email using token
    verify_response = client.post(
        f"/api/v1/auth/verify-email?token={token}"
    )
    assert verify_response.status_code == 200
    assert verify_response.json()["message"] == "Email verified successfully"

    # Step 4: Verify user can now login (verification status doesn't block login in current implementation)
    login_response = client.post(
        "/api/v1/auth/login",
        data={
            "username": "newuser@example.com",
            "password": "SecurePassword123"
        }
    )
    assert login_response.status_code == 200


def test_verification_token_cannot_be_reused_maliciously(client, test_user, db_session):
    """Test that verification token has proper security characteristics."""
    # Ensure user is not verified
    test_user.is_verified = False
    db_session.commit()

    # Generate token
    token = create_email_verification_token(test_user.email)

    # Verify once
    response1 = client.post(f"/api/v1/auth/verify-email?token={token}")
    assert response1.status_code == 200

    # Try to verify again with same token (should be idempotent)
    response2 = client.post(f"/api/v1/auth/verify-email?token={token}")
    assert response2.status_code == 200
    assert "already verified" in response2.json()["message"].lower()
