from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from decimal import Decimal

from app.models.invoice import Invoice, InvoiceStatus, Currency
from app.models.tenant import Tenant
from app.models.user import User, UserRole
from app.core.security import get_password_hash


def test_invoice_summary_empty(
    client: TestClient,
    test_tenant: Tenant,
    test_user: User,
    auth_headers: dict
):
    """Test invoice summary with no invoices."""
    response = client.get(
        "/api/v1/analytics/invoice-summary",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total_invoices"] == 0
    assert data["draft_count"] == 0
    assert data["sent_count"] == 0
    assert data["paid_count"] == 0
    assert data["overdue_count"] == 0
    assert data["total_revenue"] == {}
    assert data["pending_amount"] == {}
    assert data["overdue_amount"] == {}


def test_invoice_summary_with_data(
    client: TestClient,
    test_tenant: Tenant,
    test_user: User,
    auth_headers: dict,
    db_session: Session
):
    """Test invoice summary with various invoice statuses."""
    # Create invoices with different statuses
    # 2 Draft invoices
    draft1 = Invoice(
        invoice_number="INV-001",
        tenant_id=test_tenant.id,
        creator_id=test_user.id,
        customer_name="Customer 1",
        status=InvoiceStatus.DRAFT,
        currency=Currency.USD,
        issue_date="2024-01-01",
        total_amount=Decimal("100.00")
    )
    draft2 = Invoice(
        invoice_number="INV-002",
        tenant_id=test_tenant.id,
        creator_id=test_user.id,
        customer_name="Customer 2",
        status=InvoiceStatus.DRAFT,
        currency=Currency.USD,
        issue_date="2024-01-02",
        total_amount=Decimal("200.00")
    )

    # 1 Sent invoice
    sent1 = Invoice(
        invoice_number="INV-003",
        tenant_id=test_tenant.id,
        creator_id=test_user.id,
        customer_name="Customer 3",
        status=InvoiceStatus.SENT,
        currency=Currency.USD,
        issue_date="2024-01-03",
        total_amount=Decimal("300.00")
    )

    # 2 Paid invoices
    paid1 = Invoice(
        invoice_number="INV-004",
        tenant_id=test_tenant.id,
        creator_id=test_user.id,
        customer_name="Customer 4",
        status=InvoiceStatus.PAID,
        currency=Currency.USD,
        issue_date="2024-01-04",
        total_amount=Decimal("400.00")
    )
    paid2 = Invoice(
        invoice_number="INV-005",
        tenant_id=test_tenant.id,
        creator_id=test_user.id,
        customer_name="Customer 5",
        status=InvoiceStatus.PAID,
        currency=Currency.USD,
        issue_date="2024-01-05",
        total_amount=Decimal("500.00")
    )

    # 1 Overdue invoice
    overdue1 = Invoice(
        invoice_number="INV-006",
        tenant_id=test_tenant.id,
        creator_id=test_user.id,
        customer_name="Customer 6",
        status=InvoiceStatus.OVERDUE,
        currency=Currency.USD,
        issue_date="2024-01-06",
        total_amount=Decimal("600.00")
    )

    db_session.add_all([draft1, draft2, sent1, paid1, paid2, overdue1])
    db_session.commit()

    # Get invoice summary
    response = client.get(
        "/api/v1/analytics/invoice-summary",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total_invoices"] == 6
    assert data["draft_count"] == 2
    assert data["sent_count"] == 1
    assert data["paid_count"] == 2
    assert data["overdue_count"] == 1
    # Total revenue = 400 + 500 = 900 (USD)
    assert Decimal(data["total_revenue"]["USD"]) == Decimal("900.00")
    # Pending amount = 300 (USD)
    assert Decimal(data["pending_amount"]["USD"]) == Decimal("300.00")
    # Overdue amount = 600 (USD)
    assert Decimal(data["overdue_amount"]["USD"]) == Decimal("600.00")


def test_invoice_summary_tenant_isolation(
    client: TestClient,
    test_tenant: Tenant,
    test_user: User,
    auth_headers: dict,
    db_session: Session
):
    """Test that invoice summary respects tenant isolation."""
    # Create another tenant and user
    other_tenant = Tenant(
        name="Other Tenant",
        plan_type="free"
    )
    db_session.add(other_tenant)
    db_session.commit()
    db_session.refresh(other_tenant)

    other_user = User(
        email="other@example.com",
        full_name="Other User",
        hashed_password=get_password_hash("password123"),
        role=UserRole.OWNER,
        tenant_id=other_tenant.id
    )
    db_session.add(other_user)
    db_session.commit()

    # Create invoices for test_tenant
    invoice1 = Invoice(
        invoice_number="INV-001",
        tenant_id=test_tenant.id,
        creator_id=test_user.id,
        customer_name="Customer 1",
        status=InvoiceStatus.PAID,
        currency=Currency.USD,
        issue_date="2024-01-01",
        total_amount=Decimal("100.00")
    )

    # Create invoices for other_tenant
    invoice2 = Invoice(
        invoice_number="INV-002",
        tenant_id=other_tenant.id,
        creator_id=other_user.id,
        customer_name="Customer 2",
        status=InvoiceStatus.PAID,
        currency=Currency.USD,
        issue_date="2024-01-02",
        total_amount=Decimal("200.00")
    )

    db_session.add_all([invoice1, invoice2])
    db_session.commit()

    # Get summary for test_tenant
    response = client.get(
        "/api/v1/analytics/invoice-summary",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    # Should only see test_tenant's invoice
    assert data["total_invoices"] == 1
    assert data["paid_count"] == 1
    assert Decimal(data["total_revenue"]["USD"]) == Decimal("100.00")


def test_revenue_by_status(
    client: TestClient,
    test_tenant: Tenant,
    test_user: User,
    auth_headers: dict,
    db_session: Session
):
    """Test revenue breakdown by status."""
    # Create invoices with different statuses
    draft = Invoice(
        invoice_number="INV-001",
        tenant_id=test_tenant.id,
        creator_id=test_user.id,
        customer_name="Customer 1",
        status=InvoiceStatus.DRAFT,
        currency=Currency.USD,
        issue_date="2024-01-01",
        total_amount=Decimal("100.00")
    )
    sent = Invoice(
        invoice_number="INV-002",
        tenant_id=test_tenant.id,
        creator_id=test_user.id,
        customer_name="Customer 2",
        status=InvoiceStatus.SENT,
        currency=Currency.USD,
        issue_date="2024-01-02",
        total_amount=Decimal("200.00")
    )
    paid = Invoice(
        invoice_number="INV-003",
        tenant_id=test_tenant.id,
        creator_id=test_user.id,
        customer_name="Customer 3",
        status=InvoiceStatus.PAID,
        currency=Currency.USD,
        issue_date="2024-01-03",
        total_amount=Decimal("300.00")
    )

    db_session.add_all([draft, sent, paid])
    db_session.commit()

    # Get revenue by status
    response = client.get(
        "/api/v1/analytics/revenue-by-status",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3

    # Convert to dict for easier testing
    status_dict = {item["status"]: item for item in data}

    assert status_dict["draft"]["count"] == 1
    assert Decimal(status_dict["draft"]["total_amount"]["USD"]) == Decimal("100.00")

    assert status_dict["sent"]["count"] == 1
    assert Decimal(status_dict["sent"]["total_amount"]["USD"]) == Decimal("200.00")

    assert status_dict["paid"]["count"] == 1
    assert Decimal(status_dict["paid"]["total_amount"]["USD"]) == Decimal("300.00")


def test_revenue_by_status_empty(
    client: TestClient,
    test_tenant: Tenant,
    test_user: User,
    auth_headers: dict
):
    """Test revenue by status with no invoices."""
    response = client.get(
        "/api/v1/analytics/revenue-by-status",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 0


def test_analytics_requires_authentication(client: TestClient):
    """Test that analytics endpoints require authentication."""
    # Test invoice summary
    response = client.get("/api/v1/analytics/invoice-summary")
    assert response.status_code == 401

    # Test revenue by status
    response = client.get("/api/v1/analytics/revenue-by-status")
    assert response.status_code == 401


def test_analytics_with_multiple_statuses(
    client: TestClient,
    test_tenant: Tenant,
    test_user: User,
    auth_headers: dict,
    db_session: Session
):
    """Test analytics with invoices in all statuses."""
    # Create 3 invoices in each status
    invoices = []
    statuses = [
        InvoiceStatus.DRAFT,
        InvoiceStatus.SENT,
        InvoiceStatus.PAID,
        InvoiceStatus.OVERDUE
    ]
    amounts = [100, 200, 300, 400]

    for idx, status in enumerate(statuses):
        for i in range(3):
            invoice = Invoice(
                invoice_number=f"INV-{idx}-{i}",
                tenant_id=test_tenant.id,
                creator_id=test_user.id,
                customer_name=f"Customer {idx}-{i}",
                status=status,
                currency=Currency.USD,
                issue_date=f"2024-01-{idx + 1:02d}",
                total_amount=Decimal(str(amounts[idx]))
            )
            invoices.append(invoice)

    db_session.add_all(invoices)
    db_session.commit()

    # Get summary
    response = client.get(
        "/api/v1/analytics/invoice-summary",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total_invoices"] == 12
    assert data["draft_count"] == 3
    assert data["sent_count"] == 3
    assert data["paid_count"] == 3
    assert data["overdue_count"] == 3
    # Total revenue = 3 * 300 = 900 (USD)
    assert Decimal(data["total_revenue"]["USD"]) == Decimal("900.00")
    # Pending amount = 3 * 200 = 600 (USD)
    assert Decimal(data["pending_amount"]["USD"]) == Decimal("600.00")
    # Overdue amount = 3 * 400 = 1200 (USD)
    assert Decimal(data["overdue_amount"]["USD"]) == Decimal("1200.00")


def test_revenue_by_status_tenant_isolation(
    client: TestClient,
    test_tenant: Tenant,
    test_user: User,
    auth_headers: dict,
    db_session: Session
):
    """Test revenue by status respects tenant isolation."""
    # Create another tenant
    other_tenant = Tenant(
        name="Other Tenant",
        plan_type="free"
    )
    db_session.add(other_tenant)
    db_session.commit()
    db_session.refresh(other_tenant)

    other_user = User(
        email="other@example.com",
        full_name="Other User",
        hashed_password=get_password_hash("password123"),
        role=UserRole.OWNER,
        tenant_id=other_tenant.id
    )
    db_session.add(other_user)
    db_session.commit()

    # Create invoice for test_tenant
    invoice1 = Invoice(
        invoice_number="INV-001",
        tenant_id=test_tenant.id,
        creator_id=test_user.id,
        customer_name="Customer 1",
        status=InvoiceStatus.PAID,
        currency=Currency.USD,
        issue_date="2024-01-01",
        total_amount=Decimal("100.00")
    )

    # Create invoice for other_tenant
    invoice2 = Invoice(
        invoice_number="INV-002",
        tenant_id=other_tenant.id,
        creator_id=other_user.id,
        customer_name="Customer 2",
        status=InvoiceStatus.PAID,
        currency=Currency.USD,
        issue_date="2024-01-02",
        total_amount=Decimal("500.00")
    )

    db_session.add_all([invoice1, invoice2])
    db_session.commit()

    # Get revenue by status for test_tenant
    response = client.get(
        "/api/v1/analytics/revenue-by-status",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["status"] == "paid"
    assert data[0]["count"] == 1
    # Should only see test_tenant's revenue
    assert Decimal(data[0]["total_amount"]["USD"]) == Decimal("100.00")


def test_invoice_summary_multi_currency(
    client: TestClient,
    test_tenant: Tenant,
    test_user: User,
    auth_headers: dict,
    db_session: Session
):
    """Test invoice summary with multiple currencies."""
    # Create paid invoices in different currencies
    paid_usd = Invoice(
        invoice_number="INV-001",
        tenant_id=test_tenant.id,
        creator_id=test_user.id,
        customer_name="Customer 1",
        status=InvoiceStatus.PAID,
        currency=Currency.USD,
        issue_date="2024-01-01",
        total_amount=Decimal("100.00")
    )
    paid_eur = Invoice(
        invoice_number="INV-002",
        tenant_id=test_tenant.id,
        creator_id=test_user.id,
        customer_name="Customer 2",
        status=InvoiceStatus.PAID,
        currency=Currency.EUR,
        issue_date="2024-01-02",
        total_amount=Decimal("200.00")
    )
    paid_gbp = Invoice(
        invoice_number="INV-003",
        tenant_id=test_tenant.id,
        creator_id=test_user.id,
        customer_name="Customer 3",
        status=InvoiceStatus.PAID,
        currency=Currency.GBP,
        issue_date="2024-01-03",
        total_amount=Decimal("150.00")
    )

    # Create sent invoices in different currencies
    sent_usd = Invoice(
        invoice_number="INV-004",
        tenant_id=test_tenant.id,
        creator_id=test_user.id,
        customer_name="Customer 4",
        status=InvoiceStatus.SENT,
        currency=Currency.USD,
        issue_date="2024-01-04",
        total_amount=Decimal("300.00")
    )
    sent_eur = Invoice(
        invoice_number="INV-005",
        tenant_id=test_tenant.id,
        creator_id=test_user.id,
        customer_name="Customer 5",
        status=InvoiceStatus.SENT,
        currency=Currency.EUR,
        issue_date="2024-01-05",
        total_amount=Decimal("400.00")
    )

    db_session.add_all([paid_usd, paid_eur, paid_gbp, sent_usd, sent_eur])
    db_session.commit()

    # Get invoice summary
    response = client.get(
        "/api/v1/analytics/invoice-summary",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total_invoices"] == 5
    assert data["paid_count"] == 3
    assert data["sent_count"] == 2

    # Verify revenue is grouped by currency
    assert "USD" in data["total_revenue"]
    assert "EUR" in data["total_revenue"]
    assert "GBP" in data["total_revenue"]
    assert Decimal(data["total_revenue"]["USD"]) == Decimal("100.00")
    assert Decimal(data["total_revenue"]["EUR"]) == Decimal("200.00")
    assert Decimal(data["total_revenue"]["GBP"]) == Decimal("150.00")

    # Verify pending amounts are grouped by currency
    assert "USD" in data["pending_amount"]
    assert "EUR" in data["pending_amount"]
    assert Decimal(data["pending_amount"]["USD"]) == Decimal("300.00")
    assert Decimal(data["pending_amount"]["EUR"]) == Decimal("400.00")


def test_revenue_by_status_multi_currency(
    client: TestClient,
    test_tenant: Tenant,
    test_user: User,
    auth_headers: dict,
    db_session: Session
):
    """Test revenue by status with multiple currencies."""
    # Create paid invoices in different currencies
    paid_usd = Invoice(
        invoice_number="INV-001",
        tenant_id=test_tenant.id,
        creator_id=test_user.id,
        customer_name="Customer 1",
        status=InvoiceStatus.PAID,
        currency=Currency.USD,
        issue_date="2024-01-01",
        total_amount=Decimal("100.00")
    )
    paid_eur = Invoice(
        invoice_number="INV-002",
        tenant_id=test_tenant.id,
        creator_id=test_user.id,
        customer_name="Customer 2",
        status=InvoiceStatus.PAID,
        currency=Currency.EUR,
        issue_date="2024-01-02",
        total_amount=Decimal("200.00")
    )
    
    # Create sent invoices in different currencies
    sent_usd = Invoice(
        invoice_number="INV-003",
        tenant_id=test_tenant.id,
        creator_id=test_user.id,
        customer_name="Customer 3",
        status=InvoiceStatus.SENT,
        currency=Currency.USD,
        issue_date="2024-01-03",
        total_amount=Decimal("300.00")
    )
    sent_gbp = Invoice(
        invoice_number="INV-004",
        tenant_id=test_tenant.id,
        creator_id=test_user.id,
        customer_name="Customer 4",
        status=InvoiceStatus.SENT,
        currency=Currency.GBP,
        issue_date="2024-01-04",
        total_amount=Decimal("150.00")
    )

    db_session.add_all([paid_usd, paid_eur, sent_usd, sent_gbp])
    db_session.commit()

    # Get revenue by status
    response = client.get(
        "/api/v1/analytics/revenue-by-status",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2  # 2 statuses: paid and sent

    # Convert to dict for easier testing
    status_dict = {item["status"]: item for item in data}

    # Verify paid invoices are grouped by currency
    assert status_dict["paid"]["count"] == 2
    assert "USD" in status_dict["paid"]["total_amount"]
    assert "EUR" in status_dict["paid"]["total_amount"]
    assert Decimal(status_dict["paid"]["total_amount"]["USD"]) == Decimal("100.00")
    assert Decimal(status_dict["paid"]["total_amount"]["EUR"]) == Decimal("200.00")

    # Verify sent invoices are grouped by currency
    assert status_dict["sent"]["count"] == 2
    assert "USD" in status_dict["sent"]["total_amount"]
    assert "GBP" in status_dict["sent"]["total_amount"]
    assert Decimal(status_dict["sent"]["total_amount"]["USD"]) == Decimal("300.00")
    assert Decimal(status_dict["sent"]["total_amount"]["GBP"]) == Decimal("150.00")
