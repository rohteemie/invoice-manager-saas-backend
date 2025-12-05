"""
Dependencies for authentication and authorization.
Implements JWT-based authentication with role-based access control.
"""
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.core.security import decode_token
from app.db.session import get_db
from app.models.user import User, UserRole


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    Get current authenticated user from JWT token.

    Args:
        token: JWT access token
        db: Database session

    Returns:
        User object

    Raises:
        HTTPException: If token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decode_token(token)
    if payload is None:
        raise credentials_exception

    user_id: Optional[str] = payload.get("sub")
    if user_id is None:
        raise credentials_exception

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )

    return user


def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get current active user.

    Args:
        current_user: Current user from token

    Returns:
        User object

    Raises:
        HTTPException: If user is not active
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    return current_user


def require_role(required_role: UserRole):
    """
    Dependency factory for role-based access control.

    Args:
        required_role: Minimum required role for access

    Returns:
        Dependency function that checks user role
    """
    role_hierarchy = {
        UserRole.OWNER: 4,
        UserRole.ADMIN: 3,
        UserRole.MANAGER: 2,
        UserRole.ATTENDANT: 1
    }

    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        # Superadmins bypass all role checks
        if current_user.is_superadmin:
            return current_user
            
        user_role_level = role_hierarchy.get(current_user.role, 0)
        required_role_level = role_hierarchy.get(required_role, 0)

        if user_role_level < required_role_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. "
                       f"Required role: {required_role.value}"
            )
        return current_user

    return role_checker


def require_superadmin(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependency for Super Admin access control.
    
    Checks if the current user has is_superadmin flag set to True.
    Super admins have platform-level access across all tenants.
    
    Args:
        current_user: Current user from token
        
    Returns:
        User object if user is a super admin
        
    Raises:
        HTTPException: If user is not a super admin
    """
    if not current_user.is_superadmin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super admin access required"
        )
    return current_user
