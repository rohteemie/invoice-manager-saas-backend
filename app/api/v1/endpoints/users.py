"""
User management endpoints with role-based access control.
Supports CRUD operations with tenant-aware data isolation.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import User as UserModel, UserRole
from app.schemas.user import User, UserUpdate, OwnerUserCreate
from app.schemas.pagination import PaginatedResponse, create_paginated_response
from app.core.deps import get_current_user, require_role
from app.services.audit_logger import log_user_event
from app.models.audit_log import AuditAction
from app.core.security import get_password_hash

router = APIRouter()


@router.get("/me", response_model=User)
def get_current_user_info(
    current_user: UserModel = Depends(get_current_user)
):
    """
    Get current user information.

    - Returns authenticated user's profile
    - No special permissions required
    """
    return current_user


@router.post("/", response_model=User, status_code=status.HTTP_201_CREATED)
def create_user(
    user_in: OwnerUserCreate,
    request: Request,
    current_user: UserModel = Depends(require_role(UserRole.OWNER)),
    db: Session = Depends(get_db)
):
    """
    Create a new user within the owner's tenant.

    - Requires Owner role
    - User is created under the same tenant as the owner
    - Can create users with any role including OWNER (co-owners)
    - All new users must change password on first login
    """
    # Superadmins do not belong to a tenant; prevent them from calling this
    if current_user.is_superadmin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Superadmins cannot create tenant users. "
                   "Use POST /api/v1/tenants/register for new organizations."
        )

    # Check if email already exists (case-insensitive)
    existing_user = db.query(UserModel).filter(
        UserModel.email == user_in.email.lower()
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Create user with must_change_password flag set to True
    new_user = UserModel(
        email=user_in.email.lower(),
        full_name=user_in.full_name,
        hashed_password=get_password_hash(user_in.password),
        role=user_in.role,
        tenant_id=current_user.tenant_id,
        is_active=True,
        is_verified=True,  # Owner-created users are pre-verified
        must_change_password=True  # Force password change on first login
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Log user creation
    log_user_event(
        db=db,
        request=request,
        action=AuditAction.USER_CREATED,
        resource_id=new_user.id,
        user_id=current_user.id,
        tenant_id=current_user.tenant_id,
        changes={
            "email": new_user.email,
            "role": new_user.role.value,
            "created_by": current_user.email
        },
        description=f"{new_user.email} created by owner {current_user.email}"
    )

    return new_user


@router.get("/", response_model=PaginatedResponse[User])
def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: UserModel = Depends(require_role(UserRole.OWNER)),
    db: Session = Depends(get_db)
):
    """
    List all users in the current tenant.

    - Requires Owner role
    - Returns only users from same tenant (data isolation)
    - Supports pagination

    Returns paginated response with metadata:
    - items: List of users
    - total: Total count of users
    - page: Current page number
    - size: Items per page
    - pages: Total number of pages
    - has_next: Whether there is a next page
    - has_previous: Whether there is a previous page
    """
    query = db.query(UserModel).filter(
        UserModel.tenant_id == current_user.tenant_id
    )

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


@router.get("/{user_id}", response_model=User)
def get_user(
    user_id: str,
    current_user: UserModel = Depends(require_role(UserRole.OWNER)),
    db: Session = Depends(get_db)
):
    """
    Get a specific user by ID.

    - Requires Owner role
    - Enforces tenant-based access control
    """
    user = db.query(UserModel).filter(
        UserModel.id == user_id,
        UserModel.tenant_id == current_user.tenant_id
    ).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user


@router.put("/{user_id}", response_model=User)
def update_user(
    user_id: str,
    user_update: UserUpdate,
    request: Request,
    current_user: UserModel = Depends(require_role(UserRole.OWNER)),
    db: Session = Depends(get_db)
):
    """
    Update user information.

    - Requires Owner role (only owners can update users)
    - Enforces tenant-based access control
    - Cannot update password through this endpoint
    - Cannot change owner role or assign owner role to any user
    - Owners can upgrade roles for other non-owner users
    """
    user = db.query(UserModel).filter(
        UserModel.id == user_id,
        UserModel.tenant_id == current_user.tenant_id
    ).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    update_data = user_update.model_dump(exclude_unset=True)

    # Capture before state for audit
    before_state = {}
    changes = {}

    # Validate role changes
    if "role" in update_data:
        new_role = update_data["role"]

        # Prevent changing an owner's role
        if user.role == UserRole.OWNER:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Owner role cannot be changed via API"
            )

        # Prevent assigning owner role to any user
        if new_role == UserRole.OWNER:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot assign owner role via API"
            )

        # Track role change for audit
        before_state["role"] = user.role.value
        changes["role"] = {"before": user.role.value, "after": new_role.value}

    # Track other changes
    for field, value in update_data.items():
        if field != "role" and hasattr(user, field):
            old_value = getattr(user, field)
            if old_value != value:
                before_state[field] = old_value
                changes[field] = {"before": old_value, "after": value}

    for field, value in update_data.items():
        setattr(user, field, value)

    db.commit()
    db.refresh(user)

    # Log user update
    action = (AuditAction.USER_ROLE_CHANGED
              if "role" in changes
              else AuditAction.USER_UPDATED)
    log_user_event(
        db=db,
        request=request,
        action=action,
        resource_id=user.id,
        user_id=current_user.id,
        tenant_id=current_user.tenant_id,
        changes=changes,
        description=(f"User {user.email} role changed from "
                     f"{changes['role']['before']} to "
                     f"{changes['role']['after']}"
                     if "role" in changes
                     else f"User {user.email} updated")
    )

    return user


@router.delete("/{user_id}")
def delete_user(
    user_id: str,
    request: Request,
    current_user: UserModel = Depends(require_role(UserRole.OWNER)),
    db: Session = Depends(get_db)
):
    """
    Soft delete a user (GDPR-compliant right-to-be-forgotten).

    - Requires Owner role
    - Sets is_active to False instead of hard delete
    - Enforces tenant-based access control
    - Maintains audit trail
    - Cannot delete own account or another owner
    """
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )

    user = db.query(UserModel).filter(
        UserModel.id == user_id,
        UserModel.tenant_id == current_user.tenant_id
    ).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Prevent owner from deleting another owner
    if user.role == UserRole.OWNER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot delete another owner account"
        )

    user.is_active = False
    db.commit()

    # Log user deletion
    log_user_event(
        db=db,
        request=request,
        action=AuditAction.USER_DELETED,
        resource_id=user.id,
        user_id=current_user.id,
        tenant_id=current_user.tenant_id,
        changes={"is_active": {"before": True, "after": False}},
        description=f"User {user.email} deactivated (soft delete)"
    )

    return {"message": "User deactivated successfully"}
