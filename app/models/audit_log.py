"""
Audit Log model for tracking critical operations.
Provides comprehensive audit trail for security and compliance.
"""
from app.models.general_model import Gen_Model, Base
from sqlalchemy import Column, String, Text, ForeignKey, Index, Enum
import enum


class AuditAction(str, enum.Enum):
    """
    Enumeration of auditable actions.
    """
    # Authentication events
    LOGIN = "login"
    LOGOUT = "logout"
    LOGIN_FAILED = "login_failed"
    LOGIN_THROTTLED = "login_throttled"
    LOGIN_EXCESSIVE_FAILURES = "login_excessive_failures"
    EMAIL_VERIFIED = "email_verified"
    TOKEN_REFRESH = "token_refresh"

    # User management events
    USER_CREATED = "user_created"
    USER_UPDATED = "user_updated"
    USER_DELETED = "user_deleted"
    USER_ROLE_CHANGED = "user_role_changed"
    PASSWORD_CHANGED = "password_changed"
    PASSWORD_CHANGE_FAILED = "password_change_failed"
    PASSWORD_RESET_REQUESTED = "password_reset_requested"
    PASSWORD_RESET_COMPLETED = "password_reset_completed"

    # Tenant management events
    TENANT_CREATED = "tenant_created"
    TENANT_UPDATED = "tenant_updated"
    TENANT_DELETED = "tenant_deleted"

    # Invoice management events
    INVOICE_CREATED = "invoice_created"
    INVOICE_UPDATED = "invoice_updated"
    INVOICE_DELETED = "invoice_deleted"
    INVOICE_STATUS_CHANGED = "invoice_status_changed"

    # Data export events
    DATA_EXPORTED = "data_exported"
    INVOICE_PDF_GENERATED = "invoice_pdf_generated"


class ResourceType(str, enum.Enum):
    """
    Enumeration of resource types that can be audited.
    """
    USER = "user"
    TENANT = "tenant"
    INVOICE = "invoice"
    INVOICE_ITEM = "invoice_item"
    AUTH = "auth"
    EXPORT = "export"


class AuditLog(Gen_Model, Base):
    """
    Audit log model for tracking critical operations.

    Attributes:
        user_id: ID of the user who performed the action (nullable for
                 failed logins)
        tenant_id: Associated tenant for multi-tenant isolation
        action: Type of action performed (from AuditAction enum)
        resource_type: Type of resource affected (from ResourceType enum)
        resource_id: ID of the affected resource (nullable for actions
                     without specific resource)
        ip_address: IP address of the client that initiated the action
        user_agent: User agent string of the client
        changes: JSON string containing before/after state for updates
        description: Human-readable description of the action
        status: Status of the action (success/failure)
    """
    __tablename__ = "audit_logs"

    user_id = Column(String(60), ForeignKey("users.id"), nullable=True,
                     index=True)
    tenant_id = Column(String(60), ForeignKey("tenants.id"), nullable=True,
                       index=True)
    action = Column(Enum(AuditAction), nullable=False, index=True)
    resource_type = Column(Enum(ResourceType), nullable=False, index=True)
    resource_id = Column(String(60), nullable=True, index=True)
    ip_address = Column(String(45), nullable=True)  # IPv6 max length
    user_agent = Column(String(500), nullable=True)
    changes = Column(Text, nullable=True)  # JSON string for before/after
    description = Column(Text, nullable=True)
    status = Column(String(20), nullable=False, default="success")

    # Composite indexes for common queries
    __table_args__ = (
        Index('idx_audit_tenant_action', 'tenant_id', 'action'),
        Index('idx_audit_user_action', 'user_id', 'action'),
        Index('idx_audit_resource', 'resource_type', 'resource_id'),
        Index('idx_audit_created_at', 'created_at'),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
