"""
Test suite for Email Verification feature.
Tests email verification token generation, sending, and verification.
"""
from datetime import datetime, timezone, timedelta


def test_register_tenant_retries_verification_email_queueing(client, monkeypatch):
    """Test queue retries for verification email during tenant registration."""
    from app.api.v1.endpoints.tenants import (
        VERIFICATION_EMAIL_QUEUE_MAX_ATTEMPTS
    )

    attempts = {"count": 0}

    def flaky_delay(**kwargs):
        attempts["count"] += 1
        if attempts["count"] < VERIFICATION_EMAIL_QUEUE_MAX_ATTEMPTS:
            raise RuntimeError("Broker unavailable")
        return None

    monkeypatch.setattr(
        "app.api.v1.endpoints.tenants.send_verification_email_task.delay",
        flaky_delay
    )

    response = client.post(
        "/api/v1/tenants/register",
        json={
            "name": "Retry Queue Company",
            "domain": "retry-queue.com",
            "plan_type": "free",
            "owner": {
                "full_name": "Retry Owner",
                "email": "retry-owner@test.com",
                "password": "SecurePass123@"
            }
        }
    )

    assert response.status_code == 201
    data = response.json()
    assert data["verification_email"]["status"] == "queued"
    assert attempts["count"] == VERIFICATION_EMAIL_QUEUE_MAX_ATTEMPTS


def test_register_tenant_rolls_back_on_queue_failure(client, monkeypatch, db_session):
    """Test tenant registration rolls back when verification queueing fails."""
    from app.api.v1.endpoints.tenants import (
        VERIFICATION_EMAIL_QUEUE_MAX_ATTEMPTS
    )
    from app.models.tenant import Tenant as TenantModel
    from app.models.user import User as UserModel

    attempts = {"count": 0}

    def always_fail_delay(**kwargs):
        attempts["count"] += 1
        raise RuntimeError("Broker unavailable")

    monkeypatch.setattr(
        "app.api.v1.endpoints.tenants.send_verification_email_task.delay",
        always_fail_delay
    )

    response = client.post(
        "/api/v1/tenants/register",
        json={
            "name": "Queue Failure Company",
            "domain": "queue-failure.com",
            "plan_type": "free",
            "owner": {
                "full_name": "Failure Owner",
                "email": "failure-owner@test.com",
                "password": "SecurePass123@"
            }
        }
    )

    assert response.status_code == 503
    assert "verification email could not be queued" in response.json()[
        "message"
    ].lower()
    assert attempts["count"] == VERIFICATION_EMAIL_QUEUE_MAX_ATTEMPTS
    assert db_session.query(TenantModel).filter(
        TenantModel.domain == "queue-failure.com"
    ).first() is None
    assert db_session.query(UserModel).filter(
        UserModel.email == "failure-owner@test.com"
    ).first() is None


def test_register_tenant_generates_verification_token(client, db_session):
    """Test that registering a tenant generates a verification token for the owner."""
    from app.models.user import User as UserModel

    response = client.post(
        "/api/v1/tenants/register",
        json={
            "name": "Test Verification Company",
            "domain": "testverify.com",
            "plan_type": "free",
            "owner": {
                "full_name": "Test Owner",
                "email": "owner@testverify.com",
                "password": "SecurePass123@"
            }
        }
    )

    assert response.status_code == 201
    data = response.json()

    # Check that owner is not verified by default
    assert data["owner"]["is_verified"] is False

    # Check that verification token was generated in database
    user = db_session.query(UserModel).filter(
        UserModel.email == "owner@testverify.com"
    ).first()
    assert user is not None
    assert user.verification_token is not None
    assert len(user.verification_token) > 0
    assert user.is_verified is False


def test_verify_email_with_valid_token(client, db_session):
    """Test email verification with a valid token."""
    from app.models.user import User as UserModel

    # Register a tenant to get a user with verification token
    register_response = client.post(
        "/api/v1/tenants/register",
        json={
            "name": "Verify Test Company",
            "domain": "verifytest.com",
            "plan_type": "free",
            "owner": {
                "full_name": "Verify Test Owner",
                "email": "verify@test.com",
                "password": "SecurePass123@"
            }
        }
    )
    assert register_response.status_code == 201

    # Get the verification token from database
    user = db_session.query(UserModel).filter(
        UserModel.email == "verify@test.com"
    ).first()
    token = user.verification_token

    # Verify email with the token
    verify_response = client.post(
        f"/api/v1/auth/verify-email?token={token}"
    )

    assert verify_response.status_code == 200
    data = verify_response.json()
    # After verification, tokens are returned
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    assert "expires_in" in data

    # Check database to ensure user is verified
    db_session.refresh(user)
    assert user.is_verified is True
    assert user.verification_token is None


def test_verify_email_with_invalid_token(client):
    """Test email verification with an invalid token."""
    response = client.post(
        "/api/v1/auth/verify-email?token=invalid-token-12345"
    )

    assert response.status_code == 400
    data = response.json()
    assert "Invalid or expired" in data["message"]


def test_verify_email_already_verified(client, db_session):
    """Test that verifying an already verified email returns an error."""
    from app.models.user import User as UserModel

    # Register a tenant
    register_response = client.post(
        "/api/v1/tenants/register",
        json={
            "name": "Already Verified Company",
            "domain": "alreadyverified.com",
            "plan_type": "free",
            "owner": {
                "full_name": "Already Verified Owner",
                "email": "alreadyverified@test.com",
                "password": "SecurePass123@"
            }
        }
    )
    assert register_response.status_code == 201

    # Get the verification token
    user = db_session.query(UserModel).filter(
        UserModel.email == "alreadyverified@test.com"
    ).first()
    token = user.verification_token

    # Verify email once
    first_verify = client.post(
        f"/api/v1/auth/verify-email?token={token}"
    )
    assert first_verify.status_code == 200

    # Try to verify again with the same token (should fail)
    second_verify = client.post(
        f"/api/v1/auth/verify-email?token={token}"
    )
    assert second_verify.status_code == 400
    data = second_verify.json()
    assert "Invalid or expired" in data["message"]


def test_verification_token_is_unique(client, db_session):
    """Test that each user gets a unique verification token."""
    from app.models.user import User as UserModel

    # Register first tenant
    client.post(
        "/api/v1/tenants/register",
        json={
            "name": "Company 1",
            "domain": "company1.com",
            "plan_type": "free",
            "owner": {
                "full_name": "Owner 1",
                "email": "owner1@company1.com",
                "password": "SecurePass123@"
            }
        }
    )

    # Register second tenant
    client.post(
        "/api/v1/tenants/register",
        json={
            "name": "Company 2",
            "domain": "company2.com",
            "plan_type": "free",
            "owner": {
                "full_name": "Owner 2",
                "email": "owner2@company2.com",
                "password": "SecurePass123@"
            }
        }
    )

    # Get both users
    user1 = db_session.query(UserModel).filter(
        UserModel.email == "owner1@company1.com"
    ).first()
    user2 = db_session.query(UserModel).filter(
        UserModel.email == "owner2@company2.com"
    ).first()

    # Tokens should be unique
    assert user1.verification_token != user2.verification_token


def test_owner_can_login_before_verification(client):
    """Test that login works before verification but protected routes stay blocked."""
    # Register tenant
    register_response = client.post(
        "/api/v1/tenants/register",
        json={
            "name": "Login Before Verify Company",
            "domain": "loginbeforeverify.com",
            "plan_type": "free",
            "owner": {
                "full_name": "Login Test Owner",
                "email": "loginbeforeverify@test.com",
                "password": "SecurePass123@"
            }
        }
    )
    assert register_response.status_code == 201

    # Try to login before verification
    login_response = client.post(
        "/api/v1/auth/login",
        data={
            "username": "loginbeforeverify@test.com",
            "password": "SecurePass123@"
        }
    )

    # Login is allowed so the user can complete onboarding, but protected
    # routes remain blocked until the email is verified.
    assert login_response.status_code == 200
    data = login_response.json()
    assert "access_token" in data
    assert "refresh_token" in data

    me_response = client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {data['access_token']}"}
    )
    assert me_response.status_code == 403
    assert "email verification required" in me_response.json()["message"].lower()


def test_token_has_expiration(client, db_session):
    """Test that verification tokens have an expiration date."""
    from app.models.user import User as UserModel

    # Register a tenant
    response = client.post(
        "/api/v1/tenants/register",
        json={
            "name": "Token Expiry Test Company",
            "domain": "tokenexpiry.com",
            "plan_type": "free",
            "owner": {
                "full_name": "Token Expiry Owner",
                "email": "tokenexpiry@test.com",
                "password": "SecurePass123@"
            }
        }
    )
    assert response.status_code == 201

    # Get user and check token expiration
    user = db_session.query(UserModel).filter(
        UserModel.email == "tokenexpiry@test.com"
    ).first()
    assert user.verification_token_expires_at is not None
    # Token should expire in the future (within 25 hours)
    assert user.verification_token_expires_at > datetime.now(timezone.utc)
    assert user.verification_token_expires_at < datetime.now(timezone.utc) + timedelta(hours=25)


def test_verify_email_with_expired_token(client, db_session):
    """Test that expired tokens are rejected."""
    from app.models.user import User as UserModel

    # Register a tenant
    response = client.post(
        "/api/v1/tenants/register",
        json={
            "name": "Expired Token Company",
            "domain": "expiredtoken.com",
            "plan_type": "free",
            "owner": {
                "full_name": "Expired Token Owner",
                "email": "expiredtoken@test.com",
                "password": "SecurePass123@"
            }
        }
    )
    assert response.status_code == 201

    # Get user and manually expire the token
    user = db_session.query(UserModel).filter(
        UserModel.email == "expiredtoken@test.com"
    ).first()
    token = user.verification_token

    # Set token expiration to the past
    user.verification_token_expires_at = datetime.now(timezone.utc) - timedelta(hours=1)
    db_session.commit()

    # Try to verify with expired token
    verify_response = client.post(
        f"/api/v1/auth/verify-email?token={token}"
    )

    assert verify_response.status_code == 400
    data = verify_response.json()
    assert "expired" in data["message"].lower()


def test_resend_verification_email(client, db_session):
    """Test resending verification email generates new token."""
    from app.models.user import User as UserModel

    # Register a tenant
    response = client.post(
        "/api/v1/tenants/register",
        json={
            "name": "Resend Test Company",
            "domain": "resendtest.com",
            "plan_type": "free",
            "owner": {
                "full_name": "Resend Test Owner",
                "email": "resend@test.com",
                "password": "SecurePass123@"
            }
        }
    )
    assert response.status_code == 201

    # Get original token
    user = db_session.query(UserModel).filter(
        UserModel.email == "resend@test.com"
    ).first()
    original_token = user.verification_token

    # Resend verification email
    resend_response = client.post(
        "/api/v1/auth/resend-verification-email",
        json={"email": "resend@test.com"}
    )

    assert resend_response.status_code == 200
    data = resend_response.json()
    assert "resent" in data["message"].lower()

    # Check that token was updated
    db_session.refresh(user)
    assert user.verification_token != original_token
    assert user.verification_token is not None


def test_resend_for_verified_user_fails(client, db_session):
    """Test that resending verification email for verified user fails."""
    from app.models.user import User as UserModel

    # Register and verify a tenant
    response = client.post(
        "/api/v1/tenants/register",
        json={
            "name": "Already Verified Resend Company",
            "domain": "alreadyverifiedresend.com",
            "plan_type": "free",
            "owner": {
                "full_name": "Already Verified Owner",
                "email": "alreadyverifiedresend@test.com",
                "password": "SecurePass123@"
            }
        }
    )
    assert response.status_code == 201

    # Get token and verify
    user = db_session.query(UserModel).filter(
        UserModel.email == "alreadyverifiedresend@test.com"
    ).first()
    token = user.verification_token

    # Verify email
    verify_response = client.post(
        f"/api/v1/auth/verify-email?token={token}"
    )
    assert verify_response.status_code == 200

    # Try to resend verification email
    resend_response = client.post(
        "/api/v1/auth/resend-verification-email",
        json={"email": "alreadyverifiedresend@test.com"}
    )

    assert resend_response.status_code == 400
    data = resend_response.json()
    assert "already verified" in data["message"].lower()


def test_resend_for_nonexistent_email(client):
    """Test that resending for non-existent email doesn't reveal user existence."""
    # Try to resend for non-existent email
    resend_response = client.post(
        "/api/v1/auth/resend-verification-email",
        json={"email": "nonexistent@test.com"}
    )

    # Should succeed (don't reveal if email exists)
    assert resend_response.status_code == 200
    data = resend_response.json()
    assert "If the email exists" in data["message"]
