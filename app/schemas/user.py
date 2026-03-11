from datetime import datetime
import re
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_validator
from app.models.user import UserRole


def validate_password_strength(v: str) -> str:
    if not re.search(r'[A-Z]', v):
        raise ValueError('Password must contain an uppercase letter')
    if not re.search(r'[a-z]', v):
        raise ValueError('Password must contain a lowercase letter')
    if not re.search(r'\d', v):
        raise ValueError('Password must contain a digit')
    if not re.search(r'[!@#$%^&*(),.?":{}|<>_\-+=]', v):
        raise ValueError('Password must contain a special character')
    return v


class UserBase(BaseModel):
    """Base user schema with common attributes."""
    email: EmailStr = Field(..., description="User's email address")
    full_name: str = Field(..., min_length=1, max_length=100,
                           description="User's full name")
    role: UserRole = Field(default=UserRole.ATTENDANT,
                           description="User role for RBAC")

    @field_validator('role', mode='before')
    @classmethod
    def normalize_role(cls, v):
        if isinstance(v, str):
            return v.lower()
        return v


class UserCreate(UserBase):
    """Schema for creating a new user."""
    password: str = Field(
        ..., min_length=8, max_length=100,
        description="User password (min 8 characters)"
    )
    tenant_id: Optional[str] = Field(
        None,
        description="Tenant ID for data isolation (null for superadmins)"
    )
    is_superadmin: Optional[bool] = Field(
        False, description="Platform-level super admin flag"
    )

    @field_validator('password')
    @classmethod
    def password_strength(cls, v: str) -> str:
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain an uppercase letter')
        return validate_password_strength(v)


class OwnerUserCreate(BaseModel):
    """Schema for owner creating users within their tenant."""
    email: EmailStr = Field(..., description="User's email address")
    full_name: str = Field(..., min_length=1, max_length=100,
                           description="User's full name")
    role: UserRole = Field(default=UserRole.ATTENDANT,
                           description="User role (cannot be OWNER)")
    password: str = Field(
        ..., min_length=8, max_length=100,
        description="User password (min 8 characters)"
    )

    @field_validator('role', mode='before')
    @classmethod
    def normalize_role(cls, v):
        if isinstance(v, str):
            return v.lower()
        return v

    @field_validator('role', mode='after')
    @classmethod
    def prevent_owner_role(cls, v):
        if v == UserRole.OWNER:
            raise ValueError('Cannot create user with OWNER role')
        return v

    @field_validator('password')
    @classmethod
    def password_strength(cls, v: str) -> str:
        return validate_password_strength(v)


class UserUpdate(BaseModel):
    """Schema for updating user information."""
    full_name: Optional[str] = Field(None, min_length=1, max_length=100)
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None

    @field_validator('role', mode='before')
    @classmethod
    def normalize_role(cls, v):
        if v is None:
            return v
        if isinstance(v, str):
            return v.lower()
        return v


class UserInDB(UserBase):
    """Schema for user in database."""
    id: str
    tenant_id: Optional[str]
    is_active: bool
    is_verified: bool
    is_superadmin: bool
    must_change_password: bool = False
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class User(UserInDB):
    """Public user schema (without password)."""
    pass


class UserLogin(BaseModel):
    """Schema for user login."""
    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., description="User password")


class Token(BaseModel):
    """JWT token response schema."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    requires_password_change: bool = False


class TokenPayload(BaseModel):
    """JWT token payload schema."""
    sub: str  # User ID
    tenant_id: Optional[str]
    role: str
    is_superadmin: Optional[bool] = False
    exp: Optional[int] = None


class ForgotPasswordRequest(BaseModel):
    """Schema for forgot password request."""
    email: EmailStr = Field(..., description="User's email address")


class ResetPasswordRequest(BaseModel):
    """Schema for reset password request."""
    token: str = Field(..., description="Password reset token")
    new_password: str = Field(
        ...,
        min_length=8,
        max_length=100,
        description="New password (min 8 characters)"
    )

    @field_validator('new_password')
    @classmethod
    def password_strength(cls, v: str) -> str:
        return validate_password_strength(v)


class RefreshTokenRequest(BaseModel):
    """Schema for refresh token request - sent in request body for security."""
    refresh_token: str = Field(..., description="JWT refresh token")


class ForceChangePasswordRequest(BaseModel):
    """Schema for force password change on first login."""
    current_password: str = Field(..., description="Current (temporary) password")
    new_password: str = Field(
        ...,
        min_length=8,
        max_length=100,
        description="New password (min 8 characters)"
    )

    @field_validator('new_password')
    @classmethod
    def password_strength(cls, v: str) -> str:
        return validate_password_strength(v)
