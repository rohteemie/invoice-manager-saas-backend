"""
Pydantic schemas for Audit Log API.
Defines request/response models for audit log operations.
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from app.models.audit_log import AuditAction, ResourceType


class AuditLogBase(BaseModel):
    """Base schema for audit log."""
    action: AuditAction
    resource_type: ResourceType
    resource_id: Optional[str] = None
    description: Optional[str] = None
    status: str = "success"


class AuditLogCreate(AuditLogBase):
    """Schema for creating an audit log entry."""
    user_id: Optional[str] = None
    tenant_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    changes: Optional[str] = None


class AuditLog(AuditLogBase):
    """Schema for audit log response."""
    id: str
    user_id: Optional[str]
    tenant_id: Optional[str]
    ip_address: Optional[str]
    user_agent: Optional[str]
    changes: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AuditLogFilter(BaseModel):
    """Schema for filtering audit logs."""
    user_id: Optional[str] = Field(None, description="Filter by user ID")
    tenant_id: Optional[str] = Field(None, description="Filter by tenant ID")
    action: Optional[AuditAction] = Field(None, description="Filter by action type")
    resource_type: Optional[ResourceType] = Field(None, description="Filter by resource type")
    resource_id: Optional[str] = Field(None, description="Filter by resource ID")
    status: Optional[str] = Field(None, description="Filter by status (success/failure)")
    start_date: Optional[datetime] = Field(None, description="Filter by start date")
    end_date: Optional[datetime] = Field(None, description="Filter by end date")
