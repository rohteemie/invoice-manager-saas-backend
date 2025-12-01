"""
Redis cache configuration and utilities.
"""
import json
from typing import Optional, Any
from functools import wraps
import redis
from app.core.config import settings
import logging


logger = logging.getLogger(__name__)

# Initialize Redis client (will be None if Redis is not configured)
redis_client: Optional[redis.Redis] = None


def _create_redis_client() -> Optional[redis.Redis]:
    """Create a configured Redis client or return None if not configured."""
    if not (hasattr(settings, 'REDIS_URL') and settings.REDIS_URL):
        return None

    try:
        client = redis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            socket_connect_timeout=int(getattr(settings, "REDIS_CONNECT_TIMEOUT", 5)),
            socket_timeout=int(getattr(settings, "REDIS_SOCKET_TIMEOUT", 5)),
            retry_on_timeout=True,
            health_check_interval=int(getattr(settings, "REDIS_HEALTH_CHECK_INTERVAL", 30)),
        )
        # Test connection
        client.ping()
        return client
    except Exception as e:

        logger.warning(f"Redis connection failed: {e}. Caching disabled.")
        logger.error(f"Cache set error: {e}")
        return None


# Try to create client at import time
redis_client = _create_redis_client()


def get_redis_client() -> Optional[redis.Redis]:
    """Get Redis client instance."""
    global redis_client
    # Lazy reconnect: if client is None try to recreate
    if redis_client is None:
        redis_client = _create_redis_client()

    if redis_client is not None:
        try:
            redis_client.ping()
        except Exception:
            # Attempt to recreate once
            redis_client = _create_redis_client()

    return redis_client


def cache_key(tenant_id: str, key: str) -> str:
    """Generate cache key with tenant isolation."""
    return f"tenant:{tenant_id}:{key}"


def set_cache(key: str, value: Any, expiry: int = 300) -> bool:
    """
    Set cache value with expiry time.

    Args:
        key: Cache key
        value: Value to cache (will be JSON serialized)
        expiry: Expiry time in seconds (default: 300 = 5 minutes)

    Returns:
        bool: True if successfully cached, False otherwise
    """
    if not redis_client:
        return False

    try:
        serialized_value = json.dumps(value)
        redis_client.setex(key, expiry, serialized_value)
        return True
    except Exception as e:
        logger.error(f"Cache set error: {e}")
        return False


def get_cache(key: str) -> Optional[Any]:
    """
    Get cached value.

    Args:
        key: Cache key

    Returns:
        Cached value if exists, None otherwise
    """
    if not redis_client:
        return None

    try:
        value = redis_client.get(key)
        if value:
            return json.loads(value)
        return None
    except Exception as e:
        logger.error(f"Cache get error: {e}")
        return None


def delete_cache(key: str) -> bool:
    """
    Delete cached value.

    Args:
        key: Cache key

    Returns:
        bool: True if successfully deleted, False otherwise
    """
    if not redis_client:
        return False

    try:
        redis_client.delete(key)
        return True
    except Exception as e:
        logger.error(f"Cache delete error: {e}")
        return False


def invalidate_tenant_cache(tenant_id: str, pattern: str = "*") -> bool:
    """
    Invalidate all cache for a tenant matching a pattern.

    Args:
        tenant_id: Tenant ID
        pattern: Key pattern to match (default: all keys)

    Returns:
        bool: True if successfully invalidated, False otherwise
    """
    if not redis_client:
        return False

    try:
        cache_pattern = cache_key(tenant_id, pattern)
        for key in redis_client.scan_iter(match=cache_pattern):
            redis_client.delete(key)
        return True
    except Exception as e:
        logger.error(f"Cache invalidation error: {e}")
        return False


def cached(expiry: int = 300):
    """
    Decorator for caching function results.

    Args:
        expiry: Cache expiry time in seconds (default: 300 = 5 minutes)
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Only cache if Redis is available
            if not redis_client:
                return func(*args, **kwargs)

            # Generate cache key from function name and arguments
            # Note: This is a simple implementation
            # In production, use a more robust key generation
            key_parts = [func.__name__]
            key_parts.extend(str(arg) for arg in args)
            key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
            cache_key_name = ":".join(key_parts)

            # Try to get from cache
            cached_value = get_cache(cache_key_name)
            if cached_value is not None:
                return cached_value

            # Execute function and cache result
            result = func(*args, **kwargs)
            set_cache(cache_key_name, result, expiry)
            return result

        return wrapper
    return decorator
