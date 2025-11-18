from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from decimal import Decimal
import logging

from app.db.session import get_db
from app.models.invoice import Invoice as InvoiceModel, InvoiceStatus
from app.models.user import User
from app.schemas.analytics import (
    InvoiceSummary,
    InvoiceSummaryUnified,
    RevenueByStatus,
    RevenueByStatusUnified
)
from app.core.deps import get_current_user
from app.core.cache import (
    get_cache,
    set_cache,
    cache_key,
)
from app.services.currency_converter import (
    convert_currency_dict,
    CurrencyConversionError
)
# invalidate_tenant_cache is removed as it is unused

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/invoice-summary", response_model=InvoiceSummary)
def get_invoice_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    unified: bool = Query(
        False,
        description="Return amounts in user's preferred currency"
    )
):
    """
    Get tenant-level invoice summary with multi-currency support.

    Returns:
    - total_invoices: Total number of invoices
    - draft_count: Number of draft invoices
    - sent_count: Number of sent invoices
    - paid_count: Number of paid invoices
    - overdue_count: Number of overdue invoices
    - total_revenue: Total revenue from paid invoices (grouped by currency)
    - pending_amount: Total amount from sent invoices (grouped by currency)
    - overdue_amount: Total amount from overdue invoices (grouped by currency)

    Multi-currency amounts are returned as dictionaries with currency codes
    as keys and amounts as values, e.g., {"USD": 1000.00, "EUR": 500.00}

    When unified=true, all amounts are converted to user's preferred currency
    and returned as single values.

    Permissions: All authenticated users can view analytics
    for their tenant.

    Note: Results are cached for 5 minutes for performance.
    """
    tenant_id = current_user.tenant_id

    # Determine cache key based on unified parameter
    cache_suffix = "unified" if unified else "multi"
    cache_key_name = cache_key(
        tenant_id,
        f"invoice_summary_{cache_suffix}_{current_user.currency_preference.value}"
    )
    cached_result = get_cache(cache_key_name)
    if cached_result:
        if unified:
            return InvoiceSummaryUnified(**cached_result)
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

    # Get total revenue from paid invoices, grouped by currency
    total_revenue_results = db.query(
        InvoiceModel.currency,
        func.sum(InvoiceModel.total_amount).label('total')
    ).filter(
        InvoiceModel.tenant_id == tenant_id,
        InvoiceModel.status == InvoiceStatus.PAID
    ).group_by(
        InvoiceModel.currency
    ).all()
    total_revenue = {
        str(currency.value): Decimal(str(total or 0))
        for currency, total in total_revenue_results
    }

    # Get pending amount from sent invoices, grouped by currency
    pending_amount_results = db.query(
        InvoiceModel.currency,
        func.sum(InvoiceModel.total_amount).label('total')
    ).filter(
        InvoiceModel.tenant_id == tenant_id,
        InvoiceModel.status == InvoiceStatus.SENT
    ).group_by(
        InvoiceModel.currency
    ).all()
    pending_amount = {
        str(currency.value): Decimal(str(total or 0))
        for currency, total in pending_amount_results
    }

    # Get overdue amount, grouped by currency
    overdue_amount_results = db.query(
        InvoiceModel.currency,
        func.sum(InvoiceModel.total_amount).label('total')
    ).filter(
        InvoiceModel.tenant_id == tenant_id,
        InvoiceModel.status == InvoiceStatus.OVERDUE
    ).group_by(
        InvoiceModel.currency
    ).all()
    overdue_amount = {
        str(currency.value): Decimal(str(total or 0))
        for currency, total in overdue_amount_results
    }

    # Convert to unified currency if requested
    if unified:
        target_currency = current_user.currency_preference.value
        try:
            unified_revenue = convert_currency_dict(
                total_revenue, target_currency
            )
            unified_pending = convert_currency_dict(
                pending_amount, target_currency
            )
            unified_overdue = convert_currency_dict(
                overdue_amount, target_currency
            )

            result = InvoiceSummaryUnified(
                total_invoices=total_invoices,
                draft_count=draft_count,
                sent_count=sent_count,
                paid_count=paid_count,
                overdue_count=overdue_count,
                total_revenue=unified_revenue,
                pending_amount=unified_pending,
                overdue_amount=unified_overdue,
                currency=target_currency
            )

            # Cache the result
            result_dict = result.model_dump()
            result_dict["total_revenue"] = str(result_dict["total_revenue"])
            result_dict["pending_amount"] = str(result_dict["pending_amount"])
            result_dict["overdue_amount"] = str(result_dict["overdue_amount"])
            set_cache(cache_key_name, result_dict, expiry=300)

            return result

        except CurrencyConversionError as e:
            logger.error(
                f"Currency conversion error for user {current_user.id}: {e}"
            )
            # Fall back to multi-currency response
            logger.warning("Falling back to multi-currency response")

    result = InvoiceSummary(
        total_invoices=total_invoices,
        draft_count=draft_count,
        sent_count=sent_count,
        paid_count=paid_count,
        overdue_count=overdue_count,
        total_revenue=total_revenue,
        pending_amount=pending_amount,
        overdue_amount=overdue_amount
    )

    # Cache the result for 5 minutes (300 seconds)
    result_dict = result.model_dump()
    # Convert Decimal to string for JSON serialization
    for key in ["total_revenue", "pending_amount", "overdue_amount"]:
        result_dict[key] = {
            currency: str(amount)
            for currency, amount in result_dict[key].items()
        }
    set_cache(cache_key_name, result_dict, expiry=300)

    return result


@router.get("/revenue-by-status", response_model=List[RevenueByStatus])
def get_revenue_by_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    unified: bool = Query(
        False,
        description="Return amounts in user's preferred currency"
    )
):
    """
    Get revenue breakdown by invoice status with multi-currency support.

    Returns a list of revenue totals grouped by status.
    Each status entry includes amounts grouped by currency code.

    Multi-currency amounts are returned as dictionaries with currency codes
    as keys and amounts as values, e.g., {"USD": 1000.00, "EUR": 500.00}

    When unified=true, all amounts are converted to user's preferred currency
    and returned as single values per status.

    Permissions: All authenticated users can view analytics
    for their tenant.

    Note: Results are cached for 5 minutes for performance.
    """
    tenant_id = current_user.tenant_id

    # Determine cache key based on unified parameter
    cache_suffix = "unified" if unified else "multi"
    cache_key_name = cache_key(
        tenant_id,
        f"revenue_by_status_{cache_suffix}_{current_user.currency_preference.value}"
    )
    cached_result = get_cache(cache_key_name)
    if cached_result:
        if unified:
            return [RevenueByStatusUnified(**item) for item in cached_result]
        return [RevenueByStatus(**item) for item in cached_result]

    # Query revenue by status and currency
    results = db.query(
        InvoiceModel.status,
        InvoiceModel.currency,
        func.count(InvoiceModel.id).label('count'),
        func.sum(InvoiceModel.total_amount).label('total_amount')
    ).filter(
        InvoiceModel.tenant_id == tenant_id
    ).group_by(
        InvoiceModel.status,
        InvoiceModel.currency
    ).all()

    # Group results by status
    status_map = {}
    for status, currency, count, total_amount in results:
        status_key = status.value
        if status_key not in status_map:
            status_map[status_key] = {
                'status': status_key,
                'count': 0,
                'total_amount': {}
            }
        status_map[status_key]['count'] += count
        status_map[status_key]['total_amount'][str(currency.value)] = Decimal(
            str(total_amount or 0)
        )

    # Convert to unified currency if requested
    if unified:
        target_currency = current_user.currency_preference.value
        try:
            unified_results = []
            for item in status_map.values():
                converted_amount = convert_currency_dict(
                    item['total_amount'],
                    target_currency
                )
                unified_results.append(
                    RevenueByStatusUnified(
                        status=item['status'],
                        count=item['count'],
                        total_amount=converted_amount,
                        currency=target_currency
                    )
                )

            # Cache the result
            result_list = [
                {
                    "status": item.status,
                    "count": item.count,
                    "total_amount": str(item.total_amount),
                    "currency": item.currency
                }
                for item in unified_results
            ]
            set_cache(cache_key_name, result_list, expiry=300)

            return unified_results

        except CurrencyConversionError as e:
            logger.error(
                f"Currency conversion error for user {current_user.id}: {e}"
            )
            # Fall back to multi-currency response
            logger.warning("Falling back to multi-currency response")

    revenue_by_status = [
        RevenueByStatus(
            status=item['status'],
            count=item['count'],
            total_amount=item['total_amount']
        )
        for item in status_map.values()
    ]

    # Cache the result for 5 minutes
    result_list = [
        {
            "status": item.status,
            "count": item.count,
            "total_amount": {
                currency: str(amount)
                for currency, amount in item.total_amount.items()
            }
        }
        for item in revenue_by_status
    ]
    set_cache(cache_key_name, result_list, expiry=300)

    return revenue_by_status
