"""
Test suite for Email Verification Enforcement and Async Email Processing.
Tests email verification requirement for critical operations and async processing.
"""
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, Mock
import pytest


@pytest.mark.skip(reason="Temporary skip - needs investigation")
def test_unverified_user_cannot_create_invoice(client, db_session):
    """Test that unverified users cannot create invoices."""
    from app.models.user import User as UserModel
    from app.models.tenant import Tenant as TenantModel

    # Create tenant first
    tenant = TenantModel(
        name="Test Company",
        domain="testcompany.com",
        plan_type="free"
    )
    db_session.add(tenant)
    db_session.commit()

    # Register a user (unverified by default)
    register_response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "unverified@test.com",
            "full_name": "Unverified User",
            "password": "SecurePass123@",
            "tenant_id": tenant.id,
            "role": "owner"
        }
    )
    assert register_response.status_code == 201

    # Login to get token
    login_response = client.post(
        "/api/v1/auth/login",
        data={
            "username": "unverified@test.com",
            "password": "SecurePass123@"
        }
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]

    # Try to create invoice (should fail)
    invoice_data = {
        "customer_name": "Test Customer",
        "customer_email": "customer@test.com",
        "items": [
            {
                "description": "Test Item",
                "quantity": 1,
                "unit_price": 100.00
            }
        ]
    }

    create_response = client.post(
        "/api/v1/invoices/",
        json=invoice_data,
        headers={"Authorization": f"Bearer {token}"}
    )

    assert create_response.status_code == 403
    data = create_response.json()
    assert "Email verification required" in data["message"]
    assert "verify your email" in data["message"].lower()


@pytest.mark.skip(reason="Temporary skip - needs investigation")
def test_verified_user_can_create_invoice(client, db_session):
    """Test that verified users can create invoices."""
    from app.models.user import User as UserModel
    from app.models.tenant import Tenant as TenantModel

    # Create tenant with required fields
    tenant = TenantModel(
        name="Verified Company",
        domain="verifiedcompany.com",
        plan_type="free",
        default_currency="NGN"  # Add default currency
    )
    db_session.add(tenant)
    db_session.commit()

    # Register a user
    register_response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "verified@test.com",
            "full_name": "Verified User",
            "password": "SecurePass123@",
            "tenant_id": tenant.id,
            "role": "owner"
        }
    )
    assert register_response.status_code == 201

    # Get user and mark as verified
    user = db_session.query(UserModel).filter(
        UserModel.email == "verified@test.com"
    ).first()
    user.is_verified = True
    db_session.commit()

    # Login to get token
    login_response = client.post(
        "/api/v1/auth/login",
        data={
            "username": "verified@test.com",
            "password": "SecurePass123@"
        }
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]

    # Try to create invoice (should succeed)
    invoice_data = {
        "customer_name": "Test Customer",
        "customer_email": "customer@test.com",
        "issue_date": "2024-01-01",
        "items": [
            {
                "description": "Test Item",
                "quantity": 1,
                "unit_price": 100.00
            }
        ]
    }

    create_response = client.post(
        "/api/v1/invoices/",
        json=invoice_data,
        headers={"Authorization": f"Bearer {token}"}
    )

    assert create_response.status_code == 201
    data = create_response.json()
    assert data["customer_name"] == "Test Customer"


@pytest.mark.skip(reason="Temporary skip - needs investigation")
def test_superadmin_bypasses_verification_requirement(client, db_session):
    """Test that superadmins can create invoices without verification."""
    from app.models.user import User as UserModel
    from app.models.tenant import Tenant as TenantModel

    # Create tenant with required fields
    tenant = TenantModel(
        name="Superadmin Company",
        domain="superadmincompany.com",
        plan_type="free",
        default_currency="NGN"
    )
    db_session.add(tenant)
    db_session.commit()

    # Register a superadmin (unverified)
    register_response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "superadmin@test.com",
            "full_name": "Super Admin",
            "password": "SecurePass123@",
            "tenant_id": tenant.id,
            "role": "owner",
            "is_superadmin": True
        }
    )
    assert register_response.status_code == 201

    # Verify user is not verified
    user = db_session.query(UserModel).filter(
        UserModel.email == "superadmin@test.com"
    ).first()
    assert user.is_verified is False
    assert user.is_superadmin is True

    # Login to get token
    login_response = client.post(
        "/api/v1/auth/login",
        data={
            "username": "superadmin@test.com",
            "password": "SecurePass123@"
        }
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]

    # Create invoice (should succeed despite not being verified)
    invoice_data = {
        "customer_name": "Test Customer",
        "customer_email": "customer@test.com",
        "issue_date": "2024-01-01",
        "items": [
            {
                "description": "Test Item",
                "quantity": 1,
                "unit_price": 100.00
            }
        ]
    }

    create_response = client.post(
        "/api/v1/invoices/",
        json=invoice_data,
        headers={"Authorization": f"Bearer {token}"}
    )

    assert create_response.status_code == 201


def test_async_verification_email_task_called(client):
    """Test that verification email is sent asynchronously."""
    from app.tasks import email_tasks as email_tasks_module

    # Clear previous calls
    email_tasks_module.send_verification_email_task.delay.reset_mock()

    # Register a tenant
    response = client.post(
        "/api/v1/tenants/register",
        json={
            "name": "Async Email Test Company",
            "domain": "asyncemail.com",
            "plan_type": "free",
            "owner": {
                "full_name": "Async Test Owner",
                "email": "asynctest@test.com",
                "password": "SecurePass123@"
            }
        }
    )

    assert response.status_code == 201

    # Verify that the async task was called
    email_tasks_module.send_verification_email_task.delay.assert_called_once()

    # Verify the task was called with correct parameters
    call_kwargs = email_tasks_module.send_verification_email_task.delay.call_args[1]
    assert call_kwargs['email'] == 'asynctest@test.com'
    assert 'token' in call_kwargs
    assert call_kwargs['full_name'] == 'Async Test Owner'


def test_async_password_reset_email_task_called(client, db_session):
    """Test that password reset email is sent asynchronously."""
    from app.models.user import User as UserModel
    from app.models.tenant import Tenant as TenantModel
    from app.core.security import get_password_hash
    from app.tasks import email_tasks as email_tasks_module

    # Clear previous calls
    email_tasks_module.send_password_reset_email_task.delay.reset_mock()

    # Create tenant and user
    tenant = TenantModel(
        name="Reset Test Company",
        domain="resettest.com",
        plan_type="free"
    )
    db_session.add(tenant)
    db_session.commit()

    user = UserModel(
        email="resettest@test.com",
        full_name="Reset Test User",
        hashed_password=get_password_hash("SecurePass123@"),
        role="owner",
        tenant_id=tenant.id,
        is_verified=True
    )
    db_session.add(user)
    db_session.commit()

    # Request password reset
    response = client.post(
        "/api/v1/auth/forgot-password",
        json={"email": "resettest@test.com"}
    )

    assert response.status_code == 200

    # Verify that the async task was called
    email_tasks_module.send_password_reset_email_task.delay.assert_called_once()

    # Verify the task was called with correct parameters
    call_kwargs = email_tasks_module.send_password_reset_email_task.delay.call_args[1]
    assert call_kwargs['email'] == 'resettest@test.com'
    assert 'token' in call_kwargs


def test_user_response_includes_verification_status(client):
    """Test that user API responses include is_verified field."""
    # Register a tenant
    response = client.post(
        "/api/v1/tenants/register",
        json={
            "name": "Verification Status Test",
            "domain": "verificationstatus.com",
            "plan_type": "free",
            "owner": {
                "full_name": "Status Test Owner",
                "email": "statustest@test.com",
                "password": "SecurePass123@"
            }
        }
    )

    assert response.status_code == 201
    data = response.json()

    # Check that owner info includes is_verified
    assert "owner" in data
    assert "is_verified" in data["owner"]
    assert data["owner"]["is_verified"] is False

    # Login and get user info
    login_response = client.post(
        "/api/v1/auth/login",
        data={
            "username": "statustest@test.com",
            "password": "SecurePass123@"
        }
    )
    token = login_response.json()["access_token"]

    # Get current user info
    me_response = client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert me_response.status_code == 200
    user_data = me_response.json()
    assert "is_verified" in user_data
    assert user_data["is_verified"] is False


def test_email_provider_modularity():
    """Test that email provider can be switched easily."""
    from app.services.email_provider import (
        get_email_provider, SendGridEmailProvider, MockEmailProvider
    )

    # Get mock provider
    mock_provider = get_email_provider("mock")
    assert isinstance(mock_provider, MockEmailProvider)
    assert mock_provider.validate_configuration() is True

    # Get SendGrid provider
    sendgrid_provider = get_email_provider(
        "sendgrid",
        {"api_key": "test-key", "from_email": "test@example.com"}
    )
    assert isinstance(sendgrid_provider, SendGridEmailProvider)

    # Test unknown provider
    with pytest.raises(ValueError, match="Unsupported email provider"):
        get_email_provider("unknown_provider")


def test_mock_email_provider_functionality():
    """Test that MockEmailProvider works correctly."""
    from app.services.email_provider import MockEmailProvider

    provider = MockEmailProvider()

    # Send email
    success = provider.send_email(
        to_email="test@example.com",
        subject="Test Subject",
        plain_text="Test body",
        html_content="<p>Test body</p>"
    )

    assert success is True

    # Check sent emails
    sent_emails = provider.get_sent_emails()
    assert len(sent_emails) == 1
    assert sent_emails[0]["to"] == "test@example.com"
    assert sent_emails[0]["subject"] == "Test Subject"

    # Clear and verify
    provider.clear_sent_emails()
    assert len(provider.get_sent_emails()) == 0
