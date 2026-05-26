from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from decimal import Decimal
from app.db.session import get_db
from app.models.invoice import Invoice as InvoiceModel, InvoiceStatus
from app.models.user import User
from app.models.tenant import Tenant
from app.schemas.analytics import InvoiceSummary, RevenueByStatus
from app.core.deps import require_verified_email
from app.core.cache import get_cache, set_cache, cache_key

router = APIRouter()


@router.get("/invoice-summary", response_model=InvoiceSummary)
def get_invoice_summary(
    current_user: User = Depends(require_verified_email),
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
    - currency: Tenant's default currency

    All invoices use the tenant's default currency.

    Permissions: All authenticated users can view analytics
    for their tenant.

    Note: Results are cached for 5 minutes for performance.
    GDPR: No personal data is exposed in this endpoint.
    """
    tenant_id = current_user.tenant_id
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    tenant_currency = tenant.default_currency

    # Check cache first
    cache_key_name = cache_key(
        tenant_id, f"invoice_summary_{tenant_currency}"
    )
    cached_result = get_cache(cache_key_name)
    if cached_result:
        return InvoiceSummary(**cached_result)

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
    total_revenue = Decimal(str(total_revenue_result or 0)).quantize(
        Decimal("0.01")
    )

    # Get pending amount from sent invoices
    pending_amount_result = db.query(
        func.sum(InvoiceModel.total_amount)
    ).filter(
        InvoiceModel.tenant_id == tenant_id,
        InvoiceModel.status == InvoiceStatus.SENT
    ).scalar()
    pending_amount = Decimal(str(pending_amount_result or 0)).quantize(
        Decimal("0.01")
    )

    # Get overdue amount
    overdue_amount_result = db.query(
        func.sum(InvoiceModel.total_amount)
    ).filter(
        InvoiceModel.tenant_id == tenant_id,
        InvoiceModel.status == InvoiceStatus.OVERDUE
    ).scalar()
    overdue_amount = Decimal(str(overdue_amount_result or 0)).quantize(
        Decimal("0.01")
    )

    result = InvoiceSummary(
        total_invoices=total_invoices,
        draft_count=draft_count,
        sent_count=sent_count,
        paid_count=paid_count,
        overdue_count=overdue_count,
        total_revenue=total_revenue,
        pending_amount=pending_amount,
        overdue_amount=overdue_amount,
        currency=tenant_currency
    )

    # Cache the result for 5 minutes (300 seconds)
    result_dict = result.model_dump()
    # Convert Decimal to string for JSON serialization
    result_dict['total_revenue'] = str(result_dict['total_revenue'])
    result_dict['pending_amount'] = str(result_dict['pending_amount'])
    result_dict['overdue_amount'] = str(result_dict['overdue_amount'])
    set_cache(cache_key_name, result_dict, expiry=300)

    return result


@router.get("/revenue-by-status", response_model=List[RevenueByStatus])
def get_revenue_by_status(
    current_user: User = Depends(require_verified_email),
    db: Session = Depends(get_db)
):
    """
    Get revenue breakdown by invoice status.

    Returns a list of revenue totals grouped by status.
    All invoices use the tenant's default currency.

    Permissions: All authenticated users can view analytics
    for their tenant.

    Note: Results are cached for 5 minutes for performance.
    GDPR: No personal data is exposed in this endpoint.
    """
    tenant_id = current_user.tenant_id
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    tenant_currency = tenant.default_currency

    # Check cache first
    cache_key_name = cache_key(
        tenant_id, f"revenue_by_status_{tenant_currency}"
    )
    cached_result = get_cache(cache_key_name)
    if cached_result:
        return [RevenueByStatus(**item) for item in cached_result]

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

    # Build response
    revenue_by_status = []
    for status, count, total_amount in results:
        revenue_by_status.append(
            RevenueByStatus(
                status=status.value,
                count=count,
                total_amount=Decimal(str(total_amount or 0)).quantize(
                    Decimal("0.01")
                ),
                currency=tenant_currency
            )
        )

    # Cache the result for 5 minutes
    result_list = [
        {
            "status": item.status,
            "count": item.count,
            "total_amount": str(item.total_amount),
            "currency": item.currency
        }
        for item in revenue_by_status
    ]
    set_cache(cache_key_name, result_list, expiry=300)

    return revenue_by_status
