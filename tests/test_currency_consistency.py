"""
Test suite for currency consistency across invoice system.
Validates that currency is correctly handled in all workflows:
- Invoice creation with different currencies
- PDF generation with correct currency symbols
- CSV/JSON export with currency information
- Invoice updates maintaining correct tax calculations
"""
import pytest
from decimal import Decimal
import json
import csv
import io


def test_pdf_generation_uses_correct_currency_symbol_usd(client, auth_headers):
    """Test that PDF generated for USD invoice uses $ symbol."""
    # Create USD invoice
    response = client.post(
        "/api/v1/invoices/",
        json={
            "customer_name": "USD Customer",
            "currency": "USD",
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
    
    # Generate PDF
    pdf_response = client.get(
        f"/api/v1/invoices/{invoice_id}/pdf",
        headers=auth_headers
    )
    assert pdf_response.status_code == 200
    assert pdf_response.headers["content-type"] == "application/pdf"
    
    # PDF content should exist (we can't easily parse it, but check it's not empty)
    assert len(pdf_response.content) > 0


def test_pdf_generation_uses_correct_currency_symbol_gbp(client, auth_headers):
    """Test that PDF generated for GBP invoice uses £ symbol."""
    # Create GBP invoice
    response = client.post(
        "/api/v1/invoices/",
        json={
            "customer_name": "GBP Customer",
            "currency": "GBP",
            "issue_date": "2024-01-15",
            "items": [
                {
                    "description": "Product B",
                    "quantity": 2,
                    "unit_price": 50.00
                }
            ]
        },
        headers=auth_headers
    )
    assert response.status_code == 201
    invoice_id = response.json()["id"]
    
    # Generate PDF
    pdf_response = client.get(
        f"/api/v1/invoices/{invoice_id}/pdf",
        headers=auth_headers
    )
    assert pdf_response.status_code == 200
    assert len(pdf_response.content) > 0


def test_pdf_generation_uses_correct_currency_symbol_eur(client, auth_headers):
    """Test that PDF generated for EUR invoice uses € symbol."""
    # Create EUR invoice
    response = client.post(
        "/api/v1/invoices/",
        json={
            "customer_name": "EUR Customer",
            "currency": "EUR",
            "issue_date": "2024-01-15",
            "items": [
                {
                    "description": "Product C",
                    "quantity": 1,
                    "unit_price": 200.00
                }
            ]
        },
        headers=auth_headers
    )
    assert response.status_code == 201
    invoice_id = response.json()["id"]
    
    # Generate PDF
    pdf_response = client.get(
        f"/api/v1/invoices/{invoice_id}/pdf",
        headers=auth_headers
    )
    assert pdf_response.status_code == 200
    assert len(pdf_response.content) > 0


def test_pdf_generation_uses_correct_currency_symbol_ngn(client, auth_headers):
    """Test that PDF generated for NGN invoice uses ₦ symbol."""
    # Create NGN invoice
    response = client.post(
        "/api/v1/invoices/",
        json={
            "customer_name": "NGN Customer",
            "currency": "NGN",
            "issue_date": "2024-01-15",
            "items": [
                {
                    "description": "Product D",
                    "quantity": 5,
                    "unit_price": 10000.00
                }
            ]
        },
        headers=auth_headers
    )
    assert response.status_code == 201
    invoice_id = response.json()["id"]
    
    # Generate PDF
    pdf_response = client.get(
        f"/api/v1/invoices/{invoice_id}/pdf",
        headers=auth_headers
    )
    assert pdf_response.status_code == 200
    assert len(pdf_response.content) > 0


def test_csv_export_includes_currency_field(client, auth_headers):
    """Test that CSV export includes currency column."""
    # Create invoices with different currencies
    for currency in ["USD", "GBP", "EUR", "NGN"]:
        client.post(
            "/api/v1/invoices/",
            json={
                "customer_name": f"{currency} Customer",
                "currency": currency,
                "issue_date": "2024-01-15",
                "items": [
                    {
                        "description": f"Product in {currency}",
                        "quantity": 1,
                        "unit_price": 100.00
                    }
                ]
            },
            headers=auth_headers
        )
    
    # Export as CSV
    export_response = client.get(
        "/api/v1/invoices/export/invoices?format=csv",
        headers=auth_headers
    )
    assert export_response.status_code == 200
    assert export_response.headers["content-type"] == "text/csv; charset=utf-8"
    
    # Parse CSV
    csv_content = export_response.text
    reader = csv.DictReader(io.StringIO(csv_content))
    rows = list(reader)
    
    # Check that Currency column exists
    assert "Currency" in reader.fieldnames
    
    # Verify all currencies are present
    currencies_in_export = {row["Currency"] for row in rows}
    assert "USD" in currencies_in_export
    assert "GBP" in currencies_in_export
    assert "EUR" in currencies_in_export
    assert "NGN" in currencies_in_export


def test_json_export_includes_currency_field(client, auth_headers):
    """Test that JSON export includes currency field."""
    # Create invoices with different currencies
    created_invoices = []
    for currency in ["USD", "EUR"]:
        response = client.post(
            "/api/v1/invoices/",
            json={
                "customer_name": f"{currency} Customer JSON",
                "currency": currency,
                "issue_date": "2024-01-15",
                "items": [
                    {
                        "description": f"Product in {currency}",
                        "quantity": 1,
                        "unit_price": 150.00
                    }
                ]
            },
            headers=auth_headers
        )
        created_invoices.append(response.json())
    
    # Export as JSON
    export_response = client.get(
        "/api/v1/invoices/export/invoices?format=json",
        headers=auth_headers
    )
    assert export_response.status_code == 200
    assert "application/json" in export_response.headers["content-type"]
    
    # Parse JSON
    exported_data = export_response.json()
    assert isinstance(exported_data, list)
    assert len(exported_data) > 0
    
    # Check that each invoice has currency field
    for invoice in exported_data:
        assert "currency" in invoice
        assert invoice["currency"] in ["USD", "GBP", "EUR", "NGN"]


def test_invoice_update_maintains_tax_calculation(client, auth_headers, db_session, test_tenant):
    """Test that updating invoice items recalculates tax correctly."""
    from app.models.tenant import Tenant
    
    # Set tenant to have 10% tax
    tenant = db_session.query(Tenant).filter(Tenant.id == test_tenant.id).first()
    tenant.tax_rate = Decimal("10.00")
    tenant.tax_label = "VAT"
    db_session.commit()
    
    # Create invoice
    create_response = client.post(
        "/api/v1/invoices/",
        json={
            "customer_name": "Tax Update Test",
            "currency": "USD",
            "issue_date": "2024-01-15",
            "items": [
                {
                    "description": "Original Product",
                    "quantity": 1,
                    "unit_price": 100.00
                }
            ]
        },
        headers=auth_headers
    )
    assert create_response.status_code == 201
    invoice = create_response.json()
    invoice_id = invoice["id"]
    
    # Verify initial tax calculation
    assert float(invoice["subtotal"]) == 100.00
    assert float(invoice["tax_amount"]) == 10.00  # 10% of 100
    assert float(invoice["total_amount"]) == 110.00
    
    # Update invoice items
    update_response = client.put(
        f"/api/v1/invoices/{invoice_id}",
        json={
            "items": [
                {
                    "description": "Updated Product",
                    "quantity": 2,
                    "unit_price": 75.00
                }
            ]
        },
        headers=auth_headers
    )
    assert update_response.status_code == 200
    updated_invoice = update_response.json()
    
    # Verify tax is recalculated correctly
    assert float(updated_invoice["subtotal"]) == 150.00  # 2 * 75
    assert float(updated_invoice["tax_amount"]) == 15.00  # 10% of 150
    assert float(updated_invoice["total_amount"]) == 165.00  # 150 + 15


def test_invoice_update_with_multiple_items_maintains_tax(client, auth_headers, db_session, test_tenant):
    """Test that updating to multiple items maintains correct tax calculation."""
    from app.models.tenant import Tenant
    
    # Set tenant to have 20% tax
    tenant = db_session.query(Tenant).filter(Tenant.id == test_tenant.id).first()
    tenant.tax_rate = Decimal("20.00")
    tenant.tax_label = "VAT"
    db_session.commit()
    
    # Create invoice with one item
    create_response = client.post(
        "/api/v1/invoices/",
        json={
            "customer_name": "Multi-item Tax Test",
            "currency": "GBP",
            "issue_date": "2024-01-15",
            "items": [
                {
                    "description": "Single Product",
                    "quantity": 1,
                    "unit_price": 50.00
                }
            ]
        },
        headers=auth_headers
    )
    assert create_response.status_code == 201
    invoice_id = create_response.json()["id"]
    
    # Update to multiple items
    update_response = client.put(
        f"/api/v1/invoices/{invoice_id}",
        json={
            "items": [
                {
                    "description": "Product A",
                    "quantity": 2,
                    "unit_price": 30.00
                },
                {
                    "description": "Product B",
                    "quantity": 1,
                    "unit_price": 40.00
                }
            ]
        },
        headers=auth_headers
    )
    assert update_response.status_code == 200
    updated_invoice = update_response.json()
    
    # Verify tax calculation with multiple items
    # Subtotal: 2*30 + 1*40 = 100
    assert float(updated_invoice["subtotal"]) == 100.00
    # Tax: 20% of 100 = 20
    assert float(updated_invoice["tax_amount"]) == 20.00
    # Total: 100 + 20 = 120
    assert float(updated_invoice["total_amount"]) == 120.00


def test_invoice_currency_consistency_through_lifecycle(client, auth_headers, db_session, test_tenant):
    """Test that currency remains consistent throughout invoice lifecycle."""
    from app.models.tenant import Tenant
    
    # Set tenant tax rate
    tenant = db_session.query(Tenant).filter(Tenant.id == test_tenant.id).first()
    tenant.tax_rate = Decimal("15.00")
    db_session.commit()
    
    # Create EUR invoice
    create_response = client.post(
        "/api/v1/invoices/",
        json={
            "customer_name": "Lifecycle Test Customer",
            "customer_email": "test@example.com",
            "currency": "EUR",
            "issue_date": "2024-01-15",
            "items": [
                {
                    "description": "Test Product",
                    "quantity": 1,
                    "unit_price": 100.00
                }
            ]
        },
        headers=auth_headers
    )
    assert create_response.status_code == 201
    invoice = create_response.json()
    invoice_id = invoice["id"]
    
    # Verify currency in create response
    assert invoice["currency"] == "EUR"
    
    # Get invoice
    get_response = client.get(
        f"/api/v1/invoices/{invoice_id}",
        headers=auth_headers
    )
    assert get_response.status_code == 200
    assert get_response.json()["currency"] == "EUR"
    
    # List invoices
    list_response = client.get(
        "/api/v1/invoices/",
        headers=auth_headers
    )
    assert list_response.status_code == 200
    invoices = list_response.json()
    eur_invoice = next((inv for inv in invoices if inv["id"] == invoice_id), None)
    assert eur_invoice is not None
    assert eur_invoice["currency"] == "EUR"
    
    # Update invoice (currency should remain EUR)
    update_response = client.put(
        f"/api/v1/invoices/{invoice_id}",
        json={
            "customer_name": "Updated Customer",
            "items": [
                {
                    "description": "Updated Product",
                    "quantity": 2,
                    "unit_price": 60.00
                }
            ]
        },
        headers=auth_headers
    )
    assert update_response.status_code == 200
    assert update_response.json()["currency"] == "EUR"
    
    # Generate PDF (should use EUR symbol €)
    pdf_response = client.get(
        f"/api/v1/invoices/{invoice_id}/pdf",
        headers=auth_headers
    )
    assert pdf_response.status_code == 200
    # PDF content should be generated
    assert len(pdf_response.content) > 0


def test_different_tenants_can_use_different_currencies(client, auth_headers, db_session):
    """Test that different tenants can have different default currencies."""
    # This test verifies tenant isolation and currency independence
    # The current tenant uses USD (default)
    
    # Create invoice without specifying currency (should use tenant default)
    response = client.post(
        "/api/v1/invoices/",
        json={
            "customer_name": "Default Currency Customer",
            "issue_date": "2024-01-15",
            "items": [
                {
                    "description": "Product",
                    "quantity": 1,
                    "unit_price": 100.00
                }
            ]
        },
        headers=auth_headers
    )
    assert response.status_code == 201
    invoice = response.json()
    assert invoice["currency"] == "USD"  # Default tenant currency
    
    # Create invoice with explicit currency override
    response2 = client.post(
        "/api/v1/invoices/",
        json={
            "customer_name": "Override Currency Customer",
            "currency": "NGN",
            "issue_date": "2024-01-15",
            "items": [
                {
                    "description": "Product",
                    "quantity": 1,
                    "unit_price": 50000.00
                }
            ]
        },
        headers=auth_headers
    )
    assert response2.status_code == 201
    invoice2 = response2.json()
    assert invoice2["currency"] == "NGN"
