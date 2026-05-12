
"""
Test suite for Invoice CRUD operations and lifecycle management.
Tests invoice creation, retrieval, updates, status transitions, and deletion.
"""

import app.tasks.email_tasks


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


def test_create_invoice_invalid_due_date_format(client, auth_headers):
    """Test that invoice creation fails with invalid due date formats."""
    for due_date in ["2024-02-15T10:00:00", "02/15/2024"]:
        response = client.post(
            "/api/v1/invoices/",
            json={
                "customer_name": "John Doe",
                "issue_date": "2024-01-15",
                "due_date": due_date,
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
        assert response.status_code == 422  # Validation error
        error = response.json()
        assert "details" in error
        assert any(
            "due_date" in str(detail) and "YYYY-MM-DD" in str(detail)
            for detail in error["details"]
        )


def test_create_invoice_invalid_issue_date_format(client, auth_headers):
    """Test that invoice creation fails with invalid issue date formats."""
    for issue_date in ["2024-01-15T10:00:00", "01/15/2024"]:
        response = client.post(
            "/api/v1/invoices/",
            json={
                "customer_name": "John Doe",
                "issue_date": issue_date,
                "due_date": "2024-02-15",
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
        assert response.status_code == 422  # Validation error
        error = response.json()
        assert "details" in error
        assert any(
            "issue_date" in str(detail) and "YYYY-MM-DD" in str(detail)
            for detail in error["details"]
        )


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


def test_create_invoice_too_many_items(client, auth_headers):
    """Test that invoice creation fails with more than 100 items."""
    # Create 101 items to exceed the maximum
    items = [
        {
            "description": f"Item {i}",
            "quantity": 1,
            "unit_price": 10.00
        }
        for i in range(101)
    ]

    response = client.post(
        "/api/v1/invoices/",
        json={
            "customer_name": "John Doe",
            "issue_date": "2024-01-15",
            "items": items
        },
        headers=auth_headers
    )
    assert response.status_code == 422  # Validation error


def test_create_invoice_negative_quantity(client, auth_headers):
    """Test that invoice creation fails with negative quantity."""
    response = client.post(
        "/api/v1/invoices/",
        json={
            "customer_name": "John Doe",
            "issue_date": "2024-01-15",
            "items": [
                {
                    "description": "Product A",
                    "quantity": -1,
                    "unit_price": 100.00
                }
            ]
        },
        headers=auth_headers
    )
    assert response.status_code == 422  # Validation error


def test_create_invoice_zero_quantity(client, auth_headers):
    """Test that invoice creation fails with zero quantity."""
    response = client.post(
        "/api/v1/invoices/",
        json={
            "customer_name": "John Doe",
            "issue_date": "2024-01-15",
            "items": [
                {
                    "description": "Product A",
                    "quantity": 0,
                    "unit_price": 100.00
                }
            ]
        },
        headers=auth_headers
    )
    assert response.status_code == 422  # Validation error


def test_create_invoice_negative_unit_price(client, auth_headers):
    """Test that invoice creation fails with negative unit price."""
    response = client.post(
        "/api/v1/invoices/",
        json={
            "customer_name": "John Doe",
            "issue_date": "2024-01-15",
            "items": [
                {
                    "description": "Product A",
                    "quantity": 1,
                    "unit_price": -50.00
                }
            ]
        },
        headers=auth_headers
    )
    assert response.status_code == 422  # Validation error


def test_create_invoice_max_items_allowed(client, auth_headers):
    """Test that invoice creation succeeds with exactly 100 items."""
    # Create exactly 100 items (the maximum allowed)
    items = [
        {
            "description": f"Item {i}",
            "quantity": 1,
            "unit_price": 10.00
        }
        for i in range(100)
    ]

    response = client.post(
        "/api/v1/invoices/",
        json={
            "customer_name": "John Doe",
            "issue_date": "2024-01-15",
            "items": items
        },
        headers=auth_headers
    )
    assert response.status_code == 201
    data = response.json()
    assert len(data["items"]) == 100
    assert float(data["subtotal"]) == 1000.00  # 100 items * 10.00 each


def test_update_invoice_too_many_items(client, auth_headers, manager_auth_headers):
    """Test that invoice update fails with more than 100 items."""
    # Create an invoice first
    create_response = client.post(
        "/api/v1/invoices/",
        json={
            "customer_name": "Test",
            "issue_date": "2024-01-15",
            "items": [
                {"description": "Original Item", "quantity": 1, "unit_price": 100}
            ]
        },
        headers=auth_headers
    )
    invoice_id = create_response.json()["id"]

    # Try to update with 101 items
    items = [
        {
            "description": f"Item {i}",
            "quantity": 1,
            "unit_price": 10.00
        }
        for i in range(101)
    ]

    response = client.put(
        f"/api/v1/invoices/{invoice_id}",
        json={"items": items},
        headers=manager_auth_headers
    )
    assert response.status_code == 422  # Validation error


def test_update_invoice_empty_items(client, auth_headers, manager_auth_headers):
    """Test that invoice update fails with empty items list."""
    # Create an invoice first
    create_response = client.post(
        "/api/v1/invoices/",
        json={
            "customer_name": "Test",
            "issue_date": "2024-01-15",
            "items": [
                {"description": "Original Item", "quantity": 1, "unit_price": 100}
            ]
        },
        headers=auth_headers
    )
    invoice_id = create_response.json()["id"]

    # Try to update with empty items list
    response = client.put(
        f"/api/v1/invoices/{invoice_id}",
        json={"items": []},
        headers=manager_auth_headers
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

    # Check pagination metadata
    assert "items" in data
    assert "total" in data
    assert "page" in data
    assert "size" in data
    assert "pages" in data
    assert "has_next" in data
    assert "has_previous" in data

    # Check items
    assert len(data["items"]) >= 3
    assert data["total"] >= 3
    assert data["page"] == 1
    assert data["size"] == 100
    assert data["has_previous"] is False


def test_list_invoices_with_status_filter(client, auth_headers):
    """Test filtering invoices by status."""
    response = client.get(
        "/api/v1/invoices/?status=draft",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()

    # Check pagination metadata
    assert "items" in data
    assert "total" in data

    # Check items
    for invoice in data["items"]:
        assert invoice["status"] == "draft"


def test_list_invoices_pagination(client, auth_headers):
    """Test invoice list pagination."""
    response = client.get(
        "/api/v1/invoices/?skip=0&limit=2",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()

    # Check pagination metadata
    assert "items" in data
    assert "total" in data
    assert "page" in data
    assert "size" in data
    assert "pages" in data
    assert "has_next" in data
    assert "has_previous" in data

    # Check items
    assert len(data["items"]) <= 2
    assert data["size"] == 2
    assert data["page"] == 1
    assert data["has_previous"] is False


def test_pagination_metadata(client, auth_headers):
    """Test pagination metadata fields are correctly calculated."""
    # Create 10 invoices
    for i in range(10):
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

    # Test first page
    response = client.get(
        "/api/v1/invoices/?skip=0&limit=5",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()

    assert data["total"] >= 10
    assert data["page"] == 1
    assert data["size"] == 5
    assert data["pages"] >= 2
    assert data["has_next"] is True
    assert data["has_previous"] is False
    assert len(data["items"]) == 5

    # Test second page
    response = client.get(
        "/api/v1/invoices/?skip=5&limit=5",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()

    assert data["page"] == 2
    assert data["size"] == 5
    assert data["has_previous"] is True
    assert len(data["items"]) <= 5


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
        headers=manager_auth_headers
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
        headers=manager_auth_headers
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
        headers=manager_auth_headers
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
    assert "DRAFT" in response.json()["message"]


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
        headers=manager_auth_headers
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
        headers=manager_auth_headers
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
        json={"status": "paid", "payment_method": "card"},
        headers=manager_auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "paid"
    assert data["payment_method"] == "card"
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
        headers=manager_auth_headers
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
        headers=manager_auth_headers
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
        json={"status": "paid", "payment_method": "transfer"},
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
        headers=manager_auth_headers
    )
    invoice_id = create_response.json()["id"]

    # Try to go directly from DRAFT to PAID (should fail)
    response = client.patch(
        f"/api/v1/invoices/{invoice_id}/status",
        json={"status": "paid", "payment_method": "Cash"},
        headers=manager_auth_headers
    )
    assert response.status_code == 400
    assert "Invalid status transition" in response.json()["message"]


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
        headers=manager_auth_headers
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
    assert "payment method" in response.json()["message"].lower()


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
        headers=admin_auth_headers
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
        headers=admin_auth_headers
    )
    invoice_id = create_response.json()["id"]

    # Change status to SENT
    client.patch(
        f"/api/v1/invoices/{invoice_id}/status",
        json={"status": "sent"},
        headers=admin_auth_headers
    )

    # Try to delete (should fail)
    response = client.delete(
        f"/api/v1/invoices/{invoice_id}",
        headers=admin_auth_headers
    )
    assert response.status_code == 400
    assert "DRAFT" in response.json()["message"]


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


def test_export_invoices_csv(client, auth_headers):
    """Test exporting invoices in CSV format."""
    # Create test invoices
    for i in range(3):
        client.post(
            "/api/v1/invoices/",
            json={
                "customer_name": f"Customer {i}",
                "customer_email": f"customer{i}@example.com",
                "issue_date": "2024-01-15",
                "items": [{"description": "Item", "quantity": 1,
                           "unit_price": 100}]
            },
            headers=auth_headers
        )

    # Export as CSV
    response = client.get(
        "/api/v1/invoices/export/invoices?format=csv",
        headers=auth_headers
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/csv; charset=utf-8"
    assert "attachment" in response.headers["content-disposition"]
    assert "invoices_" in response.headers["content-disposition"]
    assert ".csv" in response.headers["content-disposition"]

    # Check CSV content
    csv_content = response.text
    lines = csv_content.strip().split("\n")
    assert len(lines) >= 4  # Header + at least 3 data rows
    assert "Invoice Number" in lines[0]
    assert "Customer Name" in lines[0]
    assert "Total Amount" in lines[0]


def test_export_invoices_json(client, auth_headers):
    """Test exporting invoices in JSON format."""
    # Create test invoices
    paid_invoice_number = None
    for i in range(2):
        create_response = client.post(
            "/api/v1/invoices/",
            json={
                "customer_name": f"Customer {i}",
                "customer_email": f"customer{i}@example.com",
                "issue_date": "2024-01-15",
                "items": [
                    {"description": "Item A", "quantity": 2,
                     "unit_price": 50},
                    {"description": "Item B", "quantity": 1,
                     "unit_price": 100}
                ]
            },
            headers=auth_headers
        )
        assert create_response.status_code == 201
        if i == 0:
            invoice_id = create_response.json()["id"]
            paid_invoice_number = create_response.json()["invoice_number"]

            sent_response = client.patch(
                f"/api/v1/invoices/{invoice_id}/status",
                json={"status": "sent"},
                headers=auth_headers
            )
            assert sent_response.status_code == 200

            paid_response = client.patch(
                f"/api/v1/invoices/{invoice_id}/status",
                json={"status": "paid", "payment_method": "cash"},
                headers=auth_headers
            )
            assert paid_response.status_code == 200

    # Export as JSON
    response = client.get(
        "/api/v1/invoices/export/invoices?format=json",
        headers=auth_headers
    )
    assert response.status_code == 200
    assert "application/json" in response.headers["content-type"]
    assert "attachment" in response.headers["content-disposition"]
    assert "invoices_" in response.headers["content-disposition"]
    assert ".json" in response.headers["content-disposition"]

    # Check JSON content
    json_data = response.json()
    assert isinstance(json_data, list)
    assert len(json_data) >= 2
    assert "invoice_number" in json_data[0]
    assert "customer_name" in json_data[0]
    assert "items" in json_data[0]
    assert isinstance(json_data[0]["items"], list)
    assert len(json_data[0]["items"]) == 2
    assert (
        paid_invoice_number is not None
    ), "Paid invoice was not created during test setup"
    paid_invoice = next(
        (
            invoice for invoice in json_data
            if invoice["invoice_number"] == paid_invoice_number
        ),
        None
    )
    assert paid_invoice is not None
    assert paid_invoice["payment_method"] == "cash"


def test_export_invoices_with_status_filter(client, auth_headers,
                                            manager_auth_headers):
    """Test exporting invoices with status filter."""
    # Create invoices with different statuses

    sent_response = client.post(
        "/api/v1/invoices/",
        json={
            "customer_name": "Sent Customer",
            "issue_date": "2024-01-15",
            "items": [{"description": "Item", "quantity": 1,
                       "unit_price": 100}]
        },
        headers=manager_auth_headers
    )
    sent_id = sent_response.json()["id"]

    # Change one to SENT status
    client.patch(
        f"/api/v1/invoices/{sent_id}/status",
        json={"status": "sent"},
        headers=manager_auth_headers
    )

    # Export only SENT invoices
    response = client.get(
        "/api/v1/invoices/export/invoices?format=json&status=sent",
        headers=manager_auth_headers
    )
    assert response.status_code == 200
    json_data = response.json()
    # Should have at least the one SENT invoice
    sent_invoices = [inv for inv in json_data if inv["status"] == "sent"]
    assert len(sent_invoices) >= 1
    # All returned invoices should be SENT
    for invoice in json_data:
        assert invoice["status"] == "sent"


def test_export_invoices_with_date_filter(client, auth_headers):
    """Test exporting invoices with date range filter."""
    # Create invoice
    client.post(
        "/api/v1/invoices/",
        json={
            "customer_name": "Test Customer",
            "issue_date": "2024-01-15",
            "items": [{"description": "Item", "quantity": 1,
                       "unit_price": 100}]
        },
        headers=auth_headers
    )

    # Export with date filter (future date - should return nothing new)
    response = client.get(
        "/api/v1/invoices/export/invoices?format=json&"
        "start_date=2025-01-01",
        headers=auth_headers
    )
    assert response.status_code == 200
    json_data = response.json()
    # May be empty or have older invoices from other tests
    assert isinstance(json_data, list)


def test_export_invoices_invalid_format(client, auth_headers):
    """Test that invalid export format is rejected."""
    response = client.get(
        "/api/v1/invoices/export/invoices?format=xml",
        headers=auth_headers
    )
    assert response.status_code == 422  # Validation error


def test_export_invoices_unauthenticated(client):
    """Test that unauthenticated users cannot export invoices."""
    response = client.get(
        "/api/v1/invoices/export/invoices?format=csv"
    )
    assert response.status_code == 401


def test_export_invoices_tenant_isolation(client, auth_headers,
                                          second_tenant_auth_headers):
    """Test that exports are tenant-isolated."""
    # Create invoice in first tenant
    client.post(
        "/api/v1/invoices/",
        json={
            "customer_name": "Tenant 1 Customer",
            "issue_date": "2024-01-15",
            "items": [{"description": "Item", "quantity": 1,
                       "unit_price": 100}]
        },
        headers=auth_headers
    )

    # Create invoice in second tenant
    client.post(
        "/api/v1/invoices/",
        json={
            "customer_name": "Tenant 2 Customer",
            "issue_date": "2024-01-15",
            "items": [{"description": "Item", "quantity": 1,
                       "unit_price": 100}]
        },
        headers=second_tenant_auth_headers
    )

    # Export from first tenant
    response = client.get(
        "/api/v1/invoices/export/invoices?format=json",
        headers=auth_headers
    )
    assert response.status_code == 200
    json_data = response.json()

    # Should only contain Tenant 1's invoices
    for invoice in json_data:
        assert "Tenant 2" not in invoice["customer_name"]


def test_export_csv_format_structure(client, auth_headers):
    """Test CSV export has correct structure and data types."""
    # Create invoice with all fields
    client.post(
        "/api/v1/invoices/",
        json={
            "customer_name": "Full Data Customer",
            "customer_email": "full@example.com",
            "customer_phone": "+1234567890",
            "customer_address": "123 Main St",
            "issue_date": "2024-01-15",
            "due_date": "2024-02-15",
            "notes": "Test notes",
            "items": [{"description": "Item", "quantity": 2,
                       "unit_price": 50}]
        },
        headers=auth_headers
    )

    # Export as CSV
    response = client.get(
        "/api/v1/invoices/export/invoices?format=csv",
        headers=auth_headers
    )
    assert response.status_code == 200

    csv_content = response.text
    lines = csv_content.strip().split("\n")

    # Check header columns
    header = lines[0]
    assert "Invoice Number" in header
    assert "Customer Name" in header
    assert "Customer Email" in header
    assert "Status" in header
    assert "Total Amount" in header


def test_export_json_includes_items(client, auth_headers):
    """Test JSON export includes invoice items."""
    # Create invoice with multiple items
    client.post(
        "/api/v1/invoices/",
        json={
            "customer_name": "Items Test Customer",
            "issue_date": "2024-01-15",
            "items": [
                {"description": "Item A", "quantity": 2, "unit_price": 50},
                {"description": "Item B", "quantity": 1, "unit_price": 100},
                {"description": "Item C", "quantity": 3, "unit_price": 25}
            ]
        },
        headers=auth_headers
    )

    # Export as JSON
    response = client.get(
        "/api/v1/invoices/export/invoices?format=json",
        headers=auth_headers
    )
    assert response.status_code == 200
    json_data = response.json()

    # Find our invoice
    test_invoice = None
    for invoice in json_data:
        if invoice["customer_name"] == "Items Test Customer":
            test_invoice = invoice
            break

    assert test_invoice is not None
    assert "items" in test_invoice
    assert len(test_invoice["items"]) == 3
    assert test_invoice["items"][0]["description"] == "Item A"
    assert test_invoice["items"][0]["quantity"] == 2.0
    assert test_invoice["items"][0]["unit_price"] == 50.0


def test_send_invoice_success(client, manager_auth_headers, mocker):
    """Test successfully sending an invoice via email."""
    # Mock the Celery task instead of the old function
    mock_send_task = mocker.patch(
        'app.tasks.email_tasks.send_invoice_email_task.delay',
        return_value=mocker.Mock(id='task-id')
    )

    # Create a draft invoice with customer email
    response = client.post(
        "/api/v1/invoices/",
        json={
            "customer_name": "John Doe",
            "customer_email": "john@example.com",
            "issue_date": "2024-01-15",
            "items": [
                {
                    "description": "Product A",
                    "quantity": 2,
                    "unit_price": 100.00
                }
            ]
        },
        headers=manager_auth_headers
    )
    assert response.status_code == 201
    invoice_id = response.json()["id"]

    # Send the invoice
    response = client.post(
        f"/api/v1/invoices/{invoice_id}/send",
        headers=manager_auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "sent"
    assert data["id"] == invoice_id

    # Verify async task was called
    assert mock_send_task.called
    call_kwargs = mock_send_task.call_args[1]
    assert call_kwargs["email"] == "john@example.com"
    assert call_kwargs["customer_name"] == "John Doe"
    assert "invoice_number" in call_kwargs
    assert "pdf_bytes_b64" in call_kwargs  # Now base64 encoded


def test_send_invoice_without_email(client, manager_auth_headers):
    """Test that sending an invoice without customer email fails."""
    # Create a draft invoice without customer email
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
        headers=manager_auth_headers
    )
    assert response.status_code == 201
    invoice_id = response.json()["id"]

    # Try to send the invoice
    response = client.post(
        f"/api/v1/invoices/{invoice_id}/send",
        headers=manager_auth_headers
    )

    assert response.status_code == 400
    assert "email" in response.json()["message"].lower()
    assert "download" in response.json()["message"].lower()


def test_send_invoice_not_draft(client, manager_auth_headers, mocker):
    """Test that only draft invoices can be sent."""
    # Mock the Celery task instead of the old function
    mocker.patch(
        'app.tasks.email_tasks.send_invoice_email_task.delay',
        return_value=mocker.Mock(id='task-id')
    )

    # Create and send an invoice
    response = client.post(
        "/api/v1/invoices/",
        json={
            "customer_name": "John Doe",
            "customer_email": "john@example.com",
            "issue_date": "2024-01-15",
            "items": [
                {
                    "description": "Product",
                    "quantity": 1,
                    "unit_price": 100.00
                }
            ]
        },
        headers=manager_auth_headers
    )
    invoice_id = response.json()["id"]

    # Send the invoice once
    response = client.post(
        f"/api/v1/invoices/{invoice_id}/send",
        headers=manager_auth_headers
    )
    assert response.status_code == 200

    # Try to send it again
    response = client.post(
        f"/api/v1/invoices/{invoice_id}/send",
        headers=manager_auth_headers
    )

    assert response.status_code == 400
    assert "DRAFT" in response.json()["message"]


def test_send_invoice_not_found(client, manager_auth_headers):
    """Test sending a non-existent invoice."""
    response = client.post(
        "/api/v1/invoices/nonexistent-id/send",
        headers=manager_auth_headers
    )

    assert response.status_code == 404
    assert "not found" in response.json()["message"].lower()


def test_send_invoice_attendant_permission(client, attendant_auth_headers):
    """Test that attendants cannot send invoices."""
    # Create a draft invoice
    response = client.post(
        "/api/v1/invoices/",
        json={
            "customer_name": "John Doe",
            "customer_email": "john@example.com",
            "issue_date": "2024-01-15",
            "items": [
                {
                    "description": "Product",
                    "quantity": 1,
                    "unit_price": 100.00
                }
            ]
        },
        headers=attendant_auth_headers
    )
    invoice_id = response.json()["id"]

    # Try to send as attendant (should fail - requires manager role)
    response = client.post(
        f"/api/v1/invoices/{invoice_id}/send",
        headers=attendant_auth_headers
    )

    assert response.status_code == 403


def test_send_invoice_email_failure(client, manager_auth_headers, mocker):
    """Test handling of email sending failure."""
    # Mock the Celery task to raise an exception (simulate queueing failure)
    mocker.patch(
        'app.tasks.email_tasks.send_invoice_email_task.delay',
        side_effect=Exception("Failed to queue email")
    )

    # Create a draft invoice with customer email
    response = client.post(
        "/api/v1/invoices/",
        json={
            "customer_name": "John Doe",
            "customer_email": "john@example.com",
            "issue_date": "2024-01-15",
            "items": [
                {
                    "description": "Product",
                    "quantity": 1,
                    "unit_price": 100.00
                }
            ]
        },
        headers=manager_auth_headers
    )
    invoice_id = response.json()["id"]

    # Try to send the invoice - should succeed but log error
    # (graceful degradation - invoice still marked as sent)
    response = client.post(
        f"/api/v1/invoices/{invoice_id}/send",
        headers=manager_auth_headers
    )

    # Invoice is still marked as sent despite email failure
    assert response.status_code == 200
    assert response.json()["status"] == "sent"


def test_send_invoice_tenant_isolation(
    client,
    manager_auth_headers,
    second_tenant_auth_headers,
    mocker
):
    """Test that users can't send invoices from other tenants."""
    # Mock the Celery task
    mocker.patch(
        'app.tasks.email_tasks.send_invoice_email_task.delay',
        return_value=mocker.Mock(id='task-id')
    )

    # Create an invoice in first tenant
    response = client.post(
        "/api/v1/invoices/",
        json={
            "customer_name": "John Doe",
            "customer_email": "john@example.com",
            "issue_date": "2024-01-15",
            "items": [
                {
                    "description": "Product",
                    "quantity": 1,
                    "unit_price": 100.00
                }
            ]
        },
        headers=manager_auth_headers
    )
    invoice_id = response.json()["id"]

    # Try to send it as second tenant user
    response = client.post(
        f"/api/v1/invoices/{invoice_id}/send",
        headers=second_tenant_auth_headers
    )

    assert response.status_code == 404


def test_send_invoice_pdf_matches_download(client, manager_auth_headers, mocker):
    """Test that the PDF sent via email uses the same template as download."""
    # Variable to capture the PDF bytes sent via email
    sent_pdf_bytes = None

    def mock_send_email(**kwargs):
        nonlocal sent_pdf_bytes
        # Decode the base64 PDF
        import base64
        sent_pdf_bytes = base64.b64decode(kwargs['pdf_bytes_b64'])
        return mocker.Mock(id='task-id')

    mocker.patch(
        'app.tasks.email_tasks.send_invoice_email_task.delay',
        side_effect=mock_send_email
    )

    # Create a draft invoice with customer email
    response = client.post(
        "/api/v1/invoices/",
        json={
            "customer_name": "John Doe",
            "customer_email": "john@example.com",
            "issue_date": "2024-01-15",
            "items": [
                {
                    "description": "Product A",
                    "quantity": 2,
                    "unit_price": 100.00
                }
            ]
        },
        headers=manager_auth_headers
    )
    assert response.status_code == 201
    invoice_id = response.json()["id"]

    # Download the PDF
    download_response = client.get(
        f"/api/v1/invoices/{invoice_id}/pdf",
        headers=manager_auth_headers
    )
    assert download_response.status_code == 200
    downloaded_pdf_bytes = download_response.content

    # Send the invoice (which triggers PDF generation and email)
    send_response = client.post(
        f"/api/v1/invoices/{invoice_id}/send",
        headers=manager_auth_headers
    )
    assert send_response.status_code == 200

    # Verify that both are valid PDFs
    assert sent_pdf_bytes is not None, "Email was not sent"
    assert downloaded_pdf_bytes.startswith(b'%PDF'), "Downloaded PDF invalid"
    assert sent_pdf_bytes.startswith(b'%PDF'), "Sent PDF invalid"

    # Both PDFs should have similar sizes (within 5% due to metadata)
    size_diff = abs(len(sent_pdf_bytes) - len(downloaded_pdf_bytes))
    size_tolerance = max(len(sent_pdf_bytes), len(downloaded_pdf_bytes)) * 0.05
    assert size_diff < size_tolerance, (
        f"PDF sizes differ significantly. "
        f"Downloaded: {len(downloaded_pdf_bytes)} bytes, "
        f"Sent: {len(sent_pdf_bytes)} bytes, "
        f"Difference: {size_diff} bytes"
    )


def test_send_invoice_xss_protection(client, manager_auth_headers, mocker):
    """Test that HTML in customer data is properly escaped to prevent XSS."""
    # Variable to capture the email content
    sent_email_html = None

    def mock_send_email(**kwargs):
        # Simulate what the email task would do - compose the email
        from app.services.email_service import compose_invoice_email

        customer_name = kwargs['customer_name']
        invoice_number = kwargs['invoice_number']
        total_amount = kwargs['total_amount']

        # Compose the email to get HTML content
        _, html_content = compose_invoice_email(customer_name, invoice_number, total_amount)

        nonlocal sent_email_html
        sent_email_html = html_content
        return mocker.Mock(id='task-id')

    mocker.patch(
        'app.tasks.email_tasks.send_invoice_email_task.delay',
        side_effect=mock_send_email
    )

    # Create an invoice with potential XSS in customer name
    malicious_name = "<script>alert('xss')</script>"
    response = client.post(
        "/api/v1/invoices/",
        json={
            "customer_name": malicious_name,
            "customer_email": "test@example.com",
            "issue_date": "2024-01-15",
            "items": [
                {
                    "description": "Product",
                    "quantity": 1,
                    "unit_price": 100.00
                }
            ]
        },
        headers=manager_auth_headers
    )
    assert response.status_code == 201
    invoice_id = response.json()["id"]

    # Send the invoice
    response = client.post(
        f"/api/v1/invoices/{invoice_id}/send",
        headers=manager_auth_headers
    )
    assert response.status_code == 200

    # Verify HTML escaping prevented XSS
    assert sent_email_html is not None
    assert "&lt;script&gt;" in sent_email_html
    assert "<script>" not in sent_email_html
    assert "alert(&#x27;xss&#x27;)" in sent_email_html or "alert('xss')" not in sent_email_html


# =============================
# Invoice Search Enhancement Tests
# =============================


def test_list_invoices_search_by_customer_name(client, auth_headers):
    """Test searching invoices by customer name (partial, case-insensitive)."""
    # Create invoices with different customer names
    customer_names = ["John Smith", "Jane Doe", "Johnny Appleseed"]
    for name in customer_names:
        client.post(
            "/api/v1/invoices/",
            json={
                "customer_name": name,
                "issue_date": "2024-01-15",
                "items": [{"description": "Item", "quantity": 1,
                           "unit_price": 100}]
            },
            headers=auth_headers
        )

    # Search for "john" - should match "John Smith" and "Johnny Appleseed"
    response = client.get(
        "/api/v1/invoices/?customer_name=john",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert "items" in data

    # Filter to only check our created invoices
    john_invoices = [
        inv for inv in data["items"]
        if "john" in inv["customer_name"].lower()
    ]
    assert len(john_invoices) >= 2

    # All returned "john" matches should contain "john" (case-insensitive)
    for invoice in john_invoices:
        assert "john" in invoice["customer_name"].lower()


def test_list_invoices_search_by_customer_name_case_insensitive(
    client, auth_headers
):
    """Test customer name search is case-insensitive."""
    # Create an invoice
    client.post(
        "/api/v1/invoices/",
        json={
            "customer_name": "UPPERCASE Customer",
            "issue_date": "2024-01-15",
            "items": [{"description": "Item", "quantity": 1, "unit_price": 100}]
        },
        headers=auth_headers
    )

    # Search with lowercase
    response = client.get(
        "/api/v1/invoices/?customer_name=uppercase",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()

    # Should find the invoice regardless of case
    found = any(
        "uppercase" in inv["customer_name"].lower()
        for inv in data["items"]
    )
    assert found


def test_list_invoices_search_by_invoice_number(client, auth_headers):
    """Test searching invoices by invoice number (partial, case-insensitive)."""
    # Create an invoice
    create_response = client.post(
        "/api/v1/invoices/",
        json={
            "customer_name": "Test Customer",
            "issue_date": "2024-01-15",
            "items": [{"description": "Item", "quantity": 1, "unit_price": 100}]
        },
        headers=auth_headers
    )
    invoice_number = create_response.json()["invoice_number"]

    # Search by partial invoice number (last 4 digits)
    partial_number = invoice_number[-4:]
    response = client.get(
        f"/api/v1/invoices/?invoice_number={partial_number}",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()

    # Should find at least one invoice
    matching = [
        inv for inv in data["items"]
        if partial_number in inv["invoice_number"]
    ]
    assert len(matching) >= 1


def test_list_invoices_date_range_filter(client, auth_headers):
    """Test filtering invoices by date range."""
    # Create an invoice
    client.post(
        "/api/v1/invoices/",
        json={
            "customer_name": "Date Range Test",
            "issue_date": "2024-01-15",
            "items": [{"description": "Item", "quantity": 1, "unit_price": 100}]
        },
        headers=auth_headers
    )

    # Filter with start_date (should include today's invoice)
    response = client.get(
        "/api/v1/invoices/?start_date=2024-01-01",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert data["total"] >= 1

    # Filter with future start_date (after the created invoice; should return no results)
    response = client.get(
        "/api/v1/invoices/?start_date=2030-01-01",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0


def test_list_invoices_end_date_filter(client, auth_headers):
    """Test filtering invoices by end_date."""
    # Create an invoice
    client.post(
        "/api/v1/invoices/",
        json={
            "customer_name": "End Date Test",
            "issue_date": "2024-01-15",
            "items": [{"description": "Item", "quantity": 1, "unit_price": 100}]
        },
        headers=auth_headers
    )

    # Filter with past end_date (should return no new invoices)
    response = client.get(
        "/api/v1/invoices/?end_date=2020-01-01",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0


def test_list_invoices_date_range_combined(client, auth_headers):
    """Test filtering invoices with both start_date and end_date."""
    # Create an invoice
    client.post(
        "/api/v1/invoices/",
        json={
            "customer_name": "Combined Date Test",
            "issue_date": "2024-01-15",
            "items": [{"description": "Item", "quantity": 1, "unit_price": 100}]
        },
        headers=auth_headers
    )

    # Filter with date range that should include today
    response = client.get(
        "/api/v1/invoices/?start_date=2024-01-01&end_date=2030-12-31",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1


def test_list_invoices_invalid_date_format(client, auth_headers):
    """Test that invalid date format returns validation error."""
    response = client.get(
        "/api/v1/invoices/?start_date=invalid-date",
        headers=auth_headers
    )
    assert response.status_code == 422
    assert "Invalid date format" in response.json()["message"]


def test_list_invoices_amount_filter_min(client, auth_headers):
    """Test filtering invoices by minimum amount."""
    # Create invoices with different amounts
    for amount in [50, 100, 200]:
        client.post(
            "/api/v1/invoices/",
            json={
                "customer_name": f"Amount Test {amount}",
                "issue_date": "2024-01-15",
                "items": [
                    {"description": "Item", "quantity": 1, "unit_price": amount}
                ]
            },
            headers=auth_headers
        )

    # Filter by minimum amount
    response = client.get(
        "/api/v1/invoices/?min_amount=150",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()

    # All returned invoices should have total_amount >= 150
    for invoice in data["items"]:
        assert float(invoice["total_amount"]) >= 150


def test_list_invoices_amount_filter_max(client, auth_headers):
    """Test filtering invoices by maximum amount."""
    # Create invoices with different amounts
    for amount in [50, 100, 200]:
        client.post(
            "/api/v1/invoices/",
            json={
                "customer_name": f"Max Amount Test {amount}",
                "issue_date": "2024-01-15",
                "items": [
                    {"description": "Item", "quantity": 1, "unit_price": amount}
                ]
            },
            headers=auth_headers
        )

    # Filter by maximum amount
    response = client.get(
        "/api/v1/invoices/?max_amount=75",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()

    # All returned invoices should have total_amount <= 75
    for invoice in data["items"]:
        assert float(invoice["total_amount"]) <= 75


def test_list_invoices_amount_filter_range(client, auth_headers):
    """Test filtering invoices by amount range (min and max)."""
    # Create invoices with different amounts
    for amount in [50, 100, 150, 200]:
        client.post(
            "/api/v1/invoices/",
            json={
                "customer_name": f"Range Amount Test {amount}",
                "issue_date": "2024-01-15",
                "items": [
                    {"description": "Item", "quantity": 1, "unit_price": amount}
                ]
            },
            headers=auth_headers
        )

    # Filter by amount range
    response = client.get(
        "/api/v1/invoices/?min_amount=75&max_amount=175",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()

    # All returned invoices should have 75 <= total_amount <= 175
    for invoice in data["items"]:
        amount = float(invoice["total_amount"])
        assert 75 <= amount <= 175


def test_list_invoices_combined_filters(client, auth_headers,
                                        manager_auth_headers):
    """Test combining multiple filters."""
    # Create a specific invoice we can search for
    client.post(
        "/api/v1/invoices/",
        json={
            "customer_name": "Combined Filter Customer",
            "issue_date": "2024-01-15",
            "items": [
                {"description": "Item", "quantity": 1, "unit_price": 300}
            ]
        },
        headers=auth_headers
    )

    # Combine status, customer_name, and amount filters
    response = client.get(
        "/api/v1/invoices/?status=draft&customer_name=Combined&min_amount=250",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()

    # All matching invoices should satisfy all conditions
    for invoice in data["items"]:
        assert invoice["status"] == "draft"
        assert "combined" in invoice["customer_name"].lower()
        assert float(invoice["total_amount"]) >= 250


def test_list_invoices_search_no_results(client, auth_headers):
    """Test search that returns no results."""
    response = client.get(
        "/api/v1/invoices/?customer_name=NonExistentCustomerXYZ123",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["items"] == []


def test_list_invoices_search_tenant_isolation(client, auth_headers,
                                               second_tenant_auth_headers):
    """Test that search respects tenant isolation."""
    # Create invoice in first tenant
    client.post(
        "/api/v1/invoices/",
        json={
            "customer_name": "Isolated Search Customer",
            "issue_date": "2024-01-15",
            "items": [{"description": "Item", "quantity": 1, "unit_price": 100}]
        },
        headers=auth_headers
    )

    # Search from second tenant - should not find first tenant's invoice
    response = client.get(
        "/api/v1/invoices/?customer_name=Isolated",
        headers=second_tenant_auth_headers
    )
    assert response.status_code == 200
    data = response.json()

    # Should not contain invoices from first tenant
    for invoice in data["items"]:
        assert "Isolated Search Customer" not in invoice["customer_name"]


def test_list_invoices_wildcard_escape_customer_name(client, auth_headers):
    """Test that SQL wildcards in customer name search are escaped."""
    # Create invoices - one with underscore, one that would match if _ not escaped
    client.post(
        "/api/v1/invoices/",
        json={
            "customer_name": "test_user",
            "issue_date": "2024-01-15",
            "items": [{"description": "Item", "quantity": 1, "unit_price": 100}]
        },
        headers=auth_headers
    )
    client.post(
        "/api/v1/invoices/",
        json={
            "customer_name": "testXuser",
            "issue_date": "2024-01-15",
            "items": [{"description": "Item", "quantity": 1, "unit_price": 100}]
        },
        headers=auth_headers
    )

    # Search for "test_user" - should only match literal underscore
    response = client.get(
        "/api/v1/invoices/?customer_name=test_user",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()

    # Should find only the invoice with literal underscore
    matching = [
        inv for inv in data["items"]
        if inv["customer_name"] == "test_user"
    ]
    assert len(matching) >= 1

    # Should NOT match testXuser (if _ was treated as wildcard)
    wrong_matches = [
        inv for inv in data["items"]
        if inv["customer_name"] == "testXuser"
    ]
    assert len(wrong_matches) == 0


def test_list_invoices_wildcard_escape_percent(client, auth_headers):
    """Test that percent sign in search is treated literally."""
    # Create an invoice with percent sign
    client.post(
        "/api/v1/invoices/",
        json={
            "customer_name": "50% Discount Corp",
            "issue_date": "2024-01-15",
            "items": [{"description": "Item", "quantity": 1, "unit_price": 100}]
        },
        headers=auth_headers
    )

    # Search for "50%" - should match literally
    response = client.get(
        "/api/v1/invoices/?customer_name=50%25",  # URL encoded %
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()

    # Should find the invoice with percent sign
    matching = [
        inv for inv in data["items"]
        if "50%" in inv["customer_name"]
    ]
    assert len(matching) >= 1


def test_list_invoices_wildcard_escape_invoice_number(client, auth_headers):
    """Test that SQL wildcards in invoice number search are escaped."""
    # Create an invoice
    client.post(
        "/api/v1/invoices/",
        json={
            "customer_name": "Wildcard Test",
            "issue_date": "2024-01-15",
            "items": [{"description": "Item", "quantity": 1, "unit_price": 100}]
        },
        headers=auth_headers
    )

    # Search with underscore that should be literal (not wildcard)
    # This should not match if underscore is escaped properly
    response = client.get(
        "/api/v1/invoices/?invoice_number=INV_NONEXISTENT",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()

    # Should find no invoices (underscore is literal)
    assert data["total"] == 0


def test_list_invoices_date_range_validation(client, auth_headers):
    """Test that start_date > end_date returns validation error."""
    response = client.get(
        "/api/v1/invoices/?start_date=2024-12-31&end_date=2024-01-01",
        headers=auth_headers
    )
    assert response.status_code == 422
    assert "start_date must be less than or equal to end_date" in \
        response.json()["message"]


def test_list_invoices_amount_range_validation(client, auth_headers):
    """Test that min_amount > max_amount returns validation error."""
    response = client.get(
        "/api/v1/invoices/?min_amount=100&max_amount=50",
        headers=auth_headers
    )
    assert response.status_code == 422
    assert "min_amount must be less than or equal to max_amount" in \
        response.json()["message"]
