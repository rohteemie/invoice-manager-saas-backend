from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from app.models.user import UserRole


class UserBase(BaseModel):
    """Base user schema with common attributes."""
    email: EmailStr = Field(..., description="User's email address")
    full_name: str = Field(..., min_length=1, max_length=100,
                           description="User's full name")
    role: UserRole = Field(default=UserRole.ATTENDANT,
                           description="User role for RBAC")


class UserCreate(UserBase):
    """
    Schema for creating a new user.
    
    Requires password and optional tenant_id. Super admins can be created without a tenant_id.
    Currency preference defaults to NGN and cannot be changed after account creation.
    """
    password: str = Field(
        ..., min_length=8, max_length=100,
        description="User password (min 8 characters)"
    )
    tenant_id: Optional[str] = Field(
        None,
        description="Tenant ID for data isolation (null for superadmins)"
    )
    currency_preference: Optional[str] = Field(
        "NGN",
        description="User's preferred currency (NGN, USD, GBP, EUR). "
                    "Defaults to NGN and cannot be changed once set."
    )
    is_superadmin: Optional[bool] = Field(
        False, description="Platform-level super admin flag"
    )


class UserUpdate(BaseModel):
    """Schema for updating user information."""
    full_name: Optional[str] = Field(None, min_length=1, max_length=100)
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None


class UserInDB(UserBase):
    """
    Complete user schema as stored in the database (without password hash).
    
    Includes all user fields including system-generated ones like ID and timestamps.
    The password hash is stored in the database model but excluded from this schema
    for security - it's never exposed through API responses.
    """
    id: str
    tenant_id: Optional[str]
    is_active: bool
    is_verified: bool
    is_superadmin: bool
    currency_preference: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class User(UserInDB):
    """
    Public user schema returned by API endpoints.
    
    This is the schema used in API responses. Password hash is never exposed.
    """
    pass


class UserLogin(BaseModel):
    """
    Schema for user login credentials.
    
    Used for authentication via the login endpoint.
    """
    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., description="User password")


class Token(BaseModel):
    """
    JWT token response schema.
    
    Returned after successful login or token refresh.
    Contains both access token (short-lived) and refresh token (long-lived).
    """
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    """
    JWT token payload schema.
    
    Internal schema representing the decoded JWT token contents.
    """
    sub: str  # User ID
    tenant_id: Optional[str]
    role: str
    is_superadmin: Optional[bool] = False
    exp: Optional[int] = None


class ForgotPasswordRequest(BaseModel):
    """
    Schema for forgot password request.
    
    Used to initiate password reset flow. An email with reset link is sent.
    """
    email: EmailStr = Field(..., description="User's email address")


class ResetPasswordRequest(BaseModel):
    """
    Schema for password reset request.
    
    Used to complete password reset with token received via email.
    """
    token: str = Field(..., description="Password reset token")
    new_password: str = Field(
        ...,
        min_length=8,
        max_length=100,
        description="New password (min 8 characters)"
    )
