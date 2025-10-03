"""
Tests for client management endpoints.
Covers CRUD operations, RBAC, tenant isolation, and GDPR compliance.
"""
import pytest
from app.models.client import Client as ClientModel


def test_create_client_as_admin(client, admin_auth_headers, test_tenant):
    """Test that admin can create a client."""
    response = client.post(
        "/api/v1/clients/",
        json={
            "name": "Acme Corporation",
            "email": "contact@acme.com",
            "phone": "+1234567890",
            "address": "123 Main St, City, State 12345",
            "tax_id": "TAX-123456",
            "tenant_id": test_tenant.id
        },
        headers=admin_auth_headers
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Acme Corporation"
    assert data["email"] == "contact@acme.com"
    assert data["phone"] == "+1234567890"
    assert data["address"] == "123 Main St, City, State 12345"
    assert data["tax_id"] == "TAX-123456"
    assert data["tenant_id"] == test_tenant.id
    assert data["is_active"] is True
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data


def test_create_client_as_owner(client, auth_headers, test_tenant):
    """Test that owner can create a client."""
    response = client.post(
        "/api/v1/clients/",
        json={
            "name": "Tech Solutions Inc",
            "email": "info@techsolutions.com",
            "tenant_id": test_tenant.id
        },
        headers=auth_headers
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Tech Solutions Inc"
    assert data["email"] == "info@techsolutions.com"


def test_create_client_as_manager_forbidden(client, manager_auth_headers,
                                            test_tenant):
    """Test that manager cannot create a client."""
    response = client.post(
        "/api/v1/clients/",
        json={
            "name": "Test Client",
            "tenant_id": test_tenant.id
        },
        headers=manager_auth_headers
    )
    assert response.status_code == 403


def test_create_client_as_attendant_forbidden(client, attendant_auth_headers,
                                              test_tenant):
    """Test that attendant cannot create a client."""
    response = client.post(
        "/api/v1/clients/",
        json={
            "name": "Test Client",
            "tenant_id": test_tenant.id
        },
        headers=attendant_auth_headers
    )
    assert response.status_code == 403


def test_create_client_minimal_data(client, admin_auth_headers, test_tenant):
    """Test creating a client with only required fields."""
    response = client.post(
        "/api/v1/clients/",
        json={
            "name": "John Doe",
            "tenant_id": test_tenant.id
        },
        headers=admin_auth_headers
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "John Doe"
    assert data["email"] is None
    assert data["phone"] is None
    assert data["address"] is None
    assert data["tax_id"] is None


def test_create_client_duplicate_email_same_tenant(
        client, admin_auth_headers, test_tenant):
    """Test that duplicate email in same tenant is rejected."""
    # Create first client
    client.post(
        "/api/v1/clients/",
        json={
            "name": "First Client",
            "email": "duplicate@example.com",
            "tenant_id": test_tenant.id
        },
        headers=admin_auth_headers
    )

    # Try to create second client with same email
    response = client.post(
        "/api/v1/clients/",
        json={
            "name": "Second Client",
            "email": "duplicate@example.com",
            "tenant_id": test_tenant.id
        },
        headers=admin_auth_headers
    )
    assert response.status_code == 400
    assert "email already exists" in response.json()["detail"]


def test_create_client_for_another_tenant_forbidden(
        client, admin_auth_headers, second_tenant):
    """Test that user cannot create client for another tenant."""
    response = client.post(
        "/api/v1/clients/",
        json={
            "name": "Cross Tenant Client",
            "tenant_id": second_tenant.id
        },
        headers=admin_auth_headers
    )
    assert response.status_code == 403
    assert "another tenant" in response.json()["detail"]


def test_list_clients_as_admin(client, admin_auth_headers, test_tenant,
                               db_session):
    """Test that admin can list clients."""
    # Create test clients
    for i in range(3):
        test_client = ClientModel(
            name=f"Client {i}",
            email=f"client{i}@example.com",
            tenant_id=test_tenant.id
        )
        db_session.add(test_client)
    db_session.commit()

    response = client.get("/api/v1/clients/", headers=admin_auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    assert all(c["tenant_id"] == test_tenant.id for c in data)


def test_list_clients_as_owner(client, auth_headers, test_tenant,
                               db_session):
    """Test that owner can list clients."""
    # Create test clients
    test_client = ClientModel(
        name="Test Client",
        tenant_id=test_tenant.id
    )
    db_session.add(test_client)
    db_session.commit()

    response = client.get("/api/v1/clients/", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1


def test_list_clients_as_manager_forbidden(client, manager_auth_headers):
    """Test that manager cannot list clients."""
    response = client.get("/api/v1/clients/", headers=manager_auth_headers)
    assert response.status_code == 403


def test_list_clients_pagination(client, admin_auth_headers, test_tenant,
                                 db_session):
    """Test client listing pagination."""
    # Create 10 test clients
    for i in range(10):
        test_client = ClientModel(
            name=f"Client {i}",
            tenant_id=test_tenant.id
        )
        db_session.add(test_client)
    db_session.commit()

    # Get first 5 clients
    response = client.get(
        "/api/v1/clients/?skip=0&limit=5",
        headers=admin_auth_headers
    )
    assert response.status_code == 200
    assert len(response.json()) == 5

    # Get next 5 clients
    response = client.get(
        "/api/v1/clients/?skip=5&limit=5",
        headers=admin_auth_headers
    )
    assert response.status_code == 200
    assert len(response.json()) == 5


def test_list_clients_excludes_inactive(client, admin_auth_headers,
                                        test_tenant, db_session):
    """Test that inactive clients are not listed."""
    # Create active client
    active_client = ClientModel(
        name="Active Client",
        tenant_id=test_tenant.id,
        is_active=True
    )
    # Create inactive client
    inactive_client = ClientModel(
        name="Inactive Client",
        tenant_id=test_tenant.id,
        is_active=False
    )
    db_session.add(active_client)
    db_session.add(inactive_client)
    db_session.commit()

    response = client.get("/api/v1/clients/", headers=admin_auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Active Client"


def test_get_client_by_id_as_admin(client, admin_auth_headers, test_tenant,
                                   db_session):
    """Test that admin can get a specific client by ID."""
    test_client = ClientModel(
        name="Specific Client",
        email="specific@example.com",
        tenant_id=test_tenant.id
    )
    db_session.add(test_client)
    db_session.commit()
    db_session.refresh(test_client)

    response = client.get(
        f"/api/v1/clients/{test_client.id}",
        headers=admin_auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == test_client.id
    assert data["name"] == "Specific Client"
    assert data["email"] == "specific@example.com"


def test_get_client_by_id_as_owner(client, auth_headers, test_tenant,
                                   db_session):
    """Test that owner can get a specific client by ID."""
    test_client = ClientModel(
        name="Owner Client",
        tenant_id=test_tenant.id
    )
    db_session.add(test_client)
    db_session.commit()
    db_session.refresh(test_client)

    response = client.get(
        f"/api/v1/clients/{test_client.id}",
        headers=auth_headers
    )
    assert response.status_code == 200
    assert response.json()["id"] == test_client.id


def test_get_client_by_id_as_manager_forbidden(
        client, manager_auth_headers, test_tenant, db_session):
    """Test that manager cannot get client by ID."""
    test_client = ClientModel(
        name="Test Client",
        tenant_id=test_tenant.id
    )
    db_session.add(test_client)
    db_session.commit()
    db_session.refresh(test_client)

    response = client.get(
        f"/api/v1/clients/{test_client.id}",
        headers=manager_auth_headers
    )
    assert response.status_code == 403


def test_get_client_not_found(client, admin_auth_headers):
    """Test that getting non-existent client returns 404."""
    response = client.get(
        "/api/v1/clients/nonexistent-id",
        headers=admin_auth_headers
    )
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


def test_update_client_as_admin(client, admin_auth_headers, test_tenant,
                                db_session):
    """Test that admin can update a client."""
    test_client = ClientModel(
        name="Original Name",
        email="original@example.com",
        tenant_id=test_tenant.id
    )
    db_session.add(test_client)
    db_session.commit()
    db_session.refresh(test_client)

    response = client.put(
        f"/api/v1/clients/{test_client.id}",
        json={
            "name": "Updated Name",
            "email": "updated@example.com",
            "phone": "+9876543210"
        },
        headers=admin_auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Name"
    assert data["email"] == "updated@example.com"
    assert data["phone"] == "+9876543210"


def test_update_client_as_owner(client, auth_headers, test_tenant,
                                db_session):
    """Test that owner can update a client."""
    test_client = ClientModel(
        name="Client Name",
        tenant_id=test_tenant.id
    )
    db_session.add(test_client)
    db_session.commit()
    db_session.refresh(test_client)

    response = client.put(
        f"/api/v1/clients/{test_client.id}",
        json={"name": "New Name"},
        headers=auth_headers
    )
    assert response.status_code == 200
    assert response.json()["name"] == "New Name"


def test_update_client_as_manager_forbidden(client, manager_auth_headers,
                                            test_tenant, db_session):
    """Test that manager cannot update a client."""
    test_client = ClientModel(
        name="Test Client",
        tenant_id=test_tenant.id
    )
    db_session.add(test_client)
    db_session.commit()
    db_session.refresh(test_client)

    response = client.put(
        f"/api/v1/clients/{test_client.id}",
        json={"name": "Updated Name"},
        headers=manager_auth_headers
    )
    assert response.status_code == 403


def test_update_client_partial(client, admin_auth_headers, test_tenant,
                               db_session):
    """Test partial client update."""
    test_client = ClientModel(
        name="Original Name",
        email="original@example.com",
        phone="+1111111111",
        tenant_id=test_tenant.id
    )
    db_session.add(test_client)
    db_session.commit()
    db_session.refresh(test_client)

    # Update only phone
    response = client.put(
        f"/api/v1/clients/{test_client.id}",
        json={"phone": "+2222222222"},
        headers=admin_auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Original Name"  # Unchanged
    assert data["email"] == "original@example.com"  # Unchanged
    assert data["phone"] == "+2222222222"  # Updated


def test_update_client_duplicate_email(client, admin_auth_headers,
                                       test_tenant, db_session):
    """Test that updating to duplicate email is rejected."""
    # Create first client
    client1 = ClientModel(
        name="Client 1",
        email="first@example.com",
        tenant_id=test_tenant.id
    )
    # Create second client
    client2 = ClientModel(
        name="Client 2",
        email="second@example.com",
        tenant_id=test_tenant.id
    )
    db_session.add(client1)
    db_session.add(client2)
    db_session.commit()
    db_session.refresh(client2)

    # Try to update client2 to have client1's email
    response = client.put(
        f"/api/v1/clients/{client2.id}",
        json={"email": "first@example.com"},
        headers=admin_auth_headers
    )
    assert response.status_code == 400
    assert "email already exists" in response.json()["detail"]


def test_update_client_not_found(client, admin_auth_headers):
    """Test that updating non-existent client returns 404."""
    response = client.put(
        "/api/v1/clients/nonexistent-id",
        json={"name": "New Name"},
        headers=admin_auth_headers
    )
    assert response.status_code == 404


def test_delete_client_as_owner(client, auth_headers, test_tenant,
                                db_session):
    """Test that owner can soft delete a client."""
    test_client = ClientModel(
        name="Client to Delete",
        tenant_id=test_tenant.id
    )
    db_session.add(test_client)
    db_session.commit()
    db_session.refresh(test_client)

    response = client.delete(
        f"/api/v1/clients/{test_client.id}",
        headers=auth_headers
    )
    assert response.status_code == 200
    assert "deactivated successfully" in response.json()["message"]

    # Verify client is soft deleted
    db_session.refresh(test_client)
    assert test_client.is_active is False


def test_delete_client_as_admin_forbidden(client, admin_auth_headers,
                                          test_tenant, db_session):
    """Test that admin cannot delete a client (only owner can)."""
    test_client = ClientModel(
        name="Test Client",
        tenant_id=test_tenant.id
    )
    db_session.add(test_client)
    db_session.commit()
    db_session.refresh(test_client)

    response = client.delete(
        f"/api/v1/clients/{test_client.id}",
        headers=admin_auth_headers
    )
    assert response.status_code == 403


def test_delete_client_as_manager_forbidden(client, manager_auth_headers,
                                            test_tenant, db_session):
    """Test that manager cannot delete a client."""
    test_client = ClientModel(
        name="Test Client",
        tenant_id=test_tenant.id
    )
    db_session.add(test_client)
    db_session.commit()
    db_session.refresh(test_client)

    response = client.delete(
        f"/api/v1/clients/{test_client.id}",
        headers=manager_auth_headers
    )
    assert response.status_code == 403


def test_delete_client_not_found(client, auth_headers):
    """Test that deleting non-existent client returns 404."""
    response = client.delete(
        "/api/v1/clients/nonexistent-id",
        headers=auth_headers
    )
    assert response.status_code == 404


def test_client_validation_name_too_short(client, admin_auth_headers,
                                          test_tenant):
    """Test that empty name is rejected."""
    response = client.post(
        "/api/v1/clients/",
        json={
            "name": "",
            "tenant_id": test_tenant.id
        },
        headers=admin_auth_headers
    )
    assert response.status_code == 422


def test_client_validation_invalid_email(client, admin_auth_headers,
                                         test_tenant):
    """Test that invalid email format is rejected."""
    response = client.post(
        "/api/v1/clients/",
        json={
            "name": "Test Client",
            "email": "not-an-email",
            "tenant_id": test_tenant.id
        },
        headers=admin_auth_headers
    )
    assert response.status_code == 422
