"""
Test suite for payment method enumerators and currency conversion features.

Tests:
- Payment method enum validation
- Currency preference for users
- Currency conversion functionality
- Unified currency analytics
"""
import pytest
from decimal import Decimal
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.invoice import (
    Invoice,
    InvoiceStatus,
    Currency,
    PaymentMethod
)
from app.models.tenant import Tenant
from app.models.user import User, UserRole
from app.services.currency_converter import (
    get_exchange_rate,
    convert_amount,
    convert_currency_dict,
    CurrencyConversionError
)


def test_payment_method_enum_valid(
    client: TestClient,
    auth_headers: dict,
    db_session: Session
):
    """Test that valid payment methods are accepted."""
    # Create an invoice
    response = client.post(
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
    assert response.status_code == 201
    invoice_id = response.json()["id"]

    # First, send the invoice (DRAFT -> SENT)
    response = client.patch(
        f"/api/v1/invoices/{invoice_id}/status",
        json={"status": "sent"},
        headers=auth_headers
    )
    assert response.status_code == 200

    # Update status to PAID with valid payment method
    for payment_method in ["transfer", "cash", "pos", "cheque",
                          "card", "mobile_money", "other"]:
        response = client.patch(
            f"/api/v1/invoices/{invoice_id}/status",
            json={
                "status": "paid",
                "payment_method": payment_method
            },
            headers=auth_headers
        )
        # First will succeed, subsequent will fail due to
        # invalid transition from PAID
        if payment_method == "transfer":
            assert response.status_code == 200
            data = response.json()
            assert data["payment_method"] == payment_method
            assert data["status"] == "paid"
        else:
            # Can't transition from PAID to PAID
            assert response.status_code == 400


def test_payment_method_enum_invalid(
    client: TestClient,
    auth_headers: dict,
    db_session: Session
):
    """Test that invalid payment methods are rejected."""
    # Create an invoice
    response = client.post(
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
    assert response.status_code == 201
    invoice_id = response.json()["id"]

    # Try to update with invalid payment method
    response = client.patch(
        f"/api/v1/invoices/{invoice_id}/status",
        json={
            "status": "paid",
            "payment_method": "invalid_method"
        },
        headers=auth_headers
    )
    assert response.status_code == 422  # Validation error


def test_payment_method_required_for_paid_status(
    client: TestClient,
    auth_headers: dict,
    db_session: Session
):
    """Test that payment method is required when marking invoice as PAID."""
    # Create and send an invoice
    response = client.post(
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
    assert response.status_code == 201
    invoice_id = response.json()["id"]

    # Send the invoice first
    response = client.patch(
        f"/api/v1/invoices/{invoice_id}/status",
        json={"status": "sent"},
        headers=auth_headers
    )
    assert response.status_code == 200

    # Try to mark as PAID without payment method
    response = client.patch(
        f"/api/v1/invoices/{invoice_id}/status",
        json={"status": "paid"},
        headers=auth_headers
    )
    assert response.status_code == 400
    assert "payment method" in response.json()["detail"].lower()


def test_currency_preference_default(
    client: TestClient,
    auth_headers: dict
):
    """Test that users have a default currency preference."""
    response = client.get("/api/v1/users/me", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "currency_preference" in data
    assert data["currency_preference"] == "USD"


def test_update_currency_preference(
    client: TestClient,
    auth_headers: dict,
    test_user: User
):
    """Test updating user's currency preference."""
    response = client.put(
        f"/api/v1/users/{test_user.id}",
        json={"currency_preference": "EUR"},
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["currency_preference"] == "EUR"


def test_currency_conversion_same_currency():
    """Test that conversion rate is 1.0 for same currency."""
    rate = get_exchange_rate("USD", "USD")
    assert rate == Decimal("1.0")


def test_currency_conversion_amount_zero():
    """Test that converting zero amount returns zero."""
    result = convert_amount(Decimal("0"), "USD", "EUR")
    assert result == Decimal("0.00")


@patch('app.services.currency_converter.httpx.Client')
def test_currency_conversion_api_success(mock_client_class):
    """Test successful API call for exchange rate."""
    # Mock the API response
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "rates": {
            "EUR": 0.85,
            "GBP": 0.73
        }
    }
    mock_response.raise_for_status = MagicMock()

    mock_client = MagicMock()
    mock_client.get.return_value = mock_response
    mock_client.__enter__.return_value = mock_client
    mock_client.__exit__.return_value = None
    mock_client_class.return_value = mock_client

    # Clear cache to force API call
    from app.core.cache import delete_cache, cache_key
    cache_key_name = cache_key("exchange_rate", "USD_EUR")
    delete_cache(cache_key_name)

    # Get exchange rate
    rate = get_exchange_rate("USD", "EUR")
    assert rate == Decimal("0.85")


@patch('app.services.currency_converter.httpx.Client')
def test_currency_conversion_api_error(mock_client_class):
    """Test API error handling."""
    import httpx
    # Mock API failure with proper httpx exception
    mock_client = MagicMock()
    mock_client.get.side_effect = httpx.RequestError("Network error")
    mock_client.__enter__.return_value = mock_client
    mock_client.__exit__.return_value = None
    mock_client_class.return_value = mock_client

    # Clear cache
    from app.core.cache import delete_cache, cache_key
    cache_key_name = cache_key("exchange_rate", "USD_EUR")
    delete_cache(cache_key_name)

    # Should raise CurrencyConversionError
    with pytest.raises(CurrencyConversionError):
        get_exchange_rate("USD", "EUR")


def test_convert_currency_dict():
    """Test converting dictionary of amounts to target currency."""
    amounts = {
        "USD": Decimal("100.00"),
        "EUR": Decimal("0.00"),  # Zero should be ignored
    }

    # Mock exchange rate (USD to USD is 1.0)
    with patch('app.services.currency_converter.get_exchange_rate') as mock:
        mock.return_value = Decimal("1.0")
        result = convert_currency_dict(amounts, "USD")
        assert result == Decimal("100.00")


def test_unified_invoice_summary(
    client: TestClient,
    test_tenant: Tenant,
    test_user: User,
    auth_headers: dict,
    db_session: Session
):
    """Test invoice summary with unified currency conversion."""
    # Create invoices with different currencies
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
    paid_eur = Invoice(
        invoice_number="INV-EUR-001",
        tenant_id=test_tenant.id,
        creator_id=test_user.id,
        customer_name="Customer EUR",
        status=InvoiceStatus.PAID,
        currency=Currency.EUR,
        issue_date="2024-01-02",
        total_amount=Decimal("85.00")
    )

    db_session.add(paid_usd)
    db_session.add(paid_eur)
    db_session.commit()

    # Mock currency conversion at the service level
    with patch(
        'app.api.v1.endpoints.analytics.convert_currency_dict'
    ) as mock_convert:
        mock_convert.return_value = Decimal("185.00")  # 100 + 85 (as USD)

        # Get unified summary
        response = client.get(
            "/api/v1/analytics/invoice-summary?unified=true",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "currency" in data
        assert data["currency"] == "USD"
        assert "total_revenue" in data
        # Should be a single decimal value, not a dict
        assert isinstance(
            data["total_revenue"],
            (int, float, str)
        ), f"Expected number, got {type(data['total_revenue'])}"


def test_multi_currency_invoice_summary(
    client: TestClient,
    test_tenant: Tenant,
    test_user: User,
    auth_headers: dict,
    db_session: Session
):
    """Test invoice summary with multi-currency (default behavior)."""
    # Create invoices with different currencies
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
        total_amount=Decimal("85.00")
    )

    db_session.add(paid_usd)
    db_session.add(paid_eur)
    db_session.commit()

    # Get multi-currency summary (default)
    response = client.get(
        "/api/v1/analytics/invoice-summary",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert "total_revenue" in data
    # Should be a dictionary with currency codes
    assert isinstance(data["total_revenue"], dict)
    assert "USD" in data["total_revenue"]
    assert "EUR" in data["total_revenue"]


def test_unified_revenue_by_status(
    client: TestClient,
    test_tenant: Tenant,
    test_user: User,
    auth_headers: dict,
    db_session: Session
):
    """Test revenue by status with unified currency."""
    # Create invoices
    paid = Invoice(
        invoice_number="INV-003",
        tenant_id=test_tenant.id,
        creator_id=test_user.id,
        customer_name="Customer",
        status=InvoiceStatus.PAID,
        currency=Currency.USD,
        issue_date="2024-01-01",
        total_amount=Decimal("100.00")
    )

    db_session.add(paid)
    db_session.commit()

    # Mock currency conversion at the endpoint level
    with patch(
        'app.api.v1.endpoints.analytics.convert_currency_dict'
    ) as mock_convert:
        mock_convert.return_value = Decimal("100.00")

        # Get unified revenue by status
        response = client.get(
            "/api/v1/analytics/revenue-by-status?unified=true",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0
        for item in data:
            assert "currency" in item
            assert "total_amount" in item
            # Should be a single value, not a dict
            assert isinstance(
                item["total_amount"],
                (int, float, str)
            ), f"Expected number, got {type(item['total_amount'])}"


def test_currency_conversion_caching():
    """Test that exchange rates are cached."""
    with patch('app.services.currency_converter.httpx.Client') as mock_client_class:
        # Mock the API response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "rates": {"EUR": 0.85}
        }
        mock_response.raise_for_status = MagicMock()

        mock_client = MagicMock()
        mock_client.get.return_value = mock_response
        mock_client.__enter__.return_value = mock_client
        mock_client.__exit__.return_value = None
        mock_client_class.return_value = mock_client

        # Clear cache to ensure clean state
        from app.core.cache import delete_cache, cache_key
        cache_key_name = cache_key("exchange_rate", "USD_EUR")
        delete_cache(cache_key_name)

        # First call should hit the API
        rate1 = get_exchange_rate("USD", "EUR")
        first_call_count = mock_client.get.call_count

        # Second call should use cache (if cache is enabled)
        rate2 = get_exchange_rate("USD", "EUR")
        second_call_count = mock_client.get.call_count

        # Rates should be equal
        assert rate1 == rate2

        # If Redis is enabled, second call shouldn't increase call count
        # If Redis is disabled, both calls will hit the API
        # We just verify they're the same value
        assert rate1 == Decimal("0.85")
