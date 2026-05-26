"""
Audit Log endpoints for querying audit trail.
Provides read-only access to audit logs with filtering capabilities.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc
from datetime import datetime

from app.db.session import get_db
from app.models.audit_log import (
    AuditLog as AuditLogModel,
    AuditAction,
    ResourceType
)
from app.models.user import User as UserModel, UserRole
from app.schemas.audit_log import AuditLog
from app.schemas.pagination import PaginatedResponse, create_paginated_response
from app.core.deps import require_role, require_verified_email

router = APIRouter()


def apply_common_filters(
    query,
    actions: Optional[List[AuditAction]] = None,
    resource_types: Optional[List[ResourceType]] = None,
    resource_id: Optional[str] = None,
    status: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
):
    """
    Apply common filters to audit log query.

    This function implements DRY principle by centralizing filter logic
    that is reused across multiple endpoints.

    Args:
        query: SQLAlchemy query object
        actions: List of actions to filter by (OR logic)
        resource_types: List of resource types to filter by (OR logic)
        resource_id: Filter by specific resource ID
        status: Filter by status (success/failure)
        start_date: Filter by start date
        end_date: Filter by end date

    Returns:
        Modified query with filters applied
    """
    # Filter by multiple actions (OR logic)
    if actions:
        query = query.filter(AuditLogModel.action.in_(actions))

    # Filter by multiple resource types (OR logic)
    if resource_types:
        query = query.filter(AuditLogModel.resource_type.in_(resource_types))

    # Filter by resource ID
    if resource_id:
        query = query.filter(AuditLogModel.resource_id == resource_id)

    # Filter by status
    if status:
        query = query.filter(AuditLogModel.status == status)

    # Filter by date range
    if start_date:
        query = query.filter(AuditLogModel.created_at >= start_date)

    if end_date:
        query = query.filter(AuditLogModel.created_at <= end_date)

    return query


@router.get("/", response_model=PaginatedResponse[AuditLog])
def list_audit_logs(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(
        100, ge=1, le=1000,
        description="Maximum number of records to return"
    ),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    actions: Optional[List[AuditAction]] = Query(
        None, description="Filter by action types (supports multiple)"
    ),
    resource_types: Optional[List[ResourceType]] = Query(
        None, description="Filter by resource types (supports multiple)"
    ),
    resource_id: Optional[str] = Query(
        None, description="Filter by resource ID"
    ),
    status: Optional[str] = Query(
        None, description="Filter by status (success/failure)"
    ),
    start_date: Optional[datetime] = Query(
        None, description="Filter by start date (ISO 8601 format)"
    ),
    end_date: Optional[datetime] = Query(
        None, description="Filter by end date (ISO 8601 format)"
    ),
    _verified_user: UserModel = Depends(require_verified_email),
    current_user: UserModel = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    """
    List audit logs with optional filtering.

    - Requires Admin role or higher
    - Returns only logs for current tenant (data isolation)
    - Supports pagination and multiple filters
    - Supports filtering by multiple actions and resource types
    - Results are ordered by created_at descending (newest first)

    Example:
        GET /audit-logs/?actions=login&actions=login_failed
        GET /audit-logs/?resource_types=user&resource_types=tenant

    Returns paginated response with metadata:
    - items: List of audit logs
    - total: Total count of audit logs
    - page: Current page number
    - size: Items per page
    - pages: Total number of pages
    - has_next: Whether there is a next page
    - has_previous: Whether there is a previous page
    """
    # Build query with tenant isolation
    query = db.query(AuditLogModel).filter(
        AuditLogModel.tenant_id == current_user.tenant_id
    )

    # Filter by user ID
    if user_id:
        query = query.filter(AuditLogModel.user_id == user_id)

    # Apply common filters
    query = apply_common_filters(
        query,
        actions=actions,
        resource_types=resource_types,
        resource_id=resource_id,
        status=status,
        start_date=start_date,
        end_date=end_date
    )

    # Order by created_at descending (newest first)
    query = query.order_by(desc(AuditLogModel.created_at))

    # Get total count
    total = query.count()

    # Apply pagination
    audit_logs = query.offset(skip).limit(limit).all()

    return create_paginated_response(
        items=audit_logs,
        total=total,
        skip=skip,
        limit=limit
    )


@router.get("/{audit_log_id}", response_model=AuditLog)
def get_audit_log(
    audit_log_id: str,
    _verified_user: UserModel = Depends(require_verified_email),
    current_user: UserModel = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    """
    Get a specific audit log by ID.

    - Requires Admin role or higher
    - Enforces tenant-based access control
    """
    audit_log = db.query(AuditLogModel).filter(
        AuditLogModel.id == audit_log_id,
        AuditLogModel.tenant_id == current_user.tenant_id
    ).first()

    if not audit_log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audit log not found"
        )

    return audit_log


@router.get("/user/{user_id}", response_model=PaginatedResponse[AuditLog])
def get_user_audit_logs(
    user_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    actions: Optional[List[AuditAction]] = Query(
        None, description="Filter by action types (supports multiple)"
    ),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    _verified_user: UserModel = Depends(require_verified_email),
    current_user: UserModel = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    """
    Get audit logs for a specific user.

    - Requires Admin role or higher
    - Returns logs where the user was the actor or the resource
    - Enforces tenant-based access control
    - Supports filtering by multiple actions

    Example:
        GET /audit-logs/user/{user_id}?actions=login&actions=login_failed

    Returns paginated response with metadata:
    - items: List of audit logs
    - total: Total count of audit logs
    - page: Current page number
    - size: Items per page
    - pages: Total number of pages
    - has_next: Whether there is a next page
    - has_previous: Whether there is a previous page
    """
    # Build query with tenant isolation
    query = db.query(AuditLogModel).filter(
        AuditLogModel.tenant_id == current_user.tenant_id,
        or_(
            AuditLogModel.user_id == user_id,
            and_(
                AuditLogModel.resource_type == ResourceType.USER,
                AuditLogModel.resource_id == user_id
            )
        )
    )

    # Apply common filters
    query = apply_common_filters(
        query,
        actions=actions,
        start_date=start_date,
        end_date=end_date
    )

    # Order by created_at descending
    query = query.order_by(desc(AuditLogModel.created_at))

    # Get total count
    total = query.count()

    # Apply pagination
    audit_logs = query.offset(skip).limit(limit).all()

    return create_paginated_response(
        items=audit_logs,
        total=total,
        skip=skip,
        limit=limit
    )


@router.get("/resource/{resource_type}/{resource_id}",
            response_model=PaginatedResponse[AuditLog])
def get_resource_audit_logs(
    resource_type: ResourceType,
    resource_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    actions: Optional[List[AuditAction]] = Query(
        None, description="Filter by action types (supports multiple)"
    ),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    _verified_user: UserModel = Depends(require_verified_email),
    current_user: UserModel = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    """
    Get audit logs for a specific resource.

    - Requires Admin role or higher
    - Returns all actions performed on the specified resource
    - Enforces tenant-based access control
    - Supports filtering by multiple actions

    Example:
        GET /audit-logs/resource/invoice/{id}?actions=created&actions=updated

    Returns paginated response with metadata:
    - items: List of audit logs
    - total: Total count of audit logs
    - page: Current page number
    - size: Items per page
    - pages: Total number of pages
    - has_next: Whether there is a next page
    - has_previous: Whether there is a previous page
    """
    # Build query with tenant isolation and resource filters
    query = db.query(AuditLogModel).filter(
        AuditLogModel.tenant_id == current_user.tenant_id,
        AuditLogModel.resource_type == resource_type,
        AuditLogModel.resource_id == resource_id
    )

    # Apply common filters
    query = apply_common_filters(
        query,
        actions=actions,
        start_date=start_date,
        end_date=end_date
    )

    # Order by created_at descending
    query = query.order_by(desc(AuditLogModel.created_at))

    # Get total count
    total = query.count()

    # Apply pagination
    audit_logs = query.offset(skip).limit(limit).all()

    return create_paginated_response(
        items=audit_logs,
        total=total,
        skip=skip,
        limit=limit
    )
