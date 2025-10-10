"""
Authentication endpoints for user registration, login, and token refresh.
Implements JWT-based authentication with secure password handling.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.db.session import get_db
from app.models.user import User as UserModel
from app.schemas.user import UserCreate, User, Token
from app.core.security import (
    verify_password, get_password_hash,
    create_access_token, create_refresh_token, decode_token
)
from app.core.rate_limit import limiter

router = APIRouter()


@router.post("/register", response_model=User, status_code=201)
@limiter.limit("5/minute")
def register(
    request: Request,
    user_in: UserCreate,
    db: Session = Depends(get_db)
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
            tenant_id=user_in.tenant_id
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create user. Email may already exist."
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
