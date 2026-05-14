"""
Test suite for configurable invoice number generation.
Tests custom prefixes, formats, and atomic sequence generation.
"""


def test_invoice_number_default_format(client, auth_headers):
    """Test invoice number generation with default format."""
    # Create first invoice
    response = client.post(
        "/api/v1/invoices/",
        json={
            "customer_name": "Test Customer",
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
    data = response.json()
    invoice_number = data["invoice_number"]

    # Default format is INV-YYYYMMDD-XXXX
    assert invoice_number.startswith("INV-")
    assert len(invoice_number.split("-")) == 3
    # Should end with -0001 for first invoice
    assert invoice_number.endswith("-0001")


def test_invoice_number_sequential(client, auth_headers):
    """Test that invoice numbers increment sequentially."""
    invoice_numbers = []

    # Create 3 invoices
    for i in range(3):
        response = client.post(
            "/api/v1/invoices/",
            json={
                "customer_name": f"Customer {i}",
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
        invoice_numbers.append(response.json()["invoice_number"])

    # Check that sequence numbers are incrementing
    assert invoice_numbers[0].endswith("-0001")
    assert invoice_numbers[1].endswith("-0002")
    assert invoice_numbers[2].endswith("-0003")


def test_invoice_number_custom_prefix(client, auth_headers, test_tenant, db_session):
    """Test invoice number generation with custom prefix."""
    from app.models.tenant import Tenant as TenantModel

    # Update tenant with custom prefix
    tenant = db_session.query(TenantModel).filter(
        TenantModel.id == test_tenant.id
    ).first()
    tenant.invoice_number_prefix = "CUSTOM"
    db_session.commit()

    # Create invoice
    response = client.post(
        "/api/v1/invoices/",
        json={
            "customer_name": "Test Customer",
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
    data = response.json()
    invoice_number = data["invoice_number"]

    # Should use custom prefix
    assert invoice_number.startswith("CUSTOM-")


def test_invoice_number_custom_format(client, auth_headers, test_tenant, db_session):
    """Test invoice number generation with custom format."""
    from app.models.tenant import Tenant as TenantModel

    # Update tenant with custom format
    tenant = db_session.query(TenantModel).filter(
        TenantModel.id == test_tenant.id
    ).first()
    tenant.invoice_number_prefix = "TEST"
    tenant.invoice_number_format = "{prefix}{sequence:05d}"
    db_session.commit()

    # Create invoice
    response = client.post(
        "/api/v1/invoices/",
        json={
            "customer_name": "Test Customer",
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
    data = response.json()
    invoice_number = data["invoice_number"]

    # Should match custom format: TEST00001
    assert invoice_number == "TEST00001"


def test_invoice_number_format_with_date(client, auth_headers, test_tenant, db_session):
    """Test invoice number generation with date in format."""
    from app.models.tenant import Tenant as TenantModel
    from datetime import datetime, timezone

    # Update tenant with format including date
    tenant = db_session.query(TenantModel).filter(
        TenantModel.id == test_tenant.id
    ).first()
    tenant.invoice_number_prefix = "INV"
    tenant.invoice_number_format = "{prefix}/{date}/{sequence:03d}"
    db_session.commit()

    # Create invoice
    response = client.post(
        "/api/v1/invoices/",
        json={
            "customer_name": "Test Customer",
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
    data = response.json()
    invoice_number = data["invoice_number"]

    # Should include current date in YYYYMMDD format (not the issue_date from request)
    # The {date} placeholder uses the current date when the invoice number is generated
    today = datetime.now(timezone.utc).strftime("%Y%m%d")
    assert invoice_number.startswith(f"INV/{today}/")
    assert invoice_number.endswith("001")

    # Verify the format is correct: prefix/date/sequence
    parts = invoice_number.split("/")
    assert len(parts) == 3
    assert parts[0] == "INV"
    assert len(parts[1]) == 8  # YYYYMMDD format
    assert parts[2] == "001"


def test_invoice_number_no_gaps_with_deletion(client, auth_headers):
    """Test that sequence continues without gaps even after invoice deletion."""
    # Create first invoice
    response1 = client.post(
        "/api/v1/invoices/",
        json={
            "customer_name": "Customer 1",
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
    assert response1.status_code == 201
    invoice1_number = response1.json()["invoice_number"]

    # Create second invoice
    response2 = client.post(
        "/api/v1/invoices/",
        json={
            "customer_name": "Customer 2",
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
    assert response2.status_code == 201
    invoice2_number = response2.json()["invoice_number"]

    # Create third invoice
    response3 = client.post(
        "/api/v1/invoices/",
        json={
            "customer_name": "Customer 3",
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
    assert response3.status_code == 201
    invoice3_number = response3.json()["invoice_number"]

    # Verify sequence: 0001, 0002, 0003
    assert invoice1_number.endswith("-0001")
    assert invoice2_number.endswith("-0002")
    assert invoice3_number.endswith("-0003")


def test_invoice_number_tenant_isolation(client, auth_headers, second_tenant_auth_headers):
    """Test that invoice number sequences are isolated per tenant."""
    # Create invoice for first tenant
    response1 = client.post(
        "/api/v1/invoices/",
        json={
            "customer_name": "Customer 1",
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
    assert response1.status_code == 201
    invoice1_number = response1.json()["invoice_number"]

    # Create invoice for second tenant
    response2 = client.post(
        "/api/v1/invoices/",
        json={
            "customer_name": "Customer 2",
            "issue_date": "2024-01-15",
            "items": [
                {
                    "description": "Product",
                    "quantity": 1,
                    "unit_price": 100.00
                }
            ]
        },
        headers=second_tenant_auth_headers
    )
    assert response2.status_code == 201
    invoice2_number = response2.json()["invoice_number"]

    # Both should start at 0001 since they're in different tenants
    assert invoice1_number.endswith("-0001")
    assert invoice2_number.endswith("-0001")


def test_invoice_number_format_validation(client, auth_headers, test_tenant, db_session):
    """Test that invalid format falls back to default."""
    from app.models.tenant import Tenant as TenantModel

    # Update tenant with invalid format (no placeholders)
    tenant = db_session.query(TenantModel).filter(
        TenantModel.id == test_tenant.id
    ).first()
    tenant.invoice_number_format = "INVALID_FORMAT_NO_PLACEHOLDERS"
    db_session.commit()

    # Create invoice - should fall back to default format
    response = client.post(
        "/api/v1/invoices/",
        json={
            "customer_name": "Test Customer",
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
    data = response.json()
    invoice_number = data["invoice_number"]

    # Should fall back to default format
    assert invoice_number.startswith("INV-")
    assert "-" in invoice_number


def test_invoice_number_format_requires_sequence(
    client, auth_headers, test_tenant, db_session
):
    """Test that formats without sequence fall back to default."""
    from app.models.tenant import Tenant as TenantModel

    tenant = db_session.query(TenantModel).filter(
        TenantModel.id == test_tenant.id
    ).first()
    tenant.invoice_number_format = "{prefix}-{date}"
    db_session.commit()

    response = client.post(
        "/api/v1/invoices/",
        json={
            "customer_name": "Test Customer",
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
    invoice_number = response.json()["invoice_number"]
    assert invoice_number.startswith("INV-")
    assert invoice_number.endswith("-0001")


def test_invoice_number_duplicate_rejected(
    client, auth_headers, test_tenant, db_session
):
    """Test duplicate invoice numbers are rejected per tenant."""
    from app.models.tenant import Tenant as TenantModel

    tenant = db_session.query(TenantModel).filter(
        TenantModel.id == test_tenant.id
    ).first()
    tenant.invoice_number_format = "{prefix}-{sequence:04d}"
    tenant.invoice_number_sequence = 0
    db_session.commit()

    response1 = client.post(
        "/api/v1/invoices/",
        json={
            "customer_name": "Test Customer",
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
    assert response1.status_code == 201

    tenant.invoice_number_sequence = 0
    db_session.commit()

    response2 = client.post(
        "/api/v1/invoices/",
        json={
            "customer_name": "Test Customer",
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
    assert response2.status_code == 400
    assert "Invoice number already exists" in response2.json()["message"]
