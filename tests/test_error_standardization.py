"""
Test suite for standardized error response format.

Verifies that all API errors follow consistent format with proper codes.
"""
from fastapi import status


def test_validation_error_format(client):
    """Test that validation errors return standardized format."""
    # Use forgot-password with an invalid email format to trigger a
    # Pydantic validation error without requiring authentication.
    response = client.post(
        "/api/v1/auth/forgot-password",
        json={
            "email": "not-an-email",  # Invalid email
        }
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    data = response.json()

    # Check standardized format
    assert "error" in data
    assert "message" in data
    assert "code" in data
    assert data["code"] == "VALIDATION_ERROR"
    assert data["error"] == "ValidationError"

    # Check details are present
    assert "details" in data
    assert isinstance(data["details"], list)
    assert len(data["details"]) > 0

    # Check detail structure
    detail = data["details"][0]
    assert "field" in detail or "message" in detail


def test_not_found_error_format(client, auth_headers):
    """Test that 404 errors return standardized format."""
    # Try to get non-existent invoice
    response = client.get(
        "/api/v1/invoices/99999999-9999-9999-9999-999999999999",
        headers=auth_headers
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()

    # Check standardized format
    assert "error" in data
    assert "message" in data
    assert "code" in data
    assert data["code"] == "NOT_FOUND"
    assert "request_id" in data  # Should include request ID for tracking


def test_authentication_error_format(client):
    """Test that authentication errors return standardized format."""
    # Try to access protected endpoint without token
    response = client.get("/api/v1/users/me")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    data = response.json()

    # Check standardized format
    assert "error" in data
    assert "message" in data
    assert "code" in data
    assert data["code"] == "UNAUTHORIZED"


def test_forbidden_error_format(client, test_user, db_session):
    """Test that permission errors return standardized format."""
    # Login as regular user
    from app.core.security import create_access_token
    token = create_access_token(
        data={
            "sub": test_user.id,
            "tenant_id": test_user.tenant_id,
            "role": test_user.role.value
        }
    )
    headers = {"Authorization": f"Bearer {token}"}

    # Try to access admin-only endpoint
    response = client.get("/api/v1/admin/tenants", headers=headers)

    assert response.status_code == status.HTTP_403_FORBIDDEN
    data = response.json()

    # Check standardized format
    assert "error" in data
    assert "message" in data
    assert "code" in data
    assert data["code"] == "FORBIDDEN"


def test_duplicate_entry_error_format(client, auth_headers, test_tenant):
    """Test that duplicate entry errors return standardized format."""
    # Create a user via the owner-user endpoint
    response1 = client.post(
        "/api/v1/users/",
        headers=auth_headers,
        json={
            "email": "duplicate@testcompany.com",
            "full_name": "First User",
            "password": "TestPass123!",
            "role": "manager",
        }
    )
    assert response1.status_code == status.HTTP_201_CREATED

    # Try to create the same user again (same email in same tenant)
    response2 = client.post(
        "/api/v1/users/",
        headers=auth_headers,
        json={
            "email": "duplicate@testcompany.com",
            "full_name": "Second User",
            "password": "TestPass123!",
            "role": "attendant",
        }
    )

    # Should return error with standard format
    assert response2.status_code in [
        status.HTTP_400_BAD_REQUEST,
        status.HTTP_409_CONFLICT
    ]
    data = response2.json()

    # Check standardized format
    assert "error" in data
    assert "message" in data
    assert "code" in data
    assert "request_id" in data


def test_error_response_no_password_leak(client, test_tenant):
    """Test that error responses don't leak sensitive information."""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "test@example.com",
            "full_name": "Test User",
            "password": "TestPass123!",
            "role": "manager",
            "tenant_id": test_tenant.id
        }
    )

    # Check that response doesn't contain password
    data = response.json()
    assert "password" not in str(data).lower() or "hashed" in str(data).lower()


def test_error_codes_are_machine_readable(client):
    """Test that error codes are consistent and machine-readable."""
    # Test validation error code
    response = client.post(
        "/api/v1/auth/register",
        json={"email": "invalid"}  # Missing required fields
    )

    data = response.json()
    assert "code" in data
    assert isinstance(data["code"], str)
    assert data["code"].isupper()  # Code should be uppercase
    # Should be snake_case or single word
    assert "_" in data["code"] or data["code"].isalpha()


def test_error_message_is_human_readable(client, test_tenant):
    """Test that error messages are human-readable."""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "test@example.com",
            "full_name": "Test User",
            "password": "short",  # Too short
            "role": "manager",
            "tenant_id": test_tenant.id
        }
    )

    data = response.json()
    assert "message" in data
    assert isinstance(data["message"], str)
    assert len(data["message"]) > 0
    # Message should not contain technical jargon like stack traces
    assert "Traceback" not in data["message"]
    assert "Exception" not in data["message"]


def test_request_id_present_in_errors(client):
    """Test that all errors include a request_id for tracking."""
    # Trigger an error
    response = client.get("/api/v1/users/me")

    data = response.json()
    assert "request_id" in data
    assert isinstance(data["request_id"], str)
    assert len(data["request_id"]) > 0


def test_error_details_optional(client, auth_headers):
    """Test that details field is optional and only present when needed."""
    # Simple error without details
    response = client.get(
        "/api/v1/invoices/invalid-id",
        headers=auth_headers
    )

    data = response.json()
    # Details may or may not be present, but if present should be a list
    if "details" in data:
        assert isinstance(data["details"], list)


def test_consistent_error_structure_across_endpoints(client, test_tenant):
    """Test that error structure is consistent across different endpoints."""
    errors = []

    # Collect errors from different endpoints
    # 1. Auth endpoint error
    response1 = client.post(
        "/api/v1/auth/register",
        json={"email": "invalid"}
    )
    errors.append(response1.json())

    # 2. Protected endpoint without auth
    response2 = client.get("/api/v1/users/me")
    errors.append(response2.json())

    # All errors should have same structure
    required_fields = ["error", "message", "code"]
    for error in errors:
        for field in required_fields:
            assert field in error, f"Missing {field} in error response"
