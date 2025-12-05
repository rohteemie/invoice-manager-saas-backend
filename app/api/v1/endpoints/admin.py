"""
Admin routes for Super Admin platform management.
Provides platform-level endpoints for managing tenants, users, and audit logs.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db.session import get_db
from app.models.tenant import Tenant as TenantModel
from app.models.user import User as UserModel
from app.models.audit_log import AuditLog as AuditLogModel
from app.schemas.tenant import Tenant
from app.schemas.user import User
from app.schemas.audit_log import AuditLog
from app.core.deps import require_superadmin
from app.services.audit_logger import log_tenant_event
from app.models.audit_log import AuditAction

router = APIRouter()


@router.get("/tenants", response_model=List[Tenant])
def list_all_tenants(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(
        100, ge=1, le=1000,
        description="Maximum number of records to return"
    ),
    is_active: Optional[bool] = Query(
        None, description="Filter by active status"
    ),
    current_user: UserModel = Depends(require_superadmin),
    db: Session = Depends(get_db)
):
    """
    List all tenants in the platform.

    Requires Super Admin access.

    Query Parameters:
        - skip: Number of records to skip (for pagination)
        - limit: Maximum number of records to return
        - is_active: Filter by active status (optional)

    Returns:
        List of tenants
    """
    query = db.query(TenantModel)

    if is_active is not None:
        query = query.filter(TenantModel.is_active == is_active)

    tenants = query.offset(skip).limit(limit).all()
    return tenants


@router.get("/tenants/{tenant_id}", response_model=Tenant)
def get_tenant(
    tenant_id: str,
    current_user: UserModel = Depends(require_superadmin),
    db: Session = Depends(get_db)
):
    """
    Get details of a specific tenant.

    Requires Super Admin access.

    Args:
        tenant_id: ID of the tenant

    Returns:
        Tenant details
    """
    tenant = db.query(TenantModel).filter(TenantModel.id == tenant_id).first()

    if not tenant:
        raise HTTPException(
            status_code=404,
            detail=f"Tenant with ID {tenant_id} not found"
        )

    return tenant


@router.put("/tenants/{tenant_id}/suspend")
def suspend_tenant(
    tenant_id: str,
    request: Request,
    current_user: UserModel = Depends(require_superadmin),
    db: Session = Depends(get_db)
):
    """
    Suspend a tenant (set is_active to False).

    Requires Super Admin access.

    Args:
        tenant_id: ID of the tenant to suspend

    Returns:
        Success message with updated tenant
    """
    tenant = db.query(TenantModel).filter(TenantModel.id == tenant_id).first()

    if not tenant:
        raise HTTPException(
            status_code=404,
            detail=f"Tenant with ID {tenant_id} not found"
        )

    if not tenant.is_active:
        raise HTTPException(
            status_code=400,
            detail="Tenant is already suspended"
        )

    tenant.is_active = False
    db.commit()
    db.refresh(tenant)

    # Log the suspension
    log_tenant_event(
        db=db,
        request=request,
        action=AuditAction.TENANT_UPDATED,
        resource_id=tenant_id,
        tenant_id=tenant_id,
        user_id=current_user.id,
        description=(
            f"Tenant {tenant.name} suspended by "
            f"super admin {current_user.email}"
        ),
        changes={"is_active": {"before": True, "after": False}}
    )

    return {
        "message": f"Tenant {tenant.name} has been suspended",
        "tenant": tenant
    }


@router.put("/tenants/{tenant_id}/reactivate")
def reactivate_tenant(
    tenant_id: str,
    request: Request,
    current_user: UserModel = Depends(require_superadmin),
    db: Session = Depends(get_db)
):
    """
    Reactivate a suspended tenant (set is_active to True).

    Requires Super Admin access.

    Args:
        tenant_id: ID of the tenant to reactivate

    Returns:
        Success message with updated tenant
    """
    tenant = db.query(TenantModel).filter(TenantModel.id == tenant_id).first()

    if not tenant:
        raise HTTPException(
            status_code=404,
            detail=f"Tenant with ID {tenant_id} not found"
        )

    if tenant.is_active:
        raise HTTPException(
            status_code=400,
            detail="Tenant is already active"
        )

    tenant.is_active = True
    db.commit()
    db.refresh(tenant)

    # Log the reactivation
    log_tenant_event(
        db=db,
        request=request,
        action=AuditAction.TENANT_UPDATED,
        resource_id=tenant_id,
        tenant_id=tenant_id,
        user_id=current_user.id,
        description=(
            f"Tenant {tenant.name} reactivated by "
            f"super admin {current_user.email}"
        ),
        changes={"is_active": {"before": False, "after": True}}
    )

    return {
        "message": f"Tenant {tenant.name} has been reactivated",
        "tenant": tenant
    }


@router.get("/users", response_model=List[User])
def list_all_users(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(
        100, ge=1, le=1000,
        description="Maximum number of records to return"
    ),
    tenant_id: Optional[str] = Query(
        None, description="Filter by tenant ID"
    ),
    is_active: Optional[bool] = Query(
        None, description="Filter by active status"
    ),
    is_superadmin: Optional[bool] = Query(
        None, description="Filter by superadmin status"
    ),
    current_user: UserModel = Depends(require_superadmin),
    db: Session = Depends(get_db)
):
    """
    List all users across all tenants.

    Requires Super Admin access.

    Query Parameters:
        - skip: Number of records to skip (for pagination)
        - limit: Maximum number of records to return
        - tenant_id: Filter by specific tenant (optional)
        - is_active: Filter by active status (optional)
        - is_superadmin: Filter by superadmin status (optional)

    Returns:
        List of users
    """
    query = db.query(UserModel)

    if tenant_id is not None:
        query = query.filter(UserModel.tenant_id == tenant_id)

    if is_active is not None:
        query = query.filter(UserModel.is_active == is_active)

    if is_superadmin is not None:
        query = query.filter(UserModel.is_superadmin == is_superadmin)

    users = query.offset(skip).limit(limit).all()
    return users


@router.get("/audit-logs", response_model=List[AuditLog])
def list_platform_audit_logs(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(
        100, ge=1, le=1000,
        description="Maximum number of records to return"
    ),
    tenant_id: Optional[str] = Query(
        None, description="Filter by tenant ID"
    ),
    user_id: Optional[str] = Query(
        None, description="Filter by user ID"
    ),
    action: Optional[str] = Query(
        None, description="Filter by action type"
    ),
    current_user: UserModel = Depends(require_superadmin),
    db: Session = Depends(get_db)
):
    """
    List platform-wide audit logs.

    Requires Super Admin access.

    Query Parameters:
        - skip: Number of records to skip (for pagination)
        - limit: Maximum number of records to return
        - tenant_id: Filter by specific tenant (optional)
        - user_id: Filter by specific user (optional)
        - action: Filter by action type (optional)

    Returns:
        List of audit logs
    """
    query = db.query(AuditLogModel)

    if tenant_id is not None:
        query = query.filter(AuditLogModel.tenant_id == tenant_id)

    if user_id is not None:
        query = query.filter(AuditLogModel.user_id == user_id)

    if action is not None:
        query = query.filter(AuditLogModel.action == action)

    # Order by created_at descending (most recent first)
    logs = (query.order_by(AuditLogModel.created_at.desc())
            .offset(skip).limit(limit).all())
    return logs


@router.get("/stats")
def get_platform_stats(
    current_user: UserModel = Depends(require_superadmin),
    db: Session = Depends(get_db)
):
    """
    Get platform-wide statistics.

    Requires Super Admin access.

    Returns:
        Platform statistics including:
        - Total tenants
        - Active tenants
        - Total users
        - Active users
        - Super admins count
    """
    total_tenants = db.query(func.count(TenantModel.id)).scalar()
    active_tenants = db.query(func.count(TenantModel.id)).filter(
        TenantModel.is_active.is_(True)
    ).scalar()

    total_users = db.query(func.count(UserModel.id)).scalar()
    active_users = db.query(func.count(UserModel.id)).filter(
        UserModel.is_active.is_(True)
    ).scalar()
    superadmins_count = db.query(func.count(UserModel.id)).filter(
        UserModel.is_superadmin.is_(True)
    ).scalar()

    return {
        "total_tenants": total_tenants,
        "active_tenants": active_tenants,
        "suspended_tenants": total_tenants - active_tenants,
        "total_users": total_users,
        "active_users": active_users,
        "inactive_users": total_users - active_users,
        "superadmins_count": superadmins_count
    }
