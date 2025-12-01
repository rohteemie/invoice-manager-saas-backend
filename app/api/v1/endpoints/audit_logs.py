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
from app.core.deps import require_role

router = APIRouter()


@router.get("/", response_model=List[AuditLog])
def list_audit_logs(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000,
                       description="Maximum number of records to return"),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    action: Optional[AuditAction] = Query(None,
                                          description="Filter by action type"),
    resource_type: Optional[ResourceType] = Query(
        None, description="Filter by resource type"
    ),
    resource_id: Optional[str] = Query(None,
                                       description="Filter by resource ID"),
    status: Optional[str] = Query(None,
                                  description="Filter by status (success/failure)"),
    start_date: Optional[datetime] = Query(
        None, description="Filter by start date (ISO 8601 format)"
    ),
    end_date: Optional[datetime] = Query(
        None, description="Filter by end date (ISO 8601 format)"
    ),
    current_user: UserModel = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    """
    List audit logs with optional filtering.

    - Requires Admin role or higher
    - Returns only logs for current tenant (data isolation)
    - Supports pagination and multiple filters
    - Results are ordered by created_at descending (newest first)
    """
    # Build query with tenant isolation
    query = db.query(AuditLogModel).filter(
        AuditLogModel.tenant_id == current_user.tenant_id
    )

    # Apply filters
    if user_id:
        query = query.filter(AuditLogModel.user_id == user_id)

    if action:
        query = query.filter(AuditLogModel.action == action)

    if resource_type:
        query = query.filter(AuditLogModel.resource_type == resource_type)

    if resource_id:
        query = query.filter(AuditLogModel.resource_id == resource_id)

    if status:
        query = query.filter(AuditLogModel.status == status)

    if start_date:
        query = query.filter(AuditLogModel.created_at >= start_date)

    if end_date:
        query = query.filter(AuditLogModel.created_at <= end_date)

    # Order by created_at descending (newest first)
    query = query.order_by(desc(AuditLogModel.created_at))

    # Apply pagination
    audit_logs = query.offset(skip).limit(limit).all()

    return audit_logs


@router.get("/{audit_log_id}", response_model=AuditLog)
def get_audit_log(
    audit_log_id: str,
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


@router.get("/user/{user_id}", response_model=List[AuditLog])
def get_user_audit_logs(
    user_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    action: Optional[AuditAction] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    current_user: UserModel = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    """
    Get audit logs for a specific user.

    - Requires Admin role or higher
    - Returns logs where the user was the actor or the resource
    - Enforces tenant-based access control
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

    # Apply additional filters
    if action:
        query = query.filter(AuditLogModel.action == action)

    if start_date:
        query = query.filter(AuditLogModel.created_at >= start_date)

    if end_date:
        query = query.filter(AuditLogModel.created_at <= end_date)

    # Order by created_at descending
    query = query.order_by(desc(AuditLogModel.created_at))

    # Apply pagination
    audit_logs = query.offset(skip).limit(limit).all()

    return audit_logs


@router.get("/resource/{resource_type}/{resource_id}",
            response_model=List[AuditLog])
def get_resource_audit_logs(
    resource_type: ResourceType,
    resource_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    action: Optional[AuditAction] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    current_user: UserModel = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    """
    Get audit logs for a specific resource.

    - Requires Admin role or higher
    - Returns all actions performed on the specified resource
    - Enforces tenant-based access control
    """
    # Build query with tenant isolation
    query = db.query(AuditLogModel).filter(
        AuditLogModel.tenant_id == current_user.tenant_id,
        AuditLogModel.resource_type == resource_type,
        AuditLogModel.resource_id == resource_id
    )

    # Apply additional filters
    if action:
        query = query.filter(AuditLogModel.action == action)

    if start_date:
        query = query.filter(AuditLogModel.created_at >= start_date)

    if end_date:
        query = query.filter(AuditLogModel.created_at <= end_date)

    # Order by created_at descending
    query = query.order_by(desc(AuditLogModel.created_at))

    # Apply pagination
    audit_logs = query.offset(skip).limit(limit).all()

    return audit_logs
