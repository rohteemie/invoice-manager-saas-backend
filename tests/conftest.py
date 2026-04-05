
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

# --- Superadmin fixtures (must be after imports) ---


@pytest.fixture
def test_superadmin(db_session):
    """
    Create a test superadmin user.
    """
    from app.models.user import UserRole
    user = User(
        email="superadmin@testcompany.com",
        full_name="Test Superadmin",
        hashed_password=get_password_hash("TestPass123!"),
        role=UserRole.ATTENDANT,
        tenant_id=None,
        is_active=True,
        is_verified=True,
        is_superadmin=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def superadmin_auth_headers(client, test_superadmin):
    """
    Get authentication headers for superadmin user.
    """
    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": "superadmin@testcompany.com",
            "password": "TestPass123!"
        }
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="session", autouse=True)
def cleanup_test_db():
    """Remove test database file before test session starts."""
    test_db_path = "./test.db"
    if os.path.exists(test_db_path):
        os.remove(test_db_path)
    yield
    # Cleanup after all tests complete
    if os.path.exists(test_db_path):
        os.remove(test_db_path)


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
    # Ensure any existing connections are closed and transactions rolled back
    engine.dispose()

    # Drop all tables first to ensure clean state (checkfirst to avoid errors)
    Base.metadata.drop_all(bind=engine, checkfirst=True)
    # Create all tables
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        # Explicitly rollback any pending transactions
        db.rollback()
        db.close()
        # Dispose of connection pool to ensure all connections are closed
        engine.dispose()
        # Drop all tables to ensure clean state for next test
        Base.metadata.drop_all(bind=engine, checkfirst=True)


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
        hashed_password=get_password_hash("TestPass123!"),
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
def auth_headers(client, test_user):
    """
    Get authentication headers for test user.
    """
    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": "owner@testcompany.com",
            "password": "TestPass123!"
        }
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def test_admin(db_session, test_tenant):
    """
    Create a test admin user.
    """
    user = User(
        email="admin@testcompany.com",
        full_name="Test Admin",
        hashed_password=get_password_hash("TestPass123!"),
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
        hashed_password=get_password_hash("TestPass123!"),
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
        hashed_password=get_password_hash("TestPass123!"),
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
        hashed_password=get_password_hash("TestPass123!"),
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
        hashed_password=get_password_hash("TestPass123!"),
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
def admin_auth_headers(client, test_admin):
    """
    Get authentication headers for admin user.
    """
    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": "admin@testcompany.com",
            "password": "TestPass123!"
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
            "password": "TestPass123!"
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
            "password": "TestPass123!"
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
            "password": "TestPass123!"
        }
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def test_tenant2(db_session):
    """
    Create a second test tenant for multi-tenant tests.
    """
    tenant = Tenant(
        name="Test Company 2",
        domain="testcompany2.com",
        plan_type="Standard",
        description="A second test company"
    )
    db_session.add(tenant)
    db_session.commit()
    db_session.refresh(tenant)
    return tenant


@pytest.fixture
def test_tenant2_owner(db_session, test_tenant2):
    """
    Create an owner user for test_tenant2.
    """
    user = User(
        email="owner2@testcompany2.com",
        full_name="Test Owner 2",
        hashed_password=get_password_hash("TestPass123!"),
        role=UserRole.OWNER,
        tenant_id=test_tenant2.id,
        is_active=True,
        is_verified=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def auth_headers_tenant2(client, test_tenant2_owner):
    """
    Get authentication headers for test_tenant2 owner.
    """
    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": "owner2@testcompany2.com",
            "password": "TestPass123!"
        }
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
