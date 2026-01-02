"""
Rate limiting configuration using SlowAPI.
Implements tiered rate limiting based on user roles and operation types.
"""
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.core.cache import get_redis_client


def get_user_identifier(request: Request) -> str:
    """
    Get identifier for rate limiting.
    Uses user ID if authenticated, otherwise IP address.
    Returns None for exempt users/IPs.
    """
    # Check if IP is exempt
    client_ip = get_remote_address(request)
    if is_ip_exempt(client_ip):
        return None

    # Try to get user from request state (set by auth dependency)
    user = getattr(request.state, "user", None)
    if user:
        # Exempt superadmin users from rate limiting
        if getattr(user, "is_superadmin", False):
            return None
        return f"user:{user.id}"

    # Fall back to IP address
    return client_ip


def is_ip_exempt(ip: str) -> bool:
    """Check if an IP address is exempt from rate limiting."""
    if not settings.RATE_LIMIT_EXEMPT_IPS:
        return False

    exempt_ips = [
        ip.strip()
        for ip in settings.RATE_LIMIT_EXEMPT_IPS.split(",")
        if ip.strip()
    ]
    return ip in exempt_ips


def get_role_based_limit(request: Request) -> str:
    """
    Get rate limit based on user role.
    Returns higher limits for higher roles.
    """
    user = getattr(request.state, "user", None)

    if not user:
        return settings.RATE_LIMIT_UNAUTHENTICATED

    # Superadmin gets unlimited (handled by get_user_identifier returning None)
    if getattr(user, "is_superadmin", False):
        return "1000000/minute"  # Effectively unlimited

    # Import UserRole locally to avoid circular import
    # (models imports core.security)
    from app.models.user import UserRole

    role = getattr(user, "role", None)

    if role == UserRole.OWNER:
        return settings.RATE_LIMIT_OWNER
    elif role == UserRole.ADMIN:
        return settings.RATE_LIMIT_ADMIN
    elif role == UserRole.MANAGER:
        return settings.RATE_LIMIT_MANAGER
    elif role == UserRole.ATTENDANT:
        return settings.RATE_LIMIT_ATTENDANT

    # Default to authenticated user limit
    return settings.RATE_LIMIT_ATTENDANT


def get_read_limit(request: Request) -> str:
    """
    Get rate limit for read operations (GET requests).
    Applies a multiplier to base role limit.
    """
    base_limit = get_role_based_limit(request)
    return apply_multiplier(base_limit, settings.RATE_LIMIT_READ_MULTIPLIER)


def get_write_limit(request: Request) -> str:
    """
    Get rate limit for write operations (POST, PUT, PATCH, DELETE).
    Applies a multiplier to base role limit.
    """
    base_limit = get_role_based_limit(request)
    return apply_multiplier(base_limit, settings.RATE_LIMIT_WRITE_MULTIPLIER)


def apply_multiplier(limit_str: str, multiplier: float) -> str:
    """
    Apply a multiplier to a rate limit string.
    Example: "100/minute" with 2.0 multiplier -> "200/minute"
    """
    try:
        parts = limit_str.split("/")
        if len(parts) != 2:
            return limit_str

        count = int(parts[0])
        period = parts[1]
        new_count = int(count * multiplier)

        return f"{new_count}/{period}"
    except (ValueError, IndexError):
        return limit_str


# Initialize rate limiter
# Use Redis if available, otherwise in-memory storage
redis_client = get_redis_client()

if redis_client:
    # Use Redis for distributed rate limiting
    # from slowapi.extension import Limiter as RedisLimiter

    limiter = Limiter(
        key_func=get_user_identifier,
        storage_uri=settings.REDIS_URL,
        strategy="fixed-window"
    )
else:
    # Fall back to in-memory storage
    limiter = Limiter(
        key_func=get_user_identifier,
        default_limits=["100/minute"]
    )


def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    """
    Custom handler for rate limit exceeded errors.
    Adds rate limit headers to response.
    """
    import re

    # Extract retry-after value using regex for robustness
    retry_after = settings.RATE_LIMIT_RETRY_AFTER_FALLBACK

    # Try to extract from detail message
    # Common formats: "Retry in 30 seconds", "30 seconds", etc.
    if hasattr(exc, 'detail') and exc.detail:
        detail_str = str(exc.detail)
        # Look for numbers followed by optional time unit
        match = re.search(r'(\d+)\s*(?:second|minute|hour)?s?', detail_str)
        if match:
            retry_after = match.group(1)

    # Get current limit info for headers
    limit_str = get_role_based_limit(request)

    # Parse limit for headers
    try:
        limit_parts = limit_str.split("/")
        limit_value = limit_parts[0] if len(limit_parts) > 0 else "100"
    except (ValueError, IndexError, AttributeError):
        limit_value = "100"

    detail_msg = "Rate limit exceeded"
    if hasattr(exc, 'detail'):
        detail_msg = str(exc.detail)

    return JSONResponse(
        status_code=429,
        content={
            "error": "Rate limit exceeded",
            "message": "Too many requests. Please try again later.",
            "detail": detail_msg
        },
        headers={
            "Retry-After": str(retry_after),
            "X-RateLimit-Limit": limit_value,
            "X-RateLimit-Remaining": "0",
            "X-RateLimit-Reset": str(retry_after)
        }
    )
