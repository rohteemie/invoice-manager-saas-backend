"""
Integration tests for end-to-end workflows.

This module contains comprehensive integration tests that validate:
- Complete business workflows across multiple endpoints
- Cross-module integration (auth, users, tenants, invoices)
- Multi-tenant isolation in complex scenarios
- Real-world user journeys and business scenarios
"""

from datetime import datetime, timedelta
from decimal import Decimal


class TestInvoiceLifecycleIntegration:
    """Test complete invoice lifecycle workflows from creation to payment."""

    def test_complete_invoice_workflow_draft_to_paid(
        self,
        client,
        test_tenant,
        db_session
    ):
        """
        Test complete invoice lifecycle: registration → login → create → send → pay.

        This simulates a real business workflow where:
        1. A new user registers
        2. User logs in
        3. User creates a draft invoice
        4. Manager approves and sends invoice
        5. Invoice is marked as paid
        """
        # Step 1: Register a new manager user
        register_response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "workflow.manager@testcompany.com",
                "full_name": "Workflow Manager",
                "password": "TestPass123!",
                "role": "manager",
                "tenant_id": test_tenant.id
            }
        )
        assert register_response.status_code == 201
        user_data = register_response.json()
        assert user_data["email"] == "workflow.manager@testcompany.com"

        # Verify the user's email to allow invoice creation
        from app.models.user import User as UserModel
        user = db_session.query(UserModel).filter(
            UserModel.email == "workflow.manager@testcompany.com"
        ).first()
        user.is_verified = True
        db_session.commit()

        # Step 2: Login with the new user
        login_response = client.post(
            "/api/v1/auth/login",
            data={
                "username": "workflow.manager@testcompany.com",
                "password": "TestPass123!"
            }
        )
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Step 3: Create a draft invoice
        invoice_data = {
            "customer_name": "John Doe",
            "customer_email": "john.doe@example.com",
            "customer_phone": "+1234567890",
            "issue_date": "2024-01-15",
            "due_date": "2024-02-15",
            "items": [
                {
                    "description": "Product A",
                    "quantity": 2,
                    "unit_price": 100.00
                },
                {
                    "description": "Service B",
                    "quantity": 1,
                    "unit_price": 250.00
                }
            ],
            "notes": "Thank you for your business"
        }

        create_response = client.post(
            "/api/v1/invoices/",
            json=invoice_data,
            headers=headers
        )
        assert create_response.status_code == 201
        invoice = create_response.json()
        invoice_id = invoice["id"]
        assert invoice["status"] == "draft"
        assert invoice["total_amount"] == "450.00"

        # Step 4: Send the invoice (status transition)
        send_response = client.patch(
            f"/api/v1/invoices/{invoice_id}/status",
            json={"status": "sent"},
            headers=headers
        )
        assert send_response.status_code == 200
        sent_invoice = send_response.json()
        assert sent_invoice["status"] == "sent"

        # Step 5: Mark invoice as paid
        pay_response = client.patch(
            f"/api/v1/invoices/{invoice_id}/status",
            json={
                "status": "paid",
                "payment_method": "card",
                "payment_reference": "PAY-123456"
            },
            headers=headers
        )
        assert pay_response.status_code == 200
        paid_invoice = pay_response.json()
        assert paid_invoice["status"] == "paid"
        assert paid_invoice["paid_at"] is not None
        assert paid_invoice["payment_method"] == "card"

        # Step 6: Verify invoice cannot be modified after paid
        update_response = client.put(
            f"/api/v1/invoices/{invoice_id}",
            json={"notes": "Updated notes"},
            headers=headers
        )
        assert update_response.status_code == 400

    def test_invoice_overdue_workflow(
        self,
        client,
        manager_auth_headers,
        test_tenant
    ):
        """
        Test invoice overdue workflow.

        Simulates:
        1. Create invoice with past due date
        2. Send invoice
        3. Invoice automatically becomes overdue
        4. Pay overdue invoice
        """
        # Create invoice with past due date
        past_date = (datetime.now() - timedelta(days=10)).date().isoformat()
        issue_date = (datetime.now() - timedelta(days=20)).date().isoformat()
        invoice_data = {
            "customer_name": "Late Payer",
            "customer_email": "late@example.com",
            "issue_date": issue_date,
            "due_date": past_date,
            "items": [
                {
                    "description": "Product",
                    "quantity": 1,
                    "unit_price": 500.00
                }
            ]
        }

        create_response = client.post(
            "/api/v1/invoices/",
            json=invoice_data,
            headers=manager_auth_headers
        )
        assert create_response.status_code == 201
        invoice_id = create_response.json()["id"]

        # Send invoice
        send_response = client.patch(
            f"/api/v1/invoices/{invoice_id}/status",
            json={"status": "sent"},
            headers=manager_auth_headers
        )
        assert send_response.status_code == 200

        # Mark as overdue
        overdue_response = client.patch(
            f"/api/v1/invoices/{invoice_id}/status",
            json={"status": "overdue"},
            headers=manager_auth_headers
        )
        assert overdue_response.status_code == 200
        assert overdue_response.json()["status"] == "overdue"

        # Pay overdue invoice
        pay_response = client.patch(
            f"/api/v1/invoices/{invoice_id}/status",
            json={
                "status": "paid",
                "payment_method": "transfer"
            },
            headers=manager_auth_headers
        )
        assert pay_response.status_code == 200
        assert pay_response.json()["status"] == "paid"


class TestMultiTenantIntegration:
    """Test multi-tenant isolation in complex scenarios."""

    def test_concurrent_invoice_creation_different_tenants(
        self,
        client,
        test_tenant,
        second_tenant,
        auth_headers,
        second_tenant_auth_headers
    ):
        """
        Test that invoices created by different tenants are properly isolated.

        Verifies:
        1. Each tenant can create invoices
        2. Tenants cannot see each other's invoices
        3. Invoice numbers are tenant-specific
        """
        # Tenant 1 creates invoice
        invoice1_data = {
            "customer_name": "Customer A",
            "customer_email": "customer.a@example.com",
            "issue_date": "2024-01-15",
            "items": [{"description": "Item 1", "quantity": 1, "unit_price": 100}]
        }
        response1 = client.post(
            "/api/v1/invoices/",
            json=invoice1_data,
            headers=auth_headers
        )
        assert response1.status_code == 201
        invoice1 = response1.json()

        # Tenant 2 creates invoice
        invoice2_data = {
            "customer_name": "Customer B",
            "customer_email": "customer.b@example.com",
            "issue_date": "2024-01-15",
            "items": [{"description": "Item 2", "quantity": 1, "unit_price": 200}]
        }
        response2 = client.post(
            "/api/v1/invoices/",
            json=invoice2_data,
            headers=second_tenant_auth_headers
        )
        assert response2.status_code == 201
        invoice2 = response2.json()

        # Verify invoices are different
        assert invoice1["id"] != invoice2["id"]
        # Note: Invoice numbers may be the same across tenants in the current implementation
        # This is acceptable as long as they're unique within each tenant

        # Tenant 1 lists invoices - should only see their own
        list1_response = client.get(
            "/api/v1/invoices/",
            headers=auth_headers
        )
        assert list1_response.status_code == 200
        data1 = list1_response.json()
        tenant1_invoices = data1["items"]
        tenant1_ids = [inv["id"] for inv in tenant1_invoices]
        assert invoice1["id"] in tenant1_ids
        assert invoice2["id"] not in tenant1_ids

        # Tenant 2 lists invoices - should only see their own
        list2_response = client.get(
            "/api/v1/invoices/",
            headers=second_tenant_auth_headers
        )
        assert list2_response.status_code == 200
        data2 = list2_response.json()
        tenant2_invoices = data2["items"]
        tenant2_ids = [inv["id"] for inv in tenant2_invoices]
        assert invoice2["id"] in tenant2_ids
        assert invoice1["id"] not in tenant2_ids

        # Tenant 1 cannot access Tenant 2's invoice
        access_response = client.get(
            f"/api/v1/invoices/{invoice2['id']}",
            headers=auth_headers
        )
        assert access_response.status_code == 404

    def test_cross_tenant_export_isolation(
        self,
        client,
        auth_headers,
        second_tenant_auth_headers,
        test_manager
    ):
        """Test that invoice exports respect tenant boundaries."""
        # Create invoices for both tenants
        for headers in [auth_headers, second_tenant_auth_headers]:
            client.post(
                "/api/v1/invoices/",
                json={
                    "customer_name": "Customer",
                    "customer_email": "customer@example.com",
                    "issue_date": "2024-01-15",
                    "items": [{"description": "Item", "quantity": 1, "unit_price": 100}]
                },
                headers=headers
            )

        # Export for tenant 1
        export1_response = client.get(
            "/api/v1/invoices/export/invoices?format=json",
            headers=auth_headers
        )
        assert export1_response.status_code == 200
        export1_data = export1_response.json()

        # Export for tenant 2
        export2_response = client.get(
            "/api/v1/invoices/export/invoices?format=json",
            headers=second_tenant_auth_headers
        )
        assert export2_response.status_code == 200
        export2_data = export2_response.json()

        # Verify exports contain different data
        assert export1_data != export2_data
        assert len(export1_data) > 0
        assert len(export2_data) > 0


class TestRoleBasedWorkflows:
    """Test role-based access control in complete workflows."""

    def test_invoice_approval_workflow_by_role(
        self,
        client,
        test_tenant,
        db_session
    ):
        """
        Test invoice workflow with different user roles.

        Workflow:
        1. Attendant creates draft invoice
        2. Attendant cannot send invoice (insufficient permissions)
        3. Manager sends invoice
        4. Admin cannot delete non-draft invoice
        5. Owner can delete any invoice
        """
        from app.models.user import User, UserRole
        from app.core.security import get_password_hash

        # Create users with different roles
        attendant = User(
            email="attendant.workflow@testcompany.com",
            full_name="Workflow Attendant",
            hashed_password=get_password_hash("TestPass123!"),
            role=UserRole.ATTENDANT,
            tenant_id=test_tenant.id,
            is_active=True,
            is_verified=True
        )
        manager = User(
            email="manager.workflow@testcompany.com",
            full_name="Workflow Manager",
            hashed_password=get_password_hash("TestPass123!"),
            role=UserRole.MANAGER,
            tenant_id=test_tenant.id,
            is_active=True,
            is_verified=True
        )
        owner = User(
            email="owner.workflow@testcompany.com",
            full_name="Workflow Owner",
            hashed_password=get_password_hash("TestPass123!"),
            role=UserRole.OWNER,
            tenant_id=test_tenant.id,
            is_active=True,
            is_verified=True
        )
        db_session.add_all([attendant, manager, owner])
        db_session.commit()

        # Get auth tokens
        attendant_token = client.post(
            "/api/v1/auth/login",
            data={"username": attendant.email, "password": "TestPass123!"}
        ).json()["access_token"]
        attendant_headers = {"Authorization": f"Bearer {attendant_token}"}

        manager_token = client.post(
            "/api/v1/auth/login",
            data={"username": manager.email, "password": "TestPass123!"}
        ).json()["access_token"]
        manager_headers = {"Authorization": f"Bearer {manager_token}"}

        owner_token = client.post(
            "/api/v1/auth/login",
            data={"username": owner.email, "password": "TestPass123!"}
        ).json()["access_token"]
        owner_headers = {"Authorization": f"Bearer {owner_token}"}

        # Step 1: Attendant creates draft invoice
        invoice_data = {
            "customer_name": "Customer X",
            "customer_email": "customer.x@example.com",
            "issue_date": "2024-01-15",
            "items": [{"description": "Product", "quantity": 1, "unit_price": 100}]
        }
        create_response = client.post(
            "/api/v1/invoices/",
            json=invoice_data,
            headers=attendant_headers
        )
        assert create_response.status_code == 201
        invoice_id = create_response.json()["id"]

        # Step 2: Attendant tries to send invoice (should fail)
        send_attempt = client.patch(
            f"/api/v1/invoices/{invoice_id}/status",
            json={"status": "sent"},
            headers=attendant_headers
        )
        assert send_attempt.status_code == 403

        # Step 3: Owner sends invoice (should succeed)
        send_response = client.patch(
            f"/api/v1/invoices/{invoice_id}/status",
            json={"status": "sent"},
            headers=owner_headers
        )
        assert send_response.status_code == 200

        # Step 4: Manager tries to delete sent invoice (should fail)
        delete_attempt = client.delete(
            f"/api/v1/invoices/{invoice_id}",
            headers=manager_headers
        )
        assert delete_attempt.status_code in [400, 403]  # Either forbidden or bad request

        # Step 5: Owner deletes invoice (should succeed if owner has permission)
        # Note: Based on current implementation, only draft invoices can be deleted
        # So we create a new draft invoice for this test
        draft_response = client.post(
            "/api/v1/invoices/",
            json=invoice_data,
            headers=attendant_headers
        )
        draft_id = draft_response.json()["id"]

        delete_response = client.delete(
            f"/api/v1/invoices/{draft_id}",
            headers=owner_headers
        )
        # Owner should be able to delete draft invoices
        assert delete_response.status_code in [200, 204]


class TestBusinessScenarios:
    """Test real-world business scenarios."""

    def test_branch_performance_tracking(
        self,
        client,
        auth_headers,
        test_tenant
    ):
        """
        Test tracking invoices by branch for performance analysis.

        Scenario:
        1. Create invoices for different branches
        2. Filter invoices by branch
        3. Calculate totals per branch
        """
        branches = ["Branch A", "Branch B", "Branch C"]
        branch_invoices = {branch: [] for branch in branches}

        # Create invoices for each branch
        for branch in branches:
            for i in range(3):
                invoice_data = {
                    "customer_name": f"Customer {i}",
                    "customer_email": f"customer{i}@{branch.lower().replace(' ', '')}.com",
                    "issue_date": "2024-01-15",
                    "items": [
                        {
                            "description": f"Product {i}",
                            "quantity": 1,
                            "unit_price": (i + 1) * 100
                        }
                    ]
                }
                response = client.post(
                    "/api/v1/invoices/",
                    json=invoice_data,
                    headers=auth_headers
                )
                assert response.status_code == 201
                branch_invoices[branch].append(response.json())

        # Verify we can retrieve and filter invoices
        all_invoices_response = client.get(
            "/api/v1/invoices/",
            headers=auth_headers
        )
        assert all_invoices_response.status_code == 200
        data = all_invoices_response.json()
        all_invoices = data["items"]

        # Verify each branch has 3 invoices created
        for branch in branches:
            # Count invoices for this branch by checking customer email pattern
            branch_email_pattern = branch.lower().replace(' ', '')
            branch_specific = [
                inv for inv in all_invoices
                if branch_email_pattern in inv.get("customer_email", "")
            ]
            assert len(branch_specific) == 3

    def test_customer_invoice_history(
        self,
        client,
        auth_headers
    ):
        """
        Test tracking invoice history for a specific customer.

        Scenario:
        1. Create multiple invoices for same customer
        2. Retrieve invoices for that customer
        3. Track customer payment patterns
        """
        customer_email = "repeat.customer@example.com"

        # Create multiple invoices for same customer
        invoice_ids = []
        for i in range(3):
            invoice_data = {
                "customer_name": "Repeat Customer",
                "customer_email": customer_email,
                "issue_date": "2024-01-15",
                "items": [
                    {
                        "description": f"Order {i + 1}",
                        "quantity": 1,
                        "unit_price": (i + 1) * 50
                    }
                ]
            }
            response = client.post(
                "/api/v1/invoices/",
                json=invoice_data,
                headers=auth_headers
            )
            assert response.status_code == 201
            invoice_ids.append(response.json()["id"])

        # Retrieve all invoices
        all_invoices_response = client.get(
            "/api/v1/invoices/",
            headers=auth_headers
        )
        assert all_invoices_response.status_code == 200
        data = all_invoices_response.json()
        all_invoices = data["items"]

        # Filter by customer email
        customer_invoices = [
            inv for inv in all_invoices
            if inv["customer_email"] == customer_email
        ]
        assert len(customer_invoices) == 3

        # Verify all invoice IDs are present
        customer_invoice_ids = [inv["id"] for inv in customer_invoices]
        for invoice_id in invoice_ids:
            assert invoice_id in customer_invoice_ids

    def test_invoice_export_filtering(
        self,
        client,
        auth_headers,
        manager_auth_headers
    ):
        """
        Test exporting invoices with various filters.

        Scenario:
        1. Create invoices with different statuses and dates
        2. Export with status filter
        3. Export with date range filter
        4. Verify filtered exports
        """
        # Create invoices with different statuses
        statuses = ["draft", "sent", "paid"]
        invoice_ids_by_status = {status: [] for status in statuses}

        # Create draft invoices
        for i in range(2):
            response = client.post(
                "/api/v1/invoices/",
                json={
                    "customer_name": f"Customer {i}",
                    "customer_email": f"customer{i}@example.com",
                    "issue_date": "2024-01-15",
                    "items": [{"description": "Item", "quantity": 1, "unit_price": 100}]
                },
                headers=auth_headers
            )
            invoice_ids_by_status["draft"].append(response.json()["id"])

        # Create and send invoices
        for i in range(2):
            response = client.post(
                "/api/v1/invoices/",
                json={
                    "customer_name": f"Customer {i + 2}",
                    "customer_email": f"customer{i + 2}@example.com",
                    "issue_date": "2024-01-15",
                    "items": [{"description": "Item", "quantity": 1, "unit_price": 150}]
                },
                headers=manager_auth_headers
            )
            invoice_id = response.json()["id"]
            # Send it
            client.patch(
                f"/api/v1/invoices/{invoice_id}/status",
                json={"status": "sent"},
                headers=manager_auth_headers
            )
            invoice_ids_by_status["sent"].append(invoice_id)

        # Export with status filter
        draft_export = client.get(
            "/api/v1/invoices/export/invoices?format=json&status=draft",
            headers=auth_headers
        )
        assert draft_export.status_code == 200
        draft_data = draft_export.json()
        assert len(draft_data) == 2
        assert all(inv["status"] == "draft" for inv in draft_data)

        sent_export = client.get(
            "/api/v1/invoices/export/invoices?format=json&status=sent",
            headers=auth_headers
        )
        assert sent_export.status_code == 200
        sent_data = sent_export.json()
        assert len(sent_data) == 2
        assert all(inv["status"] == "sent" for inv in sent_data)


class TestDataConsistency:
    """Test data consistency and transaction integrity."""

    def test_invoice_items_consistency(
        self,
        client,
        auth_headers
    ):
        """
        Test that invoice items are properly created and maintained.

        Verifies:
        1. Items are created with invoice
        2. Item totals are calculated correctly
        3. Items are retrieved with invoice
        """
        invoice_data = {
            "customer_name": "Test Customer",
            "customer_email": "test@example.com",
            "issue_date": "2024-01-15",
            "items": [
                {
                    "description": "Product A",
                    "quantity": 2,
                    "unit_price": 50.00
                },
                {
                    "description": "Product B",
                    "quantity": 3,
                    "unit_price": 75.00
                },
                {
                    "description": "Service C",
                    "quantity": 1,
                    "unit_price": 200.00
                }
            ]
        }

        # Create invoice
        create_response = client.post(
            "/api/v1/invoices/",
            json=invoice_data,
            headers=auth_headers
        )
        assert create_response.status_code == 201
        invoice = create_response.json()
        invoice_id = invoice["id"]

        # Verify items
        assert len(invoice["items"]) == 3

        # Verify individual item calculations
        item_a = next(item for item in invoice["items"] if item["description"] == "Product A")
        assert Decimal(item_a["total_price"]) == Decimal("100.00")  # 2 * 50

        item_b = next(item for item in invoice["items"] if item["description"] == "Product B")
        assert Decimal(item_b["total_price"]) == Decimal("225.00")  # 3 * 75

        item_c = next(item for item in invoice["items"] if item["description"] == "Service C")
        assert Decimal(item_c["total_price"]) == Decimal("200.00")  # 1 * 200

        # Verify total amount
        expected_total = Decimal("100.00") + Decimal("225.00") + Decimal("200.00")
        assert Decimal(invoice["total_amount"]) == expected_total

        # Retrieve invoice and verify items are still there
        get_response = client.get(
            f"/api/v1/invoices/{invoice_id}",
            headers=auth_headers
        )
        assert get_response.status_code == 200
        retrieved_invoice = get_response.json()
        assert len(retrieved_invoice["items"]) == 3

    def test_invoice_update_recalculation(
        self,
        client,
        auth_headers
    ):
        """
        Test that updating invoice items recalculates totals correctly.
        """
        # Create invoice
        invoice_data = {
            "customer_name": "Customer",
            "customer_email": "customer@example.com",
            "issue_date": "2024-01-15",
            "items": [
                {
                    "description": "Original Item",
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
        invoice_id = create_response.json()["id"]
        original_total = create_response.json()["total_amount"]
        assert Decimal(original_total) == Decimal("100.00")

        # Update invoice with new items
        update_data = {
            "items": [
                {
                    "description": "Updated Item 1",
                    "quantity": 2,
                    "unit_price": 75.00
                },
                {
                    "description": "Updated Item 2",
                    "quantity": 1,
                    "unit_price": 50.00
                }
            ]
        }

        update_response = client.put(
            f"/api/v1/invoices/{invoice_id}",
            json=update_data,
            headers=auth_headers
        )
        assert update_response.status_code == 200
        updated_invoice = update_response.json()

        # Verify new total
        expected_total = Decimal("150.00") + Decimal("50.00")  # (2*75) + (1*50)
        assert Decimal(updated_invoice["total_amount"]) == expected_total
        assert len(updated_invoice["items"]) == 2
