from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, EmailStr, ConfigDict
from decimal import Decimal


class TenantBase(BaseModel):
    """
    Base tenant schema with common tenant attributes.

    Tenants represent organizations using the platform. Each tenant has complete
    data isolation and can customize branding, currency, tax settings, and invoice formatting.
    """

    name: str = Field(..., min_length=1, max_length=100, description="Tenant name")
    domain: Optional[str] = Field(
        None, min_length=3, max_length=100, description="Unique tenant domain"
    )
    description: Optional[str] = Field(
        None, max_length=500, description="Tenant description"
    )
    plan_type: str = Field("free", description="Tenant plan type")
    default_currency: Optional[str] = Field(
        "USD", description="Default currency (NGN, USD, GBP, EUR)"
    )
    tax_rate: Optional[Decimal] = Field(
        None,
        ge=0,
        le=100,
        description="Tax/VAT rate as percentage (0-100, null for tax-free)",
    )
    tax_label: Optional[str] = Field(
        None, max_length=50, description="Tax label (e.g., 'VAT', 'GST', 'Sales Tax')"
    )
    address: Optional[str] = Field(
        None, max_length=1000, description="Tenant business address for invoices"
    )
    phone: Optional[str] = Field(
        None, max_length=20, description="Tenant contact phone number"
    )
    email: Optional[EmailStr] = Field(
        None, description="Tenant contact email for invoices"
    )
    invoice_number_prefix: Optional[str] = Field(
        "INV", max_length=20, description="Custom prefix for invoice numbers"
    )
    invoice_number_format: Optional[str] = Field(
        "{prefix}-{date}-{sequence:04d}",
        max_length=100,
        description=(
            "Format string for invoice numbers. "
            "Supported placeholders: {prefix}, {date}, {sequence}"
        ),
    )


class TenantCreate(TenantBase):
    """Schema for creating a new tenant. Inherits all fields from TenantBase."""

    pass


class TenantUpdate(BaseModel):
    """
    Schema for updating tenant information.

    All fields are optional. Only provided fields will be updated.
    Used by tenant owners and admins to modify tenant settings.
    """

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    domain: Optional[str] = Field(None, min_length=3, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    plan_type: Optional[str] = None
    is_active: Optional[bool] = None
    default_currency: Optional[str] = Field(
        None, description="Default currency (NGN, USD, GBP, EUR)"
    )
    tax_rate: Optional[Decimal] = Field(
        None,
        ge=0,
        le=100,
        description="Tax/VAT rate as percentage (0-100, null for tax-free)",
    )
    tax_label: Optional[str] = Field(
        None, max_length=50, description="Tax label (e.g., 'VAT', 'GST', 'Sales Tax')"
    )
    address: Optional[str] = Field(
        None, max_length=1000, description="Tenant business address for invoices"
    )
    phone: Optional[str] = Field(
        None, max_length=20, description="Tenant contact phone number"
    )
    email: Optional[EmailStr] = Field(
        None, description="Tenant contact email for invoices"
    )
    invoice_number_prefix: Optional[str] = Field(
        None, max_length=20, description="Custom prefix for invoice numbers"
    )
    invoice_number_format: Optional[str] = Field(
        None,
        max_length=100,
        description=(
            "Format string for invoice numbers. "
            "Supported placeholders: {prefix}, {date}, {sequence}"
        ),
    )


class TenantInDB(TenantBase):
    """
    Complete tenant schema as stored in the database.

    Includes system-generated fields like ID, timestamps, and invoice sequence counter.
    """

    id: str
    is_active: bool
    logo_url: Optional[str] = None
    invoice_number_sequence: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class Tenant(TenantInDB):
    """Public tenant schema returned by API endpoints."""

    pass


# Schema for owner user info in combined registration
class OwnerCreate(BaseModel):
    """
    Schema for owner user information during tenant registration.

    Used when registering a new tenant with an owner account in a single operation.
    """

    full_name: str = Field(
        ..., min_length=1, max_length=100, description="Owner's full name"
    )
    email: EmailStr = Field(..., description="Owner's email address")
    password: str = Field(
        ...,
        min_length=8,
        max_length=100,
        description="Owner password (min 8 characters)",
    )


# Schema for combined tenant + owner registration request
class TenantRegister(TenantBase):
    """
    Schema for registering a new tenant with an owner account.

    Combines tenant information and owner user details for streamlined onboarding.
    This creates both a tenant organization and its first user (owner) in one request.
    """

    owner: OwnerCreate = Field(..., description="Owner user information")


# Schema for combined tenant + owner response
class TenantWithOwner(BaseModel):
    """
    Response schema for tenant registration endpoint.

    Returns both the created tenant and owner information (without sensitive data).
    """

    tenant: Tenant
    owner: dict  # We'll return owner info without sensitive data

    model_config = ConfigDict(from_attributes=True)
