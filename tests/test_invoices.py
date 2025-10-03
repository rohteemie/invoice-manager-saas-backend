"""
Test suite for Invoice CRUD operations and lifecycle management.
Tests invoice creation, retrieval, updates, status transitions, and deletion.
"""
import pytest
from decimal import Decimal


def test_create_invoice(client, auth_headers):
    """Test creating a new invoice."""
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
    data = response.json()
    assert data["customer_name"] == "John Doe"
    assert data["customer_email"] == "john@example.com"
    assert data["status"] == "draft"
    assert float(data["subtotal"]) == 250.00
    assert float(data["total_amount"]) == 250.00
    assert "invoice_number" in data
    assert len(data["items"]) == 2
    assert "id" in data


def test_create_invoice_minimal(client, auth_headers):
    """Test creating an invoice with minimal required fields."""
    response = client.post(
        "/api/v1/invoices/",
        json={
            "customer_name": "Jane Doe",
            "issue_date": "2024-01-15",
            "items": [
                {
                    "description": "Service",
                    "quantity": 1,
                    "unit_price": 100.00
                }
            ]
        },
        headers=auth_headers
    )
    assert response.status_code == 201
    data = response.json()
    assert data["customer_name"] == "Jane Doe"
    assert data["customer_email"] is None
    assert float(data["total_amount"]) == 100.00


def test_create_invoice_no_items(client, auth_headers):
    """Test that invoice creation fails without items."""
    response = client.post(
        "/api/v1/invoices/",
        json={
            "customer_name": "John Doe",
            "issue_date": "2024-01-15",
            "items": []
        },
        headers=auth_headers
    )
    assert response.status_code == 422  # Validation error


def test_create_invoice_unauthenticated(client):
    """Test that unauthenticated users cannot create invoices."""
    response = client.post(
        "/api/v1/invoices/",
        json={
            "customer_name": "John Doe",
            "issue_date": "2024-01-15",
            "items": [{"description": "Test", "quantity": 1,
                       "unit_price": 100}]
        }
    )
    assert response.status_code == 401


def test_list_invoices(client, auth_headers):
    """Test listing invoices."""
    # Create a few invoices first
    for i in range(3):
        client.post(
            "/api/v1/invoices/",
            json={
                "customer_name": f"Customer {i}",
                "issue_date": "2024-01-15",
                "items": [{"description": "Item", "quantity": 1,
                           "unit_price": 100}]
            },
            headers=auth_headers
        )

    response = client.get("/api/v1/invoices/", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 3


def test_list_invoices_with_status_filter(client, auth_headers):
    """Test filtering invoices by status."""
    response = client.get(
        "/api/v1/invoices/?status=draft",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    for invoice in data:
        assert invoice["status"] == "draft"


def test_list_invoices_pagination(client, auth_headers):
    """Test invoice list pagination."""
    response = client.get(
        "/api/v1/invoices/?skip=0&limit=2",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) <= 2


def test_get_invoice_by_id(client, auth_headers):
    """Test retrieving a specific invoice by ID."""
    # Create an invoice
    create_response = client.post(
        "/api/v1/invoices/",
        json={
            "customer_name": "Test Customer",
            "issue_date": "2024-01-15",
            "items": [{"description": "Item", "quantity": 1,
                       "unit_price": 100}]
        },
        headers=auth_headers
    )
    invoice_id = create_response.json()["id"]

    # Get the invoice
    response = client.get(
        f"/api/v1/invoices/{invoice_id}",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == invoice_id
    assert data["customer_name"] == "Test Customer"


def test_get_invoice_not_found(client, auth_headers):
    """Test retrieving a non-existent invoice."""
    response = client.get(
        "/api/v1/invoices/nonexistent-id",
        headers=auth_headers
    )
    assert response.status_code == 404


def test_update_invoice_draft(client, auth_headers, manager_auth_headers):
    """Test updating a DRAFT invoice."""
    # Create an invoice
    create_response = client.post(
        "/api/v1/invoices/",
        json={
            "customer_name": "Original Name",
            "issue_date": "2024-01-15",
            "items": [{"description": "Item", "quantity": 1,
                       "unit_price": 100}]
        },
        headers=auth_headers
    )
    invoice_id = create_response.json()["id"]

    # Update the invoice (requires manager role)
    response = client.put(
        f"/api/v1/invoices/{invoice_id}",
        json={
            "customer_name": "Updated Name",
            "notes": "Updated notes"
        },
        headers=manager_auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["customer_name"] == "Updated Name"
    assert data["notes"] == "Updated notes"


def test_update_invoice_items(client, auth_headers, manager_auth_headers):
    """Test updating invoice items."""
    # Create an invoice
    create_response = client.post(
        "/api/v1/invoices/",
        json={
            "customer_name": "Test",
            "issue_date": "2024-01-15",
            "items": [{"description": "Original Item", "quantity": 1,
                       "unit_price": 100}]
        },
        headers=auth_headers
    )
    invoice_id = create_response.json()["id"]

    # Update items
    response = client.put(
        f"/api/v1/invoices/{invoice_id}",
        json={
            "items": [
                {"description": "New Item 1", "quantity": 2,
                 "unit_price": 50},
                {"description": "New Item 2", "quantity": 1,
                 "unit_price": 100}
            ]
        },
        headers=manager_auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 2
    assert float(data["total_amount"]) == 200.00


def test_update_non_draft_invoice_fails(
    client, auth_headers, manager_auth_headers
):
    """Test that only DRAFT invoices can be updated."""
    # Create and send an invoice
    create_response = client.post(
        "/api/v1/invoices/",
        json={
            "customer_name": "Test",
            "issue_date": "2024-01-15",
            "items": [{"description": "Item", "quantity": 1,
                       "unit_price": 100}]
        },
        headers=auth_headers
    )
    invoice_id = create_response.json()["id"]

    # Change status to SENT
    client.patch(
        f"/api/v1/invoices/{invoice_id}/status",
        json={"status": "sent"},
        headers=manager_auth_headers
    )

    # Try to update (should fail)
    response = client.put(
        f"/api/v1/invoices/{invoice_id}",
        json={"customer_name": "Updated"},
        headers=manager_auth_headers
    )
    assert response.status_code == 400
    assert "DRAFT" in response.json()["detail"]


def test_update_invoice_requires_manager(client, auth_headers,
                                         attendant_auth_headers):
    """Test that only Manager+ can update invoices."""
    # Create an invoice
    create_response = client.post(
        "/api/v1/invoices/",
        json={
            "customer_name": "Test",
            "issue_date": "2024-01-15",
            "items": [{"description": "Item", "quantity": 1,
                       "unit_price": 100}]
        },
        headers=auth_headers
    )
    invoice_id = create_response.json()["id"]

    # Try to update with attendant role (should fail)
    response = client.put(
        f"/api/v1/invoices/{invoice_id}",
        json={"customer_name": "Updated"},
        headers=attendant_auth_headers
    )
    assert response.status_code == 403


def test_status_transition_draft_to_sent(client, auth_headers,
                                         manager_auth_headers):
    """Test valid status transition: DRAFT → SENT."""
    # Create an invoice
    create_response = client.post(
        "/api/v1/invoices/",
        json={
            "customer_name": "Test",
            "issue_date": "2024-01-15",
            "items": [{"description": "Item", "quantity": 1,
                       "unit_price": 100}]
        },
        headers=auth_headers
    )
    invoice_id = create_response.json()["id"]

    # Change status to SENT
    response = client.patch(
        f"/api/v1/invoices/{invoice_id}/status",
        json={"status": "sent"},
        headers=manager_auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "sent"


def test_status_transition_sent_to_paid(client, auth_headers,
                                        manager_auth_headers):
    """Test valid status transition: SENT → PAID."""
    # Create and send an invoice
    create_response = client.post(
        "/api/v1/invoices/",
        json={
            "customer_name": "Test",
            "issue_date": "2024-01-15",
            "items": [{"description": "Item", "quantity": 1,
                       "unit_price": 100}]
        },
        headers=auth_headers
    )
    invoice_id = create_response.json()["id"]

    client.patch(
        f"/api/v1/invoices/{invoice_id}/status",
        json={"status": "sent"},
        headers=manager_auth_headers
    )

    # Change status to PAID
    response = client.patch(
        f"/api/v1/invoices/{invoice_id}/status",
        json={"status": "paid", "payment_method": "Credit Card"},
        headers=manager_auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "paid"
    assert data["payment_method"] == "Credit Card"
    assert data["paid_at"] is not None


def test_status_transition_sent_to_overdue(client, auth_headers,
                                           manager_auth_headers):
    """Test valid status transition: SENT → OVERDUE."""
    # Create and send an invoice
    create_response = client.post(
        "/api/v1/invoices/",
        json={
            "customer_name": "Test",
            "issue_date": "2024-01-15",
            "items": [{"description": "Item", "quantity": 1,
                       "unit_price": 100}]
        },
        headers=auth_headers
    )
    invoice_id = create_response.json()["id"]

    client.patch(
        f"/api/v1/invoices/{invoice_id}/status",
        json={"status": "sent"},
        headers=manager_auth_headers
    )

    # Change status to OVERDUE
    response = client.patch(
        f"/api/v1/invoices/{invoice_id}/status",
        json={"status": "overdue"},
        headers=manager_auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "overdue"


def test_status_transition_overdue_to_paid(client, auth_headers,
                                           manager_auth_headers):
    """Test valid status transition: OVERDUE → PAID."""
    # Create, send, and mark overdue
    create_response = client.post(
        "/api/v1/invoices/",
        json={
            "customer_name": "Test",
            "issue_date": "2024-01-15",
            "items": [{"description": "Item", "quantity": 1,
                       "unit_price": 100}]
        },
        headers=auth_headers
    )
    invoice_id = create_response.json()["id"]

    client.patch(
        f"/api/v1/invoices/{invoice_id}/status",
        json={"status": "sent"},
        headers=manager_auth_headers
    )
    client.patch(
        f"/api/v1/invoices/{invoice_id}/status",
        json={"status": "overdue"},
        headers=manager_auth_headers
    )

    # Change status to PAID
    response = client.patch(
        f"/api/v1/invoices/{invoice_id}/status",
        json={"status": "paid", "payment_method": "Bank Transfer"},
        headers=manager_auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "paid"


def test_invalid_status_transition(client, auth_headers,
                                   manager_auth_headers):
    """Test invalid status transition: DRAFT → PAID."""
    create_response = client.post(
        "/api/v1/invoices/",
        json={
            "customer_name": "Test",
            "issue_date": "2024-01-15",
            "items": [{"description": "Item", "quantity": 1,
                       "unit_price": 100}]
        },
        headers=auth_headers
    )
    invoice_id = create_response.json()["id"]

    # Try to go directly from DRAFT to PAID (should fail)
    response = client.patch(
        f"/api/v1/invoices/{invoice_id}/status",
        json={"status": "paid", "payment_method": "Cash"},
        headers=manager_auth_headers
    )
    assert response.status_code == 400
    assert "Invalid status transition" in response.json()["detail"]


def test_paid_status_requires_payment_method(client, auth_headers,
                                             manager_auth_headers):
    """Test that PAID status requires payment_method."""
    # Create and send an invoice
    create_response = client.post(
        "/api/v1/invoices/",
        json={
            "customer_name": "Test",
            "issue_date": "2024-01-15",
            "items": [{"description": "Item", "quantity": 1,
                       "unit_price": 100}]
        },
        headers=auth_headers
    )
    invoice_id = create_response.json()["id"]

    client.patch(
        f"/api/v1/invoices/{invoice_id}/status",
        json={"status": "sent"},
        headers=manager_auth_headers
    )

    # Try to mark as PAID without payment method
    response = client.patch(
        f"/api/v1/invoices/{invoice_id}/status",
        json={"status": "paid"},
        headers=manager_auth_headers
    )
    assert response.status_code == 400
    assert "payment method" in response.json()["detail"].lower()


def test_status_update_requires_manager(
    client, auth_headers, attendant_auth_headers
):
    """Test that only Manager+ can update invoice status."""
    create_response = client.post(
        "/api/v1/invoices/",
        json={
            "customer_name": "Test",
            "issue_date": "2024-01-15",
            "items": [{"description": "Item", "quantity": 1,
                       "unit_price": 100}]
        },
        headers=auth_headers
    )
    invoice_id = create_response.json()["id"]

    # Try to update status with attendant role (should fail)
    response = client.patch(
        f"/api/v1/invoices/{invoice_id}/status",
        json={"status": "sent"},
        headers=attendant_auth_headers
    )
    assert response.status_code == 403


def test_delete_draft_invoice(client, auth_headers, admin_auth_headers):
    """Test deleting a DRAFT invoice."""
    create_response = client.post(
        "/api/v1/invoices/",
        json={
            "customer_name": "Test",
            "issue_date": "2024-01-15",
            "items": [{"description": "Item", "quantity": 1,
                       "unit_price": 100}]
        },
        headers=auth_headers
    )
    invoice_id = create_response.json()["id"]

    # Delete the invoice (requires admin role)
    response = client.delete(
        f"/api/v1/invoices/{invoice_id}",
        headers=admin_auth_headers
    )
    assert response.status_code == 200
    assert "deleted" in response.json()["message"].lower()

    # Verify it's deleted
    get_response = client.get(
        f"/api/v1/invoices/{invoice_id}",
        headers=auth_headers
    )
    assert get_response.status_code == 404


def test_delete_non_draft_invoice_fails(client, auth_headers,
                                        admin_auth_headers,
                                        manager_auth_headers):
    """Test that only DRAFT invoices can be deleted."""
    create_response = client.post(
        "/api/v1/invoices/",
        json={
            "customer_name": "Test",
            "issue_date": "2024-01-15",
            "items": [{"description": "Item", "quantity": 1,
                       "unit_price": 100}]
        },
        headers=auth_headers
    )
    invoice_id = create_response.json()["id"]

    # Change status to SENT
    client.patch(
        f"/api/v1/invoices/{invoice_id}/status",
        json={"status": "sent"},
        headers=manager_auth_headers
    )

    # Try to delete (should fail)
    response = client.delete(
        f"/api/v1/invoices/{invoice_id}",
        headers=admin_auth_headers
    )
    assert response.status_code == 400
    assert "DRAFT" in response.json()["detail"]


def test_delete_requires_admin(client, auth_headers, manager_auth_headers):
    """Test that only Admin+ can delete invoices."""
    create_response = client.post(
        "/api/v1/invoices/",
        json={
            "customer_name": "Test",
            "issue_date": "2024-01-15",
            "items": [{"description": "Item", "quantity": 1,
                       "unit_price": 100}]
        },
        headers=auth_headers
    )
    invoice_id = create_response.json()["id"]

    # Try to delete with manager role (should fail)
    response = client.delete(
        f"/api/v1/invoices/{invoice_id}",
        headers=manager_auth_headers
    )
    assert response.status_code == 403


def test_tenant_isolation(client, auth_headers, second_tenant_auth_headers):
    """Test that tenants can only access their own invoices."""
    # Create invoice in first tenant
    create_response = client.post(
        "/api/v1/invoices/",
        json={
            "customer_name": "Test",
            "issue_date": "2024-01-15",
            "items": [{"description": "Item", "quantity": 1,
                       "unit_price": 100}]
        },
        headers=auth_headers
    )
    invoice_id = create_response.json()["id"]

    # Try to access from second tenant (should fail)
    response = client.get(
        f"/api/v1/invoices/{invoice_id}",
        headers=second_tenant_auth_headers
    )
    assert response.status_code == 404
