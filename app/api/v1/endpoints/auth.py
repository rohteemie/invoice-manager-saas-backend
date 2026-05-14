"""
Authentication endpoints for user registration, login, and token refresh.
Implements JWT-based authentication with secure password handling.
"""
from datetime import datetime, timezone
import logging
import os
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi import status, Request, Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func
from typing import Union
from pydantic import BaseModel, EmailStr
from app.db.session import get_db
from app.models.user import User as UserModel
from app.models.tenant import Tenant as TenantModel
from app.schemas.user import ForgotPasswordRequest, UserCreate, User, Token
from app.schemas.user import ResetPasswordRequest, RefreshTokenRequest
from app.schemas.user import ForceChangePasswordRequest, MultiTenantLoginResponse
from app.schemas.user import SelectTenantRequest
from app.core.security import verify_password, get_password_hash
from app.core.security import create_access_token, create_refresh_token
from app.core.security import decode_token, generate_verification_token
from app.core.security import generate_password_reset_token
from app.core.rate_limit import limiter
from app.core.config import settings
from app.core.login_throttle import get_login_throttle
from app.core.deps import require_superadmin, get_current_user
from app.services.audit_logger import log_auth_event
from app.models.audit_log import AuditAction
from app.tasks.email_tasks import send_verification_email_task
from app.tasks.email_tasks import send_password_reset_email_task


router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/register", response_model=User, status_code=201)
@limiter.limit("5/minute")
def register(
    request: Request,
    user_in: UserCreate,
    response: Response,
    current_user: UserModel = Depends(require_superadmin),
    db: Session = Depends(get_db),
):
    """
    Register a new superadmin user.

    - Requires SUPERADMIN authentication
    - Only allows creating superadmin users (no tenant assignment)
    - Validates that email is unique
    - Hashes password using bcrypt

    NOTE: For regular user registration:
    - New organizations: Use POST /api/v1/tenants/register
    - Adding users to existing tenant: Use POST /api/v1/users (owner only)
    """
    # Only superadmins can be created via this endpoint
    if not user_in.is_superadmin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This endpoint is for superadmin creation only. "
                   "Use POST /api/v1/tenants/register for new organizations "
                   "or POST /api/v1/users for adding users to a tenant."
        )

    # Superadmins should not have tenant_id
    if user_in.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Superadmins cannot be associated with a tenant"
        )

    existing_user = db.query(UserModel).filter(
        func.lower(UserModel.email) == user_in.email.lower()
    ).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    try:
        hashed_password = get_password_hash(user_in.password)
        db_user = UserModel(
            email=user_in.email.lower(),
            full_name=user_in.full_name,
            hashed_password=hashed_password,
            role=user_in.role,
            tenant_id=None,  # Superadmins have no tenant
            is_superadmin=True,  # Forced superadmin creation
        )

        # Generate verification token and expiration and attach to user
        verification_token, token_expires_at = (
            generate_verification_token()
        )
        db_user.verification_token = verification_token
        db_user.verification_token_expires_at = token_expires_at

        db.add(db_user)
        db.commit()
        db.refresh(db_user)

        # Build verification link for use in the email and in debug
        base = settings.EMAIL_VERIFICATION_BASE_URL or ""
        verification_link = (
            f"{base.rstrip('/')}/verify-email?token={verification_token}"
        )

        # Send verification email asynchronously (background task)
        try:
            send_verification_email_task.delay(
                email=db_user.email,
                token=verification_token,
                full_name=db_user.full_name,
                base_url=(
                    settings.EMAIL_VERIFICATION_BASE_URL
                    or "http://localhost:5173"
                ),
            )
            logger.info(
                "Verification email task queued for %s", db_user.email
            )
        except Exception as e:
            logger.warning(
                "Failed to queue verification email for %s: %s",
                db_user.email, str(e)
            )

        # For non-production or test runs, expose the link in a header
        env = os.environ.get("TESTING") or settings.ENVIRONMENT
        if env and env != "production":
            response.headers["X-Verification-Link"] = verification_link

        return db_user
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Failed to create user. Email may already exist."
            ),
        )


@router.post("/login", response_model=Union[Token, MultiTenantLoginResponse])
@limiter.limit("10/minute")
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Login endpoint for OAuth2 password flow with multi-tenant support.

    **Single-Tenant Response** (unchanged from before):
    - Returns Token with access_token, refresh_token, expires_in
    - Backward compatible with existing single-tenant users

    **Multi-Tenant Response** (NEW):
    - When user belongs to 2+ organizations, returns MultiTenantLoginResponse
    - Contains list of tenants with tenant_id, tenant_name, and user's role
    - Frontend uses this to show tenant selection screen
    - User must call /select-tenant endpoint to complete login

    **Security**:
    - Implements progressive delay based on failed attempts (OWASP ASVS)
    - Access token expires in configured time (default: 30 min)
    - Refresh token expires in configured time (default: 7 days)

    Progressive delay policy:
    - 1-3 attempts: No delay
    - 4-5 attempts: Short delay (default 2s)
    - 6-8 attempts: Medium delay (default 30s)
    - 9+ attempts: Long cooldown (default 15min)

    **Email Behavior**:
    - Emails are case-insensitive and unique per tenant
    - Same email can exist in different organizations
    - Example: john@example.com can be in both "Acme Corp" and "TechCo"
    """
    throttle = get_login_throttle()
    email = form_data.username.lower()

    # Query ALL users with this email (case-insensitive)
    # Users can have the same email across different tenants
    users = db.query(UserModel).filter(
        UserModel.email.ilike(email)
    ).all()

    # Validate credentials against all matching users
    authenticated_users = []
    for user in users:
        if verify_password(form_data.password, user.hashed_password):
            authenticated_users.append(user)

    # Handle failed authentication
    if not authenticated_users:
        # Record failed attempt
        new_count = throttle.record_failed_attempt(email)

        # Log failed login attempt with throttle info
        log_auth_event(
            db=db,
            request=request,
            action=AuditAction.LOGIN_FAILED,
            user_id=None,
            tenant_id=None,
            status="failure",
            description=(
                f"Failed login attempt for {form_data.username} "
                f"(attempt {new_count})"
            )
        )

        # Log excessive failures for monitoring/alerting
        if new_count >= settings.LOGIN_DELAY_THRESHOLD_LONG:
            log_auth_event(
                db=db,
                request=request,
                action=AuditAction.LOGIN_EXCESSIVE_FAILURES,
                user_id=None,
                tenant_id=None,
                status="warning",
                description=(
                    f"Excessive login failures for {form_data.username} "
                    f"({new_count} attempts)"
                )
            )

        # Apply progressive delay (constant-time even for non-existent users)
        delay_applied, _ = await throttle.apply_delay(email, new_count)

        if delay_applied > 0:
            # Log throttling action
            log_auth_event(
                db=db,
                request=request,
                action=AuditAction.LOGIN_THROTTLED,
                user_id=None,
                tenant_id=None,
                status="info",
                description=(
                    f"Login throttled for {form_data.username} "
                    f"({delay_applied}s delay)"
                )
            )

        # Generic error message (no info leak)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Filter out inactive users and check their tenants
    active_users = []
    for user in authenticated_users:
        if not user.is_active:
            # Log failed login for inactive user
            log_auth_event(
                db=db,
                request=request,
                action=AuditAction.LOGIN_FAILED,
                user_id=user.id,
                tenant_id=user.tenant_id,
                status="failure",
                description="Login attempt for inactive user account"
            )
            continue

        # Check if tenant is active (skip for superadmins)
        if user.tenant_id and not user.is_superadmin:
            tenant = db.query(TenantModel).filter(
                TenantModel.id == user.tenant_id
            ).first()
            if not tenant or not tenant.is_active:
                log_auth_event(
                    db=db,
                    request=request,
                    action=AuditAction.LOGIN_FAILED,
                    user_id=user.id,
                    tenant_id=user.tenant_id,
                    status="failure",
                    description="Login attempt for user in deactivated tenant"
                )
                continue

        active_users.append(user)

    # No active users found
    if not active_users:
        # Record as failed attempt
        new_count = throttle.record_failed_attempt(email)
        await throttle.apply_delay(email, new_count)

        # Generic error message to avoid account enumeration
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Successful authentication - clear throttle counters
    throttle.clear_failed_attempts(email)

    # SINGLE TENANT: User exists in only one tenant
    if len(active_users) == 1:
        user = active_users[0]

        # Generate tokens
        token_data = {
            "sub": user.id,
            "tenant_id": user.tenant_id,
            "role": user.role.value,
            "is_superadmin": user.is_superadmin
        }

        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)

        # Log successful login
        log_auth_event(
            db=db,
            request=request,
            action=AuditAction.LOGIN,
            user_id=user.id,
            tenant_id=user.tenant_id,
            description=f"Successful login for {user.email}"
        )

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRATION * 60,
            "requires_password_change": user.must_change_password
        }

    # MULTI-TENANT: User exists in multiple tenants
    # Return list of tenants for user to select from
    tenant_options = []
    for user in active_users:
        tenant = db.query(TenantModel).filter(
            TenantModel.id == user.tenant_id
        ).first()

        tenant_options.append({
            "tenant_id": user.tenant_id,
            "tenant_name": tenant.name if tenant else "Unknown Organization",
            "role": user.role.value
        })

    # Log multi-tenant login attempt
    log_auth_event(
        db=db,
        request=request,
        action=AuditAction.LOGIN,
        user_id=None,
        tenant_id=None,
        status="info",
        description=(
            f"Multi-tenant login for {email} - "
            f"user belongs to {len(active_users)} tenants"
        )
    )

    return {
        "requires_tenant_selection": True,
        "email": email,
        "tenants": tenant_options,
        "message": "You belong to multiple organizations. "
                   "Please select the one you want to access."
    }


@router.post("/select-tenant", response_model=Token)
@limiter.limit("10/minute")
async def select_tenant(
    request: Request,
    select_request: SelectTenantRequest,
    db: Session = Depends(get_db)
):
    """
    Complete login by selecting desired tenant.

    **Used for**:
    - Multi-tenant users who need to select which organization to access
    - Called AFTER the initial login returns requires_tenant_selection=true

    **Flow**:
    1. User logs in with email/password (initial login)
    2. If user has multiple tenants, frontend shows tenant selection screen
    3. User selects a tenant
    4. Frontend calls this endpoint with email, password, and selected tenant_id
    5. Backend re-authenticates and returns tokens for that tenant

    **Security**:
    - Requires re-authentication (email + password must be valid)
    - Validates that user actually belongs to the selected tenant
    - Rate limited to 10 requests per minute
    - Returns 401 if credentials invalid
    - Returns 400 if tenant invalid or user doesn't have access

    **Parameters**:
    - email: User's email address
    - password: User's password (re-authentication required)
    - tenant_id: ID of tenant to authenticate into

    **Response**:
    - Same as regular login: access_token, refresh_token, token_type, expires_in
    - Token will be scoped to the selected tenant
    """
    email = select_request.email.lower()

    # Find user by email and tenant_id combination
    user = db.query(UserModel).filter(
        UserModel.email.ilike(email),
        UserModel.tenant_id == select_request.tenant_id
    ).first()

    # User not found in specified tenant
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid tenant selection or user not in this tenant"
        )

    # Verify password
    if not verify_password(select_request.password, user.hashed_password):
        log_auth_event(
            db=db,
            request=request,
            action=AuditAction.LOGIN_FAILED,
            user_id=user.id,
            tenant_id=user.tenant_id,
            status="failure",
            description="Failed tenant selection - incorrect password"
        )

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if user is active
    if not user.is_active:
        log_auth_event(
            db=db,
            request=request,
            action=AuditAction.LOGIN_FAILED,
            user_id=user.id,
            tenant_id=user.tenant_id,
            status="failure",
            description="Tenant selection for inactive user"
        )

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is inactive"
        )

    # Check if tenant is active
    tenant = db.query(TenantModel).filter(
        TenantModel.id == select_request.tenant_id
    ).first()

    if not tenant or not tenant.is_active:
        log_auth_event(
            db=db,
            request=request,
            action=AuditAction.LOGIN_FAILED,
            user_id=user.id,
            tenant_id=user.tenant_id,
            status="failure",
            description="Tenant selection for deactivated tenant"
        )

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Selected tenant is not active"
        )

    if user.must_change_password:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "Password change required. Please call POST "
                "/api/v1/auth/force-change-password before selecting a tenant."
            )
        )

    # All checks passed - generate tokens
    token_data = {
        "sub": user.id,
        "tenant_id": user.tenant_id,
        "role": user.role.value,
        "is_superadmin": user.is_superadmin
    }

    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    # Log successful tenant selection
    log_auth_event(
        db=db,
        request=request,
        action=AuditAction.LOGIN,
        user_id=user.id,
        tenant_id=user.tenant_id,
        description=(
            f"Successful tenant selection login for {user.email} "
            f"in tenant {tenant.name}"
        )
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRATION * 60,
        "requires_password_change": user.must_change_password
    }


@router.post("/refresh", response_model=Token)
@limiter.limit("20/minute")
def refresh_token(
    request: Request,
    token_request: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    """
    Refresh access token using refresh token.

    - Validates refresh token (sent in request body for security)
    - Issues new access and refresh tokens
    - Maintains user session security

    Security Note: Refresh token is accepted in the request body instead of
    query parameters to prevent token exposure in server logs, browser history,
    and proxy logs.
    """
    payload = decode_token(token_request.refresh_token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id: str = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )

    token_data = {
        "sub": user.id,
        "tenant_id": user.tenant_id,
        "role": user.role.value,
        "is_superadmin": user.is_superadmin
    }

    new_access_token = create_access_token(token_data)
    new_refresh_token = create_refresh_token(token_data)

    # Log token refresh
    log_auth_event(
        db=db,
        request=request,
        action=AuditAction.TOKEN_REFRESH,
        user_id=user.id,
        tenant_id=user.tenant_id,
        description="Token refresh successful"
    )

    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRATION * 60
    }


@router.post("/verify-email", response_model=Token)
@limiter.limit("10/minute")
def verify_email(
    request: Request,
    token: str = Query(..., description="Attach token as query parameter"),
    db: Session = Depends(get_db)
):
    """
    Verify user email with verification token.

    - Validates the verification token
    - Checks token expiration
    - Marks user as verified
    - Clears the verification token

    Args:
        token: The verification token sent via email

    Returns:
        Success message with user details
    """
    # Find user by verification token
    user = db.query(UserModel).filter(
        UserModel.verification_token == token
    ).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token"
        )

    # Check if user is already verified
    if user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is already verified. You can now log in to your account."
        )

    # Check if token has expired
    if (
        user.verification_token_expires_at
        and user.verification_token_expires_at < datetime.now(timezone.utc)
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification token has expired. Please request a new verification email."
        )

    # Mark user as verified and clear token
    user.is_verified = True
    user.verification_token = None
    user.verification_token_expires_at = None
    db.commit()
    db.refresh(user)

    # Capture values before logging, because audit logging commits too.
    user_id = user.id
    user_tenant_id = user.tenant_id
    user_email = user.email
    user_role = user.role.value
    user_is_superadmin = user.is_superadmin

    log_auth_event(
        db=db,
        request=request,
        action=AuditAction.EMAIL_VERIFIED,
        user_id=user_id,
        tenant_id=user_tenant_id,
        description=f"Email verified successfully for {user_email}"
    )

    token_data = {
        "sub": user_id,
        "tenant_id": user_tenant_id,
        "role": user_role,
        "is_superadmin": user_is_superadmin
    }
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRATION * 60
    }


class ResendVerificationRequest(BaseModel):
    """Schema for resend verification email request."""
    email: EmailStr


@router.post("/resend-verification-email")
@limiter.limit("3/hour")
def resend_verification_email(
    request: Request,
    resend_request: ResendVerificationRequest,
    db: Session = Depends(get_db)
):
    """
    Resend verification email to user.

    - Finds user by email
    - Checks if user is already verified
    - Generates new verification token
    - Sends new verification email

    Args:
        resend_request: Email address to resend verification

    Returns:
        Success message
    """
    # Find user by email, case-insensitively
    user = db.query(UserModel).filter(
        func.lower(UserModel.email) == resend_request.email.lower()
    ).first()

    if not user:
        # Don't reveal whether user exists for security
        return {
            "message": "If the email exists in our system,\
                a verification email will be sent.",
            "email": resend_request.email
        }

    # Check if user is already verified
    if user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is already verified. You can log in to your account."
        )

    # Generate new verification token
    verification_token, token_expires_at = generate_verification_token()

    # Update user with new token
    user.verification_token = verification_token
    user.verification_token_expires_at = token_expires_at
    db.commit()

    # Send verification email asynchronously
    try:
        send_verification_email_task.delay(
            email=user.email,
            token=verification_token,
            full_name=user.full_name,
            base_url=(
                settings.EMAIL_VERIFICATION_BASE_URL or "http://localhost:5173"
            ),
        )
    except Exception as e:
        logger.warning(
            "Failed to queue verification email for %s: %s",
            user.email, str(e)
        )

    return {
        "message": "Verification email has been resent.\
        Please check your inbox.",
        "email": user.email
    }


@router.post("/forgot-password")
@limiter.limit("3/hour")
def forgot_password(
    request: Request,
    password_request: ForgotPasswordRequest,
    response: Response = None,
    db: Session = Depends(get_db)
):
    """
    Request password reset.

    - Finds user by email
    - Generates password reset token
    - Sends password reset email
    - Always returns success message (security: don't reveal if email exists)

    Args:
        forgot_request: Email address for password reset

    Returns:
        Success message
    """
    email_value = password_request.email

    # Find user by email, case-insensitively
    user = db.query(UserModel).filter(
        func.lower(UserModel.email) == email_value.lower()
    ).first()

    # Always return success message to prevent email enumeration
    success_message = {
        "message": "If the email exists in our system, "
                   "a password reset link will be sent.",
        "email": email_value
    }

    if not user:
        # Don't reveal whether user exists for security
        logger.info(
            "Password reset requested for non-existent email: %s",
            email_value
        )
        return success_message

    # Check if user is active
    if not user.is_active:
        logger.warning(
            "Password reset requested for inactive user: %s",
            email_value
        )
        return success_message

    if not user.is_verified:
        logger.warning(
            "Password reset requested for unverified user: %s",
            email_value
        )
        return success_message

    # Generate password reset token
    reset_token, token_expires_at = generate_password_reset_token()

    # Update user with reset token
    user.reset_password_token = reset_token
    user.reset_password_token_expires_at = token_expires_at
    db.commit()

    # Build reset link for use in the email and in debug
    base = settings.EMAIL_VERIFICATION_BASE_URL or ""
    reset_link = (
        f"{base.rstrip('/')}/reset-password?token={reset_token}"
    )

    # Send password reset email asynchronously
    try:
        send_password_reset_email_task.delay(
            email=user.email,
            token=reset_token,
            full_name=user.full_name,
            base_url=(
                settings.EMAIL_VERIFICATION_BASE_URL or "http://localhost:5173"
            )
        )
        logger.info(
            "Password reset email task queued for %s", user.email
        )
    except Exception as e:
        logger.warning(
            "Failed to queue password reset email for %s: %s",
            user.email, str(e)
        )

    # Log password reset action for audit
    logger.info(
        "Password reset requested for user: %s (tenant: %s)",
        user.email, user.tenant_id
    )

    # For non-production or test runs, expose the link in a header
    env = os.environ.get("TESTING") or settings.ENVIRONMENT
    if env and env != "production":
        response.headers["X-Reset-Link"] = reset_link

    return success_message


@router.post("/reset-password")
@limiter.limit("5/hour")
def reset_password(
    request: Request,
    reset_request: ResetPasswordRequest,
    db: Session = Depends(get_db)
):
    """
    Reset password using reset token.

    - Validates the reset token
    - Checks token expiration
    - Updates password (hashed)
    - Invalidates the reset token
    - Logs password reset action

    Args:
        reset_request: Reset token and new password

    Returns:
        Success message
    """
    # Find user by reset token
    user = db.query(UserModel).filter(
        UserModel.reset_password_token == reset_request.token
    ).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )

    # Check if token has expired
    if (
        user.reset_password_token_expires_at
        and user.reset_password_token_expires_at < datetime.now(timezone.utc)
    ):
        # Clear expired token
        user.reset_password_token = None
        user.reset_password_token_expires_at = None
        db.commit()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset token has expired.\
                Please request a new password reset."
        )

    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )

    if not user.is_verified:
        user.reset_password_token = None
        user.reset_password_token_expires_at = None
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )

    # Update password with new hashed password
    user.hashed_password = get_password_hash(reset_request.new_password)

    # Invalidate the reset token
    user.reset_password_token = None
    user.reset_password_token_expires_at = None

    db.commit()
    db.refresh(user)

    # Log password reset action for audit
    logger.info(
        "Password successfully reset for user: %s (tenant: %s)",
        user.email, user.tenant_id
    )

    return {
        "message": "Password has been reset successfully.\
            You can now log in with your new password.",
        "email": user.email
    }


@router.post("/force-change-password")
@limiter.limit("5/minute")
def force_change_password(
    request: Request,
    change_request: ForceChangePasswordRequest,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Force password change for users who must change password on first login.

    - Validates current (temporary) password
    - Updates password with new user-chosen password
    - Clears must_change_password flag
    - Logs password change action

    This endpoint is used when a user is created by an owner and must
    change their temporary password before accessing the system.

    Args:
        change_request: Current password and new password

    Returns:
        Success message
    """
    # Ensure this endpoint is only usable when a password change is required
    if not current_user.must_change_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password change is not required for this account"
        )

    # Check if user is active
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )

    # Verify current password
    if not verify_password(
        change_request.current_password, current_user.hashed_password
    ):
        log_auth_event(
            db=db,
            request=request,
            action=AuditAction.PASSWORD_CHANGE_FAILED,
            user_id=current_user.id,
            tenant_id=current_user.tenant_id,
            status="failure",
            description="Failed password change - incorrect current password"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect current password"
        )

    # Ensure new password is different from current
    if verify_password(change_request.new_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be different from current password"
        )

    # Update password
    current_user.hashed_password = get_password_hash(change_request.new_password)
    current_user.must_change_password = False

    db.commit()
    db.refresh(current_user)

    # Log password change action
    log_auth_event(
        db=db,
        request=request,
        action=AuditAction.PASSWORD_CHANGED,
        user_id=current_user.id,
        tenant_id=current_user.tenant_id,
        description=f"Password changed successfully for user {current_user.email}"
    )

    logger.info(
        "Password changed for user: %s (tenant: %s) - "
        "must_change_password cleared",
        current_user.email, current_user.tenant_id
    )

    return {
        "message": "Password changed successfully. You can now access "
                   "the system with your new password.",
        "email": current_user.email
    }
