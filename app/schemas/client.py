from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class ClientBase(BaseModel):
    """Base client schema with common attributes."""
    name: str = Field(..., min_length=1, max_length=200,
                      description="Client's full name or company name")
    email: Optional[EmailStr] = Field(None,
                                      description="Client's email address")
    phone: Optional[str] = Field(None, max_length=50,
                                 description="Client's phone number")
    address: Optional[str] = Field(None, max_length=500,
                                   description="Client's physical address")
    tax_id: Optional[str] = Field(None, max_length=100,
                                  description="Client's tax ID "
                                              "(GDPR-sensitive)")


class ClientCreate(ClientBase):
    """Schema for creating a new client."""
    tenant_id: str = Field(..., description="Tenant ID for data isolation")


class ClientUpdate(BaseModel):
    """Schema for updating client information."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=50)
    address: Optional[str] = Field(None, max_length=500)
    tax_id: Optional[str] = Field(None, max_length=100)
    is_active: Optional[bool] = None


class ClientInDB(ClientBase):
    """Schema for client in database."""
    id: str
    tenant_id: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class Client(ClientInDB):
    """Public client schema."""
    pass
