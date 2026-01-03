"""
Custom exception classes for the application.
These exceptions provide error codes and consistent messaging.
"""
from typing import Optional, List, Dict, Any
from fastapi import status


class AppException(Exception):
    """
    Base exception class for all application exceptions.

    Attributes:
        message: Human-readable error message
        code: Machine-readable error code
        status_code: HTTP status code
        details: Optional additional error details
    """
    def __init__(
        self,
        message: str,
        code: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        details: Optional[List[Dict[str, Any]]] = None
    ):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or []
        super().__init__(self.message)


class ValidationException(AppException):
    """Raised when input validation fails."""
    def __init__(
        self,
        message: str = "Validation error",
        details: Optional[List[Dict[str, Any]]] = None
    ):
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=details
        )


class NotFoundException(AppException):
    """Raised when a requested resource is not found."""
    def __init__(
        self,
        message: str = "Resource not found",
        resource: Optional[str] = None
    ):
        code = f"{resource.upper()}_NOT_FOUND" if resource else "NOT_FOUND"
        super().__init__(
            message=message,
            code=code,
            status_code=status.HTTP_404_NOT_FOUND
        )


class UnauthorizedException(AppException):
    """Raised when authentication fails."""
    def __init__(
        self,
        message: str = "Authentication required",
        code: str = "UNAUTHORIZED"
    ):
        super().__init__(
            message=message,
            code=code,
            status_code=status.HTTP_401_UNAUTHORIZED
        )


class ForbiddenException(AppException):
    """Raised when user lacks permission for an action."""
    def __init__(
        self,
        message: str = "Access forbidden",
        code: str = "FORBIDDEN"
    ):
        super().__init__(
            message=message,
            code=code,
            status_code=status.HTTP_403_FORBIDDEN
        )


class ConflictException(AppException):
    """Raised when there's a conflict (e.g., duplicate resource)."""
    def __init__(
        self,
        message: str = "Resource conflict",
        code: str = "CONFLICT"
    ):
        super().__init__(
            message=message,
            code=code,
            status_code=status.HTTP_409_CONFLICT
        )


class DatabaseException(AppException):
    """Raised when database operations fail."""
    def __init__(
        self,
        message: str = "Database operation failed",
        code: str = "DATABASE_ERROR"
    ):
        super().__init__(
            message=message,
            code=code,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class ExternalServiceException(AppException):
    """Raised when external service calls fail."""
    def __init__(
        self,
        message: str = "External service error",
        service: Optional[str] = None
    ):
        code = (
            f"{service.upper()}_ERROR"
            if service
            else "EXTERNAL_SERVICE_ERROR"
        )
        super().__init__(
            message=message,
            code=code,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE
        )
