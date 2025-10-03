# Test Suite Documentation

This directory contains comprehensive tests for the Multi-Tenant SaaS Backend, focusing on authentication, user management, tenant operations, and tenant isolation.

## Table of Contents

- [Overview](#overview)
- [Test Structure](#test-structure)
- [Running Tests](#running-tests)
- [Test Coverage](#test-coverage)
- [Test Files](#test-files)
- [Fixtures](#fixtures)
- [Testing Best Practices](#testing-best-practices)

## Overview

The test suite validates the following core functionalities:

1. **Authentication & Authorization**: JWT-based authentication, token management, role-based access control (RBAC)
2. **User Management**: CRUD operations, role hierarchy, soft deletion (GDPR compliance)
3. **Tenant Management**: Tenant CRUD operations, domain uniqueness, soft deletion
4. **Tenant Isolation**: Cross-tenant access prevention, data isolation verification

## Test Structure

```
tests/
├── conftest.py                    # Test configuration and fixtures
├── test_auth.py                   # Authentication tests
├── test_users.py                  # User management tests
├── test_tenants.py                # Tenant CRUD tests
├── test_tenant_isolation.py       # Tenant isolation tests
└── README.md                      # This file
```

## Running Tests

### Prerequisites

1. Install test dependencies:
```bash
pip install -r requirements.txt
```

2. Ensure you have a test environment set up (tests use SQLite in-memory database)

### Run All Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run with coverage report
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_auth.py

# Run specific test
pytest tests/test_auth.py::test_login_success
```

### Run Tests by Category

```bash
# Authentication tests
pytest tests/test_auth.py -v

# User management tests
pytest tests/test_users.py -v

# Tenant tests
pytest tests/test_tenants.py -v

# Tenant isolation tests
pytest tests/test_tenant_isolation.py -v
```

## Test Coverage

### Authentication Tests (`test_auth.py`)

- ✅ User registration with validation
- ✅ Duplicate email detection
- ✅ Email format validation
- ✅ Password length validation
- ✅ Password hashing verification
- ✅ Successful login
- ✅ Login with incorrect credentials
- ✅ Login with non-existent user
- ✅ Inactive user blocking
- ✅ Token generation and structure
- ✅ Token refresh flow
- ✅ Invalid token handling
- ✅ Token expiration inclusion
- ✅ Different users get different tokens

**Total**: 17+ test cases

### User Management Tests (`test_users.py`)

- ✅ Get current user info
- ✅ Unauthorized access prevention
- ✅ Invalid token rejection
- ✅ List users (with role checks)
- ✅ Pagination support
- ✅ Get user by ID
- ✅ Update user information
- ✅ Update verification status
- ✅ Soft delete users (GDPR compliance)
- ✅ Self-deletion prevention
- ✅ Role hierarchy validation
  - Owner: Full access
  - Admin: Manage users (except delete)
  - Manager: Read-only self
  - Attendant: Read-only self
- ✅ Inactive user access prevention

**Total**: 30+ test cases

### Tenant Tests (`test_tenants.py`)

- ✅ Create tenant
- ✅ Duplicate domain detection
- ✅ Create tenant without domain
- ✅ List all tenants
- ✅ Pagination support
- ✅ Get tenant by ID
- ✅ Update tenant information
- ✅ Update tenant domain
- ✅ Prevent duplicate domain on update
- ✅ Soft delete tenant
- ✅ Validation for name length (min/max)
- ✅ Not found error handling

**Total**: 15+ test cases

### Tenant Isolation Tests (`test_tenant_isolation.py`)

- ✅ Users only see their tenant's users
- ✅ Cannot access other tenant's users by ID
- ✅ Cannot update other tenant's users
- ✅ Cannot delete other tenant's users
- ✅ Bidirectional isolation verification
- ✅ JWT tokens contain correct tenant_id
- ✅ User list filtered by tenant
- ✅ Cross-tenant access via auth token prevented
- ✅ Global unique email constraint
- ✅ Deactivated users don't affect other tenants
- ✅ Registration enforces tenant_id
- ✅ Comprehensive admin isolation test

**Total**: 14+ test cases

## Test Files

### `conftest.py`

Contains all test fixtures and configuration:

**Database Fixtures**:
- `db_session`: Fresh database session for each test
- `client`: Test client with database override

**Tenant Fixtures**:
- `test_tenant`: Primary test tenant
- `second_tenant`: Secondary tenant for isolation tests

**User Fixtures**:
- `test_user`: Owner role user
- `test_admin`: Admin role user
- `test_manager`: Manager role user
- `test_attendant`: Attendant role user
- `second_tenant_user`: User in second tenant
- `inactive_user`: Deactivated user

**Auth Fixtures**:
- `auth_headers`: Authentication headers for owner
- `admin_auth_headers`: Authentication headers for admin
- `manager_auth_headers`: Authentication headers for manager
- `attendant_auth_headers`: Authentication headers for attendant
- `second_tenant_auth_headers`: Authentication headers for second tenant user

### `test_auth.py`

Tests authentication endpoints (`/api/v1/auth/*`):

**Key Test Scenarios**:
- Registration validation and security
- Login authentication flow
- Token generation and structure
- Token refresh mechanism
- Password hashing verification
- Inactive user handling

**Security Validations**:
- Passwords are never returned in responses
- Passwords are properly hashed with bcrypt
- Tokens contain user ID, tenant ID, and role
- Tokens have expiration timestamps
- Invalid credentials are rejected

### `test_users.py`

Tests user management endpoints (`/api/v1/users/*`):

**Key Test Scenarios**:
- Current user retrieval
- User listing with pagination
- User retrieval by ID
- User updates
- Soft deletion (GDPR compliance)

**RBAC Validations**:
- Owner can perform all operations
- Admin can list, get, and update users
- Admin cannot delete users
- Manager cannot access user management
- Attendant cannot access user management
- Users cannot delete themselves

### `test_tenants.py`

Tests tenant management endpoints (`/api/v1/tenants/*`):

**Key Test Scenarios**:
- Tenant creation with validation
- Domain uniqueness enforcement
- Tenant listing with pagination
- Tenant updates
- Soft deletion

**Validation Tests**:
- Name length constraints
- Domain uniqueness on create and update
- Optional domain handling
- Not found error handling

### `test_tenant_isolation.py`

Tests data isolation between tenants:

**Key Test Scenarios**:
- Cross-tenant user visibility
- Cross-tenant user access by ID
- Cross-tenant user modification prevention
- Token tenant_id verification
- Bidirectional isolation
- Deactivated user isolation

**Security Validations**:
- Users can only see their tenant's data
- Authentication doesn't bypass tenant isolation
- User lists are filtered by tenant
- All operations respect tenant boundaries

## Fixtures

### Database Fixtures

#### `db_session`
- **Scope**: Function (new for each test)
- **Purpose**: Provides isolated database session
- **Features**: Automatic rollback, clean state per test

#### `client`
- **Scope**: Function
- **Purpose**: FastAPI TestClient with database override
- **Usage**: For making HTTP requests in tests

### User Role Fixtures

The test suite provides pre-configured users for each role:

| Fixture | Role | Email | Use Case |
|---------|------|-------|----------|
| `test_user` | Owner | owner@testcompany.com | Full permissions testing |
| `test_admin` | Admin | admin@testcompany.com | Admin permission testing |
| `test_manager` | Manager | manager@testcompany.com | Limited permission testing |
| `test_attendant` | Attendant | attendant@testcompany.com | Minimal permission testing |
| `second_tenant_user` | Owner | owner@secondcompany.com | Isolation testing |
| `inactive_user` | Attendant | inactive@testcompany.com | Inactive user testing |

### Authentication Fixtures

Authentication header fixtures automatically:
1. Create the user if not exists
2. Perform login
3. Extract access token
4. Return properly formatted Authorization header

Example usage:
```python
def test_example(client, auth_headers):
    response = client.get("/api/v1/users/me", headers=auth_headers)
    assert response.status_code == 200
```

## Testing Best Practices

### Isolation

Each test is completely isolated:
- Fresh database for each test
- No shared state between tests
- Automatic cleanup after each test

### Naming Convention

Tests follow descriptive naming:
```python
def test_[action]_[scenario]_[expected_result]
```

Examples:
- `test_login_success`
- `test_login_incorrect_password`
- `test_list_users_as_manager_forbidden`

### Assertions

Tests use clear, descriptive assertions:
```python
# Good
assert response.status_code == 200
assert "email" in data
assert data["role"] == "owner"

# Check error messages
assert "not found" in response.json()["detail"].lower()
```

### Test Organization

Tests are organized by:
1. **Feature**: Each file tests a specific feature area
2. **Scenario**: Related tests are grouped together
3. **Complexity**: Simple cases before edge cases

### Common Patterns

#### Testing Protected Endpoints
```python
def test_protected_endpoint(client, auth_headers):
    response = client.get("/api/v1/users/me", headers=auth_headers)
    assert response.status_code == 200
```

#### Testing Role-Based Access
```python
def test_admin_required(client, manager_auth_headers):
    response = client.get("/api/v1/users/", headers=manager_auth_headers)
    assert response.status_code == 403
```

#### Testing Tenant Isolation
```python
def test_cross_tenant_access(client, auth_headers, second_tenant_user):
    response = client.get(
        f"/api/v1/users/{second_tenant_user.id}",
        headers=auth_headers
    )
    assert response.status_code == 404
```

## Expected Test Output

When all tests pass, you should see:

```
tests/test_auth.py ..................                    [ 21%]
tests/test_tenants.py ...............                    [ 40%]
tests/test_tenant_isolation.py ..............            [ 58%]
tests/test_users.py ..............................        [100%]

======================== 76 passed in 2.45s ========================
```

## Troubleshooting

### Database Issues

If you see database errors:
1. Ensure test database is clean: `rm -f test.db`
2. Check SQLAlchemy models are imported correctly
3. Verify database initialization in `conftest.py`

### Import Errors

If you see import errors:
1. Ensure you're running from project root
2. Check PYTHONPATH includes project directory
3. Verify all dependencies are installed

### Fixture Errors

If fixtures are not found:
1. Ensure `conftest.py` is in the tests directory
2. Check fixture naming matches usage
3. Verify pytest discovers the conftest file

## Contributing

When adding new tests:

1. **Follow naming conventions**: Descriptive test names
2. **Use existing fixtures**: Don't duplicate fixture logic
3. **Test one thing**: Each test should validate one scenario
4. **Document complex tests**: Add docstrings for clarity
5. **Maintain isolation**: Don't rely on test execution order

## Next Steps

Future test enhancements:

- [ ] Performance tests (response times)
- [ ] Load testing for concurrent users
- [ ] Email verification flow tests
- [ ] Password reset flow tests
- [ ] API rate limiting tests
- [ ] Integration tests with real database
- [ ] End-to-end workflow tests

---

**Last Updated**: Phase 1 - Authentication & Tenant Isolation
**Test Framework**: pytest 7.4.3
**Coverage Target**: >80% code coverage
