from pydantic import BaseModel
from decimal import Decimal
from typing import Dict


class InvoiceSummary(BaseModel):
    """
    Tenant-level invoice summary schema.
    Multi-currency amounts are grouped by currency code.
    """
    total_invoices: int
    draft_count: int
    sent_count: int
    paid_count: int
    overdue_count: int
    total_revenue: Dict[str, Decimal]
    pending_amount: Dict[str, Decimal]
    overdue_amount: Dict[str, Decimal]

    class Config:
        from_attributes = True


class InvoiceSummaryUnified(BaseModel):
    """
    Tenant-level invoice summary with unified currency.
    All amounts are converted to user's preferred currency.
    """
    total_invoices: int
    draft_count: int
    sent_count: int
    paid_count: int
    overdue_count: int
    total_revenue: Decimal
    pending_amount: Decimal
    overdue_amount: Decimal
    currency: str

    class Config:
        from_attributes = True


class RevenueByStatus(BaseModel):
    """
    Revenue breakdown by invoice status.
    Amounts are grouped by currency code.
    """
    status: str
    count: int
    total_amount: Dict[str, Decimal]

    class Config:
        from_attributes = True


class RevenueByStatusUnified(BaseModel):
    """
    Revenue breakdown by invoice status with unified currency.
    All amounts are converted to user's preferred currency.
    """
    status: str
    count: int
    total_amount: Decimal
    currency: str

    class Config:
        from_attributes = True
