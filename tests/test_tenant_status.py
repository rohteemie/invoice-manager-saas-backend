"""
Tests for tenant status validation.
Users should be blocked when their tenant is deactivated.
"""


class TestTenantStatusValidation:
    """Tests for tenant deactivation blocking user access."""

    def test_login_blocked_for_deactivated_tenant(
        self, client, test_tenant, test_user, db_session, superadmin_auth_headers
    ):
        """Test that users cannot login when tenant is deactivated."""
        # First deactivate the tenant
        delete_response = client.delete(
            f"/api/v1/tenants/{test_tenant.id}",
            headers=superadmin_auth_headers
        )
        assert delete_response.status_code == 200

        # Try to login as the tenant user
        login_response = client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user.email,
                "password": "TestPass123!"
            }
        )
        assert login_response.status_code == 401
        # Anti-enumeration: generic message, not "deactivated"
        assert "incorrect" in login_response.json()["message"].lower()

    def test_api_access_blocked_after_tenant_deactivation(
        self, client, test_tenant, auth_headers, db_session, superadmin_auth_headers
    ):
        """Test that API access is blocked after tenant deactivation."""
        # First verify user can access API
        initial_response = client.get(
            "/api/v1/invoices/",
            headers=auth_headers
        )
        assert initial_response.status_code == 200

        # Deactivate the tenant
        delete_response = client.delete(
            f"/api/v1/tenants/{test_tenant.id}",
            headers=superadmin_auth_headers
        )
        assert delete_response.status_code == 200

        # Try to access API with existing token
        blocked_response = client.get(
            "/api/v1/invoices/",
            headers=auth_headers
        )
        assert blocked_response.status_code == 403
        assert "deactivated" in blocked_response.json()["message"].lower()

    def test_superadmin_not_blocked_by_tenant_status(
        self, client, superadmin_auth_headers
    ):
        """Test that superadmin can still access system."""
        response = client.get(
            "/api/v1/admin/stats",
            headers=superadmin_auth_headers
        )
        assert response.status_code == 200

    def test_user_access_restored_after_reactivation(
        self, client, test_tenant, test_user, db_session, superadmin_auth_headers
    ):
        """Test that users can login after tenant is reactivated."""
        # Deactivate the tenant
        delete_response = client.delete(
            f"/api/v1/tenants/{test_tenant.id}",
            headers=superadmin_auth_headers
        )
        assert delete_response.status_code == 200

        # Verify login is blocked
        blocked_login = client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user.email,
                "password": "TestPass123!"
            }
        )
        assert blocked_login.status_code == 401

        # Reactivate the tenant
        reactivate_response = client.put(
            f"/api/v1/admin/tenants/{test_tenant.id}/reactivate",
            headers=superadmin_auth_headers
        )
        assert reactivate_response.status_code == 200

        # Now login should work
        login_response = client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user.email,
                "password": "TestPass123!"
            }
        )
        assert login_response.status_code == 200
        assert "access_token" in login_response.json()
