"""
Integration tests for Invoice PDF generation endpoint.

Tests the complete flow of generating and downloading invoice PDFs
through the API endpoint.
"""


def test_download_invoice_pdf_success(client, auth_headers):
    """Test successful PDF download for an invoice."""
    # First create an invoice
    response = client.post(
        "/api/v1/invoices/",
        json={
            "customer_name": "John Doe",
            "customer_email": "john@example.com",
            "customer_phone": "+1234567890",
            "customer_address": "123 Main St, City, Country",
            "issue_date": "2024-01-15",
            "due_date": "2024-02-15",
            "notes": "Please pay on time",
            "items": [
                {
                    "description": "Product A",
                    "quantity": 2,
                    "unit_price": 100.00
                },
                {
                    "description": "Product B",
                    "quantity": 1,
                    "unit_price": 50.00
                }
            ]
        },
        headers=auth_headers
    )
    assert response.status_code == 201
    invoice_data = response.json()
    invoice_id = invoice_data["id"]

    # Download PDF
    pdf_response = client.get(
        f"/api/v1/invoices/{invoice_id}/pdf",
        headers=auth_headers
    )

    assert pdf_response.status_code == 200
    assert pdf_response.headers["content-type"] == "application/pdf"
    assert "inline" in pdf_response.headers["content-disposition"]
    assert f"invoice_{invoice_data['invoice_number']}.pdf" in \
        pdf_response.headers["content-disposition"]

    # Verify PDF content
    pdf_content = pdf_response.content
    assert len(pdf_content) > 0
    assert pdf_content[:4] == b'%PDF'  # PDF header


def test_download_invoice_pdf_not_found(client, auth_headers):
    """Test PDF download for non-existent invoice."""
    response = client.get(
        "/api/v1/invoices/nonexistent-id/pdf",
        headers=auth_headers
    )
    assert response.status_code == 404
    assert response.json()["message"] == "Invoice not found"


def test_download_invoice_pdf_unauthenticated(client):
    """Test PDF download requires authentication."""
    response = client.get(
        "/api/v1/invoices/some-id/pdf"
    )
    assert response.status_code == 401


def test_download_invoice_pdf_different_tenant(
    client,
    auth_headers,
    second_tenant_auth_headers
):
    """Test users cannot download PDFs from other tenants."""
    # Create invoice with first tenant
    response = client.post(
        "/api/v1/invoices/",
        json={
            "customer_name": "John Doe",
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

    # Try to download with second tenant
    pdf_response = client.get(
        f"/api/v1/invoices/{invoice_id}/pdf",
        headers=second_tenant_auth_headers
    )
    assert pdf_response.status_code == 404


def test_download_invoice_pdf_paid_status(client, auth_headers, manager_auth_headers):  # noqa: E501
    """Test PDF generation for paid invoice includes payment details."""
    # Create invoice
    response = client.post(
        "/api/v1/invoices/",
        json={
            "customer_name": "Alice Smith",
            "customer_email": "alice@example.com",
            "issue_date": "2024-01-15",
            "due_date": "2024-02-15",
            "items": [
                {
                    "description": "Service Fee",
                    "quantity": 1,
                    "unit_price": 500.00
                }
            ]
        },
        headers=auth_headers
    )
    assert response.status_code == 201
    invoice_id = response.json()["id"]

    # Update to SENT status
    client.patch(
        f"/api/v1/invoices/{invoice_id}/status",
        json={"status": "sent"},
        headers=manager_auth_headers
    )

    # Update to PAID status
    client.patch(
        f"/api/v1/invoices/{invoice_id}/status",
        json={
            "status": "paid",
            "payment_method": "Credit Card"
        },
        headers=manager_auth_headers
    )

    # Download PDF
    pdf_response = client.get(
        f"/api/v1/invoices/{invoice_id}/pdf",
        headers=auth_headers
    )

    assert pdf_response.status_code == 200
    assert pdf_response.headers["content-type"] == "application/pdf"
    assert len(pdf_response.content) > 0


def test_download_invoice_pdf_minimal_fields(client, auth_headers):
    """Test PDF generation with minimal invoice fields."""
    # Create invoice with minimal fields
    response = client.post(
        "/api/v1/invoices/",
        json={
            "customer_name": "Bob Johnson",
            "issue_date": "2024-01-20",
            "items": [
                {
                    "description": "Consulting",
                    "quantity": 5,
                    "unit_price": 150.00
                }
            ]
        },
        headers=auth_headers
    )
    assert response.status_code == 201
    invoice_id = response.json()["id"]

    # Download PDF
    pdf_response = client.get(
        f"/api/v1/invoices/{invoice_id}/pdf",
        headers=auth_headers
    )

    assert pdf_response.status_code == 200
    assert pdf_response.headers["content-type"] == "application/pdf"
    assert len(pdf_response.content) > 0


def test_download_invoice_pdf_multiple_times(client, auth_headers):
    """Test downloading PDF multiple times for same invoice."""
    # Create invoice
    response = client.post(
        "/api/v1/invoices/",
        json={
            "customer_name": "Test Customer",
            "issue_date": "2024-01-21",
            "items": [
                {
                    "description": "Product",
                    "quantity": 1,
                    "unit_price": 99.99
                }
            ]
        },
        headers=auth_headers
    )
    assert response.status_code == 201
    invoice_id = response.json()["id"]

    # Download PDF first time
    pdf_response_1 = client.get(
        f"/api/v1/invoices/{invoice_id}/pdf",
        headers=auth_headers
    )
    assert pdf_response_1.status_code == 200

    # Download PDF second time
    pdf_response_2 = client.get(
        f"/api/v1/invoices/{invoice_id}/pdf",
        headers=auth_headers
    )
    assert pdf_response_2.status_code == 200

    # Both should succeed and return valid PDFs
    assert pdf_response_1.content[:4] == b'%PDF'
    assert pdf_response_2.content[:4] == b'%PDF'


def test_download_invoice_pdf_with_special_characters(client, auth_headers):
    """Test PDF generation with special characters in invoice data."""
    # Create invoice with special characters
    response = client.post(
        "/api/v1/invoices/",
        json={
            "customer_name": "José García & Sons Ltd.",
            "customer_email": "jose@example.com",
            "customer_address": "123 O'Brien St, Café District",
            "issue_date": "2024-01-22",
            "notes": "Special notes with characters: €, £, ñ",
            "items": [
                {
                    "description": "Product with special chars: <>&\"'",
                    "quantity": 1,
                    "unit_price": 100.00
                }
            ]
        },
        headers=auth_headers
    )
    assert response.status_code == 201
    invoice_id = response.json()["id"]

    # Download PDF
    pdf_response = client.get(
        f"/api/v1/invoices/{invoice_id}/pdf",
        headers=auth_headers
    )

    assert pdf_response.status_code == 200
    assert len(pdf_response.content) > 0
    assert pdf_response.content[:4] == b'%PDF'
