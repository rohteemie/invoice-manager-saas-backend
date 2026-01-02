"""
Middleware to add rate limit headers to responses.
"""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from typing import Callable
from app.core.rate_limit import get_role_based_limit


class RateLimitHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware that adds rate limit information headers to all responses.
    Headers include:
    - X-RateLimit-Limit: Maximum requests allowed in the time window
    - X-RateLimit-Remaining: Requests remaining in current window
    - X-RateLimit-Reset: Seconds until the rate limit resets
    """
    
    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:
        """Process request and add rate limit headers to response."""
        # Get response
        response = await call_next(request)
        
        # Don't add headers to health check or metrics endpoints
        if request.url.path in ["/health", "/metrics", "/"]:
            return response
        
        # Get user's rate limit
        try:
            limit_str = get_role_based_limit(request)
            
            # Parse limit string (e.g., "100/minute")
            limit_parts = limit_str.split("/")
            if len(limit_parts) == 2:
                limit_value = limit_parts[0]
                
                # Add headers if not already present (429 handler sets these)
                if "X-RateLimit-Limit" not in response.headers:
                    response.headers["X-RateLimit-Limit"] = limit_value
                    
                    # We don't track remaining count in this middleware
                    # as that would require accessing the rate limiter storage
                    # The headers are mainly informational
                    response.headers["X-RateLimit-Reset"] = "60"
        except Exception:
            # Don't fail request if header addition fails
            pass
        
        return response
