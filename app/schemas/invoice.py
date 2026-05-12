import re
from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel, Field, EmailStr, field_validator, ConfigDict
from decimal import Decimal
from app.models.invoice import InvoiceStatus, Currency, PaymentMethod

ISO_DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")
ISO_DATE_ERROR_TEMPLATE = (
    "{field_name} must be a valid ISO 8601 date (YYYY-MM-DD)"
)


def validate_iso_date(value: Optional[str], field_name: str) -> Optional[str]:
    if value is None:
        return None
    error_message = ISO_DATE_ERROR_TEMPLATE.format(field_name=field_name)
    if not isinstance(value, str):
        raise ValueError(error_message)
    if not ISO_DATE_PATTERN.match(value):
        raise ValueError(error_message)
    try:
        date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(error_message) from exc
    return value


class InvoiceItemBase(BaseModel):
    """Base invoice item schema."""
    description: str = Field(..., min_length=1, max_length=255,
                             description="Item description")
    quantity: Decimal = Field(..., gt=0, description="Item quantity")
    unit_price: Decimal = Field(..., ge=0, description="Price per unit")


class InvoiceItemCreate(InvoiceItemBase):
    """Schema for creating invoice item."""
    pass


class InvoiceItemUpdate(BaseModel):
    """Schema for updating invoice item."""
    description: Optional[str] = Field(None, min_length=1, max_length=255)
    quantity: Optional[Decimal] = Field(None, gt=0)
    unit_price: Optional[Decimal] = Field(None, ge=0)


class InvoiceItemInDB(InvoiceItemBase):
    """Schema for invoice item in database."""
    id: str
    invoice_id: str
    total_price: Decimal
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)


class InvoiceItem(InvoiceItemInDB):
    """Public invoice item schema."""
    pass


class InvoiceBase(BaseModel):
    """
    Base invoice schema with common attributes.

    Note: Currency is always inherited from the tenant's default_currency
    setting and cannot be specified per invoice. Tax amounts are
    automatically calculated from the tenant's tax_rate.
    """
    customer_name: str = Field(..., min_length=1, max_length=100,
                               description="Customer name")
    customer_email: Optional[EmailStr] = Field(None,
                                               description="Customer email")
    customer_phone: Optional[str] = Field(None, max_length=20,
                                          description="Customer phone")
    customer_address: Optional[str] = Field(None, max_length=500,
                                            description="Customer address")
    issue_date: str = Field(..., description="Invoice issue date (ISO 8601)")
    due_date: Optional[str] = Field(
        None, description="Payment due date (ISO 8601)"
    )
    notes: Optional[str] = Field(
        None, max_length=1000, description="Additional notes"
    )


class InvoiceCreate(InvoiceBase):
    """Schema for creating a new invoice."""
    items: List[InvoiceItemCreate] = Field(
        ..., min_length=1, max_length=100, description="Invoice line items"
    )

    @field_validator('due_date', mode='before')
    @classmethod
    def validate_due_date(cls, v):
        return validate_iso_date(v, "due_date")


class InvoiceUpdate(BaseModel):
    """Schema for updating invoice information."""
    customer_name: Optional[str] = Field(
        None, min_length=1, max_length=100
    )
    customer_email: Optional[EmailStr] = None
    customer_phone: Optional[str] = Field(None, max_length=20)
    customer_address: Optional[str] = Field(None, max_length=500)
    issue_date: Optional[str] = None
    due_date: Optional[str] = None
    notes: Optional[str] = Field(None, max_length=1000)
    items: Optional[List[InvoiceItemCreate]] = Field(
        None, min_length=1, max_length=100
    )

    @field_validator('due_date', mode='before')
    @classmethod
    def validate_due_date(cls, v):
        return validate_iso_date(v, "due_date")


class InvoiceStatusUpdate(BaseModel):
    """Schema for updating invoice status."""
    status: InvoiceStatus = Field(..., description="New invoice status")
    payment_method: Optional[PaymentMethod] = Field(
        None,
        description="Payment method (required for PAID status)"
    )

    @field_validator('payment_method', mode='before')
    @classmethod
    def normalize_payment_method(cls, v):
        """Normalize payment method to lowercase for enum matching."""
        if v is None:
            return v
        if isinstance(v, str):
            # Convert to lowercase for case-insensitive matching
            normalized = v.lower()
            # Try to match with enum values
            try:
                return PaymentMethod(normalized)
            except ValueError:
                # Provide helpful error message with valid options
                valid_methods = [m.value for m in PaymentMethod]
                raise ValueError(
                    f"Invalid payment method '{v}'. "
                    f"Valid options are: {', '.join(valid_methods)}"
                )
        return v


class InvoiceInDB(InvoiceBase):
    """Schema for invoice in database."""
    id: str
    invoice_number: str
    tenant_id: str
    creator_id: str
    status: InvoiceStatus
    currency: Currency
    subtotal: Decimal
    tax_amount: Decimal
    discount_amount: Decimal
    total_amount: Decimal
    payment_method: Optional[PaymentMethod]
    paid_at: Optional[str]
    created_at: datetime
    updated_at: datetime
    items: List[InvoiceItem] = []

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)


class Invoice(InvoiceInDB):
    """Public invoice schema."""
    pass
