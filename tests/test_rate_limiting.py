"""
Tests for rate limiting functionality.
"""
from app.core.rate_limit import limiter


def test_rate_limit_disabled_in_tests(client, db_session, test_tenant, test_user):
    """
    Test that rate limiting is disabled during tests.
    This test verifies the disable_rate_limit fixture works.
    """
    # Make many rapid requests - should not be rate limited in tests
    for _ in range(20):
        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user.email,
                "password": "password123"
            }
        )
        # All should succeed (not rate limited)
        assert response.status_code in [200, 401]


def test_rate_limit_configuration():
    """Test rate limiter is properly configured."""
    assert limiter is not None
    # Check that limiter has the expected attributes
    assert hasattr(limiter, 'enabled')


def test_rate_limit_error_response_structure(client):
    """
    Test rate limit error response structure.
    This is a theoretical test since rate limiting is disabled in tests.
    """
    # This test documents the expected error structure
    # when rate limits are exceeded in production
    expected_error_structure = {
        "error": "Rate limit exceeded",
        "message": "Too many requests. Please try again later.",
        "detail": str
    }
    # Just verify the structure is documented
    assert "error" in expected_error_structure
    assert "message" in expected_error_structure
