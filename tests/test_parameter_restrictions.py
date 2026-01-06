"""
Tests for parameter restriction enforcement:
- Business registration number uniqueness
- Domain uniqueness 
- Plan type restriction to super admins
- Invoice currency enforcement from tenant settings
- Invoice tax enforcement from tenant settings
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models.tenant import Tenant as TenantModel
from app.models.user import User as UserModel, UserRole
from app.models.invoice import Invoice as InvoiceModel
from app.core.security import get_password_hash


@pytest.fixture
def superadmin_user(db_session):
    """Create a super admin user for testing."""
    superadmin = UserModel(
        email="superadmin@platform.com",
        full_name="Super Admin",
        hashed_password=get_password_hash("superadmin123"),
        role=UserRole.ATTENDANT,  # Role doesn't matter for superadmin
        tenant_id=None,  # Superadmins don't belong to any tenant
        is_superadmin=True,
        is_verified=True
    )
    db_session.add(superadmin)
    db_session.commit()
    db_session.refresh(superadmin)
    return superadmin


@pytest.fixture
def superadmin_token_headers(client, superadmin_user):
    """Get auth headers for super admin."""
    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": "superadmin@platform.com",
            "password": "superadmin123"
        }
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def test_invoice(db_session, test_tenant, test_user):
    """Create a test invoice."""
    from app.models.invoice import Invoice, InvoiceItem, InvoiceStatus, Currency
    
    invoice = Invoice(
        invoice_number="INV-001",
        tenant_id=test_tenant.id,
        creator_id=test_user.id,
        customer_name="Test Customer",
        status=InvoiceStatus.DRAFT,
        currency=Currency.NGN,
        issue_date="2024-01-01",
        subtotal=100.00,
        tax_amount=0.00,
        discount_amount=0.00,
        total_amount=100.00
    )
    db_session.add(invoice)
    db_session.commit()
    db_session.refresh(invoice)
    return invoice


def test_tenant_creation_requires_domain_or_business_number(
    client: TestClient,
    db_session: Session
):
    """Test that tenant creation requires at least one unique identifier."""
    # Try to create tenant without domain or business registration number
    tenant_data = {
        "name": "Test Company",
        "description": "Test description",
        "default_currency": "USD"
    }
    
    response = client.post("/api/v1/tenants/", json=tenant_data)
    assert response.status_code == 400
    response_data = response.json()
    # Check using standardized error format
    assert "domain or business_registration_number must be provided" in response_data.get("message", "").lower()


def test_tenant_creation_with_domain_only(
    client: TestClient,
    db_session: Session
):
    """Test that tenant can be created with domain only."""
    tenant_data = {
        "name": "Test Company",
        "domain": "testcompany.com",
        "description": "Test description",
        "default_currency": "USD"
    }
    
    response = client.post("/api/v1/tenants/", json=tenant_data)
    assert response.status_code == 201
    assert response.json()["domain"] == "testcompany.com"
    assert response.json()["business_registration_number"] is None


def test_tenant_creation_with_business_number_only(
    client: TestClient,
    db_session: Session
):
    """Test that tenant can be created with business registration number only."""
    tenant_data = {
        "name": "Test Company",
        "business_registration_number": "BRN123456",
        "description": "Test description",
        "default_currency": "USD"
    }
    
    response = client.post("/api/v1/tenants/", json=tenant_data)
    assert response.status_code == 201
    assert response.json()["business_registration_number"] == "BRN123456"
    assert response.json()["domain"] is None


def test_tenant_domain_uniqueness(
    client: TestClient,
    db_session: Session
):
    """Test that domain must be unique across tenants."""
    # Create first tenant
    tenant_data1 = {
        "name": "Company 1",
        "domain": "company.com",
        "default_currency": "USD"
    }
    response1 = client.post("/api/v1/tenants/", json=tenant_data1)
    assert response1.status_code == 201
    
    # Try to create second tenant with same domain
    tenant_data2 = {
        "name": "Company 2",
        "domain": "company.com",
        "default_currency": "USD"
    }
    response2 = client.post("/api/v1/tenants/", json=tenant_data2)
    assert response2.status_code == 400
    response_data = response2.json()
    assert "domain already exists" in response_data.get("message", "").lower()


def test_tenant_business_number_uniqueness(
    client: TestClient,
    db_session: Session
):
    """Test that business registration number must be unique across tenants."""
    # Create first tenant
    tenant_data1 = {
        "name": "Company 1",
        "business_registration_number": "BRN12345",
        "default_currency": "USD"
    }
    response1 = client.post("/api/v1/tenants/", json=tenant_data1)
    assert response1.status_code == 201
    
    # Try to create second tenant with same business registration number
    tenant_data2 = {
        "name": "Company 2",
        "business_registration_number": "BRN12345",
        "default_currency": "USD"
    }
    response2 = client.post("/api/v1/tenants/", json=tenant_data2)
    assert response2.status_code == 400
    response_data = response2.json()
    assert "business registration number already exists" in response_data.get("message", "").lower()


def test_tenant_register_requires_domain_or_business_number(
    client: TestClient,
    db_session: Session
):
    """Test that tenant registration requires at least one unique identifier."""
    registration_data = {
        "name": "Test Company",
        "description": "Test",
        "default_currency": "USD",
        "owner": {
            "full_name": "John Doe",
            "email": "john@example.com",
            "password": "SecurePass123"
        }
    }
    
    response = client.post("/api/v1/tenants/register", json=registration_data)
    assert response.status_code == 400
    response_data = response.json()
    assert "domain or business_registration_number must be provided" in response_data.get("message", "").lower()


def test_default_plan_type_is_standard(
    client: TestClient,
    db_session: Session
):
    """Test that new tenants default to 'Standard' plan type."""
    tenant_data = {
        "name": "Test Company",
        "domain": "testplan.com",
        "default_currency": "USD"
    }
    
    response = client.post("/api/v1/tenants/", json=tenant_data)
    assert response.status_code == 201
    assert response.json()["plan_type"] == "Standard"


def test_regular_user_cannot_update_plan_type(
    client: TestClient,
    db_session: Session,
    test_tenant: TenantModel,
    test_user: UserModel,
    auth_headers: dict
):
    """Test that regular users cannot update plan_type."""
    update_data = {
        "plan_type": "Premium"
    }
    
    response = client.put(
        f"/api/v1/tenants/{test_tenant.id}",
        json=update_data,
        headers=auth_headers
    )
    
    # The update should succeed but plan_type should not be changed
    # because plan_type is not in TenantUpdate schema
    assert response.status_code == 200
    # Plan type should remain unchanged
    assert response.json()["plan_type"] == test_tenant.plan_type


def test_superadmin_can_update_plan_type(
    client: TestClient,
    db_session: Session,
    test_tenant: TenantModel,
    superadmin_token_headers: dict
):
    """Test that super admins can update plan_type."""
    update_data = {
        "plan_type": "Premium"
    }
    
    response = client.put(
        f"/api/v1/admin/tenants/{test_tenant.id}",
        json=update_data,
        headers=superadmin_token_headers
    )
    
    assert response.status_code == 200
    assert response.json()["plan_type"] == "Premium"


def test_invoice_currency_always_from_tenant(
    client: TestClient,
    db_session: Session,
    test_tenant: TenantModel,
    auth_headers: dict
):
    """Test that invoice currency is always taken from tenant settings."""
    # Set tenant default currency to EUR
    test_tenant.default_currency = "EUR"
    db_session.commit()
    
    # Try to create invoice - currency should not be in the request
    invoice_data = {
        "customer_name": "Test Customer",
        "issue_date": "2024-01-01",
        "items": [
            {
                "description": "Item 1",
                "quantity": 1,
                "unit_price": 100.00
            }
        ]
    }
    
    response = client.post(
        "/api/v1/invoices/",
        json=invoice_data,
        headers=auth_headers
    )
    
    assert response.status_code == 201
    # Currency should be EUR from tenant
    assert response.json()["currency"] == "EUR"


def test_invoice_tax_always_from_tenant(
    client: TestClient,
    db_session: Session,
    test_tenant: TenantModel,
    auth_headers: dict
):
    """Test that invoice tax is always calculated from tenant tax_rate."""
    # Set tenant tax rate to 10%
    test_tenant.tax_rate = 10.0
    db_session.commit()
    
    # Create invoice with subtotal of 100
    invoice_data = {
        "customer_name": "Test Customer",
        "issue_date": "2024-01-01",
        "items": [
            {
                "description": "Item 1",
                "quantity": 1,
                "unit_price": 100.00
            }
        ]
    }
    
    response = client.post(
        "/api/v1/invoices/",
        json=invoice_data,
        headers=auth_headers
    )
    
    assert response.status_code == 201
    # Tax amount should be 10.00 (10% of 100)
    assert float(response.json()["subtotal"]) == 100.00
    assert float(response.json()["tax_amount"]) == 10.00
    assert float(response.json()["total_amount"]) == 110.00


def test_invoice_update_preserves_tenant_currency(
    client: TestClient,
    db_session: Session,
    test_tenant: TenantModel,
    test_invoice: InvoiceModel,
    manager_auth_headers: dict
):
    """Test that updating invoice preserves tenant currency."""
    # Ensure invoice uses tenant currency
    assert test_invoice.currency.value == test_tenant.default_currency
    
    # Update invoice
    update_data = {
        "customer_name": "Updated Customer"
    }
    
    response = client.put(
        f"/api/v1/invoices/{test_invoice.id}",
        json=update_data,
        headers=manager_auth_headers
    )
    
    assert response.status_code == 200
    # Currency should remain the same
    assert response.json()["currency"] == test_tenant.default_currency


def test_invoice_update_recalculates_tax_from_tenant(
    client: TestClient,
    db_session: Session,
    test_tenant: TenantModel,
    test_invoice: InvoiceModel,
    manager_auth_headers: dict
):
    """Test that updating invoice items recalculates tax from tenant rate."""
    # Set tenant tax rate to 15%
    test_tenant.tax_rate = 15.0
    db_session.commit()
    
    # Update invoice with new items
    update_data = {
        "items": [
            {
                "description": "New Item",
                "quantity": 2,
                "unit_price": 50.00
            }
        ]
    }
    
    response = client.put(
        f"/api/v1/invoices/{test_invoice.id}",
        json=update_data,
        headers=manager_auth_headers
    )
    
    assert response.status_code == 200
    # Subtotal should be 100 (2 * 50)
    # Tax should be 15 (15% of 100)
    # Total should be 115
    assert float(response.json()["subtotal"]) == 100.00
    assert float(response.json()["tax_amount"]) == 15.00
    assert float(response.json()["total_amount"]) == 115.00


def test_superadmin_can_update_tenant_domain_uniqueness(
    client: TestClient,
    db_session: Session,
    superadmin_token_headers: dict
):
    """Test that super admin domain update respects uniqueness constraint."""
    # Create two tenants
    tenant1_data = {
        "name": "Company 1",
        "domain": "company1.com",
        "default_currency": "USD"
    }
    tenant2_data = {
        "name": "Company 2",
        "domain": "company2.com",
        "default_currency": "USD"
    }
    
    response1 = client.post("/api/v1/tenants/", json=tenant1_data)
    response2 = client.post("/api/v1/tenants/", json=tenant2_data)
    
    tenant1_id = response1.json()["id"]
    tenant2_id = response2.json()["id"]
    
    # Try to update tenant2 with tenant1's domain
    update_data = {
        "domain": "company1.com"
    }
    
    response = client.put(
        f"/api/v1/admin/tenants/{tenant2_id}",
        json=update_data,
        headers=superadmin_token_headers
    )
    
    assert response.status_code == 400
    response_data = response.json()
    assert "domain already exists" in response_data.get("message", "").lower()


def test_superadmin_can_update_tenant_business_number_uniqueness(
    client: TestClient,
    db_session: Session,
    superadmin_token_headers: dict
):
    """Test that super admin business number update respects uniqueness constraint."""
    # Create two tenants
    tenant1_data = {
        "name": "Company 1",
        "business_registration_number": "BRN111",
        "default_currency": "USD"
    }
    tenant2_data = {
        "name": "Company 2",
        "business_registration_number": "BRN222",
        "default_currency": "USD"
    }
    
    response1 = client.post("/api/v1/tenants/", json=tenant1_data)
    response2 = client.post("/api/v1/tenants/", json=tenant2_data)
    
    tenant1_id = response1.json()["id"]
    tenant2_id = response2.json()["id"]
    
    # Try to update tenant2 with tenant1's business registration number
    update_data = {
        "business_registration_number": "BRN111"
    }
    
    response = client.put(
        f"/api/v1/admin/tenants/{tenant2_id}",
        json=update_data,
        headers=superadmin_token_headers
    )
    
    assert response.status_code == 400
    response_data = response.json()
    assert "business registration number already exists" in response_data.get("message", "").lower()
