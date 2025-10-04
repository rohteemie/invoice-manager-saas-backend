"""
Performance benchmark tests for Phase 3 - Analytics & Reporting.

These tests measure the performance of analytics endpoints and
demonstrate the improvements from caching.
"""
import pytest
import time
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from decimal import Decimal

from app.models.invoice import Invoice, InvoiceStatus
from app.models.tenant import Tenant
from app.models.user import User


def create_test_invoices(
    db_session: Session,
    tenant: Tenant,
    user: User,
    count: int
):
    """Helper to create test invoices for benchmarking."""
    invoices = []
    statuses = [
        InvoiceStatus.DRAFT,
        InvoiceStatus.SENT,
        InvoiceStatus.PAID,
        InvoiceStatus.OVERDUE
    ]

    for i in range(count):
        status = statuses[i % len(statuses)]
        invoice = Invoice(
            invoice_number=f"INV-BENCH-{i+1:05d}",
            tenant_id=tenant.id,
            creator_id=user.id,
            customer_name=f"Customer {i+1}",
            status=status,
            issue_date="2024-01-01",
            total_amount=Decimal(str((i + 1) * 100))
        )
        invoices.append(invoice)

    db_session.add_all(invoices)
    db_session.commit()
    return invoices


@pytest.mark.benchmark
def test_invoice_summary_performance_small_dataset(
    client: TestClient,
    test_tenant: Tenant,
    test_user: User,
    auth_headers: dict,
    db_session: Session
):
    """
    Benchmark invoice summary with small dataset (100 invoices).

    Expected: < 500ms without cache, < 100ms with cache
    """
    # Create 100 test invoices
    create_test_invoices(db_session, test_tenant, test_user, 100)

    # First request (no cache)
    start_time = time.time()
    response1 = client.get(
        "/api/v1/analytics/invoice-summary",
        headers=auth_headers
    )
    first_request_time = time.time() - start_time

    assert response1.status_code == 200
    print(f"\nFirst request (no cache): {first_request_time*1000:.2f}ms")

    # Second request (with cache if Redis is available)
    start_time = time.time()
    response2 = client.get(
        "/api/v1/analytics/invoice-summary",
        headers=auth_headers
    )
    second_request_time = time.time() - start_time

    assert response2.status_code == 200
    print(f"Second request (with cache): {second_request_time*1000:.2f}ms")

    # Cache should provide some improvement (if Redis is available)
    # If Redis is not available, times will be similar
    if second_request_time < first_request_time:
        improvement = (
            (first_request_time - second_request_time) /
            first_request_time * 100
        )
        print(f"Cache improvement: {improvement:.1f}%")

    # Both requests should return same data
    assert response1.json() == response2.json()


@pytest.mark.benchmark
def test_invoice_summary_performance_medium_dataset(
    client: TestClient,
    test_tenant: Tenant,
    test_user: User,
    auth_headers: dict,
    db_session: Session
):
    """
    Benchmark invoice summary with medium dataset (500 invoices).

    Expected: < 1000ms without cache, < 100ms with cache
    """
    # Create 500 test invoices
    create_test_invoices(db_session, test_tenant, test_user, 500)

    # Measure request time
    start_time = time.time()
    response = client.get(
        "/api/v1/analytics/invoice-summary",
        headers=auth_headers
    )
    request_time = time.time() - start_time

    assert response.status_code == 200
    print(f"\nMedium dataset (500 invoices): {request_time*1000:.2f}ms")

    # Verify response
    data = response.json()
    assert data["total_invoices"] == 500


@pytest.mark.benchmark
def test_invoice_summary_performance_large_dataset(
    client: TestClient,
    test_tenant: Tenant,
    test_user: User,
    auth_headers: dict,
    db_session: Session
):
    """
    Benchmark invoice summary with large dataset (1000 invoices).

    Expected: < 2000ms without cache, < 100ms with cache
    """
    # Create 1000 test invoices
    create_test_invoices(db_session, test_tenant, test_user, 1000)

    # Measure request time
    start_time = time.time()
    response = client.get(
        "/api/v1/analytics/invoice-summary",
        headers=auth_headers
    )
    request_time = time.time() - start_time

    assert response.status_code == 200
    print(f"\nLarge dataset (1000 invoices): {request_time*1000:.2f}ms")

    # Verify response
    data = response.json()
    assert data["total_invoices"] == 1000


@pytest.mark.benchmark
def test_revenue_by_status_performance(
    client: TestClient,
    test_tenant: Tenant,
    test_user: User,
    auth_headers: dict,
    db_session: Session
):
    """
    Benchmark revenue by status endpoint.

    Expected: < 500ms without cache
    """
    # Create 500 test invoices
    create_test_invoices(db_session, test_tenant, test_user, 500)

    # First request (no cache)
    start_time = time.time()
    response1 = client.get(
        "/api/v1/analytics/revenue-by-status",
        headers=auth_headers
    )
    first_request_time = time.time() - start_time

    assert response1.status_code == 200
    print(
        f"\nRevenue by status - First request: "
        f"{first_request_time*1000:.2f}ms"
    )

    # Second request (with cache)
    start_time = time.time()
    response2 = client.get(
        "/api/v1/analytics/revenue-by-status",
        headers=auth_headers
    )
    second_request_time = time.time() - start_time

    assert response2.status_code == 200
    print(
        f"Revenue by status - Second request: "
        f"{second_request_time*1000:.2f}ms"
    )

    # Verify response
    data = response1.json()
    assert len(data) == 4  # 4 different statuses


@pytest.mark.benchmark
def test_invoice_list_performance(
    client: TestClient,
    test_tenant: Tenant,
    test_user: User,
    auth_headers: dict,
    db_session: Session
):
    """
    Benchmark invoice list endpoint with pagination.

    Expected: < 500ms for 100 invoices per page
    """
    # Create 500 test invoices
    create_test_invoices(db_session, test_tenant, test_user, 500)

    # Measure paginated request time
    start_time = time.time()
    response = client.get(
        "/api/v1/invoices?skip=0&limit=100",
        headers=auth_headers
    )
    request_time = time.time() - start_time

    assert response.status_code == 200
    print(f"\nInvoice list (100/page): {request_time*1000:.2f}ms")

    # Verify response
    data = response.json()
    assert len(data) == 100


@pytest.mark.benchmark
def test_background_task_performance(db_session: Session, test_tenant: Tenant, test_user: User):
    """
    Benchmark overdue invoice check task.

    Expected: < 2000ms for 500 invoices
    """
    from datetime import datetime, timedelta
    from app.tasks.invoice_tasks import check_overdue_invoices

    # Create 500 SENT invoices with past due dates
    past_date = (datetime.now() - timedelta(days=7)).date().isoformat()
    invoices = []

    for i in range(500):
        invoice = Invoice(
            invoice_number=f"INV-TASK-{i+1:05d}",
            tenant_id=test_tenant.id,
            creator_id=test_user.id,
            customer_name=f"Customer {i+1}",
            status=InvoiceStatus.SENT,
            issue_date="2024-01-01",
            due_date=past_date,
            total_amount=Decimal(str((i + 1) * 100))
        )
        invoices.append(invoice)

    db_session.add_all(invoices)
    db_session.commit()

    # Measure task execution time
    start_time = time.time()
    result = check_overdue_invoices()
    task_time = time.time() - start_time

    print(
        f"\nBackground task (500 invoices): {task_time*1000:.2f}ms"
    )

    # Verify task result
    assert result["status"] == "success"
    assert result["updated_count"] == 500
