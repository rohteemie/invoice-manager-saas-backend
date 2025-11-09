"""
User management endpoints with role-based access control.
Supports CRUD operations with tenant-aware data isolation.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import User as UserModel, UserRole
from app.schemas.user import User, UserUpdate
from app.core.deps import get_current_user, require_role

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


@router.get("/", response_model=List[User])
def list_users(
    skip: int = 0,
    limit: int = 100,
    current_user: UserModel = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    """
    List all users in the current tenant.

    - Requires Admin or Owner role
    - Returns only users from same tenant (data isolation)
    - Supports pagination
    """
    users = db.query(UserModel).filter(
        UserModel.tenant_id == current_user.tenant_id
    ).offset(skip).limit(limit).all()
    return users


@router.get("/{user_id}", response_model=User)
def get_user(
    user_id: str,
    current_user: UserModel = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    """
    Get a specific user by ID.

    - Requires Admin or Owner role
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
    current_user: UserModel = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    """
    Update user information.

    - Requires Admin or Owner role
    - Enforces tenant-based access control
    - Cannot update password through this endpoint
    - Cannot change owner role or assign owner role to any user
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

    for field, value in update_data.items():
        setattr(user, field, value)

    db.commit()
    db.refresh(user)
    return user


@router.delete("/{user_id}")
def delete_user(
    user_id: str,
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
    return {"message": "User deactivated successfully"}
