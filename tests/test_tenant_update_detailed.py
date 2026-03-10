
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
