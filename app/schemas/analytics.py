from pydantic import BaseModel
from typing import Optional
from decimal import Decimal


class InvoiceSummary(BaseModel):
    """
    Tenant-level invoice summary schema.
    """
    total_invoices: int
    draft_count: int
    sent_count: int
    paid_count: int
    overdue_count: int
    total_revenue: Decimal
    pending_amount: Decimal
    overdue_amount: Decimal

    class Config:
        from_attributes = True


class RevenueByStatus(BaseModel):
    """
    Revenue breakdown by invoice status.
    """
    status: str
    count: int
    total_amount: Decimal

    class Config:
        from_attributes = True
