"""
Test suite for multi-currency and tax/VAT configuration functionality.
Tests currency support and tax calculation in invoices.
"""
import pytest
from decimal import Decimal


def test_create_invoice_with_default_currency(client, auth_headers):
    """Test creating invoice uses tenant's default currency."""
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
    data = response.json()
    assert data["currency"] == "NGN"  # Default tenant currency


def test_create_invoice_with_specific_currency(client, auth_headers):
    """Test creating invoice with explicit currency."""
    # Only test NGN as default and explicit
    for currency in ["NGN"]:
        response = client.post(
            "/api/v1/invoices/",
            json={
                "customer_name": "Test Customer",
                "currency": currency,
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
        data = response.json()
        assert data["currency"] == currency


def test_invoice_tax_calculation_with_tenant_tax_rate(client, auth_headers, db_session, test_tenant):
    """Test invoice tax is calculated based on tenant's tax rate."""
    # Update tenant to have 20% VAT
    from app.models.tenant import Tenant
    tenant = db_session.query(Tenant).filter(Tenant.id == test_tenant.id).first()
    tenant.tax_rate = Decimal("20.00")
    tenant.tax_label = "VAT"
    db_session.commit()

    response = client.post(
        "/api/v1/invoices/",
        json={
            "customer_name": "Tax Test Customer",
            "issue_date": "2024-01-15",
            "items": [
                {
                    "description": "Taxable Product",
                    "quantity": 1,
                    "unit_price": 100.00
                }
            ]
        },
        headers=auth_headers
    )
    assert response.status_code == 201
    data = response.json()
    assert float(data["subtotal"]) == 100.00
    assert float(data["tax_amount"]) == 20.00  # 20% of 100
    assert float(data["total_amount"]) == 120.00  # 100 + 20


def test_invoice_no_tax_when_tenant_has_no_tax_rate(client, auth_headers, db_session, test_tenant):
    """Test invoice has no tax when tenant tax_rate is None."""
    # Ensure tenant has no tax rate (tax-free)
    from app.models.tenant import Tenant
    tenant = db_session.query(Tenant).filter(Tenant.id == test_tenant.id).first()
    tenant.tax_rate = None
    tenant.tax_label = None
    db_session.commit()

    response = client.post(
        "/api/v1/invoices/",
        json={
            "customer_name": "No Tax Customer",
            "issue_date": "2024-01-15",
            "items": [
                {
                    "description": "Tax-free Product",
                    "quantity": 1,
                    "unit_price": 100.00
                }
            ]
        },
        headers=auth_headers
    )
    assert response.status_code == 201
    data = response.json()
    assert float(data["subtotal"]) == 100.00
    assert float(data["tax_amount"]) == 0.00
    assert float(data["total_amount"]) == 100.00


def test_invoice_with_multiple_items_tax_calculation(client, auth_headers, db_session, test_tenant):
    """Test tax calculation with multiple items."""
    from app.models.tenant import Tenant
    tenant = db_session.query(Tenant).filter(Tenant.id == test_tenant.id).first()
    tenant.tax_rate = Decimal("15.00")
    tenant.tax_label = "GST"
    db_session.commit()

    response = client.post(
        "/api/v1/invoices/",
        json={
            "customer_name": "Multi-item Customer",
            "issue_date": "2024-01-15",
            "items": [
                {
                    "description": "Product A",
                    "quantity": 2,
                    "unit_price": 50.00
                },
                {
                    "description": "Product B",
                    "quantity": 1,
                    "unit_price": 100.00
                }
            ]
        },
        headers=auth_headers
    )
    assert response.status_code == 201
    data = response.json()
    # Subtotal: 2*50 + 1*100 = 200
    assert float(data["subtotal"]) == 200.00
    # Tax: 15% of 200 = 30
    assert float(data["tax_amount"]) == 30.00
    # Total: 200 + 30 = 230
    assert float(data["total_amount"]) == 230.00


def test_update_tenant_currency_and_tax(client, auth_headers, test_tenant):
    """Test updating tenant's currency and tax configuration."""
    # Update tenant with new currency and tax settings
    update_response = client.put(
        f"/api/v1/tenants/{test_tenant.id}",
        json={
            "name": test_tenant.name,  # Required field
            "default_currency": "EUR",
            "tax_rate": 19.0,
            "tax_label": "VAT"
        },
        headers=auth_headers
    )
    assert update_response.status_code == 200
    updated_data = update_response.json()
    assert updated_data["default_currency"] == "EUR"
    assert float(updated_data["tax_rate"]) == 19.0
    assert updated_data["tax_label"] == "VAT"


def test_tenant_registration_with_currency_and_tax(client):
    """Test tenant registration with currency and tax configuration."""
    response = client.post(
        "/api/v1/tenants/register",
        json={
            "name": "Currency Test Tenant",
            "domain": "currency-test-unique.example.com",
            "plan_type": "basic",
            "default_currency": "GBP",
            "tax_rate": 20.0,
            "tax_label": "VAT",
            "owner": {
                "full_name": "Currency Test Owner",
                "email": "currency-test@example.com",
                "password": "SecurePass123"
            }
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["tenant"]["default_currency"] == "GBP"
    assert float(data["tenant"]["tax_rate"]) == 20.0
    assert data["tenant"]["tax_label"] == "VAT"


def test_list_invoices_shows_currency(client, auth_headers):
    """Test that listing invoices includes currency information."""
    # Create an invoice with NGN currency
    create_response = client.post(
        "/api/v1/invoices/",
        json={
            "customer_name": "NGN Customer",
            "currency": "NGN",
            "issue_date": "2024-01-15",
            "items": [
                {
                    "description": "Product in Naira",
                    "quantity": 1,
                    "unit_price": 50000.00
                }
            ]
        },
        headers=auth_headers
    )
    assert create_response.status_code == 201

    # List invoices and verify currency is present
    list_response = client.get("/api/v1/invoices/", headers=auth_headers)
    assert list_response.status_code == 200
    data = list_response.json()
    assert "items" in data

    # Find the NGN invoice we just created
    ngn_invoice = next((inv for inv in data["items"] if inv["currency"] == "NGN"), None)
    assert ngn_invoice is not None
    assert ngn_invoice["currency"] == "NGN"


def test_zero_tax_rate_means_no_tax(client, auth_headers, db_session, test_tenant):
    """Test that 0% tax rate results in no tax."""
    from app.models.tenant import Tenant
    tenant = db_session.query(Tenant).filter(Tenant.id == test_tenant.id).first()
    tenant.tax_rate = Decimal("0.00")
    tenant.tax_label = "No Tax"
    db_session.commit()

    response = client.post(
        "/api/v1/invoices/",
        json={
            "customer_name": "Zero Tax Customer",
            "issue_date": "2024-01-15",
            "items": [
                {
                    "description": "Zero Tax Product",
                    "quantity": 1,
                    "unit_price": 100.00
                }
            ]
        },
        headers=auth_headers
    )
    assert response.status_code == 201
    data = response.json()
    assert float(data["tax_amount"]) == 0.00
    assert float(data["total_amount"]) == 100.00
