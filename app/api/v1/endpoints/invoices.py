from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from decimal import Decimal
from datetime import datetime

from app.db.session import get_db
from app.models.invoice import (
    Invoice as InvoiceModel,
    InvoiceItem as InvoiceItemModel,
    InvoiceStatus
)
from app.models.user import User, UserRole
from app.schemas.invoice import (
    Invoice,
    InvoiceCreate,
    InvoiceUpdate,
    InvoiceStatusUpdate
)
from app.core.deps import get_current_user, require_role

router = APIRouter()


def generate_invoice_number(db: Session, tenant_id: str) -> str:
    """Generate unique invoice number for tenant."""
    # Get count of invoices for this tenant
    count = db.query(InvoiceModel).filter(
        InvoiceModel.tenant_id == tenant_id
    ).count()
    # Format: INV-YYYYMMDD-XXXX
    date_str = datetime.now().strftime("%Y%m%d")
    number = f"INV-{date_str}-{count + 1:04d}"
    return number


def calculate_totals(items: List[InvoiceItemModel]) -> dict:
    """Calculate invoice totals from items."""
    subtotal = sum(item.total_price for item in items)
    # For simplicity, tax is 0 for now (can be configured later)
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
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new invoice.

    Permissions: All authenticated users can create invoices.
    Invoice is created in DRAFT status by default.
    """
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
        branch_id=invoice_in.branch_id,
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

    # Calculate invoice totals
    totals = calculate_totals(items)
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
        return db_invoice
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=f"Failed to create invoice: {str(e)}"
        )


@router.get("/", response_model=List[Invoice])
def list_invoices(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    status: Optional[InvoiceStatus] = Query(None,
                                            description="Filter by status"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get list of invoices for current user's tenant.

    Permissions: All authenticated users can list invoices.
    Results are automatically filtered by tenant_id.
    """
    query = db.query(InvoiceModel).filter(
        InvoiceModel.tenant_id == current_user.tenant_id
    )

    if status:
        query = query.filter(InvoiceModel.status == status)

    invoices = query.offset(skip).limit(limit).all()
    return invoices


@router.get("/{invoice_id}", response_model=Invoice)
def get_invoice(
    invoice_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific invoice by ID.

    Permissions: All authenticated users can view invoices in their tenant.
    """
    invoice = db.query(InvoiceModel).filter(
        InvoiceModel.id == invoice_id,
        InvoiceModel.tenant_id == current_user.tenant_id
    ).first()

    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

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

    Permissions: Manager and above can update invoices.
    Only DRAFT invoices can be updated.
    """
    invoice = db.query(InvoiceModel).filter(
        InvoiceModel.id == invoice_id,
        InvoiceModel.tenant_id == current_user.tenant_id
    ).first()

    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

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
        # Delete existing items
        db.query(InvoiceItemModel).filter(
            InvoiceItemModel.invoice_id == invoice_id
        ).delete()

        # Create new items
        items = []
        for item_in in items_data:
            total_price = item_in.quantity * item_in.unit_price
            db_item = InvoiceItemModel(
                invoice_id=invoice.id,
                description=item_in.description,
                quantity=item_in.quantity,
                unit_price=item_in.unit_price,
                total_price=total_price
            )
            items.append(db_item)

        # Recalculate totals
        totals = calculate_totals(items)
        invoice.subtotal = totals["subtotal"]
        invoice.tax_amount = totals["tax_amount"]
        invoice.discount_amount = totals["discount_amount"]
        invoice.total_amount = totals["total_amount"]

        for item in items:
            db.add(item)

    db.commit()
    db.refresh(invoice)
    return invoice


@router.patch("/{invoice_id}/status", response_model=Invoice)
def update_invoice_status(
    invoice_id: str,
    status_update: InvoiceStatusUpdate,
    current_user: User = Depends(require_role(UserRole.MANAGER)),
    db: Session = Depends(get_db)
):
    """
    Update invoice status (lifecycle management).

    Permissions: Manager and above can update invoice status.

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
        invoice.paid_at = datetime.now().isoformat()

    db.commit()
    db.refresh(invoice)
    return invoice


@router.delete("/{invoice_id}")
def delete_invoice(
    invoice_id: str,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    """
    Delete an invoice (hard delete).

    Permissions: Admin and above can delete invoices.
    Only DRAFT invoices can be deleted.
    """
    invoice = db.query(InvoiceModel).filter(
        InvoiceModel.id == invoice_id,
        InvoiceModel.tenant_id == current_user.tenant_id
    ).first()

    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    # Only draft invoices can be deleted
    if invoice.status != InvoiceStatus.DRAFT:
        raise HTTPException(
            status_code=400,
            detail="Only DRAFT invoices can be deleted"
        )

    db.delete(invoice)
    db.commit()
    return {"message": "Invoice deleted successfully"}
