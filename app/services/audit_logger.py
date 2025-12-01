"""
Audit logging service for tracking critical operations.
Provides centralized functions for creating audit log entries.
"""
import json
import logging
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from fastapi import Request

from app.models.audit_log import (
    AuditLog as AuditLogModel,
    AuditAction,
    ResourceType
)

logger = logging.getLogger(__name__)


def get_client_ip(request: Request) -> Optional[str]:
    """
    Extract client IP address from request.
    Handles proxy headers (X-Forwarded-For, X-Real-IP).
    """
    # Check for proxy headers first
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # X-Forwarded-For can contain multiple IPs, take the first one
        return forwarded_for.split(",")[0].strip()

    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()

    # Fallback to direct client IP
    if request.client:
        return request.client.host

    return None


def get_user_agent(request: Request) -> Optional[str]:
    """Extract user agent string from request."""
    return request.headers.get("User-Agent")


def create_audit_log(
    db: Session,
    action: AuditAction,
    resource_type: ResourceType,
    user_id: Optional[str] = None,
    tenant_id: Optional[str] = None,
    resource_id: Optional[str] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    changes: Optional[Dict[str, Any]] = None,
    description: Optional[str] = None,
    status: str = "success"
) -> AuditLogModel:
    """
    Create an audit log entry.

    Args:
        db: Database session
        action: Type of action performed
        resource_type: Type of resource affected
        user_id: ID of user who performed the action (optional)
        tenant_id: Associated tenant ID (optional)
        resource_id: ID of affected resource (optional)
        ip_address: Client IP address (optional)
        user_agent: Client user agent (optional)
        changes: Dictionary containing before/after state (optional)
        description: Human-readable description (optional)
        status: Status of the action (default: "success")

    Returns:
        Created AuditLog instance
    """
    try:
        # Convert changes dictionary to JSON string
        changes_json = None
        if changes:
            changes_json = json.dumps(changes, default=str)

        audit_log = AuditLogModel(
            user_id=user_id,
            tenant_id=tenant_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            ip_address=ip_address,
            user_agent=user_agent,
            changes=changes_json,
            description=description,
            status=status
        )

        db.add(audit_log)
        db.commit()
        db.refresh(audit_log)

        logger.info(
            f"Audit log created: {action.value} on {resource_type.value} "
            f"by user {user_id or 'anonymous'}"
        )

        return audit_log
    except Exception as e:
        logger.error(f"Failed to create audit log: {str(e)}")
        db.rollback()
        # Don't raise exception - audit logging should not break main flow
        return None


def log_auth_event(
    db: Session,
    request: Request,
    action: AuditAction,
    user_id: Optional[str] = None,
    tenant_id: Optional[str] = None,
    status: str = "success",
    description: Optional[str] = None
) -> AuditLogModel:
    """
    Log authentication-related events.

    Args:
        db: Database session
        request: FastAPI request object
        action: Authentication action (LOGIN, LOGOUT, LOGIN_FAILED, etc.)
        user_id: User ID (optional for failed logins)
        tenant_id: Tenant ID (optional)
        status: Status of the action
        description: Additional description

    Returns:
        Created AuditLog instance
    """
    return create_audit_log(
        db=db,
        action=action,
        resource_type=ResourceType.AUTH,
        user_id=user_id,
        tenant_id=tenant_id,
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
        description=description,
        status=status
    )


def log_user_event(
    db: Session,
    request: Request,
    action: AuditAction,
    resource_id: str,
    user_id: Optional[str] = None,
    tenant_id: Optional[str] = None,
    changes: Optional[Dict[str, Any]] = None,
    description: Optional[str] = None
) -> AuditLogModel:
    """
    Log user management events.

    Args:
        db: Database session
        request: FastAPI request object
        action: User action (USER_CREATED, USER_UPDATED, etc.)
        resource_id: ID of the affected user
        user_id: ID of user performing the action
        tenant_id: Tenant ID
        changes: Before/after state for updates
        description: Additional description

    Returns:
        Created AuditLog instance
    """
    return create_audit_log(
        db=db,
        action=action,
        resource_type=ResourceType.USER,
        user_id=user_id,
        tenant_id=tenant_id,
        resource_id=resource_id,
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
        changes=changes,
        description=description
    )


def log_tenant_event(
    db: Session,
    request: Request,
    action: AuditAction,
    resource_id: str,
    user_id: Optional[str] = None,
    tenant_id: Optional[str] = None,
    changes: Optional[Dict[str, Any]] = None,
    description: Optional[str] = None
) -> AuditLogModel:
    """
    Log tenant management events.

    Args:
        db: Database session
        request: FastAPI request object
        action: Tenant action (TENANT_CREATED, TENANT_UPDATED, etc.)
        resource_id: ID of the affected tenant
        user_id: ID of user performing the action
        tenant_id: Tenant ID (same as resource_id for tenant events)
        changes: Before/after state for updates
        description: Additional description

    Returns:
        Created AuditLog instance
    """
    return create_audit_log(
        db=db,
        action=action,
        resource_type=ResourceType.TENANT,
        user_id=user_id,
        tenant_id=tenant_id,
        resource_id=resource_id,
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
        changes=changes,
        description=description
    )


def log_invoice_event(
    db: Session,
    request: Request,
    action: AuditAction,
    resource_id: str,
    user_id: Optional[str] = None,
    tenant_id: Optional[str] = None,
    changes: Optional[Dict[str, Any]] = None,
    description: Optional[str] = None
) -> AuditLogModel:
    """
    Log invoice management events.

    Args:
        db: Database session
        request: FastAPI request object
        action: Invoice action (INVOICE_CREATED, INVOICE_STATUS_CHANGED, etc.)
        resource_id: ID of the affected invoice
        user_id: ID of user performing the action
        tenant_id: Tenant ID
        changes: Before/after state for updates
        description: Additional description

    Returns:
        Created AuditLog instance
    """
    return create_audit_log(
        db=db,
        action=action,
        resource_type=ResourceType.INVOICE,
        user_id=user_id,
        tenant_id=tenant_id,
        resource_id=resource_id,
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
        changes=changes,
        description=description
    )


def log_export_event(
    db: Session,
    request: Request,
    user_id: str,
    tenant_id: str,
    description: str,
    resource_id: Optional[str] = None
) -> AuditLogModel:
    """
    Log data export events.

    Args:
        db: Database session
        request: FastAPI request object
        user_id: ID of user performing the export
        tenant_id: Tenant ID
        description: Description of what was exported
        resource_id: Optional resource ID (e.g., invoice ID for PDF export)

    Returns:
        Created AuditLog instance
    """
    action = (AuditAction.INVOICE_PDF_GENERATED
              if "PDF" in description or "pdf" in description
              else AuditAction.DATA_EXPORTED)

    return create_audit_log(
        db=db,
        action=action,
        resource_type=ResourceType.EXPORT,
        user_id=user_id,
        tenant_id=tenant_id,
        resource_id=resource_id,
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
        description=description
    )
