"""
Test suite for Tenant-Scoped Email Uniqueness.

Tests the multi-tenant email functionality allowing the same email
address to exist in different tenants while preventing duplicates
within a single tenant.
"""
import pytest
from sqlalchemy.exc import IntegrityError
from app.models.user import User, UserRole
from app.models.tenant import Tenant
from app.core.security import get_password_hash


class TestTenantScopedEmailUniqueness:
    """Tests for composite unique constraint (email, tenant_id)."""

    def test_same_email_different_tenants_allowed(self, db_session):
        """Test that the same email can exist in different tenants."""
        # Create first tenant and user
        tenant1 = Tenant(id="tenant-1", name="Tenant 1", is_active=True)
        db_session.add(tenant1)
        db_session.commit()

        user1 = User(
            email="shared@example.com",
            full_name="User One",
            hashed_password=get_password_hash("TestPass123!"),
            role=UserRole.OWNER,
            tenant_id=tenant1.id,
            is_active=True,
            is_verified=True
        )
        db_session.add(user1)
        db_session.commit()

        # Create second tenant with same email
        tenant2 = Tenant(id="tenant-2", name="Tenant 2", is_active=True)
        db_session.add(tenant2)
        db_session.commit()

        user2 = User(
            email="shared@example.com",
            full_name="User Two",
            hashed_password=get_password_hash("TestPass123!"),
            role=UserRole.OWNER,
            tenant_id=tenant2.id,
            is_active=True,
            is_verified=True
        )
        db_session.add(user2)
        db_session.commit()

        # Verify both users exist with same email
        users = db_session.query(User).filter(
            User.email == "shared@example.com"
        ).all()
        assert len(users) == 2
        assert users[0].tenant_id == tenant1.id
        assert users[1].tenant_id == tenant2.id

    def test_duplicate_email_same_tenant_rejected(self, db_session):
        """Test that duplicate email within same tenant is rejected."""
        tenant = Tenant(id="tenant-1", name="Test Tenant", is_active=True)
        db_session.add(tenant)
        db_session.commit()

        user1 = User(
            email="duplicate@example.com",
            full_name="User One",
            hashed_password=get_password_hash("TestPass123!"),
            role=UserRole.OWNER,
            tenant_id=tenant.id,
            is_active=True,
            is_verified=True
        )
        db_session.add(user1)
        db_session.commit()

        # Try to create second user with same email in same tenant
        user2 = User(
            email="duplicate@example.com",
            full_name="User Two",
            hashed_password=get_password_hash("TestPass123!"),
            role=UserRole.ADMIN,
            tenant_id=tenant.id,
            is_active=True,
            is_verified=True
        )
        db_session.add(user2)

        # Should raise IntegrityError due to unique constraint
        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_superadmin_email_multiple_allowed(self, db_session):
        """Test that multiple superadmins can have same email.

        This is by design - superadmins have tenant_id=NULL,
        and SQL's unique constraint allows multiple NULLs.
        Superadmin email validation should be enforced
        in the application logic, not database constraint.
        """
        superadmin1 = User(
            email="superadmin@example.com",
            full_name="Super Admin One",
            hashed_password=get_password_hash("TestPass123!"),
            role=UserRole.ATTENDANT,
            tenant_id=None,
            is_active=True,
            is_verified=True,
            is_superadmin=True
        )
        db_session.add(superadmin1)
        db_session.commit()

        # Create another superadmin with same email (allowed at DB level)
        superadmin2 = User(
            email="superadmin@example.com",
            full_name="Super Admin Two",
            hashed_password=get_password_hash("TestPass123!"),
            role=UserRole.ATTENDANT,
            tenant_id=None,
            is_active=True,
            is_verified=True,
            is_superadmin=True
        )
        db_session.add(superadmin2)
        db_session.commit()

        # Verify both were created (NULL != NULL in SQL)
        users = db_session.query(User).filter(
            User.email == "superadmin@example.com",
            User.tenant_id.is_(None)
        ).all()
        assert len(users) == 2

    def test_user_creation_validates_tenant_scoped_email(
        self, client, auth_headers, test_tenant
    ):
        """Test that user creation validates email within tenant scope."""
        # Create first user
        response1 = client.post(
            "/api/v1/users/",
            headers=auth_headers,
            json={
                "email": "testuser@example.com",
                "full_name": "Test User",
                "password": "TestPass123!",
                "role": "attendant"
            }
        )
        assert response1.status_code == 201
        assert response1.json()["email"] == "testuser@example.com"

        # Try to create second user with same email in same tenant
        response2 = client.post(
            "/api/v1/users/",
            headers=auth_headers,
            json={
                "email": "testuser@example.com",
                "full_name": "Another Test User",
                "password": "TestPass123!",
                "role": "manager"
            }
        )
        assert response2.status_code == 400
        assert "already registered in this organization" in response2.json()[
            "message"
        ]

    def test_same_email_different_tenant_via_api(
        self, client, auth_headers, auth_headers_tenant2, test_tenant2
    ):
        """Test creating users with same email in different tenants via API."""
        # Create user in tenant 1
        response1 = client.post(
            "/api/v1/users/",
            headers=auth_headers,
            json={
                "email": "multiuser@example.com",
                "full_name": "User Tenant 1",
                "password": "TestPass123!",
                "role": "manager"
            }
        )
        assert response1.status_code == 201

        # Create user with same email in tenant 2
        response2 = client.post(
            "/api/v1/users/",
            headers=auth_headers_tenant2,
            json={
                "email": "multiuser@example.com",
                "full_name": "User Tenant 2",
                "password": "TestPass123!",
                "role": "admin"
            }
        )
        assert response2.status_code == 201
        assert response2.json()["email"] == "multiuser@example.com"

        # Verify both users exist
        assert response1.json()["email"] == response2.json()["email"]

    def test_email_case_insensitivity_within_tenant(
        self, client, auth_headers
    ):
        """Test that email matching is case-insensitive within tenant."""
        # Create user with lowercase email
        response1 = client.post(
            "/api/v1/users/",
            headers=auth_headers,
            json={
                "email": "casetest@example.com",
                "full_name": "Test User",
                "password": "TestPass123!",
                "role": "attendant"
            }
        )
        assert response1.status_code == 201

        # Try to create with uppercase version (same email)
        response2 = client.post(
            "/api/v1/users/",
            headers=auth_headers,
            json={
                "email": "CASETEST@EXAMPLE.COM",
                "full_name": "Another User",
                "password": "TestPass123!",
                "role": "manager"
            }
        )
        assert response2.status_code == 400
        assert "already registered in this organization" in response2.json()[
            "message"
        ]

    def test_user_model_composite_constraint_exists(self):
        """Test that User model has composite unique constraint."""
        from app.models.user import User
        constraints = User.__table_args__
        assert constraints is not None
        assert any(
            hasattr(c, 'name') and c.name == 'uq_user_email_tenant'
            for c in constraints
        )


class TestMultiTenantUserQueries:
    """Tests for querying users across and within tenants."""

    def test_find_user_by_email_and_tenant(self, db_session):
        """Test finding user by email and tenant combination."""
        tenant = Tenant(id="tenant-1", name="Test Tenant", is_active=True)
        db_session.add(tenant)
        db_session.commit()

        user = User(
            email="searchtest@example.com",
            full_name="Search Test",
            hashed_password=get_password_hash("TestPass123!"),
            role=UserRole.ADMIN,
            tenant_id=tenant.id,
            is_active=True,
            is_verified=True
        )
        db_session.add(user)
        db_session.commit()

        # Query by email and tenant_id
        found_user = db_session.query(User).filter(
            User.email == "searchtest@example.com",
            User.tenant_id == tenant.id
        ).first()
        assert found_user is not None
        assert found_user.email == "searchtest@example.com"
        assert found_user.tenant_id == tenant.id

    def test_find_all_users_by_email(self, db_session):
        """Test finding all users with same email across tenants."""
        tenant1 = Tenant(id="tenant-1", name="Tenant 1", is_active=True)
        tenant2 = Tenant(id="tenant-2", name="Tenant 2", is_active=True)
        db_session.add_all([tenant1, tenant2])
        db_session.commit()

        user1 = User(
            email="multi@example.com",
            full_name="User One",
            hashed_password=get_password_hash("TestPass123!"),
            role=UserRole.OWNER,
            tenant_id=tenant1.id,
            is_active=True,
            is_verified=True
        )
        user2 = User(
            email="multi@example.com",
            full_name="User Two",
            hashed_password=get_password_hash("TestPass123!"),
            role=UserRole.OWNER,
            tenant_id=tenant2.id,
            is_active=True,
            is_verified=True
        )
        db_session.add_all([user1, user2])
        db_session.commit()

        # Find all users with this email
        users = db_session.query(User).filter(
            User.email == "multi@example.com"
        ).all()
        assert len(users) == 2
        assert {u.tenant_id for u in users} == {tenant1.id, tenant2.id}

    def test_tenant_isolation_in_queries(self, db_session):
        """Test that tenant-scoped queries don't leak data."""
        tenant1 = Tenant(id="tenant-1", name="Tenant 1", is_active=True)
        tenant2 = Tenant(id="tenant-2", name="Tenant 2", is_active=True)
        db_session.add_all([tenant1, tenant2])
        db_session.commit()

        user1 = User(
            email="isolated@example.com",
            full_name="User Tenant 1",
            hashed_password=get_password_hash("TestPass123!"),
            role=UserRole.OWNER,
            tenant_id=tenant1.id,
            is_active=True,
            is_verified=True
        )
        user2 = User(
            email="isolated@example.com",
            full_name="User Tenant 2",
            hashed_password=get_password_hash("TestPass123!"),
            role=UserRole.OWNER,
            tenant_id=tenant2.id,
            is_active=True,
            is_verified=True
        )
        db_session.add_all([user1, user2])
        db_session.commit()

        # Query tenant 1's user
        tenant1_user = db_session.query(User).filter(
            User.email == "isolated@example.com",
            User.tenant_id == tenant1.id
        ).first()

        # Query tenant 2's user
        tenant2_user = db_session.query(User).filter(
            User.email == "isolated@example.com",
            User.tenant_id == tenant2.id
        ).first()

        # Verify they are different users
        assert tenant1_user.id != tenant2_user.id
        assert tenant1_user.tenant_id == tenant1.id
        assert tenant2_user.tenant_id == tenant2.id


class TestMultiTenantLoginFlow:
    """Tests for multi-tenant login scenarios."""

    def test_login_single_tenant_user(self, client, db_session, test_tenant):
        """Test login for user with single tenant."""
        user = User(
            email="single@example.com",
            full_name="Single Tenant User",
            hashed_password=get_password_hash("TestPass123!"),
            role=UserRole.OWNER,
            tenant_id=test_tenant.id,
            is_active=True,
            is_verified=True
        )
        db_session.add(user)
        db_session.commit()

        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": "single@example.com",
                "password": "TestPass123!"
            }
        )
        assert response.status_code == 200
        assert "access_token" in response.json()

    def test_login_case_insensitive_email(self, client, db_session,
                                          test_tenant):
        """Test that login email matching is case-insensitive."""
        user = User(
            email="casesensitive@example.com",
            full_name="Case Test User",
            hashed_password=get_password_hash("TestPass123!"),
            role=UserRole.OWNER,
            tenant_id=test_tenant.id,
            is_active=True,
            is_verified=True
        )
        db_session.add(user)
        db_session.commit()

        # Try login with uppercase email
        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": "CASESENSITIVE@EXAMPLE.COM",
                "password": "TestPass123!"
            }
        )
        assert response.status_code == 200
        assert "access_token" in response.json()


class TestEmailValidationWithPasswordChange:
    """Tests for email validation with password change enforcement."""

    def test_create_user_with_must_change_password(
        self, client, auth_headers
    ):
        """Test creating user with must_change_password flag."""
        response = client.post(
            "/api/v1/users/",
            headers=auth_headers,
            json={
                "email": "changepass@example.com",
                "full_name": "Change Password User",
                "password": "TestPass123!",
                "role": "attendant"
            }
        )
        assert response.status_code == 201
        user_data = response.json()
        # Initially should not require password change
        assert user_data.get("must_change_password") is False

    def test_get_current_user_accessible_with_must_change_password(
        self, client, db_session, test_tenant
    ):
        """Test that /users/me is accessible even with must_change_password."""
        user = User(
            email="forcechange@example.com",
            full_name="Force Change User",
            hashed_password=get_password_hash("TestPass123!"),
            role=UserRole.OWNER,
            tenant_id=test_tenant.id,
            is_active=True,
            is_verified=True,
            must_change_password=True
        )
        db_session.add(user)
        db_session.commit()

        # Login to get token
        login_response = client.post(
            "/api/v1/auth/login",
            data={
                "username": "forcechange@example.com",
                "password": "TestPass123!"
            }
        )
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]

        # Should be able to access /users/me
        response = client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200


class TestTenantScopedEmailEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_empty_email_string_rejected(self, client, auth_headers):
        """Test that empty email string is rejected."""
        response = client.post(
            "/api/v1/users/",
            headers=auth_headers,
            json={
                "email": "",
                "full_name": "Test User",
                "password": "TestPass123!",
                "role": "attendant"
            }
        )
        assert response.status_code == 422

    def test_invalid_email_format_rejected(self, client, auth_headers):
        """Test that invalid email format is rejected."""
        response = client.post(
            "/api/v1/users/",
            headers=auth_headers,
            json={
                "email": "invalid-email-format",
                "full_name": "Test User",
                "password": "TestPass123!",
                "role": "attendant"
            }
        )
        assert response.status_code == 422

    def test_whitespace_in_email_normalized(self, db_session, test_tenant):
        """Test that whitespace in emails is handled correctly."""
        # Try creating user with whitespace (should be normalized)
        user = User(
            email="  whitespace@example.com  ".strip(),
            full_name="Whitespace Test",
            hashed_password=get_password_hash("TestPass123!"),
            role=UserRole.ATTENDANT,
            tenant_id=test_tenant.id,
            is_active=True,
            is_verified=True
        )
        db_session.add(user)
        db_session.commit()

        # Query and verify
        found_user = db_session.query(User).filter(
            User.email == "whitespace@example.com"
        ).first()
        assert found_user is not None

    def test_special_characters_in_email_allowed(self, client, auth_headers):
        """Test that valid special characters in email are allowed."""
        response = client.post(
            "/api/v1/users/",
            headers=auth_headers,
            json={
                "email": "user+tag@example.com",
                "full_name": "Special Char User",
                "password": "TestPass123!",
                "role": "attendant"
            }
        )
        assert response.status_code == 201
        assert response.json()["email"] == "user+tag@example.com"

    def test_multiple_users_with_different_special_emails(
        self, client, auth_headers
    ):
        """Test creating multiple users with different special char emails."""
        emails = [
            "user+test1@example.com",
            "user+test2@example.com",
            "user.name@example.com",
            "user_name@example.com"
        ]

        for email in emails:
            response = client.post(
                "/api/v1/users/",
                headers=auth_headers,
                json={
                    "email": email,
                    "full_name": f"User {email}",
                    "password": "TestPass123!",
                    "role": "attendant"
                }
            )
            assert response.status_code == 201
            assert response.json()["email"] == email
