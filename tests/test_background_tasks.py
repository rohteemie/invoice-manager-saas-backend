from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from decimal import Decimal

from app.models.invoice import Invoice, InvoiceStatus
from app.models.tenant import Tenant
from app.models.user import User
from app.tasks.invoice_tasks import (
    check_overdue_invoices,
    process_invoice_reminder
)


def test_check_overdue_invoices_no_overdue(db_session: Session, test_tenant: Tenant, test_user: User):
    """Test check_overdue_invoices with no overdue invoices."""
    # Create a SENT invoice with future due date
    future_date = (datetime.now() + timedelta(days=7)).date().isoformat()
    invoice = Invoice(
        invoice_number="INV-001",
        tenant_id=test_tenant.id,
        creator_id=test_user.id,
        customer_name="Customer 1",
        status=InvoiceStatus.SENT,
        issue_date="2024-01-01",
        due_date=future_date,
        total_amount=Decimal("100.00")
    )
    db_session.add(invoice)
    db_session.commit()

    # Run task
    result = check_overdue_invoices()

    assert result["status"] == "success"
    assert result["updated_count"] == 0
    assert result["affected_tenants"] == 0


def test_check_overdue_invoices_with_overdue(db_session: Session, test_tenant: Tenant, test_user: User):
    """Test check_overdue_invoices marks overdue invoices."""
    # Create a SENT invoice with past due date
    past_date = (datetime.now() - timedelta(days=7)).date().isoformat()
    invoice = Invoice(
        invoice_number="INV-001",
        tenant_id=test_tenant.id,
        creator_id=test_user.id,
        customer_name="Customer 1",
        status=InvoiceStatus.SENT,
        issue_date="2024-01-01",
        due_date=past_date,
        total_amount=Decimal("100.00")
    )
    db_session.add(invoice)
    db_session.commit()
    invoice_id = invoice.id

    # Run task
    result = check_overdue_invoices()

    assert result["status"] == "success"
    assert result["updated_count"] == 1
    assert result["affected_tenants"] == 1

    # Verify invoice status was updated
    db_session.refresh(invoice)
    updated_invoice = db_session.query(Invoice).filter(Invoice.id == invoice_id).first()
    assert updated_invoice.status == InvoiceStatus.OVERDUE


def test_check_overdue_invoices_multiple_invoices(db_session: Session, test_tenant: Tenant, test_user: User):
    """Test check_overdue_invoices with multiple overdue invoices."""
    past_date = (datetime.now() - timedelta(days=7)).date().isoformat()

    # Create multiple overdue invoices
    invoices = []
    for i in range(3):
        invoice = Invoice(
            invoice_number=f"INV-{i+1:03d}",
            tenant_id=test_tenant.id,
            creator_id=test_user.id,
            customer_name=f"Customer {i+1}",
            status=InvoiceStatus.SENT,
            issue_date="2024-01-01",
            due_date=past_date,
            total_amount=Decimal("100.00")
        )
        invoices.append(invoice)
        db_session.add(invoice)

    db_session.commit()

    # Run task
    result = check_overdue_invoices()

    assert result["status"] == "success"
    assert result["updated_count"] == 3
    assert result["affected_tenants"] == 1

    # Verify all invoices were updated
    for invoice in invoices:
        db_session.refresh(invoice)
        assert invoice.status == InvoiceStatus.OVERDUE


def test_check_overdue_invoices_skips_draft_and_paid(
    db_session: Session,
    test_tenant: Tenant,
    test_user: User
):
    """Test that check_overdue_invoices only affects SENT invoices."""
    past_date = (datetime.now() - timedelta(days=7)).date().isoformat()

    # Create invoices in different statuses with past due dates
    draft_invoice = Invoice(
        invoice_number="INV-001",
        tenant_id=test_tenant.id,
        creator_id=test_user.id,
        customer_name="Customer 1",
        status=InvoiceStatus.DRAFT,
        issue_date="2024-01-01",
        due_date=past_date,
        total_amount=Decimal("100.00")
    )

    paid_invoice = Invoice(
        invoice_number="INV-002",
        tenant_id=test_tenant.id,
        creator_id=test_user.id,
        customer_name="Customer 2",
        status=InvoiceStatus.PAID,
        issue_date="2024-01-01",
        due_date=past_date,
        total_amount=Decimal("200.00")
    )

    sent_invoice = Invoice(
        invoice_number="INV-003",
        tenant_id=test_tenant.id,
        creator_id=test_user.id,
        customer_name="Customer 3",
        status=InvoiceStatus.SENT,
        issue_date="2024-01-01",
        due_date=past_date,
        total_amount=Decimal("300.00")
    )

    db_session.add_all([draft_invoice, paid_invoice, sent_invoice])
    db_session.commit()

    # Run task
    result = check_overdue_invoices()

    assert result["status"] == "success"
    assert result["updated_count"] == 1  # Only SENT invoice should be updated

    # Verify statuses
    db_session.refresh(draft_invoice)
    db_session.refresh(paid_invoice)
    db_session.refresh(sent_invoice)

    assert draft_invoice.status == InvoiceStatus.DRAFT
    assert paid_invoice.status == InvoiceStatus.PAID
    assert sent_invoice.status == InvoiceStatus.OVERDUE


def test_check_overdue_invoices_skips_no_due_date(
    db_session: Session,
    test_tenant: Tenant,
    test_user: User
):
    """Test that invoices without due dates are skipped."""
    # Create SENT invoice without due date
    invoice = Invoice(
        invoice_number="INV-001",
        tenant_id=test_tenant.id,
        creator_id=test_user.id,
        customer_name="Customer 1",
        status=InvoiceStatus.SENT,
        issue_date="2024-01-01",
        due_date=None,
        total_amount=Decimal("100.00")
    )
    db_session.add(invoice)
    db_session.commit()

    # Run task
    result = check_overdue_invoices()

    assert result["status"] == "success"
    assert result["updated_count"] == 0

    # Verify status unchanged
    db_session.refresh(invoice)
    assert invoice.status == InvoiceStatus.SENT


def test_check_overdue_invoices_handles_invalid_due_dates(
    db_session: Session,
    test_tenant: Tenant,
    test_user: User
):
    """Test that invalid due dates are skipped and datetime strings are handled."""
    past_datetime = "2024-01-01T00:00:00+00:00"

    invoice_with_datetime = Invoice(
        invoice_number="INV-010",
        tenant_id=test_tenant.id,
        creator_id=test_user.id,
        customer_name="Customer 1",
        status=InvoiceStatus.SENT,
        issue_date="2024-01-01",
        due_date=past_datetime,
        total_amount=Decimal("100.00")
    )

    invoice_with_invalid_date = Invoice(
        invoice_number="INV-011",
        tenant_id=test_tenant.id,
        creator_id=test_user.id,
        customer_name="Customer 2",
        status=InvoiceStatus.SENT,
        issue_date="2024-01-01",
        due_date="01/01/2024",
        total_amount=Decimal("200.00")
    )

    db_session.add_all([invoice_with_datetime, invoice_with_invalid_date])
    db_session.commit()

    result = check_overdue_invoices()

    assert result["status"] == "success"
    assert result["updated_count"] == 1
    assert result["affected_tenants"] == 1

    db_session.refresh(invoice_with_datetime)
    db_session.refresh(invoice_with_invalid_date)

    assert invoice_with_datetime.status == InvoiceStatus.OVERDUE
    assert invoice_with_invalid_date.status == InvoiceStatus.SENT


def test_process_invoice_reminder_existing_invoice(
    db_session: Session,
    test_tenant: Tenant,
    test_user: User
):
    """Test process_invoice_reminder with existing invoice."""
    invoice = Invoice(
        invoice_number="INV-001",
        tenant_id=test_tenant.id,
        creator_id=test_user.id,
        customer_name="Customer 1",
        status=InvoiceStatus.SENT,
        issue_date="2024-01-01",
        total_amount=Decimal("100.00")
    )
    db_session.add(invoice)
    db_session.commit()

    # Run task
    result = process_invoice_reminder(invoice.id)

    assert result["status"] == "success"
    assert result["invoice_id"] == invoice.id
    assert result["customer"] == "Customer 1"


def test_process_invoice_reminder_nonexistent_invoice(db_session: Session):
    """Test process_invoice_reminder with non-existent invoice."""
    # Run task with invalid invoice ID
    result = process_invoice_reminder("invalid-id")

    assert result["status"] == "error"
    assert "not found" in result["message"]
