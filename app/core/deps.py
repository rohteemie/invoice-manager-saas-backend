"""
Dependencies for authentication and authorization.
Implements JWT-based authentication with role-based access control.
"""
from typing import Optional
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.core.security import decode_token
from app.db.session import get_db
from app.models.user import User, UserRole


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_current_user(
    request: Request,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    Get current authenticated user from JWT token.

    Enforces mandatory password change on first login for owner-created users.

    Args:
        request: Current HTTP request
        token: JWT access token
        db: Database session

    Returns:
        User object

    Raises:
        HTTPException: If token is invalid, user not found, or
                      password change is required before
                      accessing the system
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

    # Enforce mandatory password change for owner-created users
    if user.must_change_password:
        # Allow access only to specific endpoints for password change flow
        current_path = request.url.path
        exempt_paths = [
            "/api/v1/auth/force-change-password",
            "/api/v1/auth/logout",
            "/api/v1/users/me"
        ]

        if current_path not in exempt_paths:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Password change required. Must change your password "
                       "before accessing other features. "
                       "Please call POST /api/v1/auth/force-change-password "
                       "with your current (temporary) password "
                       "and new password."
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


def require_verified_email(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependency to ensure user has verified their email.

    This dependency should be used for critical operations that require
    email verification, such as creating invoices, sending emails, etc.

    Args:
        current_user: Current user from token

    Returns:
        User object if email is verified

    Raises:
        HTTPException: If user's email is not verified
    """
    # Superadmins bypass email verification requirement
    if current_user.is_superadmin:
        return current_user

    if not current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email verification required. "
                   "Please verify your email address to perform this action. "
                   "Check inbox for verification link or request a new one."
        )
    return current_user


def check_invoice_access(invoice, current_user: User) -> None:
    """
    Check if the current user has access to the given invoice.

    Access Policy (Option B: Role-Based Flexibility):
    - ATTENDANT: Can only access invoices they created
    - MANAGER+: Can access all invoices in their tenant
    - Superadmin: Bypasses all checks

    Args:
        invoice: Invoice object to check access for
        current_user: The current authenticated user

    Raises:
        HTTPException: If user doesn't have access to the invoice
    """
    # Superadmins bypass all checks
    if current_user.is_superadmin:
        return

    # Attendants can only access their own invoices
    if (
        current_user.role == UserRole.ATTENDANT
        and invoice.creator_id != current_user.id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only access invoices you created"
        )

    # MANAGER and above can access all tenant invoices
    # (no additional check needed)
