"""
Test suite for Tenant CRUD operations.
Tests tenant creation, retrieval, updates, and soft deletion.
"""
import pytest


def test_create_tenant(client):
    """Test creating a new tenant."""
    response = client.post(
        "/api/v1/tenants/",
        json={
            "name": "New Company",
            "domain": "newcompany.com",
            "plan_type": "premium",
            "description": "A new test company"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "New Company"
    assert data["domain"] == "newcompany.com"
    assert data["plan_type"] == "premium"
    assert data["description"] == "A new test company"
    assert data["is_active"] is True
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data


def test_create_tenant_duplicate_domain(client, test_tenant):
    """Test that duplicate domain names are rejected."""
    response = client.post(
        "/api/v1/tenants/",
        json={
            "name": "Another Company",
            "domain": "testcompany.com",  # Same as test_tenant
            "plan_type": "free"
        }
    )
    assert response.status_code == 400
    assert "domain" in response.json()["detail"].lower()


def test_create_tenant_without_domain(client):
    """Test creating a tenant without a domain."""
    response = client.post(
        "/api/v1/tenants/",
        json={
            "name": "No Domain Company",
            "plan_type": "free"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "No Domain Company"
    assert data["domain"] is None


def test_list_tenants(client, test_tenant, second_tenant):
    """Test listing all tenants."""
    response = client.get("/api/v1/tenants/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2
    tenant_names = [t["name"] for t in data]
    assert "Test Company" in tenant_names
    assert "Second Company" in tenant_names


def test_list_tenants_pagination(client, test_tenant):
    """Test tenant list pagination."""
    response = client.get("/api/v1/tenants/?skip=0&limit=1")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1


def test_get_tenant_by_id(client, test_tenant):
    """Test retrieving a specific tenant by ID."""
    response = client.get(f"/api/v1/tenants/{test_tenant.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == test_tenant.id
    assert data["name"] == test_tenant.name
    assert data["domain"] == test_tenant.domain


def test_get_tenant_not_found(client):
    """Test retrieving a non-existent tenant."""
    response = client.get("/api/v1/tenants/nonexistent-id")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_update_tenant(client, test_tenant):
    """Test updating tenant information."""
    response = client.put(
        f"/api/v1/tenants/{test_tenant.id}",
        json={
            "name": "Updated Company Name",
            "description": "Updated description",
            "plan_type": "enterprise"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Company Name"
    assert data["description"] == "Updated description"
    assert data["plan_type"] == "enterprise"
    assert data["domain"] == test_tenant.domain  # Unchanged


def test_update_tenant_domain(client, test_tenant):
    """Test updating tenant domain."""
    response = client.put(
        f"/api/v1/tenants/{test_tenant.id}",
        json={"domain": "newtestcompany.com"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["domain"] == "newtestcompany.com"


def test_update_tenant_duplicate_domain(client, test_tenant, second_tenant):
    """Test that updating to a duplicate domain is rejected."""
    response = client.put(
        f"/api/v1/tenants/{test_tenant.id}",
        json={"domain": second_tenant.domain}
    )
    assert response.status_code == 400
    assert "domain" in response.json()["detail"].lower()


def test_update_tenant_not_found(client):
    """Test updating a non-existent tenant."""
    response = client.put(
        "/api/v1/tenants/nonexistent-id",
        json={"name": "New Name"}
    )
    assert response.status_code == 404


def test_soft_delete_tenant(client, test_tenant):
    """Test soft deleting a tenant."""
    response = client.delete(f"/api/v1/tenants/{test_tenant.id}")
    assert response.status_code == 200
    assert "deactivated" in response.json()["message"].lower()

    # Verify tenant is marked as inactive
    get_response = client.get(f"/api/v1/tenants/{test_tenant.id}")
    assert get_response.status_code == 200
    assert get_response.json()["is_active"] is False


def test_delete_tenant_not_found(client):
    """Test deleting a non-existent tenant."""
    response = client.delete("/api/v1/tenants/nonexistent-id")
    assert response.status_code == 404


def test_tenant_validation_min_name_length(client):
    """Test that tenant name validation enforces minimum length."""
    response = client.post(
        "/api/v1/tenants/",
        json={
            "name": "",  # Empty name
            "plan_type": "free"
        }
    )
    assert response.status_code == 422  # Validation error


def test_tenant_validation_max_name_length(client):
    """Test that tenant name validation enforces maximum length."""
    response = client.post(
        "/api/v1/tenants/",
        json={
            "name": "A" * 101,  # Exceeds 100 character limit
            "plan_type": "free"
        }
    )
    assert response.status_code == 422  # Validation error
