"""
Pagination schemas for API list endpoints.

Provides a standardized pagination response format with metadata
about total count, pages, and navigation helpers.
"""
from typing import Generic, TypeVar, List
from pydantic import BaseModel, Field, ConfigDict
from math import ceil


T = TypeVar('T')


class PaginatedResponse(BaseModel, Generic[T]):
    """
    Generic paginated response schema.

    Attributes:
        items: List of items in the current page
        total: Total count of items across all pages
        page: Current page number (1-indexed)
        size: Number of items per page (limit)
        pages: Total number of pages
        has_next: Whether there is a next page
        has_previous: Whether there is a previous page
    """
    items: List[T] = Field(..., description="List of item in the current page")
    total: int = Field(..., ge=0, description="Total count of items")
    page: int = Field(..., ge=1, description="Current page number (1-indexed)")
    size: int = Field(..., ge=1, description="Number of items per page")
    pages: int = Field(..., ge=0, description="Total number of pages")
    has_next: bool = Field(..., description="Whether there is a next page")
    has_previous: bool = Field(..., description="Whether there is a prev page")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "items": [],
                "total": 150,
                "page": 1,
                "size": 100,
                "pages": 2,
                "has_next": True,
                "has_previous": False
            }
        }
    )


def create_paginated_response(
    items: List[T],
    total: int,
    skip: int,
    limit: int
) -> dict:
    """
    Create a paginated response dictionary.

    Args:
        items: List of items for the current page
        total: Total count of all items
        skip: Number of items skipped (offset)
        limit: Maximum number of items per page

    Returns:
        Dictionary with pagination metadata and items
    """
    # Ensure limit is at least 1 to avoid division by zero
    safe_limit = max(1, limit)

    # Calculate page number (1-indexed)
    page = (skip // safe_limit) + 1

    # Calculate total pages
    pages = ceil(total / safe_limit) if total > 0 else 0

    # Determine if there are next/previous pages
    has_next = skip + safe_limit < total
    has_previous = skip > 0

    return {
        "items": items,
        "total": total,
        "page": page,
        "size": limit,  # Return original limit value
        "pages": pages,
        "has_next": has_next,
        "has_previous": has_previous
    }
