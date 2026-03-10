"""
Authentication endpoints for user registration, login, and token refresh.
Implements JWT-based authentication with secure password handling.
"""
from datetime import datetime, timezone
import logging
import os
from typing import Optional
import json
from urllib.parse import parse_qs
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi import status, Request, Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from pydantic import BaseModel, EmailStr
from app.db.session import get_db
from app.models.user import User as UserModel
from app.models.tenant import Tenant as TenantModel
from app.schemas.user import UserCreate, User, Token
from app.schemas.user import ResetPasswordRequest, RefreshTokenRequest
from app.core.security import verify_password, get_password_hash
from app.core.security import create_access_token, create_refresh_token
from app.core.security import decode_token, generate_verification_token
from app.core.security import generate_password_reset_token
from app.core.rate_limit import limiter
from app.core.config import settings
from app.core.login_throttle import get_login_throttle
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
    db: Session = Depends(get_db),
):
    """
    Register a new user.

    - Validates that email is unique
    - Hashes password using bcrypt
    - Associates user with tenant for data isolation (unless superadmin)
    - Returns user without password
    """
    existing_user = db.query(UserModel).filter(
        UserModel.email == user_in.email
    ).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Validate tenant_id requirement for non-superadmin users
    if not user_in.is_superadmin and not user_in.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="tenant_id is required for non-superadmin users"
        )

    try:
        hashed_password = get_password_hash(user_in.password)
        db_user = UserModel(
            email=user_in.email,
            full_name=user_in.full_name,
            hashed_password=hashed_password,
            role=user_in.role,
            tenant_id=user_in.tenant_id,
            is_superadmin=user_in.is_superadmin,
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


@router.post("/login", response_model=Token)
@limiter.limit("10/minute")
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Login endpoint for OAuth2 password flow with progressive throttling.

    - Validates email and password
    - Implements progressive delay based on failed attempts (OWASP ASVS)
    - Returns JWT access, refresh tokens and expires_in
    - Access token expires in configured time (default: 30 min)
    - Refresh token expires in configured time (default: 7 days)

    Progressive delay policy:
    - 1-3 attempts: No delay
    - 4-5 attempts: Short delay (default 2s)
    - 6-8 attempts: Medium delay (default 30s)
    - 9+ attempts: Long cooldown (default 15min)
    """
    throttle = get_login_throttle()
    email = form_data.username.lower()

    # Query user using case-insensitive comparison
    user = db.query(UserModel).filter(
        UserModel.email.ilike(email)
    ).first()

    # Validate credentials
    credentials_valid = user and verify_password(
        form_data.password, user.hashed_password
    )

    # Handle failed authentication
    if not credentials_valid:
        # Record failed attempt
        new_count = throttle.record_failed_attempt(email)

        # Log failed login attempt with throttle info
        log_auth_event(
            db=db,
            request=request,
            action=AuditAction.LOGIN_FAILED,
            user_id=user.id if user else None,
            tenant_id=user.tenant_id if user else None,
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
                user_id=user.id if user else None,
                tenant_id=user.tenant_id if user else None,
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
                user_id=user.id if user else None,
                tenant_id=user.tenant_id if user else None,
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

    # Credentials valid - check if user is active
    if not user.is_active:
        # Record as failed attempt to prevent enumeration
        new_count = throttle.record_failed_attempt(email)

        # Apply delay for inactive account (constant-time)
        await throttle.apply_delay(email, new_count)

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

        # Generic error message to avoid account enumeration
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if tenant is active (skip for superadmins)
    if user.tenant_id and not user.is_superadmin:
        tenant = db.query(TenantModel).filter(
            TenantModel.id == user.tenant_id
        ).first()
        if not tenant or not tenant.is_active:
            # Record as failed attempt
            new_count = throttle.record_failed_attempt(email)
            await throttle.apply_delay(email, new_count)

            log_auth_event(
                db=db,
                request=request,
                action=AuditAction.LOGIN_FAILED,
                user_id=user.id,
                tenant_id=user.tenant_id,
                status="failure",
                description="Login attempt for user in deactivated tenant"
            )

            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Your organization has been deactivated",
            )

    # Successful authentication - clear throttle counters
    throttle.clear_failed_attempts(email)

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
        "expires_in": settings.ACCESS_TOKEN_EXPIRATION * 60
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
            detail="Email is already verified.\
                You can now log in to your account."
        )

    # Check if token has expired
    if (
            user.verification_token_expires_at
            and user.verification_token_expires_at < datetime.now(timezone.utc)
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification token has expired.\
                Please request a new verification email."
        )

    # Mark user as verified and clear token
    user.is_verified = True
    user.verification_token = None
    user.verification_token_expires_at = None
    db.commit()
    db.refresh(user)

    # Generate tokens (same as login)
    token_data = {
        "sub": user.id,
        "tenant_id": user.tenant_id,
        "role": user.role.value,
        "is_superadmin": user.is_superadmin
    }
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    # Optionally, log the verification event
    # log_auth_event(
    #     db=db,
    #     request=request,
    #     action=AuditAction.EMAIL_VERIFIED,
    #     user_id=user.id,
    #     tenant_id=user.tenant_id,
    #     description=

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
    # Find user by email
    user = db.query(UserModel).filter(
        UserModel.email == resend_request.email
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
async def forgot_password(
    request: Request,
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
    # Read raw body once and log it
    try:
        raw_body = await request.body()
    except Exception:
        raw_body = b""

    content_type = request.headers.get("content-type", "")
    logger.debug("forgot-password Content-Type: %s", content_type)
    logger.debug("forgot-password raw body: %s", raw_body.decode(
        "utf-8", errors="replace"
    ))

    # Parse email from JSON or form-encoded body
    email_value: Optional[str] = None
    body_text = raw_body.decode("utf-8", errors="replace")
    if "application/json" in content_type:
        try:
            body_json = json.loads(body_text) if body_text else {}
            email_value = body_json.get("email")
        except Exception:
            email_value = None
    elif "application/x-www-form-urlencoded" in content_type:
        parsed = parse_qs(body_text)
        vals = parsed.get("email")
        if vals:
            email_value = vals[0]
    else:
        # Try JSON as fallback
        try:
            body_json = json.loads(body_text) if body_text else {}
            email_value = body_json.get("email")
        except Exception:
            email_value = None

    if not email_value:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Email is required",
        )

    # Find user by email
    user = db.query(UserModel).filter(
        UserModel.email == email_value
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
