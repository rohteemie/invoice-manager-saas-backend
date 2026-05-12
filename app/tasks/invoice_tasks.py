"""
Background tasks for invoice processing.
"""
from datetime import datetime, timezone, date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.celery_app import celery_app
from app.core.config import settings
from app.models.invoice import Invoice, InvoiceStatus
from app.core.cache import invalidate_tenant_cache


# Create database engine for tasks
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def parse_due_date(value: str | None) -> date | None:
    """
    Parse due_date strings into a date.

    Tries YYYY-MM-DD first, then ISO datetime strings (including Z suffixes) to
    handle stored values that include time components.
    """
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        normalized = value.replace("Z", "+00:00") if value.endswith("Z") else value
        try:
            return datetime.fromisoformat(normalized).date()
        except ValueError:
            return None


@celery_app.task(name='app.tasks.invoice_tasks.check_overdue_invoices')
def check_overdue_invoices():
    """
    Background task to check and mark overdue invoices.

    This task runs periodically (hourly by default) and:
    1. Finds all SENT invoices that are past their due date
    2. Updates their status to OVERDUE
    3. Invalidates analytics cache for affected tenants

    Returns:
        dict: Summary of processed invoices
    """
    db = SessionLocal()
    try:
        # Get current date
        current_date = datetime.now(timezone.utc).date()
        current_date_str = current_date.isoformat()

        # Find SENT invoices with due_date set and likely in the past
        overdue_invoices = db.query(Invoice).filter(
            Invoice.status == InvoiceStatus.SENT,
            Invoice.due_date.isnot(None),
            Invoice.due_date < current_date_str
        ).yield_per(500)

        updated_count = 0
        affected_tenants = set()

        for invoice in overdue_invoices:
            due_date = parse_due_date(invoice.due_date)
            if due_date is None or due_date >= current_date:
                continue

            invoice.status = InvoiceStatus.OVERDUE
            updated_count += 1
            affected_tenants.add(invoice.tenant_id)

        db.commit()

        # Invalidate cache for affected tenants
        for tenant_id in affected_tenants:
            invalidate_tenant_cache(tenant_id, "*")

        return {
            "status": "success",
            "updated_count": updated_count,
            "affected_tenants": len(affected_tenants),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    except Exception as e:
        db.rollback()
        return {
            "status": "error",
            "message": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    finally:
        db.close()


@celery_app.task(name='app.tasks.invoice_tasks.process_invoice_reminder')
def process_invoice_reminder(invoice_id: str):
    """
    Send reminder for an invoice (placeholder for future implementation).

    Args:
        invoice_id: Invoice ID to send reminder for

    Returns:
        dict: Result of reminder processing
    """
    db = SessionLocal()
    try:
        invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()

        if not invoice:
            return {
                "status": "error",
                "message": f"Invoice {invoice_id} not found",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

        # Placeholder: In a real implementation, this would send an email
        # or notification to the customer
        return {
            "status": "success",
            "invoice_id": invoice_id,
            "customer": invoice.customer_name,
            "message": "Reminder sent (placeholder)",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    finally:
        db.close()
