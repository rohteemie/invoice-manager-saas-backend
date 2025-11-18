"""
Authentication endpoints for user registration, login, and token refresh.
Implements JWT-based authentication with secure password handling.
"""
from datetime import datetime
import logging
import os

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    Request,
    Response,
)
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from pydantic import BaseModel, EmailStr
from app.db.session import get_db
from app.models.user import User as UserModel
from app.schemas.user import UserCreate, User, Token, ForgotPasswordRequest, ResetPasswordRequest
from app.core.security import (
    verify_password, get_password_hash,
    create_access_token, create_refresh_token, decode_token,
    generate_verification_token, generate_password_reset_token
)
from app.core.rate_limit import limiter
from app.core.email import send_verification_email, send_password_reset_email
from app.core.config import settings

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
    - Associates user with tenant for data isolation
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

    try:
        hashed_password = get_password_hash(user_in.password)
        db_user = UserModel(
            email=user_in.email,
            full_name=user_in.full_name,
            hashed_password=hashed_password,
            role=user_in.role,
            tenant_id=user_in.tenant_id,
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

        # Send verification email (best as background task in prod)
        sent = send_verification_email(
            email=db_user.email,
            token=verification_token,
            full_name=db_user.full_name,
            base_url=settings.EMAIL_VERIFICATION_BASE_URL,
        )

        if not sent:
            logger.warning(
                "Verification email not sent for %s", db_user.email
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
def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Login endpoint for OAuth2 password flow.

    - Validates email and password
    - Returns JWT access and refresh tokens
    - Access token expires in configured time (default: 30 min)
    - Refresh token expires in configured time (default: 7 days)
    """
    user = db.query(UserModel).filter(
        UserModel.email == form_data.username
    ).first()

    if not user or not verify_password(
        form_data.password, user.hashed_password
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user account"
        )

    token_data = {
        "sub": user.id,
        "tenant_id": user.tenant_id,
        "role": user.role.value
    }

    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@router.post("/refresh", response_model=Token)
@limiter.limit("20/minute")
def refresh_token(
    request: Request,
    refresh_token: str,
    db: Session = Depends(get_db)
):
    """
    Refresh access token using refresh token.

    - Validates refresh token
    - Issues new access and refresh tokens
    - Maintains user session security
    """
    payload = decode_token(refresh_token)
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
        "role": user.role.value
    }

    new_access_token = create_access_token(token_data)
    new_refresh_token = create_refresh_token(token_data)

    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer"
    }


@router.post("/verify-email")
@limiter.limit("10/minute")
def verify_email(
    request: Request,
    token: str,
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
            and user.verification_token_expires_at < datetime.now()
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

    return {
        "message": "Email verified successfully",
        "email": user.email,
        "is_verified": user.is_verified
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

    # Send verification email
    send_verification_email(
        email=user.email,
        token=verification_token,
        full_name=user.full_name,
        base_url=settings.EMAIL_VERIFICATION_BASE_URL
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
    forgot_request: ForgotPasswordRequest,
    response: Response,
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
    # Find user by email
    user = db.query(UserModel).filter(
        UserModel.email == forgot_request.email
    ).first()

    # Always return success message to prevent email enumeration
    success_message = {
        "message": "If the email exists in our system, "
                   "a password reset link will be sent.",
        "email": forgot_request.email
    }

    if not user:
        # Don't reveal whether user exists for security
        logger.info(
            "Password reset requested for non-existent email: %s",
            forgot_request.email
        )
        return success_message

    # Check if user is active
    if not user.is_active:
        logger.warning(
            "Password reset requested for inactive user: %s",
            forgot_request.email
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

    # Send password reset email
    sent = send_password_reset_email(
        email=user.email,
        token=reset_token,
        full_name=user.full_name,
        base_url=settings.EMAIL_VERIFICATION_BASE_URL
    )

    if not sent:
        logger.warning(
            "Password reset email not sent for %s", user.email
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
            and user.reset_password_token_expires_at < datetime.now()
    ):
        # Clear expired token
        user.reset_password_token = None
        user.reset_password_token_expires_at = None
        db.commit()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset token has expired. Please request a new password reset."
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
        "message": "Password has been reset successfully. You can now log in with your new password.",
        "email": user.email
    }
