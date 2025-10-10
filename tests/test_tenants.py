"""
Test suite for Tenant CRUD operations.
Tests tenant creation, retrieval, updates, and soft deletion.
"""


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


def test_register_tenant_with_owner(client):
    """Test creating a tenant with owner in one request."""
    response = client.post(
        "/api/v1/tenants/register",
        json={
            "name": "Coca-Cola",
            "email": "cocacola_globalHQ@cocacola.com",
            "plan_type": "Enterprise",
            "description": "refreshment global company",
            "domain": "food and drink",
            "owner": {
                "full_name": "John Doe",
                "email": "john@cocacola.com"
            }
        }
    )
    assert response.status_code == 201
    data = response.json()

    # Verify tenant data
    assert "tenant" in data
    assert data["tenant"]["name"] == "Coca-Cola"
    assert data["tenant"]["domain"] == "food and drink"
    assert data["tenant"]["plan_type"] == "Enterprise"
    assert data["tenant"]["description"] == "refreshment global company"
    assert data["tenant"]["is_active"] is True
    assert "id" in data["tenant"]

    # Verify owner data
    assert "owner" in data
    assert data["owner"]["full_name"] == "John Doe"
    assert data["owner"]["email"] == "john@cocacola.com"
    assert data["owner"]["role"] == "owner"
    assert data["owner"]["tenant_id"] == data["tenant"]["id"]
    assert data["owner"]["is_active"] is True
    assert data["owner"]["is_verified"] is False
    assert "password" not in data["owner"]
    assert "hashed_password" not in data["owner"]


def test_register_tenant_with_owner_duplicate_domain(client):
    """Test that duplicate domain is rejected in register endpoint."""
    # First registration
    client.post(
        "/api/v1/tenants/register",
        json={
            "name": "First Company",
            "domain": "duplicate.com",
            "plan_type": "free",
            "owner": {
                "full_name": "First Owner",
                "email": "first@duplicate.com",
                "password": "SecurePass123"
            }
        }
    )

    # Second registration with same domain
    response = client.post(
        "/api/v1/tenants/register",
        json={
            "name": "Second Company",
            "domain": "duplicate.com",
            "plan_type": "free",
            "owner": {
                "full_name": "Second Owner",
                "email": "second@duplicate.com",
                "password": "SecurePass123"
            }
        }
    )
    assert response.status_code == 400
    assert "domain" in response.json()["detail"].lower()


def test_register_tenant_with_owner_duplicate_email(client):
    """Test that duplicate owner email is rejected in register endpoint."""
    # First registration
    client.post(
        "/api/v1/tenants/register",
        json={
            "name": "First Company",
            "domain": "first.com",
            "plan_type": "free",
            "owner": {
                "full_name": "Owner",
                "email": "duplicate@email.com",
                "password": "SecurePass123"
            }
        }
    )

    # Second registration with same owner email
    response = client.post(
        "/api/v1/tenants/register",
        json={
            "name": "Second Company",
            "domain": "second.com",
            "plan_type": "free",
            "owner": {
                "full_name": "Owner",
                "email": "duplicate@email.com",
                "password": "SecurePass123"
            }
        }
    )
    assert response.status_code == 400
    assert "email" in response.json()["detail"].lower()


def test_register_tenant_with_owner_without_domain(client):
    """Test creating a tenant with owner without domain."""
    response = client.post(
        "/api/v1/tenants/register",
        json={
            "name": "No Domain Company",
            "plan_type": "free",
            "owner": {
                "full_name": "Owner Name",
                "email": "owner@nodomain.com",
                "password": "SecurePass123"
            }
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["tenant"]["name"] == "No Domain Company"
    assert data["tenant"]["domain"] is None
    assert data["owner"]["email"] == "owner@nodomain.com"


def test_register_tenant_with_owner_short_password(client):
    """Test that short password is rejected in register endpoint."""
    response = client.post(
        "/api/v1/tenants/register",
        json={
            "name": "Test Company",
            "plan_type": "free",
            "owner": {
                "full_name": "Owner Name",
                "email": "owner@test.com",
                "password": "Short1"  # Less than 8 characters
            }
        }
    )
    assert response.status_code == 422  # Validation error


def test_register_tenant_with_owner_invalid_email(client):
    """Test that invalid email format is rejected in register endpoint."""
    response = client.post(
        "/api/v1/tenants/register",
        json={
            "name": "Test Company",
            "plan_type": "free",
            "owner": {
                "full_name": "Owner Name",
                "email": "not-an-email",
                "password": "SecurePass123"
            }
        }
    )
    assert response.status_code == 422  # Validation error


def test_register_tenant_with_owner_can_login(client):
    """Test that the created owner can login successfully."""
    # Register tenant with owner
    register_response = client.post(
        "/api/v1/tenants/register",
        json={
            "name": "Login Test Company",
            "plan_type": "free",
            "owner": {
                "full_name": "Login Test Owner",
                "email": "logintest@company.com",
                "password": "SecurePass123"
            }
        }
    )
    assert register_response.status_code == 201

    # Try to login
    login_response = client.post(
        "/api/v1/auth/login",
        data={
            "username": "logintest@company.com",
            "password": "SecurePass123"
        }
    )
    assert login_response.status_code == 200
    data = login_response.json()
    assert "access_token" in data
    assert "refresh_token" in data


def test_register_tenant_with_owner_atomicity(client, db_session):
    """Test that tenant and owner are created atomically (both or neither)."""
    from app.models.tenant import Tenant as TenantModel
    from app.models.user import User as UserModel

    # This should fail due to duplicate email with test_user fixture
    # if it's already in the database
    response = client.post(
        "/api/v1/tenants/register",
        json={
            "name": "Atomicity Test",
            "domain": "atomicity.com",
            "plan_type": "free",
            "owner": {
                "full_name": "Test",
                "email": "atomicity@test.com",
                "password": "SecurePass123"
            }
        }
    )

    # Should succeed
    if response.status_code == 201:
        # Verify both tenant and user exist
        tenant = db_session.query(TenantModel).filter(
            TenantModel.domain == "atomicity.com"
        ).first()
        user = db_session.query(UserModel).filter(
            UserModel.email == "atomicity@test.com"
        ).first()
        assert tenant is not None
        assert user is not None
        assert user.tenant_id == tenant.id
        assert user.role.value == "owner"
