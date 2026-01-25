"""
Test suite for payment method enumerators and currency preference features.
Tests payment method validation, currency conversion, and unified analytics.
"""
from decimal import Decimal
import pytest
from app.models.invoice import Invoice, InvoiceStatus, Currency, PaymentMethod
from app.models.user import User


def test_payment_method_enum_valid_lowercase(
    client, auth_headers, db_session, test_tenant, test_user
):
    """Test payment method with valid lowercase value."""
    # Create invoice
    invoice_response = client.post(
        "/api/v1/invoices/",
        json={
            "customer_name": "Test Customer",
            "issue_date": "2024-01-15",
            "items": [
                {
                    "description": "Product A",
                    "quantity": 1,
                    "unit_price": 100.00
                }
            ]
        },
        headers=auth_headers
    )
    assert invoice_response.status_code == 201
    invoice_id = invoice_response.json()["id"]

    # Update to SENT status
    sent_response = client.patch(
        f"/api/v1/invoices/{invoice_id}/status",
        json={"status": "sent"},
        headers=auth_headers
    )
    assert sent_response.status_code == 200

    # Update to PAID with lowercase payment method
    response = client.patch(
        f"/api/v1/invoices/{invoice_id}/status",
        json={
            "status": "paid",
            "payment_method": "transfer"
        },
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "paid"
    assert data["payment_method"] == "transfer"


def test_payment_method_enum_valid_uppercase(
    client, auth_headers, db_session, test_tenant, test_user
):
    """Test payment method with uppercase value (should be normalized)."""
    # Create invoice
    invoice_response = client.post(
        "/api/v1/invoices/",
        json={
            "customer_name": "Test Customer",
            "issue_date": "2024-01-15",
            "items": [
                {
                    "description": "Product A",
                    "quantity": 1,
                    "unit_price": 100.00
                }
            ]
        },
        headers=auth_headers
    )
    assert invoice_response.status_code == 201
    invoice_id = invoice_response.json()["id"]

    # Update to SENT status
    sent_response = client.patch(
        f"/api/v1/invoices/{invoice_id}/status",
        json={"status": "sent"},
        headers=auth_headers
    )
    assert sent_response.status_code == 200

    # Update to PAID with uppercase payment method
    response = client.patch(
        f"/api/v1/invoices/{invoice_id}/status",
        json={
            "status": "paid",
            "payment_method": "CASH"
        },
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "paid"
    assert data["payment_method"] == "cash"


def test_payment_method_enum_invalid(
    client, auth_headers, db_session, test_tenant, test_user
):
    """Test payment method with invalid value returns error."""
    # Create invoice
    invoice_response = client.post(
        "/api/v1/invoices/",
        json={
            "customer_name": "Test Customer",
            "issue_date": "2024-01-15",
            "items": [
                {
                    "description": "Product A",
                    "quantity": 1,
                    "unit_price": 100.00
                }
            ]
        },
        headers=auth_headers
    )
    assert invoice_response.status_code == 201
    invoice_id = invoice_response.json()["id"]

    # Update to SENT status
    sent_response = client.patch(
        f"/api/v1/invoices/{invoice_id}/status",
        json={"status": "sent"},
        headers=auth_headers
    )
    assert sent_response.status_code == 200

    # Try to update to PAID with invalid payment method
    response = client.patch(
        f"/api/v1/invoices/{invoice_id}/status",
        json={
            "status": "paid",
            "payment_method": "invalid_method"
        },
        headers=auth_headers
    )
    assert response.status_code == 422
    error = response.json()
    assert "details" in error  # Changed from "detail" to "details" for validation errors
    assert isinstance(error["details"], list)  # Ensure details is a list
    # Check details for validation error message
    assert any("Invalid payment method" in str(detail) for detail in error["details"])


def test_payment_method_enum_all_valid_values(
    client, auth_headers, db_session, test_tenant, test_user
):
    """Test all valid payment method enum values."""
    valid_methods = [
        "transfer", "cash", "pos", "cheque", "card", "mobile_money", "other"
    ]

    for method in valid_methods:
        # Create invoice
        invoice_response = client.post(
            "/api/v1/invoices/",
            json={
                "customer_name": "Test Customer",
                "issue_date": "2024-01-15",
                "items": [
                    {
                        "description": "Product A",
                        "quantity": 1,
                        "unit_price": 100.00
                    }
                ]
            },
            headers=auth_headers
        )
        assert invoice_response.status_code == 201
        invoice_id = invoice_response.json()["id"]

        # Update to SENT
        client.patch(
            f"/api/v1/invoices/{invoice_id}/status",
            json={"status": "sent"},
            headers=auth_headers
        )

        # Update to PAID with this payment method
        response = client.patch(
            f"/api/v1/invoices/{invoice_id}/status",
            json={
                "status": "paid",
                "payment_method": method
            },
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["payment_method"] == method


def test_user_currency_preference_default(
    client, db_session, test_user
):
    """Test that new users have NGN as default currency preference."""
    assert test_user.currency_preference == "NGN"


def test_user_currency_preference_on_creation(
    client, db_session, test_tenant
):
    """Test setting currency preference on user creation."""
    from app.core.security import get_password_hash

    # Create user with USD preference
    user = User(
        email="usd_user@testcompany.com",
        full_name="USD User",
        hashed_password=get_password_hash("TestPass123!"),
        tenant_id=test_tenant.id,
        currency_preference="USD",
        is_active=True,
        is_verified=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    assert user.currency_preference == "USD"


def test_invoice_summary_unified_currency_ngn(
    client, auth_headers, db_session, test_tenant, test_user
):
    """Test invoice summary returns amounts in user's preferred currency."""
    # Create invoices in different currencies
    # Paid invoice in USD
    paid_usd = Invoice(
        invoice_number="INV-USD-001",
        tenant_id=test_tenant.id,
        creator_id=test_user.id,
        customer_name="Customer USD",
        status=InvoiceStatus.PAID,
        currency=Currency.USD,
        issue_date="2024-01-01",
        total_amount=Decimal("100.00")
    )

    # Sent invoice in EUR
    sent_eur = Invoice(
        invoice_number="INV-EUR-001",
        tenant_id=test_tenant.id,
        creator_id=test_user.id,
        customer_name="Customer EUR",
        status=InvoiceStatus.SENT,
        currency=Currency.EUR,
        issue_date="2024-01-02",
        total_amount=Decimal("50.00")
    )

    # Overdue invoice in GBP
    overdue_gbp = Invoice(
        invoice_number="INV-GBP-001",
        tenant_id=test_tenant.id,
        creator_id=test_user.id,
        customer_name="Customer GBP",
        status=InvoiceStatus.OVERDUE,
        currency=Currency.GBP,
        issue_date="2024-01-03",
        total_amount=Decimal("75.00")
    )

    db_session.add_all([paid_usd, sent_eur, overdue_gbp])
    db_session.commit()

    # Get summary
    response = client.get(
        "/api/v1/analytics/invoice-summary",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()

    # Verify response structure
    assert "total_revenue" in data
    assert "pending_amount" in data
    assert "overdue_amount" in data
    assert "currency" in data
    assert data["currency"] == "NGN"

    # Verify amounts are not dictionaries but single values
    assert isinstance(data["total_revenue"], (int, float, str))
    assert isinstance(data["pending_amount"], (int, float, str))
    assert isinstance(data["overdue_amount"], (int, float, str))

    # Verify conversions (100 USD = 165000 NGN, 50 EUR = 90000 NGN,
    # 75 GBP = 157500 NGN)
    total_revenue = Decimal(str(data["total_revenue"]))
    pending_amount = Decimal(str(data["pending_amount"]))
    overdue_amount = Decimal(str(data["overdue_amount"]))

    assert total_revenue == Decimal("165000.00")  # 100 USD * 1650
    assert pending_amount == Decimal("90000.00")  # 50 EUR * 1800
    assert overdue_amount == Decimal("157500.00")  # 75 GBP * 2100


def test_revenue_by_status_unified_currency(
    client, auth_headers, db_session, test_tenant, test_user
):
    """Test revenue by status returns amounts in user's preferred currency."""
    # Create invoices in different currencies with same status
    paid_usd = Invoice(
        invoice_number="INV-USD-002",
        tenant_id=test_tenant.id,
        creator_id=test_user.id,
        customer_name="Customer USD",
        status=InvoiceStatus.PAID,
        currency=Currency.USD,
        issue_date="2024-01-01",
        total_amount=Decimal("100.00")
    )

    paid_eur = Invoice(
        invoice_number="INV-EUR-002",
        tenant_id=test_tenant.id,
        creator_id=test_user.id,
        customer_name="Customer EUR",
        status=InvoiceStatus.PAID,
        currency=Currency.EUR,
        issue_date="2024-01-02",
        total_amount=Decimal("50.00")
    )

    db_session.add_all([paid_usd, paid_eur])
    db_session.commit()

    # Get revenue by status
    response = client.get(
        "/api/v1/analytics/revenue-by-status",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()

    # Find paid status entry
    paid_entry = next((item for item in data if item["status"] == "paid"),
                      None)
    assert paid_entry is not None
    assert "total_amount" in paid_entry
    assert "currency" in paid_entry
    assert paid_entry["currency"] == "NGN"

    # Verify amount is single value, not dictionary
    assert isinstance(paid_entry["total_amount"], (int, float, str))

    # Verify conversion (100 USD + 50 EUR = 165000 + 90000 = 255000 NGN)
    total_amount = Decimal(str(paid_entry["total_amount"]))
    assert total_amount == Decimal("255000.00")


def test_currency_preference_affects_analytics(
    client, db_session, test_tenant
):
    """Test that different users with different currency preferences
    see different values."""
    from app.core.security import get_password_hash

    # Create user with USD preference
    usd_user = User(
        email="usd_user2@testcompany.com",
        full_name="USD User 2",
        hashed_password=get_password_hash("TestPass123!"),
        tenant_id=test_tenant.id,
        currency_preference="USD",
        is_active=True,
        is_verified=True
    )
    db_session.add(usd_user)
    db_session.commit()

    # Create invoice in NGN
    invoice = Invoice(
        invoice_number="INV-NGN-001",
        tenant_id=test_tenant.id,
        creator_id=usd_user.id,
        customer_name="Customer NGN",
        status=InvoiceStatus.PAID,
        currency=Currency.NGN,
        issue_date="2024-01-01",
        total_amount=Decimal("1650.00")  # Exactly 1 USD worth
    )
    db_session.add(invoice)
    db_session.commit()

    # Login as USD user
    login_response = client.post(
        "/api/v1/auth/login",
        data={
            "username": "usd_user2@testcompany.com",
            "password": "TestPass123!"
        }
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    usd_headers = {"Authorization": f"Bearer {token}"}

    # Get summary
    response = client.get(
        "/api/v1/analytics/invoice-summary",
        headers=usd_headers
    )
    assert response.status_code == 200
    data = response.json()

    assert data["currency"] == "USD"
    total_revenue = Decimal(str(data["total_revenue"]))
    # 1650 NGN / 1650 = 1 USD
    assert total_revenue == Decimal("1.00")


def test_payment_method_required_for_paid_status(
    client, auth_headers, db_session, test_tenant, test_user
):
    """Test that payment method is required when marking invoice as PAID."""
    # Create invoice
    invoice_response = client.post(
        "/api/v1/invoices/",
        json={
            "customer_name": "Test Customer",
            "issue_date": "2024-01-15",
            "items": [
                {
                    "description": "Product A",
                    "quantity": 1,
                    "unit_price": 100.00
                }
            ]
        },
        headers=auth_headers
    )
    invoice_id = invoice_response.json()["id"]

    # Update to SENT
    client.patch(
        f"/api/v1/invoices/{invoice_id}/status",
        json={"status": "sent"},
        headers=auth_headers
    )

    # Try to mark as PAID without payment method
    response = client.patch(
        f"/api/v1/invoices/{invoice_id}/status",
        json={"status": "paid"},
        headers=auth_headers
    )
    assert response.status_code == 400
    assert "payment method" in response.json()["message"].lower()
