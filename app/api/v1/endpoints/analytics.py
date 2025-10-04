from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from decimal import Decimal

from app.db.session import get_db
from app.models.invoice import Invoice as InvoiceModel, InvoiceStatus
from app.models.user import User
from app.schemas.analytics import InvoiceSummary, RevenueByStatus
from app.core.deps import get_current_user

router = APIRouter()


@router.get("/invoice-summary", response_model=InvoiceSummary)
def get_invoice_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get tenant-level invoice summary.

    Returns:
    - total_invoices: Total number of invoices
    - draft_count: Number of draft invoices
    - sent_count: Number of sent invoices
    - paid_count: Number of paid invoices
    - overdue_count: Number of overdue invoices
    - total_revenue: Total revenue from paid invoices
    - pending_amount: Total amount from sent invoices
    - overdue_amount: Total amount from overdue invoices

    Permissions: All authenticated users can view analytics
    for their tenant.
    """
    tenant_id = current_user.tenant_id

    # Get total invoice count
    total_invoices = db.query(InvoiceModel).filter(
        InvoiceModel.tenant_id == tenant_id
    ).count()

    # Get counts by status
    draft_count = db.query(InvoiceModel).filter(
        InvoiceModel.tenant_id == tenant_id,
        InvoiceModel.status == InvoiceStatus.DRAFT
    ).count()

    sent_count = db.query(InvoiceModel).filter(
        InvoiceModel.tenant_id == tenant_id,
        InvoiceModel.status == InvoiceStatus.SENT
    ).count()

    paid_count = db.query(InvoiceModel).filter(
        InvoiceModel.tenant_id == tenant_id,
        InvoiceModel.status == InvoiceStatus.PAID
    ).count()

    overdue_count = db.query(InvoiceModel).filter(
        InvoiceModel.tenant_id == tenant_id,
        InvoiceModel.status == InvoiceStatus.OVERDUE
    ).count()

    # Get total revenue from paid invoices
    total_revenue_result = db.query(
        func.sum(InvoiceModel.total_amount)
    ).filter(
        InvoiceModel.tenant_id == tenant_id,
        InvoiceModel.status == InvoiceStatus.PAID
    ).scalar()
    total_revenue = Decimal(str(total_revenue_result or 0))

    # Get pending amount from sent invoices
    pending_amount_result = db.query(
        func.sum(InvoiceModel.total_amount)
    ).filter(
        InvoiceModel.tenant_id == tenant_id,
        InvoiceModel.status == InvoiceStatus.SENT
    ).scalar()
    pending_amount = Decimal(str(pending_amount_result or 0))

    # Get overdue amount
    overdue_amount_result = db.query(
        func.sum(InvoiceModel.total_amount)
    ).filter(
        InvoiceModel.tenant_id == tenant_id,
        InvoiceModel.status == InvoiceStatus.OVERDUE
    ).scalar()
    overdue_amount = Decimal(str(overdue_amount_result or 0))

    return InvoiceSummary(
        total_invoices=total_invoices,
        draft_count=draft_count,
        sent_count=sent_count,
        paid_count=paid_count,
        overdue_count=overdue_count,
        total_revenue=total_revenue,
        pending_amount=pending_amount,
        overdue_amount=overdue_amount
    )


@router.get("/revenue-by-status", response_model=List[RevenueByStatus])
def get_revenue_by_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get revenue breakdown by invoice status.

    Returns a list of revenue totals grouped by status.

    Permissions: All authenticated users can view analytics
    for their tenant.
    """
    tenant_id = current_user.tenant_id

    # Query revenue by status
    results = db.query(
        InvoiceModel.status,
        func.count(InvoiceModel.id).label('count'),
        func.sum(InvoiceModel.total_amount).label('total_amount')
    ).filter(
        InvoiceModel.tenant_id == tenant_id
    ).group_by(
        InvoiceModel.status
    ).all()

    revenue_by_status = []
    for status, count, total_amount in results:
        revenue_by_status.append(
            RevenueByStatus(
                status=status.value,
                count=count,
                total_amount=Decimal(str(total_amount or 0))
            )
        )

    return revenue_by_status
