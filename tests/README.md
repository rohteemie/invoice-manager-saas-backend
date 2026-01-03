# Test Suite Documentation

This directory contains comprehensive tests for the Multi-Tenant SaaS Backend, covering all aspects of the application from authentication to invoice management, analytics, and platform administration.

## Table of Contents

- [Overview](#overview)
- [Test Structure](#test-structure)
- [Running Tests](#running-tests)
- [Test Coverage](#test-coverage)
- [Test Files](#test-files)
- [Fixtures](#fixtures)
- [Testing Best Practices](#testing-best-practices)

## Overview

The test suite validates all core functionalities across 28 test files:

1. **Authentication & Authorization**: JWT-based authentication, email verification, password reset, login throttling
2. **User Management**: CRUD operations, role hierarchy, soft deletion (GDPR compliance)
3. **Tenant Management**: Tenant CRUD operations, branding with logos, domain uniqueness, suspension/reactivation
4. **Tenant Isolation**: Cross-tenant access prevention, data isolation verification
5. **Invoice Management**: Invoice CRUD, multi-currency support, tax calculations, PDF generation, email sending, status lifecycle
6. **Analytics & Reporting**: Invoice summaries, revenue breakdowns
7. **Audit Logging**: Comprehensive activity tracking and querying
8. **Super Admin**: Platform-level administration and cross-tenant operations
9. **Performance & Reliability**: Caching, background tasks, rate limiting, monitoring
10. **Security**: CORS, error standardization, permission checks, authentication throttling
11. **Integration Workflows**: End-to-end business processes, cross-module integration

## Test Structure

```bash
tests/
├── conftest.py                           # Test configuration and fixtures
├── test_auth.py                          # Authentication tests
├── test_auth_throttle.py                 # Authentication throttling tests
├── test_users.py                         # User management tests
├── test_tenants.py                       # Tenant CRUD tests
├── test_tenant_isolation.py              # Tenant isolation tests
├── test_tenant_logo.py                   # Tenant branding and logo tests
├── test_invoices.py                      # Invoice CRUD and lifecycle tests
├── test_invoice_pdf.py                   # Invoice PDF generation tests
├── test_invoice_number_config.py         # Invoice numbering configuration tests
├── test_multi_currency_tax.py            # Multi-currency and tax tests
├── test_currency_consistency.py          # Currency consistency tests
├── test_payment_method_and_currency.py   # Payment methods tests
├── test_analytics.py                     # Analytics and reporting tests
├── test_audit_logs.py                    # Audit logging tests
├── test_superadmin.py                    # Super Admin functionality tests
├── test_email_verification.py            # Email verification tests
├── test_email_verification_enforcement.py # Email verification enforcement tests
├── test_password_reset.py                # Password reset tests
├── test_login_throttle.py                # Login delay/throttling tests
├── test_permission_checks.py             # Permission validation tests
├── test_rate_limiting.py                 # Rate limiting tests
├── test_monitoring.py                    # Health checks and metrics tests
├── test_background_tasks.py              # Celery background tasks tests
├── test_performance.py                   # Performance benchmarking tests
├── test_pdf_generator.py                 # PDF generation service tests
├── test_cors.py                          # CORS configuration tests
├── test_error_standardization.py         # Error response format tests
├── test_integration.py                   # End-to-end integration tests
└── README.md                             # This file
```

## Running Tests

### Prerequisites

- Install test dependencies:

```bash
pip install -r requirements.txt
```

- Ensure you have a test environment set up (tests use SQLite in-memory database)

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
# Authentication and security tests
pytest tests/test_auth.py tests/test_auth_throttle.py tests/test_login_throttle.py -v

# Email verification tests
pytest tests/test_email_verification.py tests/test_email_verification_enforcement.py -v

# Password reset tests
pytest tests/test_password_reset.py -v

# User management tests
pytest tests/test_users.py tests/test_permission_checks.py -v

# Tenant tests
pytest tests/test_tenants.py tests/test_tenant_logo.py tests/test_tenant_isolation.py -v

# Invoice tests
pytest tests/test_invoices.py tests/test_invoice_pdf.py tests/test_invoice_number_config.py -v
pytest tests/test_multi_currency_tax.py tests/test_currency_consistency.py -v

# Analytics and reporting
pytest tests/test_analytics.py -v

# Audit logging and super admin
pytest tests/test_audit_logs.py tests/test_superadmin.py -v

# Performance and reliability
pytest tests/test_performance.py tests/test_background_tasks.py tests/test_rate_limiting.py -v

# Monitoring and infrastructure
pytest tests/test_monitoring.py tests/test_cors.py tests/test_error_standardization.py -v

# Integration tests
pytest tests/test_integration.py -v
```

## Test Coverage

The test suite includes **28 test files** with comprehensive coverage across all application features:

### Authentication & Security Tests

**test_auth.py** - Core authentication
- ✅ User registration with validation
- ✅ Duplicate email detection
- ✅ Email and password validation
- ✅ Password hashing verification
- ✅ Successful login
- ✅ Login with incorrect credentials
- ✅ Inactive user blocking
- ✅ Token generation and refresh
- ✅ Token expiration and validation

**test_auth_throttle.py** - Authentication throttling
- ✅ Progressive login delays for failed attempts
- ✅ OWASP ASVS compliance

**test_login_throttle.py** - Login delay enforcement
- ✅ Delay thresholds and time windows
- ✅ Brute-force protection

**test_email_verification.py** - Email verification
- ✅ Verification token generation
- ✅ Email verification flow
- ✅ Verification email sending
- ✅ Token expiration handling

**test_email_verification_enforcement.py** - Email verification enforcement
- ✅ Unverified user restrictions
- ✅ Verification requirement checks

**test_password_reset.py** - Password reset
- ✅ Password reset request
- ✅ Reset token generation
- ✅ Password reset completion
- ✅ Token expiration handling

### User Management Tests

**test_users.py** - User CRUD operations
- ✅ Get current user info
- ✅ List users with pagination
- ✅ Get user by ID
- ✅ Update user information
- ✅ Soft delete users (GDPR compliance)
- ✅ Role-based access control validation
- ✅ Self-deletion prevention

**test_permission_checks.py** - Permission validation
- ✅ Role hierarchy enforcement
- ✅ Owner, Admin, Manager, Attendant permissions
- ✅ Cross-role access prevention

### Tenant Management Tests

**test_tenants.py** - Tenant CRUD
- ✅ Create tenant
- ✅ List tenants with pagination
- ✅ Get tenant by ID
- ✅ Update tenant information
- ✅ Soft delete tenant
- ✅ Domain uniqueness validation

**test_tenant_logo.py** - Tenant branding
- ✅ Logo upload
- ✅ Logo retrieval
- ✅ Logo deletion
- ✅ File validation

**test_tenant_isolation.py** - Multi-tenancy
- ✅ User data isolation by tenant
- ✅ Cross-tenant access prevention
- ✅ JWT tenant_id enforcement
- ✅ Bidirectional isolation verification

### Invoice Management Tests

**test_invoices.py** - Invoice CRUD
- ✅ Create invoice with items
- ✅ List invoices with filters
- ✅ Get invoice by ID
- ✅ Update draft invoice
- ✅ Delete draft invoice
- ✅ Invoice status lifecycle
- ✅ CSV/JSON export

**test_invoice_pdf.py** - PDF generation
- ✅ Generate invoice PDF
- ✅ PDF download endpoint
- ✅ Template rendering

**test_invoice_number_config.py** - Invoice numbering
- ✅ Custom number formats
- ✅ Sequence management
- ✅ Prefix configuration

**test_multi_currency_tax.py** - Multi-currency and tax
- ✅ Multi-currency invoices (USD, EUR, GBP, NGN)
- ✅ Tax rate calculations
- ✅ Currency-specific formatting

**test_currency_consistency.py** - Currency consistency
- ✅ Currency consistency across invoice items
- ✅ Currency validation

**test_payment_method_and_currency.py** - Payment methods
- ✅ Payment method tracking
- ✅ Payment-currency consistency

### Analytics & Reporting Tests

**test_analytics.py** - Analytics endpoints
- ✅ Invoice summary statistics
- ✅ Revenue breakdown by status
- ✅ Tenant-scoped analytics

### Audit & Administration Tests

**test_audit_logs.py** - Audit logging
- ✅ Action tracking
- ✅ User audit logs
- ✅ Resource audit logs
- ✅ Audit log queries

**test_superadmin.py** - Super Admin
- ✅ Platform-wide tenant listing
- ✅ Tenant suspension/reactivation
- ✅ Cross-tenant user access
- ✅ Platform statistics

### Performance & Reliability Tests

**test_performance.py** - Performance benchmarking
- ✅ Response time measurements
- ✅ Caching effectiveness
- ✅ Query optimization

**test_background_tasks.py** - Celery tasks
- ✅ Email sending tasks
- ✅ Background job processing
- ✅ Task scheduling

**test_rate_limiting.py** - Rate limiting
- ✅ Tiered rate limits by role
- ✅ Rate limit headers
- ✅ Throttling behavior

### Infrastructure Tests

**test_monitoring.py** - Health & metrics
- ✅ Health check endpoint
- ✅ Prometheus metrics
- ✅ Status reporting

**test_cors.py** - CORS configuration
- ✅ CORS headers
- ✅ Origin validation

**test_error_standardization.py** - Error handling
- ✅ Standardized error responses
- ✅ Error format consistency

**test_pdf_generator.py** - PDF service
- ✅ PDF generation service
- ✅ Template handling
- ✅ Error handling

### Integration Tests

**test_integration.py** - End-to-end workflows
- ✅ Complete business process flows
- ✅ Cross-module integration
- ✅ Real-world scenarios

**Total Test Coverage**: 28 test files, 144+ passing tests

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

### `test_invoices.py`

Tests invoice module functionality (`/api/v1/invoices/*`):

**Key Test Scenarios**:

- Invoice CRUD operations
- Status lifecycle management (Draft → Sent → Paid → Overdue)
- Permission-based access control
- CSV/JSON export with filtering
- Tenant-aware data isolation

### `test_integration.py`

### NEW - Sprint 2 Integration Tests

Comprehensive end-to-end workflow tests:

**Invoice Lifecycle Integration:**

- Complete workflow from user registration to invoice payment
- Multi-step invoice lifecycle (draft → sent → paid)
- Overdue invoice handling

**Multi-Tenant Integration:**

- Concurrent operations across different tenants
- Cross-tenant data isolation verification
- Tenant-specific export isolation

**Role-Based Workflows:**

- Multi-role invoice approval workflows
- Permission validation across user roles
- Role-based operation restrictions

**Business Scenarios:**

- Branch performance tracking
- Customer invoice history
- Filtered export scenarios

**Data Consistency:**

- Invoice item calculations
- Total recalculation on updates
- Transaction integrity verification

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
| `test_user` | Owner | <owner@testcompany.com> | Full permissions testing |
| `test_admin` | Admin | <admin@testcompany.com> | Admin permission testing |
| `test_manager` | Manager | <manager@testcompany.com> | Limited permission testing |
| `test_attendant` | Attendant | <attendant@testcompany.com> | Minimal permission testing |
| `second_tenant_user` | Owner | <owner@secondcompany.com> | Isolation testing |
| `inactive_user` | Attendant | <inactive@testcompany.com> | Inactive user testing |

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

```bash
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
- [x] Integration tests with real database ✓ (Added in Sprint 2)
- [x] End-to-end workflow tests ✓ (Added in Sprint 2)

---

**Last Updated**: Sprint 2 - Invoice Management & Integration Tests
**Test Framework**: pytest 7.4.3
**Coverage Target**: >80% code coverage
**Total Tests**: 109 (including 10 integration tests)
