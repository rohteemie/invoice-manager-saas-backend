"""
Logging configuration and middleware for the application.
"""
import logging
import json
import time
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.config import settings

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log all requests and responses."""

    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:
        # Start timer
        start_time = time.time()

        # Extract request info
        request_info = {
            "method": request.method,
            "url": str(request.url),
            "client_host": request.client.host if request.client else None,
            "user_agent": request.headers.get("user-agent", ""),
        }

        # Log request
        logger.info(
            f"Request: {request.method} {request.url.path}",
            extra=request_info
        )

        # Process request
        try:
            response = await call_next(request)

            # Calculate duration
            duration = time.time() - start_time

            # Log response
            response_info = {
                **request_info,
                "status_code": response.status_code,
                "duration": f"{duration:.3f}s"
            }

            logger.info(
                f"Response: {response.status_code} "
                f"({duration:.3f}s) {request.method} {request.url.path}",
                extra=response_info
            )

            return response

        except Exception as e:
            duration = time.time() - start_time

            # Log error
            error_info = {
                **request_info,
                "error": str(e),
                "duration": f"{duration:.3f}s"
            }

            logger.error(
                f"Error processing request: {str(e)}",
                extra=error_info,
                exc_info=True
            )
            raise


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the given name."""
    return logging.getLogger(name)
