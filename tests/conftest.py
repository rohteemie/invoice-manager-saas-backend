"""
Test configuration and fixtures.
Provides database setup, test client, and common fixtures for all tests.
"""
import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.db.session import get_db
from app.models.general_model import Base
from app.models.tenant import Tenant
from app.models.user import User, UserRole
from app.core.security import get_password_hash

# Use in-memory SQLite for testing
TEST_DATABASE_URL = "sqlite:///./test.db"

# Ensure application modules pick up test DATABASE_URL before they are imported
os.environ["DATABASE_URL"] = TEST_DATABASE_URL
os.environ["TESTING"] = "1"


# Create engine bound to same TEST_DATABASE_URL used by app settings
engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


@pytest.fixture(scope="function", autouse=True)
def disable_rate_limit():
    """Disable rate limiting for tests."""
    from app.core.rate_limit import limiter
    limiter.enabled = False
    yield
    limiter.enabled = True


@pytest.fixture(scope="function")
def db_session():
    """
    Create a fresh database session for each test.
    Rolls back after each test to maintain isolation.
    """
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """
    Create a test client with database dependency override.
    """
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def test_tenant(db_session):
    """
    Create a test tenant for use in tests.
    """
    tenant = Tenant(
        name="Test Company",
        domain="testcompany.com",
        plan_type="Standard",
        description="A test company"
    )
    db_session.add(tenant)
    db_session.commit()
    db_session.refresh(tenant)
    return tenant


@pytest.fixture
def second_tenant(db_session):
    """
    Create a second test tenant for tenant isolation tests.
    """
    tenant = Tenant(
        name="Second Company",
        domain="secondcompany.com",
        plan_type="Standard",
        description="A second test company"
    )
    db_session.add(tenant)
    db_session.commit()
    db_session.refresh(tenant)
    return tenant


@pytest.fixture
def test_user(db_session, test_tenant):
    """
    Create a test user with owner role.
    """
    user = User(
        email="owner@testcompany.com",
        full_name="Test Owner",
        hashed_password=get_password_hash("TestPassword123"),
        role=UserRole.OWNER,
        tenant_id=test_tenant.id,
        is_active=True,
        is_verified=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_admin(db_session, test_tenant):
    """
    Create a test admin user.
    """
    user = User(
        email="admin@testcompany.com",
        full_name="Test Admin",
        hashed_password=get_password_hash("TestPassword123"),
        role=UserRole.ADMIN,
        tenant_id=test_tenant.id,
        is_active=True,
        is_verified=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_manager(db_session, test_tenant):
    """
    Create a test manager user.
    """
    user = User(
        email="manager@testcompany.com",
        full_name="Test Manager",
        hashed_password=get_password_hash("TestPassword123"),
        role=UserRole.MANAGER,
        tenant_id=test_tenant.id,
        is_active=True,
        is_verified=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_attendant(db_session, test_tenant):
    """
    Create a test attendant user.
    """
    user = User(
        email="attendant@testcompany.com",
        full_name="Test Attendant",
        hashed_password=get_password_hash("TestPassword123"),
        role=UserRole.ATTENDANT,
        tenant_id=test_tenant.id,
        is_active=True,
        is_verified=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def second_tenant_user(db_session, second_tenant):
    """
    Create a user in the second tenant for isolation tests.
    """
    user = User(
        email="owner@secondcompany.com",
        full_name="Second Owner",
        hashed_password=get_password_hash("TestPassword123"),
        role=UserRole.OWNER,
        tenant_id=second_tenant.id,
        is_active=True,
        is_verified=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def inactive_user(db_session, test_tenant):
    """
    Create an inactive test user.
    """
    user = User(
        email="inactive@testcompany.com",
        full_name="Inactive User",
        hashed_password=get_password_hash("TestPassword123"),
        role=UserRole.ATTENDANT,
        tenant_id=test_tenant.id,
        is_active=False,
        is_verified=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def auth_headers(client, test_user):
    """
    Get authentication headers for test user.
    """
    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": "owner@testcompany.com",
            "password": "TestPassword123"
        }
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_auth_headers(client, test_admin):
    """
    Get authentication headers for admin user.
    """
    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": "admin@testcompany.com",
            "password": "TestPassword123"
        }
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def manager_auth_headers(client, test_manager):
    """
    Get authentication headers for manager user.
    """
    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": "manager@testcompany.com",
            "password": "TestPassword123"
        }
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def attendant_auth_headers(client, test_attendant):
    """
    Get authentication headers for attendant user.
    """
    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": "attendant@testcompany.com",
            "password": "TestPassword123"
        }
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def second_tenant_auth_headers(client, second_tenant_user):
    """
    Get authentication headers for second tenant user.
    """
    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": "owner@secondcompany.com",
            "password": "TestPassword123"
        }
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
