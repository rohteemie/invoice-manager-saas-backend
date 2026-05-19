"""
Admin routes for Super Admin platform management.
Provides platform-level endpoints for managing tenants, users, and audit logs.
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from sqlalchemy import func
from slowapi.util import get_remote_address

from app.db.session import get_db
from app.models.tenant import Tenant as TenantModel
from app.models.user import User as UserModel
from app.models.audit_log import AuditLog as AuditLogModel
from app.schemas.tenant import Tenant, SuperAdminTenantUpdate
from app.schemas.user import User
from app.schemas.audit_log import AuditLog
from app.schemas.pagination import PaginatedResponse, create_paginated_response
from app.core.deps import require_superadmin
from app.core.rate_limit import limiter
from app.services.audit_logger import log_tenant_event
from app.models.audit_log import AuditAction

router = APIRouter()


@router.get("/tenants", response_model=PaginatedResponse[Tenant])
@limiter.limit("60/minute", key_func=get_remote_address)
def list_all_tenants(
    request: Request,
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

    Returns paginated response with metadata:
    - items: List of tenants
    - total: Total count of tenants
    - page: Current page number
    - size: Items per page
    - pages: Total number of pages
    - has_next: Whether there is a next page
    - has_previous: Whether there is a previous page
    """
    query = db.query(TenantModel)

    if is_active is not None:
        query = query.filter(TenantModel.is_active == is_active)

    # Get total count
    total = query.count()

    # Get paginated items
    tenants = query.offset(skip).limit(limit).all()

    return create_paginated_response(
        items=tenants,
        total=total,
        skip=skip,
        limit=limit
    )


@router.get("/tenants/{tenant_id}", response_model=Tenant)
@limiter.limit("60/minute", key_func=get_remote_address)
def get_tenant(
    request: Request,
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
@limiter.limit("30/minute", key_func=get_remote_address)
def suspend_tenant(
    request: Request,
    tenant_id: str,
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
@limiter.limit("30/minute", key_func=get_remote_address)
def reactivate_tenant(
    request: Request,
    tenant_id: str,
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


@router.put("/tenants/{tenant_id}", response_model=Tenant)
@limiter.limit("30/minute", key_func=get_remote_address)
def superadmin_update_tenant(
    tenant_id: str,
    tenant_update: SuperAdminTenantUpdate,
    request: Request,
    current_user: UserModel = Depends(require_superadmin),
    db: Session = Depends(get_db)
):
    """
    Update a tenant's plan type and any other fields defined in the
    SuperAdminTenantUpdate schema.

    Requires Super Admin access.
    Only super admins can change the plan_type.

    that schema are candidates for update (for example: plan_type, domain,
    name, activation/status flags, business_registration_number, and other
    tenant-level configuration fields). Uniqueness constraints apply to some
    fields such as domain and business_registration_number.

    Args:
        tenant_id: ID of the tenant to update.
        tenant_update: Updated tenant fields, following SuperAdminTenantUpdate.

    Returns:
        Updated tenant.
    """
    tenant = db.query(TenantModel).filter(TenantModel.id == tenant_id).first()

    if not tenant:
        raise HTTPException(
            status_code=404,
            detail=f"Tenant with ID {tenant_id} not found"
        )

    update_data = tenant_update.model_dump(exclude_unset=True)

    # Track changes for audit
    changes = {}
    for field, value in update_data.items():
        if hasattr(tenant, field):
            old_value = getattr(tenant, field)
            if old_value != value:
                changes[field] = {"before": old_value, "after": value}

    # Check for domain uniqueness if domain is being updated
    if "domain" in update_data and update_data["domain"] is not None:
        new_domain = update_data["domain"]
        if new_domain != tenant.domain:
            existing_tenant = db.query(TenantModel).filter(
                TenantModel.domain == new_domain,
                TenantModel.id != tenant_id
            ).first()
            if existing_tenant:
                raise HTTPException(
                    status_code=400,
                    detail="A tenant with this domain already exists"
                )

    # Check for business_registration_number uniqueness if being updated
    if (
        "business_registration_number" in update_data
        and update_data["business_registration_number"] is not None
    ):
        new_brn = update_data["business_registration_number"]
        if new_brn != tenant.business_registration_number:
            existing_tenant = db.query(TenantModel).filter(
                TenantModel.business_registration_number == new_brn,
                TenantModel.id != tenant_id
            ).first()
            if existing_tenant:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "A tenant with this business registration number "
                        "already exists"
                    )
                )

    # Ensure at least one unique identifier remains after the update
    final_domain = update_data.get("domain", tenant.domain)
    final_business_registration_number = update_data.get(
        "business_registration_number",
        tenant.business_registration_number,
    )
    if final_domain is None and final_business_registration_number is None:
        raise HTTPException(
            status_code=400,
            detail=(
                "Tenant must have at least one unique identifier: "
                "domain or business_registration_number"
            ),
        )

    # Apply updates
    for field, value in update_data.items():
        setattr(tenant, field, value)

    db.commit()
    db.refresh(tenant)

    # Log the update
    if changes:
        log_tenant_event(
            db=db,
            request=request,
            action=AuditAction.TENANT_UPDATED,
            resource_id=tenant_id,
            tenant_id=tenant_id,
            user_id=current_user.id,
            description=(
                f"Tenant {tenant.name} updated by "
                f"super admin {current_user.email}"
            ),
            changes=changes
        )

    return tenant


@router.get("/users", response_model=PaginatedResponse[User])
@limiter.limit("60/minute", key_func=get_remote_address)
def list_all_users(
    request: Request,
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

    Returns paginated response with metadata:
    - items: List of users
    - total: Total count of users
    - page: Current page number
    - size: Items per page
    - pages: Total number of pages
    - has_next: Whether there is a next page
    - has_previous: Whether there is a previous page
    """
    query = db.query(UserModel)

    if tenant_id is not None:
        query = query.filter(UserModel.tenant_id == tenant_id)

    if is_active is not None:
        query = query.filter(UserModel.is_active == is_active)

    if is_superadmin is not None:
        query = query.filter(UserModel.is_superadmin == is_superadmin)

    # Get total count
    total = query.count()

    # Get paginated items
    users = query.offset(skip).limit(limit).all()

    return create_paginated_response(
        items=users,
        total=total,
        skip=skip,
        limit=limit
    )


@router.get("/audit-logs", response_model=PaginatedResponse[AuditLog])
@limiter.limit("30/minute", key_func=get_remote_address)
def list_platform_audit_logs(
    request: Request,
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

    Returns paginated response with metadata:
    - items: List of audit logs
    - total: Total count of audit logs
    - page: Current page number
    - size: Items per page
    - pages: Total number of pages
    - has_next: Whether there is a next page
    - has_previous: Whether there is a previous page
    """
    query = db.query(AuditLogModel)

    if tenant_id is not None:
        query = query.filter(AuditLogModel.tenant_id == tenant_id)

    if user_id is not None:
        query = query.filter(AuditLogModel.user_id == user_id)

    if action is not None:
        query = query.filter(AuditLogModel.action == action)

    # Order by created_at descending (most recent first)
    query = query.order_by(AuditLogModel.created_at.desc())

    # Get total count
    total = query.count()

    # Get paginated items
    logs = query.offset(skip).limit(limit).all()

    return create_paginated_response(
        items=logs,
        total=total,
        skip=skip,
        limit=limit
    )


@router.get("/stats")
@limiter.limit("30/minute", key_func=get_remote_address)
def get_platform_stats(
    request: Request,
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
