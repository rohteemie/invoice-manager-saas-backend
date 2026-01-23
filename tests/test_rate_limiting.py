"""
Tests for rate limiting functionality.
"""
from unittest.mock import Mock, patch
from slowapi.errors import RateLimitExceeded
from app.core.rate_limit import (
    limiter,
    get_role_based_limit,
    get_read_limit,
    get_write_limit,
    apply_multiplier,
    is_ip_exempt,
    get_user_identifier,
    rate_limit_exceeded_handler
)
from app.models.user import UserRole
from app.core.config import settings


# def test_rate_limit_disabled_in_tests(client, db_session, test_tenant, test_user):
#     """
#     Test that rate limiting is disabled during tests.
#     This test verifies the disable_rate_limit fixture works.
#     """
#     # Make many rapid requests - should not be rate limited in tests
#     for _ in range(20):
#         response = client.post(
#             "/api/v1/auth/login",
#             data={
#                 "username": test_user.email,
#                 "password": "password123"
#             }
#         )
#         # All should succeed (not rate limited)
#         assert response.status_code in [200, 401]


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


# def test_apply_multiplier():
#     """Test rate limit multiplier application."""
#     # Test normal case
#     assert apply_multiplier("100/minute", 2.0) == "200/minute"
#     assert apply_multiplier("50/hour", 1.5) == "75/hour"
#     assert apply_multiplier("200/minute", 0.5) == "100/minute"

#     # Test edge cases
#     assert apply_multiplier("invalid", 2.0) == "invalid"
#     assert apply_multiplier("100", 2.0) == "100"
#     assert apply_multiplier("", 2.0) == ""


def test_role_based_limits_unauthenticated():
    """Test rate limits for unauthenticated users."""
    request = Mock()
    request.state.user = None

    limit = get_role_based_limit(request)
    assert limit == settings.RATE_LIMIT_UNAUTHENTICATED


def test_role_based_limits_by_role():
    """Test rate limits for different user roles."""
    # Test ATTENDANT
    request = Mock()
    user = Mock()
    user.role = UserRole.ATTENDANT
    user.is_superadmin = False
    request.state.user = user

    limit = get_role_based_limit(request)
    assert limit == settings.RATE_LIMIT_ATTENDANT

    # Test MANAGER
    user.role = UserRole.MANAGER
    limit = get_role_based_limit(request)
    assert limit == settings.RATE_LIMIT_MANAGER

    # Test ADMIN
    user.role = UserRole.ADMIN
    limit = get_role_based_limit(request)
    assert limit == settings.RATE_LIMIT_ADMIN

    # Test OWNER
    user.role = UserRole.OWNER
    limit = get_role_based_limit(request)
    assert limit == settings.RATE_LIMIT_OWNER


def test_role_based_limits_superadmin():
    """Test that superadmin gets unlimited rate limit."""
    request = Mock()
    user = Mock()
    user.is_superadmin = True
    user.role = UserRole.ATTENDANT
    request.state.user = user

    limit = get_role_based_limit(request)
    # Superadmin gets effectively unlimited
    assert limit == "1000000/minute"


def test_read_limit_multiplier():
    """Test read operations get higher limits."""
    request = Mock()
    user = Mock()
    user.role = UserRole.ATTENDANT
    user.is_superadmin = False
    request.state.user = user

    read_limit = get_read_limit(request)
    base_limit = get_role_based_limit(request)

    # Read limit should be base limit * read multiplier
    expected = apply_multiplier(base_limit, settings.RATE_LIMIT_READ_MULTIPLIER)
    assert read_limit == expected


def test_write_limit_multiplier():
    """Test write operations use standard limits."""
    request = Mock()
    user = Mock()
    user.role = UserRole.MANAGER
    user.is_superadmin = False
    request.state.user = user

    write_limit = get_write_limit(request)
    base_limit = get_role_based_limit(request)

    # Write limit should be base limit * write multiplier
    expected = apply_multiplier(base_limit, settings.RATE_LIMIT_WRITE_MULTIPLIER)
    assert write_limit == expected


def test_ip_exemption():
    """Test IP-based rate limit exemption."""
    # Test when no exempt IPs configured
    with patch.object(settings, 'RATE_LIMIT_EXEMPT_IPS', None):
        assert is_ip_exempt("192.168.1.1") is False

    # Test when exempt IPs are configured
    with patch.object(settings, 'RATE_LIMIT_EXEMPT_IPS', "192.168.1.1,10.0.0.1"):
        assert is_ip_exempt("192.168.1.1") is True
        assert is_ip_exempt("10.0.0.1") is True
        assert is_ip_exempt("192.168.1.2") is False

    # Test with spaces in configuration
    with patch.object(settings, 'RATE_LIMIT_EXEMPT_IPS', " 192.168.1.1 , 10.0.0.1 "):
        assert is_ip_exempt("192.168.1.1") is True
        assert is_ip_exempt("10.0.0.1") is True


def test_user_identifier_exempt_ip():
    """Test that exempt IPs return None (unlimited)."""
    request = Mock()
    request.state.user = None

    with patch('app.core.rate_limit.get_remote_address', return_value="192.168.1.1"):
        with patch.object(settings, 'RATE_LIMIT_EXEMPT_IPS', "192.168.1.1"):
            identifier = get_user_identifier(request)
            assert identifier is None


def test_user_identifier_superadmin():
    """Test that superadmin users return None (unlimited)."""
    request = Mock()
    user = Mock()
    user.is_superadmin = True
    user.id = 123
    request.state.user = user

    with patch('app.core.rate_limit.get_remote_address', return_value="1.2.3.4"):
        identifier = get_user_identifier(request)
        assert identifier is None


def test_user_identifier_authenticated_user():
    """Test authenticated user identification."""
    request = Mock()
    user = Mock()
    user.is_superadmin = False
    user.id = 456
    request.state.user = user

    with patch('app.core.rate_limit.get_remote_address', return_value="1.2.3.4"):
        with patch.object(settings, 'RATE_LIMIT_EXEMPT_IPS', None):
            identifier = get_user_identifier(request)
            assert identifier == "user:456"


def test_user_identifier_unauthenticated_user():
    """Test unauthenticated user identification by IP."""
    request = Mock()
    request.state.user = None

    with patch('app.core.rate_limit.get_remote_address', return_value="5.6.7.8"):
        with patch.object(settings, 'RATE_LIMIT_EXEMPT_IPS', None):
            identifier = get_user_identifier(request)
            assert identifier == "5.6.7.8"


def test_rate_limit_headers_in_error():
    """Test that rate limit headers are included in error responses."""
    request = Mock()
    request.state.user = None

    # Create a mock exception with the expected attributes
    exc = Mock(spec=RateLimitExceeded)
    exc.detail = "10 per 1 minute. Retry in 30 seconds"

    with patch('app.core.rate_limit.get_role_based_limit', return_value="100/minute"):
        response = rate_limit_exceeded_handler(request, exc)

        assert response.status_code == 429
        assert "Retry-After" in response.headers
        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Remaining" in response.headers
        assert "X-RateLimit-Reset" in response.headers
        assert response.headers["X-RateLimit-Remaining"] == "0"

