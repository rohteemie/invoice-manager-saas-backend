from app.models.general_model import Gen_Model, Base
from sqlalchemy import Column, String, Numeric, ForeignKey, Enum, Text
from sqlalchemy.orm import relationship
from typing import Optional, Any
import enum


class InvoiceStatus(str, enum.Enum):
    """
    Invoice status enumeration for lifecycle management.
    Lifecycle: Draft → Sent → Paid (or Overdue if not paid on time)
    """
    DRAFT = "draft"
    SENT = "sent"
    PAID = "paid"
    OVERDUE = "overdue"


class Currency(str, enum.Enum):
    """
    Supported currencies for invoicing.
    """
    NGN = "NGN"  # Nigerian Naira
    USD = "USD"  # US Dollar
    GBP = "GBP"  # British Pound
    EUR = "EUR"  # Euro


class PaymentMethod(str, enum.Enum):
    """
    Supported payment methods for invoices.
    """
    TRANSFER = "transfer"
    CASH = "cash"
    POS = "pos"
    CHEQUE = "cheque"
    CARD = "card"
    MOBILE_MONEY = "mobile_money"
    OTHER = "other"


PAYMENT_METHOD_LABELS = {
    PaymentMethod.TRANSFER: "Bank Transfer",
    PaymentMethod.CASH: "Cash",
    PaymentMethod.POS: "POS",
    PaymentMethod.CHEQUE: "Cheque",
    PaymentMethod.CARD: "Credit Card",
    PaymentMethod.MOBILE_MONEY: "Mobile Money",
    PaymentMethod.OTHER: "Other",
}


def format_payment_method(payment_method: Optional[Any]) -> Optional[str]:
    """Format payment method enum/value for user-facing output."""
    if payment_method is None:
        return None

    if isinstance(payment_method, PaymentMethod):
        return PAYMENT_METHOD_LABELS.get(
            payment_method, payment_method.value
        )

    if isinstance(payment_method, enum.Enum) and not isinstance(
        payment_method, PaymentMethod
    ):
        return format_payment_method(
            getattr(payment_method, "value", str(payment_method))
        )

    if isinstance(payment_method, str):
        cleaned = payment_method.strip()
        if not cleaned:
            return None
        normalized = cleaned.lower().replace(" ", "_")
        try:
            method = PaymentMethod(normalized)
        except ValueError:
            try:
                method = PaymentMethod[cleaned.upper()]
            except KeyError:
                return cleaned
        return PAYMENT_METHOD_LABELS.get(method, cleaned)

    return str(payment_method)


class Invoice(Gen_Model, Base):
    """
    Invoice model for multi-tenant invoicing system.

    Attributes:
        invoice_number: Unique invoice identifier
        tenant_id: Associated tenant for data isolation
        customer_name: Customer name
        customer_email: Customer email (optional)
        customer_phone: Customer phone (optional)
        customer_address: Customer address (optional)
        creator_id: User who created the invoice
        status: Invoice status (Draft, Sent, Paid, Overdue)
        currency: Currency code (NGN, USD, GBP, EUR)
        issue_date: Date invoice was issued
        due_date: Payment due date (optional)
        subtotal: Subtotal amount before tax
        tax_amount: Tax amount
        discount_amount: Discount amount (optional)
        total_amount: Final total amount
        notes: Additional notes (optional)
        payment_method: Payment method (optional)
        paid_at: Timestamp when invoice was paid (optional)
    """
    __tablename__ = "invoices"

    invoice_number = Column(String(50), nullable=False, index=True)
    tenant_id = Column(String(60), ForeignKey("tenants.id"), nullable=False,
                       index=True)
    customer_name = Column(String(100), nullable=False)
    customer_email = Column(String(255), nullable=True)
    customer_phone = Column(String(20), nullable=True)
    customer_address = Column(Text, nullable=True)
    creator_id = Column(String(60), ForeignKey("users.id"), nullable=False,
                        index=True)
    status = Column(Enum(InvoiceStatus), nullable=False,
                    default=InvoiceStatus.DRAFT, index=True)
    currency = Column(Enum(Currency), nullable=False, default=Currency.NGN,
                      index=True)
    issue_date = Column(String(50), nullable=False)
    due_date = Column(String(50), nullable=True)
    subtotal = Column(Numeric(10, 2), nullable=False, default=0.00)
    tax_amount = Column(Numeric(10, 2), nullable=False, default=0.00)
    discount_amount = Column(Numeric(10, 2), nullable=False, default=0.00)
    total_amount = Column(Numeric(10, 2), nullable=False, default=0.00)
    notes = Column(Text, nullable=True)
    payment_method = Column(Enum(PaymentMethod), nullable=True)
    paid_at = Column(String(50), nullable=True)

    # Relationships
    items = relationship("InvoiceItem", back_populates="invoice",
                         cascade="all, delete-orphan")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class InvoiceItem(Gen_Model, Base):
    """
    Invoice line item model.

    Attributes:
        invoice_id: Associated invoice
        description: Item description
        quantity: Item quantity
        unit_price: Price per unit
        total_price: Total price for this item (quantity * unit_price)
    """
    __tablename__ = "invoice_items"

    invoice_id = Column(String(60), ForeignKey("invoices.id"),
                        nullable=False, index=True)
    description = Column(String(255), nullable=False)
    quantity = Column(Numeric(10, 2), nullable=False, default=1.00)
    unit_price = Column(Numeric(10, 2), nullable=False, default=0.00)
    total_price = Column(Numeric(10, 2), nullable=False, default=0.00)

    # Relationships
    invoice = relationship("Invoice", back_populates="items")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
