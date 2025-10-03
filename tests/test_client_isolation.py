"""
Tests for client tenant isolation.
Ensures clients are properly isolated between tenants.
"""
from app.models.client import Client as ClientModel


def test_clients_isolated_by_tenant(client, admin_auth_headers,
                                    second_tenant_auth_headers,
                                    test_tenant, second_tenant, db_session):
    """Test that clients are properly isolated between tenants."""
    # Create client in first tenant
    client1 = ClientModel(
        name="First Tenant Client",
        email="client@tenant1.com",
        tenant_id=test_tenant.id
    )
    # Create client in second tenant
    client2 = ClientModel(
        name="Second Tenant Client",
        email="client@tenant2.com",
        tenant_id=second_tenant.id
    )
    db_session.add(client1)
    db_session.add(client2)
    db_session.commit()

    # First tenant should only see their client
    response = client.get("/api/v1/clients/", headers=admin_auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "First Tenant Client"

    # Second tenant should only see their client
    response = client.get(
        "/api/v1/clients/",
        headers=second_tenant_auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Second Tenant Client"


def test_cannot_access_other_tenant_client(client, admin_auth_headers,
                                           second_tenant, db_session):
    """Test that users cannot access clients from other tenants."""
    # Create client in second tenant
    other_client = ClientModel(
        name="Other Tenant Client",
        tenant_id=second_tenant.id
    )
    db_session.add(other_client)
    db_session.commit()
    db_session.refresh(other_client)

    # Try to access other tenant's client
    response = client.get(
        f"/api/v1/clients/{other_client.id}",
        headers=admin_auth_headers
    )
    assert response.status_code == 404


def test_cannot_update_other_tenant_client(client, admin_auth_headers,
                                           second_tenant, db_session):
    """Test that users cannot update clients from other tenants."""
    # Create client in second tenant
    other_client = ClientModel(
        name="Other Tenant Client",
        tenant_id=second_tenant.id
    )
    db_session.add(other_client)
    db_session.commit()
    db_session.refresh(other_client)

    # Try to update other tenant's client
    response = client.put(
        f"/api/v1/clients/{other_client.id}",
        json={"name": "Hacked Name"},
        headers=admin_auth_headers
    )
    assert response.status_code == 404


def test_cannot_delete_other_tenant_client(client, auth_headers,
                                           second_tenant, db_session):
    """Test that users cannot delete clients from other tenants."""
    # Create client in second tenant
    other_client = ClientModel(
        name="Other Tenant Client",
        tenant_id=second_tenant.id
    )
    db_session.add(other_client)
    db_session.commit()
    db_session.refresh(other_client)

    # Try to delete other tenant's client
    response = client.delete(
        f"/api/v1/clients/{other_client.id}",
        headers=auth_headers
    )
    assert response.status_code == 404


def test_same_email_allowed_different_tenants(client, admin_auth_headers,
                                              second_tenant_auth_headers,
                                              test_tenant, second_tenant):
    """Test that same email can exist in different tenants."""
    # Create client with email in first tenant
    response1 = client.post(
        "/api/v1/clients/",
        json={
            "name": "Client One",
            "email": "same@email.com",
            "tenant_id": test_tenant.id
        },
        headers=admin_auth_headers
    )
    assert response1.status_code == 201

    # Create client with same email in second tenant (should succeed)
    response2 = client.post(
        "/api/v1/clients/",
        json={
            "name": "Client Two",
            "email": "same@email.com",
            "tenant_id": second_tenant.id
        },
        headers=second_tenant_auth_headers
    )
    assert response2.status_code == 201

    # Verify both clients exist with same email
    client1 = response1.json()
    client2 = response2.json()
    assert client1["email"] == client2["email"]
    assert client1["tenant_id"] != client2["tenant_id"]
