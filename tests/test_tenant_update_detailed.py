
def test_owner_update_all_fields(client, test_tenant, auth_headers):
    """Test that a tenant owner can update all allowed fields (except currency)."""
    # Note: default_currency can only be changed by superadmin
    update_json = {
        "name": "New Name",
        "domain": "new-domain.com",
        "business_registration_number": "BRN-123456",
        "description": "New Description",
        "tax_rate": 7.5,
        "tax_label": "GST",
        "address": "456 Street",
        "phone": "123456789",
        "email": "contact@new-domain.com",
        "invoice_number_prefix": "TST",
        "invoice_number_format": "{prefix}-{sequence}",
        "primary_color": "#ff0000",
        "secondary_color": "#00ff00",
        "custom_footer": "New Footer",
        "draft_watermark_enabled": False
    }

    response = client.put(
        f"/api/v1/tenants/{test_tenant.id}",
        json=update_json,
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    for key, value in update_json.items():
        if key == "tax_rate":
            assert float(data[key]) == value
        else:
            assert data[key] == value


def test_owner_cannot_change_currency(client, test_tenant, auth_headers):
    """Test that owner cannot change default_currency (superadmin only)."""
    response = client.put(
        f"/api/v1/tenants/{test_tenant.id}",
        json={"default_currency": "USD"},
        headers=auth_headers
    )
    assert response.status_code == 403
    assert "currency" in response.json()["message"].lower()


def test_update_tenant_with_unset_fields(client, test_tenant, auth_headers):
    """Test that unset fields are not updated."""
    original_name = test_tenant.name

    response = client.put(
        f"/api/v1/tenants/{test_tenant.id}",
        json={"description": "Just updating description"},
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["description"] == "Just updating description"
    assert data["name"] == original_name


def test_owner_can_update_plan_type_if_same(client, test_tenant, auth_headers):
    """Test if owner is allowed if sending the current plan_type."""
    current_plan = test_tenant.plan_type

    response = client.put(
        f"/api/v1/tenants/{test_tenant.id}",
        json={"plan_type": current_plan},
        headers=auth_headers
    )

    # New implementation allows if matches current value
    assert response.status_code == 200


def test_co_owner_can_update_same_tenant(
    client,
    test_tenant,
    db_session
):
    """Test that a co-owner in the same tenant can update tenant fields."""
    from app.models.user import User, UserRole
    from app.core.security import get_password_hash

    co_owner = User(
        email="co-owner@testcompany.com",
        full_name="Co Owner",
        hashed_password=get_password_hash("TestPass123!"),
        role=UserRole.OWNER,
        tenant_id=test_tenant.id,
        is_active=True,
        is_verified=True
    )
    db_session.add(co_owner)
    db_session.commit()

    login_response = client.post(
        "/api/v1/auth/login",
        data={
            "username": "co-owner@testcompany.com",
            "password": "TestPass123!"
        }
    )
    assert login_response.status_code == 200
    login_data = login_response.json()
    assert "access_token" in login_data
    token = login_data["access_token"]

    response = client.put(
        f"/api/v1/tenants/{test_tenant.id}",
        json={"description": "Updated by co-owner"},
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    assert response.json()["description"] == "Updated by co-owner"


def test_owner_cannot_update_other_tenant(
    client,
    test_tenant,
    second_tenant,
    second_tenant_auth_headers
):
    """Test tenant isolation: owner cannot update another tenant."""
    response = client.put(
        f"/api/v1/tenants/{test_tenant.id}",
        json={"description": "Cross-tenant update attempt"},
        headers=second_tenant_auth_headers
    )

    assert response.status_code == 403
    assert "permission" in response.json()["message"].lower()
