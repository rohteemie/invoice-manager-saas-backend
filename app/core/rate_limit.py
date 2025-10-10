"""
Rate limiting configuration using SlowAPI.
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
    """
    # Try to get user from request state (set by auth dependency)
    user = getattr(request.state, "user", None)
    if user:
        return f"user:{user.id}"

    # Fall back to IP address
    return get_remote_address(request)


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
    """Custom handler for rate limit exceeded errors."""
    return JSONResponse(
        status_code=429,
        content={
            "error": "Rate limit exceeded",
            "message": "Too many requests. Please try again later.",
            "detail": str(exc.detail)
        },
        headers={
            "Retry-After": str(exc.detail.split("Retry in ")[1].split(" ")[0])
            if "Retry in" in exc.detail else str(settings.RATE_LIMIT_RETRY_AFTER_FALLBACK)
        }
    )
