from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, EmailStr
from decimal import Decimal
from app.models.invoice import InvoiceStatus, Currency, PaymentMethod


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

    class Config:
        from_attributes = True


class InvoiceItem(InvoiceItemInDB):
    """Public invoice item schema."""
    pass


class InvoiceBase(BaseModel):
    """Base invoice schema with common attributes."""
    customer_name: str = Field(..., min_length=1, max_length=100,
                               description="Customer name")
    customer_email: Optional[EmailStr] = Field(None,
                                               description="Customer email")
    customer_phone: Optional[str] = Field(None, max_length=20,
                                          description="Customer phone")
    customer_address: Optional[str] = Field(None, max_length=500,
                                            description="Customer address")
    branch_id: Optional[str] = Field(None,
                                     description="Branch ID (optional)")
    currency: Optional[Currency] = Field(
        None, description="Currency code (defaults to tenant's default)"
    )
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
        ..., min_length=1, description="Invoice line items"
    )


class InvoiceUpdate(BaseModel):
    """Schema for updating invoice information."""
    customer_name: Optional[str] = Field(
        None, min_length=1, max_length=100
    )
    customer_email: Optional[EmailStr] = None
    customer_phone: Optional[str] = Field(None, max_length=20)
    customer_address: Optional[str] = Field(None, max_length=500)
    branch_id: Optional[str] = None
    currency: Optional[Currency] = None
    issue_date: Optional[str] = None
    due_date: Optional[str] = None
    notes: Optional[str] = Field(None, max_length=1000)
    items: Optional[List[InvoiceItemCreate]] = None


class InvoiceStatusUpdate(BaseModel):
    """Schema for updating invoice status."""
    status: InvoiceStatus = Field(..., description="New invoice status")
    payment_method: Optional[PaymentMethod] = Field(
        None,
        description="Payment method (required for PAID status)"
    )


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

    class Config:
        from_attributes = True


class Invoice(InvoiceInDB):
    """Public invoice schema."""
    pass
