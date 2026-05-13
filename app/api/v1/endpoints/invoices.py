from typing import List, Optional
import base64
import logging
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse, Response
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from decimal import Decimal
from datetime import datetime, date, timezone
from string import Formatter
import csv
import io
import json
from app.db.session import get_db
from app.models.invoice import (
    Invoice as InvoiceModel,
    InvoiceItem as InvoiceItemModel,
    InvoiceStatus,
    Currency,
    format_payment_method
)
from app.models.user import User, UserRole
from app.models.tenant import Tenant as TenantModel
from app.schemas.invoice import (
    Invoice,
    InvoiceCreate,
    InvoiceUpdate,
    InvoiceStatusUpdate
)
from app.schemas.pagination import PaginatedResponse, create_paginated_response
from app.core.deps import (
    get_current_user,
    require_role,
    require_verified_email,
    check_invoice_access
)
from app.core.cache import invalidate_tenant_cache
from app.services.pdf_generator import get_pdf_generator, PDFGenerationError
from app.services.audit_logger import log_invoice_event, log_export_event
from app.models.audit_log import AuditAction
from app.tasks.email_tasks import send_invoice_email_task

router = APIRouter()
logger = logging.getLogger(__name__)


def validate_invoice_number_format(format_string: str) -> bool:
    """
    Validate invoice number format string.

    Args:
        format_string: Format string to validate

    Returns:
        True if valid, False otherwise

    Valid placeholders:
        - {prefix}: Custom prefix from tenant configuration
        - {date}: Current date in YYYYMMDD format
        - {sequence}: Atomic sequence number with optional formatting
          (e.g., {sequence:04d})
    """
    if not format_string:
        return False

    formatter = Formatter()
    field_names = [
        field_name
        for _, field_name, _, _ in formatter.parse(format_string)
        if field_name
    ]
    if not field_names:
        return False

    allowed_fields = {"prefix", "date", "sequence"}
    if any(name not in allowed_fields for name in field_names):
        return False

    if "sequence" not in field_names:
        return False

    # Test formatting with sample values to ensure format is valid
    # This will catch any malformed placeholders or invalid format strings
    try:
        test_result = format_string.format(
            prefix="TEST",
            date="20260103",
            sequence=1
        )
        # Ensure result is not empty and has reasonable length
        if len(test_result) == 0 or len(test_result) > 100:
            return False

        # Verify that at least one placeholder was used
        # (result differs from input)
        # This ensures the format string actually uses the placeholders
        return test_result != format_string
    except (KeyError, ValueError, IndexError):
        return False


def _is_invoice_number_unique_violation(error: IntegrityError) -> bool:
    """Check if integrity error is due to invoice number uniqueness."""
    orig = getattr(error, "orig", None)
    if orig is None:
        return False
    constraint_name = getattr(getattr(orig, "diag", None), "constraint_name", None)
    if constraint_name == "uq_invoice_tenant_invoice_number":
        return True
    if getattr(orig, "pgcode", None) == "23505":
        if "uq_invoice_tenant_invoice_number" in str(orig):
            return True
    message = str(orig)
    return (
        "uq_invoice_tenant_invoice_number" in message
        or (
            "invoices.tenant_id" in message
            and "invoices.invoice_number" in message
        )
    )


def generate_invoice_number(db: Session, tenant_id: str) -> str:
    """
    Generate unique invoice number for tenant using atomic counter.

    This function uses the tenant's configuration to generate invoice
    numbers in a customizable format while preventing race conditions
    through atomic database updates.

    IMPORTANT: This function acquires a row-level lock on the tenant
    record and commits the transaction after incrementing the sequence
    counter. This is necessary to release the lock immediately and
    prevent blocking other invoice creations. The caller should handle
    any additional database operations in a separate transaction after
    this function completes.

    Args:
        db: Database session
        tenant_id: Tenant ID

    Returns:
        Formatted invoice number

    Raises:
        HTTPException: If tenant not found or invalid format

    Side Effects:
        - Increments the tenant's invoice_number_sequence counter
        - Commits the database transaction to release the row lock
    """
    # Fetch tenant with FOR UPDATE lock to prevent race conditions
    tenant = db.query(TenantModel).filter(
        TenantModel.id == tenant_id
    ).with_for_update().first()

    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    # Validate format if custom format is set
    format_string = (
        tenant.invoice_number_format
        or "{prefix}-{date}-{sequence:04d}"
    )
    if not validate_invoice_number_format(format_string):
        # Fallback to default format if invalid
        format_string = "{prefix}-{date}-{sequence:04d}"

    # Atomically increment the sequence number
    new_sequence = (tenant.invoice_number_sequence or 0) + 1
    tenant.invoice_number_sequence = new_sequence

    # Generate invoice number using tenant configuration
    prefix = tenant.invoice_number_prefix or "INV"
    date_str = datetime.now(timezone.utc).strftime("%Y%m%d")

    try:
        invoice_number = format_string.format(
            prefix=prefix,
            date=date_str,
            sequence=new_sequence
        )
    except (KeyError, ValueError, IndexError):
        # Fallback to default format if formatting fails
        invoice_number = f"{prefix}-{date_str}-{new_sequence:04d}"

    # Commit the sequence update immediately to release the lock
    # This allows other invoice creations to proceed without waiting
    db.commit()

    return invoice_number


def calculate_totals(
    items: List[InvoiceItemModel],
    tax_rate: Optional[Decimal] = None
) -> dict:
    """
    Calculate invoice totals from items.

    Args:
        items: List of invoice items
        tax_rate: Tax rate as percentage (0-100), None for tax-free

    Returns:
        Dict with subtotal, tax_amount, discount_amount, and total_amount
    """
    subtotal = sum(item.total_price for item in items)

    # Calculate tax based on tenant's tax configuration
    if tax_rate is not None and tax_rate > 0:
        tax_amount = subtotal * (tax_rate / Decimal("100"))
    else:
        tax_amount = Decimal("0.00")

    discount_amount = Decimal("0.00")
    total_amount = subtotal + tax_amount - discount_amount

    return {
        "subtotal": subtotal,
        "tax_amount": tax_amount,
        "discount_amount": discount_amount,
        "total_amount": total_amount
    }


@router.post("/", response_model=Invoice, status_code=201)
def create_invoice(
    invoice_in: InvoiceCreate,
    current_user: User = Depends(require_verified_email),
    db: Session = Depends(get_db)
):
    """
    Create a new invoice.

    Permissions: All authenticated AND VERIFIED users can create invoices.
    Email verification is required to create invoices.
    Invoice is created in DRAFT status by default.
    Currency and tax are always inherited from tenant settings.
    """
    # Get tenant to access currency and tax settings
    tenant = db.query(TenantModel).filter(
        TenantModel.id == current_user.tenant_id
    ).first()

    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    # Always use tenant's default currency
    try:
        currency = Currency(tenant.default_currency)
    except ValueError:
        # Fallback to USD if tenant's currency is invalid
        currency = Currency.USD

    # Create invoice
    invoice_number = generate_invoice_number(db, current_user.tenant_id)

    db_invoice = InvoiceModel(
        invoice_number=invoice_number,
        tenant_id=current_user.tenant_id,
        creator_id=current_user.id,
        customer_name=invoice_in.customer_name,
        customer_email=invoice_in.customer_email,
        customer_phone=invoice_in.customer_phone,
        customer_address=invoice_in.customer_address,
        currency=currency,
        issue_date=invoice_in.issue_date,
        due_date=invoice_in.due_date,
        notes=invoice_in.notes,
        status=InvoiceStatus.DRAFT
    )

    # Create invoice items and calculate totals
    items = []
    for item_in in invoice_in.items:
        total_price = item_in.quantity * item_in.unit_price
        db_item = InvoiceItemModel(
            invoice_id=db_invoice.id,
            description=item_in.description,
            quantity=item_in.quantity,
            unit_price=item_in.unit_price,
            total_price=total_price
        )
        items.append(db_item)

    # Calculate invoice totals using tenant's tax rate
    totals = calculate_totals(items, tenant.tax_rate)
    db_invoice.subtotal = totals["subtotal"]
    db_invoice.tax_amount = totals["tax_amount"]
    db_invoice.discount_amount = totals["discount_amount"]
    db_invoice.total_amount = totals["total_amount"]

    try:
        db.add(db_invoice)
        for item in items:
            db.add(item)
        db.commit()
        db.refresh(db_invoice)

        # Invalidate analytics cache for this tenant
        invalidate_tenant_cache(current_user.tenant_id, "*")

        return db_invoice
    except IntegrityError as e:
        db.rollback()
        if _is_invoice_number_unique_violation(e):
            raise HTTPException(
                status_code=400,
                detail="Invoice number already exists for this tenant."
            )
        raise HTTPException(
            status_code=400,
            detail=f"Failed to create invoice: {str(e)}"
        )


@router.get("/", response_model=PaginatedResponse[Invoice])
def list_invoices(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    status: Optional[InvoiceStatus] = Query(None,
                                            description="Filter by status"),
    customer_name: Optional[str] = Query(
        None,
        max_length=100,
        description="Search by customer name (partial, case-insensitive)"
    ),
    invoice_number: Optional[str] = Query(
        None,
        max_length=50,
        description="Search by invoice number (partial, case-insensitive)"
    ),
    start_date: Optional[str] = Query(
        None, description="Filter invoices created on or after (ISO 8601)"
    ),
    end_date: Optional[str] = Query(
        None, description="Filter invoices created on or before (ISO 8601)"
    ),
    min_amount: Optional[Decimal] = Query(
        None, ge=0, description="Minimum total amount filter"
    ),
    max_amount: Optional[Decimal] = Query(
        None, ge=0, description="Maximum total amount filter"
    ),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get list of invoices for current user's tenant.

    Permissions: All authenticated users can list invoices.
    Results are automatically filtered by tenant_id.

    Filters:
    - status: Filter by invoice status (draft, sent, paid, overdue)
    - customer_name: Search by customer name (partial, case-insensitive)
    - invoice_number: Search by invoice number (partial, case-insensitive)
    - start_date: Filter invoices created on or after this date (ISO 8601)
    - end_date: Filter invoices created on or before this date (ISO 8601)
    - min_amount: Filter invoices with total_amount >= min_amount
    - max_amount: Filter invoices with total_amount <= max_amount

    Returns paginated response with metadata:
    - items: List of invoices
    - total: Total count of invoices
    - page: Current page number
    - size: Items per page
    - pages: Total number of pages
    - has_next: Whether there is a next page
    - has_previous: Whether there is a previous page
    """
    query = db.query(InvoiceModel).filter(
        InvoiceModel.tenant_id == current_user.tenant_id
    )

    # ATTENDANT users can only see their own invoices
    # MANAGER+ can see all tenant invoices
    if current_user.role == UserRole.ATTENDANT:
        query = query.filter(InvoiceModel.creator_id == current_user.id)

    # Helper to escape SQL LIKE wildcards in search terms
    def _escape_like(term: str) -> str:
        """
        Escape SQL LIKE wildcards in a search term so that % and _ are treated
        as literal characters rather than wildcards.
        """
        # First escape backslash itself, then escape % and _
        term = term.replace("\\", "\\\\")
        term = term.replace("%", "\\%").replace("_", "\\_")
        return term

    # Filter by status
    if status:
        query = query.filter(InvoiceModel.status == status)

    # Search by customer name (partial, case-insensitive)
    if customer_name:
        escaped_customer_name = _escape_like(customer_name)
        pattern = f"%{escaped_customer_name}%"
        query = query.filter(
            InvoiceModel.customer_name.ilike(pattern, escape="\\")
        )

    # Search by invoice number (partial, case-insensitive)
    if invoice_number:
        escaped_invoice_number = _escape_like(invoice_number)
        pattern = f"%{escaped_invoice_number}%"
        query = query.filter(
            InvoiceModel.invoice_number.ilike(pattern, escape="\\")
        )

    # Helper to parse ISO date/datetime query params into timezone-aware
    # datetimes
    def _parse_date_param(value: str, param_name: str,
                          end_of_day: bool = False) -> datetime:
        try:
            # Handle plain YYYY-MM-DD as a date
            if len(value) == 10 and value.count("-") == 2:
                d = date.fromisoformat(value)
                if end_of_day:
                    # Set to end of day for inclusive end date filtering
                    return datetime(d.year, d.month, d.day, 23, 59, 59,
                                    999999, tzinfo=timezone.utc)
                return datetime(d.year, d.month, d.day, tzinfo=timezone.utc)

            # Try full ISO datetime parsing
            dt = datetime.fromisoformat(value)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except ValueError:
            raise HTTPException(
                status_code=422,
                detail=(
                    f"Invalid date format for {param_name}. Use YYYY-MM-DD or "
                    "an ISO 8601 datetime string."
                ),
            )

    # Parse and validate date range filters
    sd = None
    ed = None

    if start_date:
        sd = _parse_date_param(start_date, "start_date")
    if end_date:
        ed = _parse_date_param(end_date, "end_date", end_of_day=True)

    # Validate that start_date is not after end_date
    if sd is not None and ed is not None and sd > ed:
        raise HTTPException(
            status_code=422,
            detail="start_date must be less than or equal to end_date.",
        )

    # Apply date range filters
    if sd is not None:
        query = query.filter(InvoiceModel.created_at >= sd)
    if ed is not None:
        query = query.filter(InvoiceModel.created_at <= ed)

    # Validate that min_amount is not greater than max_amount
    if (min_amount is not None and max_amount is not None
            and min_amount > max_amount):
        raise HTTPException(
            status_code=422,
            detail="min_amount must be less than or equal to max_amount.",
        )

    # Apply amount range filters
    if min_amount is not None:
        query = query.filter(InvoiceModel.total_amount >= min_amount)
    if max_amount is not None:
        query = query.filter(InvoiceModel.total_amount <= max_amount)

    # Get total count
    total = query.count()

    # Get paginated items
    invoices = query.offset(skip).limit(limit).all()

    return create_paginated_response(
        items=invoices,
        total=total,
        skip=skip,
        limit=limit
    )


@router.get("/{invoice_id}", response_model=Invoice)
def get_invoice(
    invoice_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific invoice by ID.

    Permissions:
    - ATTENDANT: Can only view invoices they created
    - MANAGER+: Can view all tenant invoices
    """
    invoice = db.query(InvoiceModel).filter(
        InvoiceModel.id == invoice_id,
        InvoiceModel.tenant_id == current_user.tenant_id
    ).first()

    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    # Check access permissions
    check_invoice_access(invoice, current_user)

    return invoice


@router.put("/{invoice_id}", response_model=Invoice)
def update_invoice(
    invoice_id: str,
    invoice_update: InvoiceUpdate,
    current_user: User = Depends(require_role(UserRole.MANAGER)),
    db: Session = Depends(get_db)
):
    """
    Update an invoice.

    Permissions:
    - Creator can update their own invoices
    - ADMIN+ can update any invoice
    Only DRAFT invoices can be updated.
    """
    invoice = db.query(InvoiceModel).filter(
        InvoiceModel.id == invoice_id,
        InvoiceModel.tenant_id == current_user.tenant_id
    ).first()

    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    # Check ownership: Creator OR ADMIN+ can modify
    if (invoice.creator_id != current_user.id
            and current_user.role not in [UserRole.ADMIN, UserRole.OWNER]
            and not current_user.is_superadmin):
        raise HTTPException(
            status_code=403,
            detail="You can only modify invoices you created"
        )

    # Only draft invoices can be updated
    if invoice.status != InvoiceStatus.DRAFT:
        raise HTTPException(
            status_code=400,
            detail="Only DRAFT invoices can be updated"
        )

    update_data = invoice_update.model_dump(exclude_unset=True)

    # Handle items update separately
    items_data = update_data.pop("items", None)

    # Update invoice fields
    for field, value in update_data.items():
        setattr(invoice, field, value)

    # Update items if provided
    if items_data is not None:
        # Get tenant to access tax rate for recalculation
        tenant = db.query(TenantModel).filter(
            TenantModel.id == current_user.tenant_id
        ).first()

        # Delete existing items
        db.query(InvoiceItemModel).filter(
            InvoiceItemModel.invoice_id == invoice_id
        ).delete()

        # Create new items
        items = []
        for item_dict in items_data:
            total_price = Decimal(str(item_dict["quantity"])) * \
                Decimal(str(item_dict["unit_price"]))
            db_item = InvoiceItemModel(
                invoice_id=invoice.id,
                description=item_dict["description"],
                quantity=item_dict["quantity"],
                unit_price=item_dict["unit_price"],
                total_price=total_price
            )
            items.append(db_item)

        # Recalculate totals with tenant's tax rate
        totals = calculate_totals(items, tenant.tax_rate if tenant else None)
        invoice.subtotal = totals["subtotal"]
        invoice.tax_amount = totals["tax_amount"]
        invoice.discount_amount = totals["discount_amount"]
        invoice.total_amount = totals["total_amount"]

        for item in items:
            db.add(item)

    db.commit()
    db.refresh(invoice)

    # Invalidate analytics cache for this tenant
    invalidate_tenant_cache(current_user.tenant_id, "*")

    return invoice


@router.patch("/{invoice_id}/status", response_model=Invoice)
def update_invoice_status(
    invoice_id: str,
    status_update: InvoiceStatusUpdate,
    request: Request,
    current_user: User = Depends(require_role(UserRole.MANAGER)),
    db: Session = Depends(get_db)
):
    """
    Update invoice status (lifecycle management).

    Permissions:
    - Creator can update status of their own invoices
    - ADMIN+ can update status of any invoice

    Valid transitions:
    - DRAFT → SENT
    - SENT → PAID
    - SENT → OVERDUE (automatic or manual)
    - OVERDUE → PAID
    """
    invoice = db.query(InvoiceModel).filter(
        InvoiceModel.id == invoice_id,
        InvoiceModel.tenant_id == current_user.tenant_id
    ).first()

    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    # Check ownership: Creator OR ADMIN+ can change status
    if (invoice.creator_id != current_user.id
            and current_user.role not in [UserRole.ADMIN, UserRole.OWNER]
            and not current_user.is_superadmin):
        raise HTTPException(
            status_code=403,
            detail="You can only change status of invoices you created"
        )

    # Validate status transitions
    valid_transitions = {
        InvoiceStatus.DRAFT: [InvoiceStatus.SENT],
        InvoiceStatus.SENT: [InvoiceStatus.PAID, InvoiceStatus.OVERDUE],
        InvoiceStatus.OVERDUE: [InvoiceStatus.PAID],
        InvoiceStatus.PAID: []  # Cannot transition from PAID
    }

    if status_update.status not in valid_transitions.get(
        invoice.status, []
    ):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status transition from "
                   f"{invoice.status.value} to {status_update.status.value}"
        )

    # Capture old status for audit
    old_status = invoice.status.value

    # Update status
    invoice.status = status_update.status

    # Handle PAID status
    if status_update.status == InvoiceStatus.PAID:
        if not status_update.payment_method:
            raise HTTPException(
                status_code=400,
                detail="Payment method is required for PAID status"
            )
        invoice.payment_method = status_update.payment_method
        invoice.paid_at = datetime.now(timezone.utc).isoformat()

    db.commit()
    db.refresh(invoice)

    # Log invoice status change
    log_invoice_event(
        db=db,
        request=request,
        action=AuditAction.INVOICE_STATUS_CHANGED,
        resource_id=invoice.id,
        user_id=current_user.id,
        tenant_id=current_user.tenant_id,
        changes={
            "status": {"before": old_status, "after": invoice.status.value}
        },
        description=(f"Invoice {invoice.invoice_number} status changed from "
                     f"{old_status} to {invoice.status.value}")
    )

    # Invalidate analytics cache for this tenant
    invalidate_tenant_cache(current_user.tenant_id, "*")

    return invoice


@router.delete("/{invoice_id}")
def delete_invoice(
    invoice_id: str,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    """
    Delete an invoice (hard delete).

    Permissions:
    - Creator can delete their own invoices
    - OWNER can delete any invoice
    Only DRAFT invoices can be deleted.
    """
    invoice = db.query(InvoiceModel).filter(
        InvoiceModel.id == invoice_id,
        InvoiceModel.tenant_id == current_user.tenant_id
    ).first()

    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    # Check ownership: Creator OR OWNER can delete
    if (invoice.creator_id != current_user.id
            and current_user.role != UserRole.OWNER
            and not current_user.is_superadmin):
        raise HTTPException(
            status_code=403,
            detail="You can only delete invoices you created"
        )

    # Only draft invoices can be deleted
    if invoice.status != InvoiceStatus.DRAFT:
        raise HTTPException(
            status_code=400,
            detail="Only DRAFT invoices can be deleted"
        )

    db.delete(invoice)
    db.commit()

    # Invalidate analytics cache for this tenant
    invalidate_tenant_cache(current_user.tenant_id, "*")

    return {"message": "Invoice deleted successfully"}


@router.get("/{invoice_id}/pdf")
def download_invoice_pdf(
    invoice_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate and download invoice as PDF.

    Permissions:
    - ATTENDANT: Can only download PDFs of invoices they created
    - MANAGER+: Can download PDFs of all tenant invoices

    This endpoint generates a professional PDF document on-demand from the
    database without storing the file. The PDF is always generated fresh,
    reflecting the current state of the invoice data.

    Returns:
        PDF file with Content-Disposition: inline for browser display
    """
    # Fetch invoice with items
    invoice = db.query(InvoiceModel).filter(
        InvoiceModel.id == invoice_id,
        InvoiceModel.tenant_id == current_user.tenant_id
    ).first()

    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    # Check access permissions
    check_invoice_access(invoice, current_user)

    # Fetch tenant for branding
    tenant = db.query(TenantModel).filter(
        TenantModel.id == current_user.tenant_id
    ).first()

    # Fetch creator user for name on PDF
    creator = db.query(User).filter(
        User.id == invoice.creator_id
    ).first()

    # Generate PDF
    try:
        pdf_generator = get_pdf_generator()
        pdf_bytes = pdf_generator.generate_invoice_pdf(
            invoice, tenant, creator
        )
    except PDFGenerationError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate PDF: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error generating PDF: {str(e)}"
        )

    # Log PDF generation
    log_export_event(
        db=db,
        request=request,
        user_id=current_user.id,
        tenant_id=current_user.tenant_id,
        description=f"PDF generated for invoice {invoice.invoice_number}",
        resource_id=invoice.id
    )

    # Return PDF response
    filename = f"invoice_{invoice.invoice_number}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'inline; filename="{filename}"'
        }
    )


@router.post("/{invoice_id}/send", response_model=Invoice)
def send_invoice(
    invoice_id: str,
    current_user: User = Depends(require_role(UserRole.MANAGER)),
    db: Session = Depends(get_db)
):
    """
    Send invoice PDF to customer via email.

    Permissions:
    - Creator can send their own invoices
    - ADMIN+ can send any invoice

    This endpoint:
    1. Validates that the invoice exists and belongs to the tenant
    2. Checks that the invoice is in DRAFT status
    3. Verifies that the customer email is available
    4. Generates the invoice PDF
    5. Sends the PDF via email to the customer
    6. Updates the invoice status to SENT
    7. Returns the updated invoice

    Returns:
        Updated invoice with status SENT

    Raises:
        403: Insufficient permissions (not creator or ADMIN+)
        404: Invoice not found
        400: Invoice not in DRAFT status
        400: Customer email missing
        500: PDF generation or email sending failure
    """
    # Fetch invoice with items
    invoice = db.query(InvoiceModel).filter(
        InvoiceModel.id == invoice_id,
        InvoiceModel.tenant_id == current_user.tenant_id
    ).first()

    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    # Check ownership: Creator OR ADMIN+ can send invoices
    if (invoice.creator_id != current_user.id
            and current_user.role not in [UserRole.ADMIN, UserRole.OWNER]
            and not current_user.is_superadmin):
        raise HTTPException(
            status_code=403,
            detail="You can only send invoices you created"
        )

    # Only draft invoices can be sent
    if invoice.status != InvoiceStatus.DRAFT:
        raise HTTPException(
            status_code=400,
            detail=f"Only DRAFT invoices can be sent. "
                   f"Current status: {invoice.status.value}"
        )

    # Customer email is required
    if not invoice.customer_email:
        raise HTTPException(
            status_code=400,
            detail="Customer email is not available. "
                   "Please add a customer email to the invoice or "
                   "download the PDF manually."
        )

    # Generate PDF
    try:
        # Fetch tenant for branding
        tenant = db.query(TenantModel).filter(
            TenantModel.id == current_user.tenant_id
        ).first()

        # Fetch creator user for name on PDF
        creator = db.query(User).filter(
            User.id == invoice.creator_id
        ).first()

        pdf_generator = get_pdf_generator()
        pdf_bytes = pdf_generator.generate_invoice_pdf(
            invoice, tenant, creator
        )
    except PDFGenerationError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate PDF: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error generating PDF: {str(e)}"
        )

    # Format total amount for email
    currency_symbol = {
        Currency.USD: "$",
        Currency.GBP: "£",
        Currency.EUR: "€",
        Currency.NGN: "₦"
    }.get(invoice.currency, "$")
    total_amount = f"{currency_symbol}{invoice.total_amount:,.2f}"

    # Send email with PDF asynchronously
    pdf_bytes_b64 = base64.b64encode(pdf_bytes).decode('utf-8')

    try:
        send_invoice_email_task.delay(
            email=invoice.customer_email,
            customer_name=invoice.customer_name,
            invoice_number=invoice.invoice_number,
            pdf_bytes_b64=pdf_bytes_b64,
            total_amount=total_amount
        )
        logger.info(
            "Invoice email task queued for invoice %s to %s",
            invoice.invoice_number,
            invoice.customer_email
        )
    except Exception as e:
        logger.error(
            "Failed to queue invoice email for invoice %s to %s: %s",
            invoice.invoice_number,
            invoice.customer_email,
            str(e)
        )
        # Don't fail the entire operation if email queueing fails
        # The invoice will still be marked as SENT

    # Update invoice status to SENT
    invoice.status = InvoiceStatus.SENT
    db.commit()
    db.refresh(invoice)

    # Invalidate analytics cache for this tenant
    invalidate_tenant_cache(current_user.tenant_id, "*")

    return invoice


@router.get("/export/invoices")
def export_invoices(
    request: Request,
    format: str = Query("csv", pattern="^(csv|json)$",
                        description="Export format: csv or json"),
    status: Optional[InvoiceStatus] = Query(None,
                                            description="Filter by status"),
    start_date: Optional[str] = Query(
        None, description="Start date filter (ISO 8601)"
    ),
    end_date: Optional[str] = Query(
        None, description="End date filter (ISO 8601)"
    ),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Export invoices in CSV or JSON format.

    Permissions:
    - ATTENDANT: Can only export invoices they created
    - MANAGER+: Can export all tenant invoices
    Results are automatically filtered by tenant_id and creator_id \n
    (for ATTENDANT).

    Optional filters:
    - status: Filter by invoice status
    - start_date: Filter invoices created on or after this date
    - end_date: Filter invoices created on or before this date
    - format: csv or json (default: csv)

    Returns file download with proper Content-Disposition header.
    """
    # Build query with tenant isolation
    query = db.query(InvoiceModel).filter(
        InvoiceModel.tenant_id == current_user.tenant_id
    )

    # ATTENDANT users can only export their own invoices
    # MANAGER+ can export all tenant invoices
    if current_user.role == UserRole.ATTENDANT:
        query = query.filter(InvoiceModel.creator_id == current_user.id)

    # Apply status filter
    if status:
        query = query.filter(InvoiceModel.status == status)

    # Helper to parse ISO date/datetime query params into timezone-aware
    # datetimes
    def _parse_date_param(value: str) -> datetime:
        try:
            # Handle plain YYYY-MM-DD as a date
            if len(value) == 10 and value.count("-") == 2:
                d = date.fromisoformat(value)
                return datetime(d.year, d.month, d.day, tzinfo=timezone.utc)

            # Try full ISO datetime parsing
            dt = datetime.fromisoformat(value)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except Exception:
            raise HTTPException(
                status_code=422,
                detail=(
                    "Invalid date format for export filter. Use YYYY-MM-DD or "
                    "an ISO 8601 datetime string."
                ),
            )

    # Apply date range filters (parse strings to datetimes first)
    if start_date:
        sd = _parse_date_param(start_date)
        query = query.filter(InvoiceModel.created_at >= sd)
    if end_date:
        ed = _parse_date_param(end_date)
        query = query.filter(InvoiceModel.created_at <= ed)

    # Get all invoices
    invoices = query.all()

    # Generate filename with timestamp
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    filename = f"invoices_{timestamp}.{format}"

    if format == "csv":
        # Create CSV in memory
        output = io.StringIO()
        writer = csv.writer(output)

        # Write header
        writer.writerow([
            "Invoice Number", "Customer Name", "Customer Email",
            "Status", "Currency", "Issue Date", "Due Date",
            "Subtotal", "Tax Amount", "Discount Amount", "Total Amount",
            "Payment Method", "Paid At", "Created At"
        ])

        # Write data rows
        for invoice in invoices:
            writer.writerow([
                invoice.invoice_number,
                invoice.customer_name,
                invoice.customer_email or "",
                invoice.status.value,
                invoice.currency.value if hasattr(
                    invoice.currency, 'value'
                ) else str(invoice.currency),
                invoice.issue_date,
                invoice.due_date or "",
                float(invoice.subtotal),
                float(invoice.tax_amount),
                float(invoice.discount_amount),
                float(invoice.total_amount),
                format_payment_method(invoice.payment_method) or "",
                invoice.paid_at or "",
                invoice.created_at.isoformat() if hasattr(
                    invoice.created_at, 'isoformat'
                ) else str(invoice.created_at)
            ])

        # Prepare response
        output.seek(0)

        # Log data export
        log_export_event(
            db=db,
            request=request,
            user_id=current_user.id,
            tenant_id=current_user.tenant_id,
            description=f"CSV export of {len(invoices)} invoices"
        )

        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
    else:  # JSON format
        # Prepare JSON data
        data = []
        for invoice in invoices:
            invoice_data = {
                "invoice_number": invoice.invoice_number,
                "customer_name": invoice.customer_name,
                "customer_email": invoice.customer_email,
                "customer_phone": invoice.customer_phone,
                "customer_address": invoice.customer_address,
                "status": invoice.status.value,
                "currency": invoice.currency.value if hasattr(
                    invoice.currency, 'value'
                ) else str(invoice.currency),
                "issue_date": invoice.issue_date,
                "due_date": invoice.due_date,
                "subtotal": float(invoice.subtotal),
                "tax_amount": float(invoice.tax_amount),
                "discount_amount": float(invoice.discount_amount),
                "total_amount": float(invoice.total_amount),
                "payment_method": format_payment_method(
                    invoice.payment_method
                ),
                "paid_at": invoice.paid_at,
                "created_at": invoice.created_at.isoformat() if hasattr(
                    invoice.created_at, 'isoformat'
                ) else str(invoice.created_at),
                "items": [
                    {
                        "description": item.description,
                        "quantity": float(item.quantity),
                        "unit_price": float(item.unit_price),
                        "total_price": float(item.total_price)
                    }
                    for item in invoice.items
                ]
            }
            data.append(invoice_data)

        # Convert to JSON
        json_str = json.dumps(data, indent=2)

        # Log data export
        log_export_event(
            db=db,
            request=request,
            user_id=current_user.id,
            tenant_id=current_user.tenant_id,
            description=f"JSON export of {len(invoices)} invoices"
        )

        # Prepare response
        return StreamingResponse(
            iter([json_str]),
            media_type="application/json",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
