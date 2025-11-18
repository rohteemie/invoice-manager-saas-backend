from app.models.general_model import Gen_Model, Base
from sqlalchemy import Column, String, Boolean, ForeignKey, Enum, DateTime
import enum


class UserRole(str, enum.Enum):
    """
    User role enumeration for RBAC.
    Roles hierarchy: Owner > Admin > Manager > Attendant
    """
    OWNER = "owner"
    ADMIN = "admin"
    MANAGER = "manager"
    ATTENDANT = "attendant"


class User(Gen_Model, Base):
    """
    User model for multi-tenant architecture with RBAC.

    Attributes:
        email: User's unique email address (GDPR-compliant identifier)
        full_name: User's full name
        hashed_password: Bcrypt hashed password for security
        role: User role (Owner, Admin, Manager, Attendant)
        tenant_id: Associated tenant for data isolation
        is_active: Soft delete flag for GDPR right-to-be-forgotten
        is_verified: Email verification status
        verification_token: Token for email verification
        verification_token_expires_at: Expiration time for verification
                                       token
        reset_password_token: Token for password reset
        reset_password_token_expires_at: Expiration time for reset token
        currency_preference: User's preferred currency for analytics
                            (NGN, USD, GBP, EUR) Defaults to NGN and
                            cannot be changed once set
    """
    __tablename__ = "users"

    email = Column(String(255), unique=True, nullable=False, index=True)
    full_name = Column(String(100), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.ATTENDANT)
    tenant_id = Column(String(60), ForeignKey("tenants.id"), nullable=False,
                       index=True)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    verification_token = Column(String(255), nullable=True, index=True)
    verification_token_expires_at = Column(DateTime, nullable=True)
    reset_password_token = Column(String(255), nullable=True, index=True)
    reset_password_token_expires_at = Column(DateTime, nullable=True)
    currency_preference = Column(String(3), nullable=False, default="NGN")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
