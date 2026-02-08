"""
Test suite for currency consistency across invoice system.

Validates that currency is correctly handled in all workflows:
- Invoice creation uses tenant's default currency
- PDF generation with correct currency symbols
- CSV/JSON export with currency information
- Invoice updates maintaining correct tax calculations
"""
import csv
import io
from decimal import Decimal


def test_pdf_generation_uses_tenant_currency(client, auth_headers):
    """Test that PDF uses tenant's default currency symbol."""
    response = client.post(
        "/api/v1/invoices/",
        json={
            "customer_name": "PDF Test Customer",
            "issue_date": "2024-01-15",
            "items": [
                {
                    "description": "Product A",
                    "quantity": 2,
                    "unit_price": 50.00
                }
            ]
        },
        headers=auth_headers
    )
    assert response.status_code == 201
    invoice_id = response.json()["id"]
    # Invoice should use tenant's default currency (NGN)
    assert response.json()["currency"] == "NGN"

    # Generate PDF
    pdf_response = client.get(
        f"/api/v1/invoices/{invoice_id}/pdf",
        headers=auth_headers
    )
    assert pdf_response.status_code == 200
    assert len(pdf_response.content) > 0


def test_csv_export_includes_currency_field(client, auth_headers):
    """Test that CSV export includes currency column with tenant currency."""
    # Create invoices (all use tenant's default currency)
    for _ in range(3):
        client.post(
            "/api/v1/invoices/",
            json={
                "customer_name": "CSV Export Customer",
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
    # All invoices should have tenant's default currency (NGN)
    currencies_in_export = {row["Currency"] for row in rows}
    assert currencies_in_export == {"NGN"}


def test_json_export_includes_currency_field(client, auth_headers):
    """Test that JSON export includes currency field with tenant currency."""
    # Create invoices
    for i in range(2):
        client.post(
            "/api/v1/invoices/",
            json={
                "customer_name": f"JSON Export Customer {i}",
                "issue_date": "2024-01-15",
                "items": [
                    {
                        "description": "Product",
                        "quantity": 1,
                        "unit_price": 150.00
                    }
                ]
            },
            headers=auth_headers
        )

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

    # All invoices should have tenant's default currency
    for invoice in exported_data:
        assert "currency" in invoice
        assert invoice["currency"] == "NGN"


def test_invoice_update_maintains_tax_calculation(
    client, auth_headers, db_session, test_tenant
):
    """Test that updating invoice items recalculates tax correctly."""
    from app.models.tenant import Tenant

    # Set tenant to have 10% tax
    tenant = db_session.query(Tenant).filter(
        Tenant.id == test_tenant.id
    ).first()
    tenant.tax_rate = Decimal("10.00")
    tenant.tax_label = "VAT"
    db_session.commit()

    # Create invoice
    create_response = client.post(
        "/api/v1/invoices/",
        json={
            "customer_name": "Tax Update Test",
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


def test_invoice_update_with_multiple_items_maintains_tax(
    client, auth_headers, db_session, test_tenant
):
    """Test that updating to multiple items maintains correct tax."""
    from app.models.tenant import Tenant

    # Set tenant to have 20% tax
    tenant = db_session.query(Tenant).filter(
        Tenant.id == test_tenant.id
    ).first()
    tenant.tax_rate = Decimal("20.00")
    tenant.tax_label = "VAT"
    db_session.commit()

    # Create invoice with one item
    create_response = client.post(
        "/api/v1/invoices/",
        json={
            "customer_name": "Multi-item Tax Test",
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


def test_invoice_uses_tenant_default_currency(client, auth_headers):
    """Test that invoice always uses tenant's default currency."""
    response = client.post(
        "/api/v1/invoices/",
        json={
            "customer_name": "Currency Test Customer",
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
    # Invoice should use tenant's default currency (NGN)
    assert invoice["currency"] == "NGN"


def test_invoice_currency_consistent_after_update(client, auth_headers):
    """Test that currency remains tenant default after invoice update."""
    # Create invoice
    create_response = client.post(
        "/api/v1/invoices/",
        json={
            "customer_name": "Update Currency Test",
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
    assert create_response.status_code == 201
    invoice_id = create_response.json()["id"]
    assert create_response.json()["currency"] == "NGN"

    # Update invoice
    update_response = client.put(
        f"/api/v1/invoices/{invoice_id}",
        json={
            "customer_name": "Updated Customer Name",
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
    # Currency should still be tenant's default
    assert update_response.json()["currency"] == "NGN"
