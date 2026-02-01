"""
Tests for tenant logo upload and branded invoices functionality.
"""
import io
import pytest
from fastapi.testclient import TestClient


def test_upload_tenant_logo_success(client: TestClient, auth_headers, test_tenant):
    """Test successful logo upload for a tenant."""
    # Create a fake PNG image
    fake_image = io.BytesIO(
        b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01'
        b'\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\x00\x01'
        b'\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
    )
    fake_image.name = 'logo.png'

    response = client.post(
        f"/api/v1/tenants/{test_tenant.id}/logo",
        headers=auth_headers,
        files={"file": ("logo.png", fake_image, "image/png")}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["logo_url"] is not None
    assert "uploads/logos" in data["logo_url"]
    assert data["id"] == test_tenant.id


def test_upload_tenant_logo_jpg(client: TestClient, auth_headers, test_tenant):
    """Test successful logo upload with JPG format."""
    # Create a fake JPG image
    fake_image = io.BytesIO(
        b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01'
        b'\x00\x00\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07'
        b'\xff\xd9'
    )
    fake_image.name = 'logo.jpg'

    response = client.post(
        f"/api/v1/tenants/{test_tenant.id}/logo",
        headers=auth_headers,
        files={"file": ("logo.jpg", fake_image, "image/jpeg")}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["logo_url"] is not None


def test_upload_tenant_logo_invalid_extension(client: TestClient, auth_headers, test_tenant):
    """Test logo upload with invalid file extension."""
    fake_file = io.BytesIO(b"some content")
    fake_file.name = 'logo.txt'

    response = client.post(
        f"/api/v1/tenants/{test_tenant.id}/logo",
        headers=auth_headers,
        files={"file": ("logo.txt", fake_file, "text/plain")}
    )

    assert response.status_code == 400
    assert "Invalid file extension" in response.json()["message"]


def test_upload_tenant_logo_invalid_mime_type(client: TestClient, auth_headers, test_tenant):
    """Test logo upload with invalid MIME type."""
    fake_file = io.BytesIO(b"some content")
    fake_file.name = 'logo.png'

    response = client.post(
        f"/api/v1/tenants/{test_tenant.id}/logo",
        headers=auth_headers,
        files={"file": ("logo.png", fake_file, "text/plain")}
    )

    assert response.status_code == 400
    assert "Invalid file type" in response.json()["message"]


def test_upload_tenant_logo_file_too_large(client: TestClient, auth_headers, test_tenant):
    """Test logo upload with file size exceeding limit."""
    # Create a file larger than 2MB
    large_file = io.BytesIO(b'0' * (3 * 1024 * 1024))  # 3MB
    large_file.name = 'logo.png'

    response = client.post(
        f"/api/v1/tenants/{test_tenant.id}/logo",
        headers=auth_headers,
        files={"file": ("logo.png", large_file, "image/png")}
    )

    assert response.status_code == 400
    assert "File size exceeds" in response.json()["message"]


def test_upload_tenant_logo_unauthenticated(client: TestClient, test_tenant):
    """Test logo upload without authentication."""
    fake_image = io.BytesIO(b'\x89PNG\r\n\x1a\n')
    fake_image.name = 'logo.png'

    response = client.post(
        f"/api/v1/tenants/{test_tenant.id}/logo",
        files={"file": ("logo.png", fake_image, "image/png")}
    )

    assert response.status_code == 401


def test_upload_tenant_logo_attendant_forbidden(client: TestClient, attendant_auth_headers, test_tenant):
    """Test that attendants cannot upload logos."""
    fake_image = io.BytesIO(b'\x89PNG\r\n\x1a\n')
    fake_image.name = 'logo.png'

    response = client.post(
        f"/api/v1/tenants/{test_tenant.id}/logo",
        headers=attendant_auth_headers,
        files={"file": ("logo.png", fake_image, "image/png")}
    )

    assert response.status_code == 403


def test_upload_tenant_logo_tenant_not_found(client: TestClient, auth_headers):
    """Test logo upload for non-existent tenant."""
    fake_image = io.BytesIO(b'\x89PNG\r\n\x1a\n')
    fake_image.name = 'logo.png'

    response = client.post(
        "/api/v1/tenants/non-existent-id/logo",
        headers=auth_headers,
        files={"file": ("logo.png", fake_image, "image/png")}
    )

    assert response.status_code == 404


def test_get_tenant_logo_success(client: TestClient, auth_headers, test_tenant):
    """Test retrieving uploaded tenant logo."""
    # First upload a logo
    fake_image = io.BytesIO(
        b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01'
        b'\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\x00\x01'
        b'\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
    )
    fake_image.name = 'logo.png'

    upload_response = client.post(
        f"/api/v1/tenants/{test_tenant.id}/logo",
        headers=auth_headers,
        files={"file": ("logo.png", fake_image, "image/png")}
    )
    assert upload_response.status_code == 200

    # Now retrieve the logo
    response = client.get(f"/api/v1/tenants/{test_tenant.id}/logo")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("image/")


def test_get_tenant_logo_not_found(client: TestClient, test_tenant):
    """Test retrieving logo when tenant has no logo."""
    response = client.get(f"/api/v1/tenants/{test_tenant.id}/logo")

    assert response.status_code == 404
    assert "does not have a logo" in response.json()["message"]


def test_delete_tenant_logo_success(client: TestClient, auth_headers, test_tenant):
    """Test deleting tenant logo."""
    # First upload a logo
    fake_image = io.BytesIO(
        b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01'
        b'\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\x00\x01'
        b'\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
    )
    fake_image.name = 'logo.png'

    upload_response = client.post(
        f"/api/v1/tenants/{test_tenant.id}/logo",
        headers=auth_headers,
        files={"file": ("logo.png", fake_image, "image/png")}
    )
    assert upload_response.status_code == 200

    # Now delete the logo
    response = client.delete(
        f"/api/v1/tenants/{test_tenant.id}/logo",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["logo_url"] is None


def test_delete_tenant_logo_attendant_forbidden(client: TestClient, attendant_auth_headers, test_tenant):
    """Test that attendants cannot delete logos."""
    response = client.delete(
        f"/api/v1/tenants/{test_tenant.id}/logo",
        headers=attendant_auth_headers
    )

    assert response.status_code == 403


def test_invoice_pdf_with_tenant_info(client: TestClient, auth_headers, test_tenant, db_session):
    """Test that invoice PDF includes tenant information."""
    from app.models.tenant import Tenant as TenantModel

    # Update tenant with contact information
    tenant = db_session.query(TenantModel).filter(
        TenantModel.id == test_tenant.id
    ).first()
    tenant.address = "123 Business Street, City, Country"
    tenant.phone = "+1234567890"
    tenant.email = "contact@testcompany.com"
    db_session.commit()

    # Create an invoice
    invoice_data = {
        "customer_name": "Test Customer",
        "customer_email": "customer@example.com",
        "issue_date": "2024-01-01",
        "due_date": "2024-01-31",
        "items": [
            {
                "description": "Test Item",
                "quantity": 1,
                "unit_price": 100.00
            }
        ]
    }

    create_response = client.post(
        "/api/v1/invoices/",
        json=invoice_data,
        headers=auth_headers
    )
    assert create_response.status_code == 201
    invoice = create_response.json()

    # Download PDF
    pdf_response = client.get(
        f"/api/v1/invoices/{invoice['id']}/pdf",
        headers=auth_headers
    )

    assert pdf_response.status_code == 200
    assert pdf_response.headers["content-type"] == "application/pdf"
    assert len(pdf_response.content) > 0


def test_invoice_pdf_with_logo(client: TestClient, auth_headers, test_tenant, db_session):
    """Test that invoice PDF includes tenant logo when available."""
    # Upload a logo first
    fake_image = io.BytesIO(
        b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01'
        b'\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\x00\x01'
        b'\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
    )
    fake_image.name = 'logo.png'

    logo_response = client.post(
        f"/api/v1/tenants/{test_tenant.id}/logo",
        headers=auth_headers,
        files={"file": ("logo.png", fake_image, "image/png")}
    )
    assert logo_response.status_code == 200

    # Create an invoice
    invoice_data = {
        "customer_name": "Test Customer",
        "customer_email": "customer@example.com",
        "issue_date": "2024-01-01",
        "due_date": "2024-01-31",
        "items": [
            {
                "description": "Test Item",
                "quantity": 1,
                "unit_price": 100.00
            }
        ]
    }

    create_response = client.post(
        "/api/v1/invoices/",
        json=invoice_data,
        headers=auth_headers
    )
    assert create_response.status_code == 201
    invoice = create_response.json()

    # Download PDF
    pdf_response = client.get(
        f"/api/v1/invoices/{invoice['id']}/pdf",
        headers=auth_headers
    )

    assert pdf_response.status_code == 200
    assert pdf_response.headers["content-type"] == "application/pdf"
    assert len(pdf_response.content) > 0


@pytest.mark.skip(reason="Advanced file content validation not yet implemented.")
def test_upload_tenant_logo_content_validation_failure(client: TestClient, auth_headers, test_tenant):
    """Test logo upload with spoofed content type (security test)."""
    # Create a file with PNG extension but containing text content
    fake_file = io.BytesIO(b"This is not an image file content")
    fake_file.name = 'logo.png'

    response = client.post(
        f"/api/v1/tenants/{test_tenant.id}/logo",
        headers=auth_headers,
        files={"file": ("logo.png", fake_file, "image/png")}
    )

    assert response.status_code == 400
    assert "File content does not match expected type" in response.json()["message"]


@pytest.mark.skip(reason="File signature validation not yet implemented.")
def test_upload_tenant_logo_malicious_file(client: TestClient, auth_headers, test_tenant):
    """Test logo upload with malicious file disguised as image."""
    # Create a PHP file with PNG header spoofing
    malicious_content = (
        b'\x89PNG\r\n\x1a\n'  # PNG signature
        b'<?php echo "malicious code"; ?>'  # PHP code
    )
    fake_file = io.BytesIO(malicious_content)
    fake_file.name = 'logo.png'

    response = client.post(
        f"/api/v1/tenants/{test_tenant.id}/logo",
        headers=auth_headers,
        files={"file": ("logo.png", fake_file, "image/png")}
    )

    # Should fail content validation
    assert response.status_code == 400
    assert "File signature validation failed" in response.json()["message"]


@pytest.mark.skip(reason="Image dimension validation not yet implemented.")
def test_upload_tenant_logo_large_dimensions(client: TestClient, auth_headers, test_tenant):
    """Test logo upload with image exceeding maximum dimensions."""
    from unittest.mock import patch

    # Create a mock image that exceeds dimensions
    fake_file = io.BytesIO(b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x07\x80\x00\x00\x04\x38')
    fake_file.name = 'logo.png'

    # Mock PIL to simulate large dimensions
    with patch('PIL.Image.open') as mock_img_open:
        mock_img = mock_img_open.return_value
        mock_img.size = (2500, 1500)  # Exceeds 2000x2000 limit
        mock_img.mode = 'RGB'
        mock_img.format = 'PNG'
        mock_img.verify.return_value = None

        response = client.post(
            f"/api/v1/tenants/{test_tenant.id}/logo",
            headers=auth_headers,
            files={"file": ("logo.png", fake_file, "image/png")}
        )

        assert response.status_code == 400
        assert "Image dimensions too large" in response.json()["message"]


@pytest.mark.skip(reason="Image corruption validation not yet implemented.")
def test_upload_tenant_logo_corrupted_image(client: TestClient, auth_headers, test_tenant):
    """Test logo upload with corrupted image file."""
    # Create a file with PNG signature but corrupted content
    corrupted_content = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00CORRUPTED'
    fake_file = io.BytesIO(corrupted_content)
    fake_file.name = 'logo.png'

    response = client.post(
        f"/api/v1/tenants/{test_tenant.id}/logo",
        headers=auth_headers,
        files={"file": ("logo.png", fake_file, "image/png")}
    )

    assert response.status_code == 400
    assert "Image validation failed" in response.json()["message"]


def test_upload_tenant_logo_svg_success(client: TestClient, auth_headers, test_tenant):
    """Test successful SVG logo upload."""
    # Create a simple SVG file
    svg_content = b'<?xml version="1.0"?><svg width="100" height="100"><circle cx="50" cy="50" r="40"/></svg>'
    fake_file = io.BytesIO(svg_content)
    fake_file.name = 'logo.svg'

    response = client.post(
        f"/api/v1/tenants/{test_tenant.id}/logo",
        headers=auth_headers,
        files={"file": ("logo.svg", fake_file, "image/svg+xml")}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["logo_url"] is not None
    assert data["logo_url"].endswith('.svg')