from app.models.general_model import Gen_Model, Base
from app.db.types import UTCDateTime
from sqlalchemy import Column, String, Boolean, ForeignKey, Enum, UniqueConstraint
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

    **Email Uniqueness Strategy**:
    - Superadmins (tenant_id=NULL): Email must be globally unique
    - Tenant users: Email must be unique per tenant (same email allowed across tenants)
    - Composite unique constraint on (email, tenant_id) ensures tenant-scoped uniqueness

    Attributes:
        email: User's email address (unique per tenant, globally unique for superadmins)
        full_name: User's full name
        hashed_password: Bcrypt hashed password for security
        role: User role (Owner, Admin, Manager, Attendant)
        tenant_id: Associated tenant for data isolation (NULL for superadmins)
                  Enables same email in different tenants
        is_active: Soft delete flag for GDPR right-to-be-forgotten
        is_verified: Email verification status
        is_superadmin: Platform-level super admin flag (default: False)
        verification_token: Token for email verification
        verification_token_expires_at: Expiration time for verification token
        reset_password_token: Token for password reset
        reset_password_token_expires_at: Expiration time for reset token
    """
    __tablename__ = "users"

    email = Column(String(255), nullable=False, index=True)
    full_name = Column(String(100), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.ATTENDANT)
    tenant_id = Column(String(60), ForeignKey("tenants.id"), nullable=True,
                       index=True)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    is_superadmin = Column(Boolean, default=False, index=True)
    must_change_password = Column(Boolean, default=False)
    verification_token = Column(String(255), nullable=True, index=True)
    verification_token_expires_at = Column(UTCDateTime(), nullable=True)
    reset_password_token = Column(String(255), nullable=True, index=True)
    reset_password_token_expires_at = Column(UTCDateTime(), nullable=True)

    # Composite unique constraint: (email, tenant_id) must be unique
    # This allows same email in different tenants while preventing duplicates within a tenant
    __table_args__ = (
        UniqueConstraint('email', 'tenant_id', name='uq_user_email_tenant'),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
