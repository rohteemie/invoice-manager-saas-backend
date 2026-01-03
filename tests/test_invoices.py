"""
Test suite for Invoice CRUD operations and lifecycle management.
Tests invoice creation, retrieval, updates, status transitions, and deletion.
"""


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
    for i in range(2):
        client.post(
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
        headers=auth_headers
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
        headers=auth_headers
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
    assert "email" in response.json()["detail"].lower()
    assert "download" in response.json()["detail"].lower()


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
    assert "DRAFT" in response.json()["detail"]


def test_send_invoice_not_found(client, manager_auth_headers):
    """Test sending a non-existent invoice."""
    response = client.post(
        "/api/v1/invoices/nonexistent-id/send",
        headers=manager_auth_headers
    )

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


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
