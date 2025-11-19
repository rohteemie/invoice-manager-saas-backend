from pydantic import BaseModel, ConfigDict
from decimal import Decimal
from typing import Dict


class InvoiceSummary(BaseModel):
    """
    Tenant-level invoice summary schema.
    Amounts are returned in user's preferred currency.
    """
    total_invoices: int
    draft_count: int
    sent_count: int
    paid_count: int
    overdue_count: int
    total_revenue: Decimal
    pending_amount: Decimal
    overdue_amount: Decimal
    currency: str  # User's preferred currency

    model_config = ConfigDict(from_attributes=True)


class InvoiceSummaryMultiCurrency(BaseModel):
    """
    Tenant-level invoice summary schema with multi-currency breakdown.
    Multi-currency amounts are grouped by currency code.
    This is available for backward compatibility.
    """
    total_invoices: int
    draft_count: int
    sent_count: int
    paid_count: int
    overdue_count: int
    total_revenue: Dict[str, Decimal]
    pending_amount: Dict[str, Decimal]
    overdue_amount: Dict[str, Decimal]

    model_config = ConfigDict(from_attributes=True)


class RevenueByStatus(BaseModel):
    """
    Revenue breakdown by invoice status.
    Amounts are returned in user's preferred currency.
    """
    status: str
    count: int
    total_amount: Decimal
    currency: str  # User's preferred currency

    model_config = ConfigDict(from_attributes=True)


class RevenueByStatusMultiCurrency(BaseModel):
    """
    Revenue breakdown by invoice status with multi-currency breakdown.
    Amounts are grouped by currency code.
    This is available for backward compatibility.
    """
    status: str
    count: int
    total_amount: Dict[str, Decimal]

    model_config = ConfigDict(from_attributes=True)
