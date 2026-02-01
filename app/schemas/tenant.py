from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, EmailStr, ConfigDict, field_validator
from decimal import Decimal
import re


# Regex pattern for hex color validation
HEX_COLOR_PATTERN = re.compile(r'^#[0-9a-fA-F]{6}$')


def validate_hex_color(v: Optional[str]) -> Optional[str]:
    """Validate hex color format."""
    if v is None:
        return v
    if not HEX_COLOR_PATTERN.match(v):
        raise ValueError('Invalid hex color format. Use format like #2563eb')
    return v


class TenantBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100,
                      description="Tenant name"
                      )
    domain: Optional[str] = Field(None, min_length=3, max_length=100,
                                  description="Unique tenant domain"
                                  )
    business_registration_number: Optional[str] = Field(
        None, min_length=3, max_length=100,
        description="Unique business registration number"
    )
    description: Optional[str] = Field(None, max_length=500,
                                       description="Tenant description"
                                       )
    plan_type: str = Field(
        "Standard",
        description="Tenant plan type (only super admin can modify)"
    )
    default_currency: Optional[str] = Field(
        "NGN", description="Default currency (NGN, USD, GBP, EUR)"
    )
    tax_rate: Optional[Decimal] = Field(
        None, ge=0, le=100,
        description="Tax/VAT rate as percentage (0-100, null for tax-free)"
    )
    tax_label: Optional[str] = Field(
        None, max_length=50,
        description="Tax label (e.g., 'VAT', 'GST', 'Sales Tax')"
    )
    address: Optional[str] = Field(
        None, max_length=1000,
        description="Tenant business address for invoices"
    )
    phone: Optional[str] = Field(
        None, max_length=20,
        description="Tenant contact phone number"
    )
    email: Optional[EmailStr] = Field(
        None, description="Tenant contact email for invoices"
    )
    invoice_number_prefix: Optional[str] = Field(
        "INV", max_length=20,
        description="Custom prefix for invoice numbers"
    )
    invoice_number_format: Optional[str] = Field(
        "{prefix}-{date}-{sequence:04d}", max_length=100,
        description=(
            "Format string for invoice numbers. "
            "Supported placeholders: {prefix}, {date}, {sequence}"
        )
    )
    primary_color: Optional[str] = Field(
        "#2563eb", max_length=7,
        description="Primary brand color for PDF (hex format, e.g., '#2563eb')"
    )
    secondary_color: Optional[str] = Field(
        "#1e40af", max_length=7,
        description="Secondary brand color for PDF (hex, e.g., '#1e40af')"
    )
    custom_footer: Optional[str] = Field(
        None, max_length=500,
        description="Custom footer text for invoices"
    )
    draft_watermark_enabled: Optional[bool] = Field(
        True,
        description="Whether to show DRAFT watermark on draft invoices"
    )

    @field_validator('primary_color', 'secondary_color', mode='before')
    @classmethod
    def validate_colors(cls, v):
        return validate_hex_color(v)


class TenantCreate(TenantBase):
    pass


class TenantUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    domain: Optional[str] = Field(None, min_length=3, max_length=100)
    business_registration_number: Optional[str] = Field(
        None, min_length=3, max_length=100,
        description="Unique business registration number"
    )
    description: Optional[str] = Field(None, max_length=500)
    is_active: Optional[bool] = None
    default_currency: Optional[str] = Field(
        None, description="Default currency (NGN, USD, GBP, EUR)"
    )
    tax_rate: Optional[Decimal] = Field(
        None, ge=0, le=100,
        description="Tax/VAT rate as percentage (0-100, null for tax-free)"
    )
    tax_label: Optional[str] = Field(
        None, max_length=50,
        description="Tax label (e.g., 'VAT', 'GST', 'Sales Tax')"
    )
    address: Optional[str] = Field(
        None, max_length=1000,
        description="Tenant business address for invoices"
    )
    phone: Optional[str] = Field(
        None, max_length=20,
        description="Tenant contact phone number"
    )
    email: Optional[EmailStr] = Field(
        None, description="Tenant contact email for invoices"
    )
    invoice_number_prefix: Optional[str] = Field(
        None, max_length=20,
        description="Custom prefix for invoice numbers"
    )
    invoice_number_format: Optional[str] = Field(
        None, max_length=100,
        description=(
            "Format string for invoice numbers. "
            "Supported placeholders: {prefix}, {date}, {sequence}"
        )
    )
    primary_color: Optional[str] = Field(
        None, max_length=7,
        description="Primary brand color for PDF (hex format, e.g., '#2563eb')"
    )
    secondary_color: Optional[str] = Field(
        None, max_length=7,
        description="Secondary brand color for PDF (hex, e.g., '#1e40af')"
    )
    custom_footer: Optional[str] = Field(
        None, max_length=500,
        description="Custom footer text for invoices"
    )
    draft_watermark_enabled: Optional[bool] = Field(
        None,
        description="Whether to show DRAFT watermark on draft invoices"
    )

    @field_validator('primary_color', 'secondary_color', mode='before')
    @classmethod
    def validate_colors(cls, v):
        return validate_hex_color(v)


class TenantInDB(TenantBase):
    id: str
    is_active: bool
    logo_url: Optional[str] = None
    invoice_number_sequence: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SuperAdminTenantUpdate(TenantUpdate):
    """Schema for super admin to update tenant, including plan_type."""
    plan_type: Optional[str] = Field(None, description="Tenant plan type")


class Tenant(TenantInDB):
    pass


# Schema for owner user info in combined registration
class OwnerCreate(BaseModel):
    full_name: str = Field(..., min_length=1, max_length=100,
                           description="Owner's full name")
    email: EmailStr = Field(..., description="Owner's email address")
    password: str = Field(..., min_length=8, max_length=100,
                          description="Owner password (min 8 characters)")

    @field_validator('password')
    @classmethod
    def password_strength(cls, v):
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain an uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain a lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain a digit')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>_\-+=]', v):
            raise ValueError('Password must contain a special character')
        return v


# Schema for combined tenant + owner registration request
class TenantRegister(TenantBase):
    owner: OwnerCreate = Field(..., description="Owner user information")


# Schema for combined tenant + owner response
class TenantWithOwner(BaseModel):
    tenant: Tenant
    owner: dict  # We'll return owner info without sensitive data

    model_config = ConfigDict(from_attributes=True)
