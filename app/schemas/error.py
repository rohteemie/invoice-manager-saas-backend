"""
Standardized error response schemas.
All API errors follow this consistent format for easy client-side handling.
"""
from typing import Optional, Dict, Any, List
from pydantic import BaseModel


class ErrorDetail(BaseModel):
    """Individual error detail."""
    field: Optional[str] = None
    message: str
    code: Optional[str] = None


class ErrorResponse(BaseModel):
    """
    Standardized error response format.
    
    All API errors return this format for consistency.
    """
    error: str  # Error type/category
    message: str  # Human-readable error message
    code: str  # Machine-readable error code for client handling
    details: Optional[List[ErrorDetail]] = None  # Optional detailed error info
    request_id: Optional[str] = None  # For tracking/debugging
    
    class Config:
        json_schema_extra = {
            "example": {
                "error": "ValidationError",
                "message": "Invalid input data",
                "code": "VALIDATION_ERROR",
                "details": [
                    {
                        "field": "email",
                        "message": "Invalid email format",
                        "code": "INVALID_EMAIL"
                    }
                ]
            }
        }
