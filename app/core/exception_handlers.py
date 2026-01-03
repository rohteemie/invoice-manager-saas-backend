"""
Custom exception handlers for standardized error responses.
Handles both custom exceptions and standard FastAPI/Pydantic errors.
"""
import logging
import traceback
from typing import Union
from uuid import uuid4

from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy.exc import IntegrityError, OperationalError

from app.core.exceptions import AppException
from app.core.config import settings


logger = logging.getLogger(__name__)


def create_error_response(
    error_type: str,
    message: str,
    code: str,
    status_code: int,
    details: list = None,
    request_id: str = None
) -> JSONResponse:
    """
    Create a standardized error response.

    Args:
        error_type: Type/category of error
        message: Human-readable error message
        code: Machine-readable error code
        status_code: HTTP status code
        details: Optional list of detailed error info
        request_id: Optional request ID for tracking

    Returns:
        JSONResponse with standardized error format
    """
    content = {
        "error": error_type,
        "message": message,
        "code": code,
    }

    if details:
        content["details"] = details

    if request_id:
        content["request_id"] = request_id

    return JSONResponse(
        status_code=status_code,
        content=content
    )


async def app_exception_handler(
    request: Request,
    exc: AppException
) -> JSONResponse:
    """
    Handler for custom AppException and its subclasses.

    Returns standardized error response with error code.
    """
    request_id = str(uuid4())

    logger.warning(
        f"AppException: {exc.code} - {exc.message} "
        f"[request_id={request_id}, path={request.url.path}]"
    )

    return create_error_response(
        error_type=exc.__class__.__name__.replace("Exception", ""),
        message=exc.message,
        code=exc.code,
        status_code=exc.status_code,
        details=exc.details if exc.details else None,
        request_id=request_id
    )


async def http_exception_handler(
    request: Request,
    exc: StarletteHTTPException
) -> JSONResponse:
    """
    Handler for FastAPI's HTTPException.

    Converts to standardized error format.
    """
    request_id = str(uuid4())

    # Map status codes to error codes
    status_code_map = {
        400: "BAD_REQUEST",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        405: "METHOD_NOT_ALLOWED",
        409: "CONFLICT",
        422: "VALIDATION_ERROR",
        500: "INTERNAL_SERVER_ERROR",
        503: "SERVICE_UNAVAILABLE",
    }

    code = status_code_map.get(exc.status_code, "ERROR")

    logger.warning(
        f"HTTPException: {code} - {exc.detail} "
        f"[request_id={request_id}, path={request.url.path}]"
    )

    return create_error_response(
        error_type="HTTPException",
        message=str(exc.detail),
        code=code,
        status_code=exc.status_code,
        request_id=request_id
    )


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError
) -> JSONResponse:
    """
    Handler for Pydantic validation errors.

    Formats validation errors into standardized response with details.
    """
    request_id = str(uuid4())

    # Extract validation error details
    details = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"] if loc != "body")
        details.append({
            "field": field or None,
            "message": error["msg"],
            "code": error["type"].upper()
        })

    logger.warning(
        f"ValidationError: {len(details)} validation error(s) "
        f"[request_id={request_id}, path={request.url.path}]"
    )

    return create_error_response(
        error_type="ValidationError",
        message="Request validation failed",
        code="VALIDATION_ERROR",
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        details=details,
        request_id=request_id
    )


async def database_exception_handler(
    request: Request,
    exc: Union[IntegrityError, OperationalError]
) -> JSONResponse:
    """
    Handler for database errors.

    Hides internal database details in production.
    """
    request_id = str(uuid4())

    # Log full error for debugging
    logger.error(
        f"DatabaseError: {str(exc)} [request_id={request_id}, "
        f"path={request.url.path}]",
        exc_info=True
    )

    # Determine user-friendly message
    if isinstance(exc, IntegrityError):
        # Check for common constraint violations
        error_msg = str(exc.orig) if hasattr(exc, 'orig') else str(exc)

        if "unique" in error_msg.lower() or "duplicate" in error_msg.lower():
            message = "A record with this information already exists"
            code = "DUPLICATE_ENTRY"
        elif "foreign key" in error_msg.lower():
            message = "Referenced resource does not exist"
            code = "INVALID_REFERENCE"
        else:
            message = "Database constraint violation"
            code = "CONSTRAINT_VIOLATION"

        status_code = status.HTTP_409_CONFLICT
    else:
        message = "Database operation failed"
        code = "DATABASE_ERROR"
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

    # In development, include more details
    details = None
    if settings.ENVIRONMENT == "development":
        details = [{
            "message": str(exc),
            "code": "DEBUG_INFO"
        }]

    return create_error_response(
        error_type="DatabaseError",
        message=message,
        code=code,
        status_code=status_code,
        details=details,
        request_id=request_id
    )


async def generic_exception_handler(
    request: Request,
    exc: Exception
) -> JSONResponse:
    """
    Catch-all handler for unexpected exceptions.

    Logs full error and returns generic message to avoid information leakage.
    """
    request_id = str(uuid4())

    # Log full error with traceback
    logger.error(
        f"Unhandled exception: {str(exc)} [request_id={request_id}, "
        f"path={request.url.path}]\n{traceback.format_exc()}"
    )

    # Generic error message in production
    if settings.ENVIRONMENT == "production":
        message = "An unexpected error occurred"
        details = None
    else:
        # More details in development
        message = f"An unexpected error occurred: {str(exc)}"
        details = [{
            "message": traceback.format_exc(),
            "code": "DEBUG_TRACEBACK"
        }]

    return create_error_response(
        error_type="InternalError",
        message=message,
        code="INTERNAL_SERVER_ERROR",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        details=details,
        request_id=request_id
    )
