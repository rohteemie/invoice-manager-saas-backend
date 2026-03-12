# API Structure Overview

## Authentication & User Management API

This document provides a visual overview of the implemented API structure.

```bash
Multi-Tenant SaaS Backend API
│
├── / (Root & Monitoring - 5 endpoints)
│   ├── GET / - Welcome/root endpoint
│   ├── GET /health - Health check endpoint
│   ├── GET /metrics - Prometheus metrics
│   ├── GET /docs - Swagger UI (Interactive API docs)
│   └── GET /redoc - ReDoc documentation
│
├── /api/v1/tenants (Tenant Management - 9 endpoints)
│   ├── POST   / - Create new tenant
│   ├── POST   /register - Register tenant with owner account
│   ├── GET    / - List all tenants (paginated)
│   ├── GET    /{tenant_id} - Get tenant by ID
│   ├── PUT    /{tenant_id} - Update tenant
│   ├── DELETE /{tenant_id} - Soft delete tenant
│   ├── POST   /{tenant_id}/logo - Upload tenant logo (Owner/Admin) ✨ NEW
│   ├── GET    /{tenant_id}/logo - Get tenant logo ✨ NEW
│   └── DELETE /{tenant_id}/logo - Delete tenant logo (Owner/Admin) ✨ NEW
│
├── /api/v1/auth (Authentication - 8 endpoints)
│   ├── POST /register - Register superadmin (Superadmin only) ⚠️ RESTRICTED
│   ├── POST /login    - Login and get tokens
│   ├── POST /refresh  - Refresh access token
│   ├── POST /verify-email - Verify email with token (Security: Token expires in 24h) ✨ NEW
│   ├── POST /resend-verification-email - Resend verification email (Rate limited: 3/hour) ✨ NEW
│   ├── POST /forgot-password - Request password reset (Rate limited: 3/hour) ✨ NEW
│   ├── POST /reset-password - Reset password with token (Rate limited: 5/hour) ✨ NEW
│   └── POST /force-change-password - Change password (Owner-created users) ✨ NEW
│
├── /api/v1/users (User Management - 6 endpoints)
│   ├── GET    /me - Get current user info (Authenticated)
│   ├── POST   /   - Create user in tenant (Owner only, any role incl. co-owner) ✨ NEW
│   ├── GET    /   - List users in tenant (Owner only)
│   ├── GET    /{user_id} - Get user by ID (Owner only)
│   ├── PUT    /{user_id} - Update user (Owner only)
│   └── DELETE /{user_id} - Soft delete user (Owner only)
│
├── /api/v1/invoices (Invoice Management - 9 endpoints)
│   ├── POST   / - Create new invoice (Manager+)
│   ├── GET    / - List invoices with filters (All roles)
│   ├── GET    /{invoice_id} - Get invoice by ID (All roles)
│   ├── PUT    /{invoice_id} - Update draft invoice (Manager+)
│   ├── PATCH  /{invoice_id}/status - Update invoice status (Manager+)
│   ├── DELETE /{invoice_id} - Delete draft invoice (Admin+)
│   ├── GET    /{invoice_id}/pdf - Download invoice as PDF (All roles) ✨ NEW
│   ├── POST   /{invoice_id}/send - Send invoice via email (Manager+) ✨ NEW
│   └── GET    /export/invoices - Export invoices (CSV/JSON) (Manager+)
│
├── /api/v1/analytics (Analytics & Reporting - 2 endpoints)
│   ├── GET /invoice-summary - Invoice summary statistics (Manager+)
│   └── GET /revenue-by-status - Revenue breakdown by status (Manager+)
│
├── /api/v1/audit-logs (Audit Logging - 4 endpoints) ✨ NEW
│   ├── GET / - List audit logs (Admin+)
│   ├── GET /{audit_log_id} - Get specific audit log (Admin+)
│   ├── GET /user/{user_id} - Get user's audit logs (Admin+)
│   └── GET /resource/{resource_type}/{resource_id} - Get resource audit logs (Admin+)
│
└── /api/v1/admin (Super Admin - Platform Management - 7 endpoints) ✨ NEW
    ├── GET /tenants - List all tenants (Super Admin only)
    ├── GET /tenants/{tenant_id} - Get tenant details (Super Admin only)
    ├── PUT /tenants/{tenant_id}/suspend - Suspend tenant (Super Admin only)
    ├── PUT /tenants/{tenant_id}/reactivate - Reactivate tenant (Super Admin only)
    ├── GET /users - List all users across tenants (Super Admin only)
    ├── GET /audit-logs - Platform-wide audit logs (Super Admin only)
    └── GET /stats - Platform statistics (Super Admin only)

Total API Endpoints: 48 (3 root/monitoring + 45 business API endpoints)
```

## Role Hierarchy

```bash
┌─────────────────────────────────────┐
│         SUPER ADMIN                 │
│  - Platform-level access ✨ NEW     │
│  - Manage all tenants               │
│  - View all users across tenants    │
│  - Access platform-wide audit logs  │
│  - Suspend/reactivate tenants       │
│  - Not tied to any tenant           │
│  - Bypasses tenant role checks      │
└─────────────┬───────────────────────┘
              │
┌─────────────▼───────────────────────┐
│            OWNER                    │
│  - Full tenant management           │
│  - Manage all users (CRUD)          │
│  - Delete users (except self/owners)│
│  - Cannot delete organization       │
│  - All admin privileges             │
└─────────────┬───────────────────────┘
              │
┌─────────────▼───────────────────────┐
│            ADMIN                    │
│  - Full business operations         │
│  - Cannot manage users              │
│  - All manager privileges           │
└─────────────┬───────────────────────┘
              │
┌─────────────▼───────────────────────┐
│           MANAGER                   │
│  - Manage Invoices and Invoice List │
│  - View reports                     │
│  - All attendant privileges         │
└─────────────┬───────────────────────┘
              │
┌─────────────▼───────────────────────┐
│          ATTENDANT                  │
│  - Create Invoice                   │
│  - View Invoice Inventory           │
│  - Basic operations only            │
└─────────────────────────────────────┘
```

## Account Management Rules

### User Deletion Rules
- **Only owners** can delete user accounts
- Owners **cannot delete themselves**
- Owners **cannot delete other owners**
- Non-owners cannot delete any accounts
- Deletion requires contacting technical team for owners

### User Update Rules
- **Only owners** can update user information
- Non-owners cannot edit their own or others' details
- Owners can upgrade roles for non-owner users
- Owner role cannot be changed via API
- Owner role cannot be assigned via API

### Organization Deletion Rules
- Owners **cannot delete their organization**
- Organization deletion requires contacting the technical team/developer organization
- This ensures data integrity and prevents accidental deletions

## Authentication Flow

```bash
┌──────────┐
│  Client  │
└────┬─────┘
     │
     │ 1. POST /api/v1/auth/register
     │    { email, password, role, tenant_id }
     │
     ▼
┌────────────────┐
│  Register API  │
│  - Hash pass   │
│  - Create user │
└────┬───────────┘
     │
     │ 2. Return User (no password)
     │
     ▼
┌──────────┐
│  Client  │
└────┬─────┘
     │
     │ 3. POST /api/v1/auth/login
     │    username=email&password=xxx
     │
     ▼
┌──────────────┐
│  Login API   │
│  - Verify    │
│  - Gen tokens│
└────┬─────────┘
     │
     │ 4. Return { access_token, refresh_token }
     │
     ▼
┌──────────┐
│  Client  │
│  Stores  │
│  Tokens  │
└────┬─────┘
     │
     │ 5. GET /api/v1/users/me
     │    Authorization: Bearer {access_token}
     │
     ▼
┌──────────────────┐
│  Protected API   │
│  - Verify token  │
│  - Check perms   │
│  - Return data   │
└──────────────────┘
```

## Data Model Relationships

```bash
┌───────────────────────────┐
│     Tenant                │
│  - id (PK)                │
│  - name                   │
│  - domain                 │
│  - plan_type              │
│  - is_active              │
│  - default_currency (ISO) │  ◄── ISO 4217 compliant
│  - tax_rate (Decimal)     │  ◄── GDPR Art. 6 compliant
│  - tax_label (String)     │
└────────┬──────────────────┘
         │
         │ 1:N
         │
         ▼
┌───────────────────────────────┐
│      User                     │
│  - id (PK)                    │
│  - email                      │
│  - full_name                  │
│  - hashed_pass                │
│  - role (enum)                │
│  - tenant_id(FK)              │◄── Foreign Key
│  - is_active                  │
│  - is_verified                │
│  - verification_token         │◄── ISO 27001: Access control
│  - verification_token_exp_at  │◄── GDPR: Data minimization
└───────────────────────────────┘
```

## Security Layers

```bash
┌─────────────────────────────────────────────┐
│         Client Request                      │
└──────────────────┬──────────────────────────┘
                   │
┌──────────────────▼──────────────────────────┐
│  Layer 1: Input Validation (Pydantic)       │
│  - Email format                             │
│  - Password length                          │
│  - Required fields                          │
└──────────────────┬──────────────────────────┘
                   │
┌──────────────────▼──────────────────────────┐
│  Layer 2: Authentication (JWT)              │
│  - Token verification                       │
│  - Token expiration check                   │
│  - User active check                        │
└──────────────────┬──────────────────────────┘
                   │
┌──────────────────▼──────────────────────────┐
│  Layer 3: Authorization (RBAC)              │
│  - Role hierarchy check                     │
│  - Permission validation                    │
└──────────────────┬──────────────────────────┘
                   │
┌──────────────────▼──────────────────────────┐
│  Layer 4: Data Isolation (Tenant Filter)    │
│  - Auto-filter by tenant_id                 │
│  - Prevent cross-tenant access              │
└──────────────────┬──────────────────────────┘
                   │
┌──────────────────▼──────────────────────────┐
│  Layer 5: Database (SQLAlchemy ORM)         │
│  - SQL injection prevention                 │
│  - Transaction management                   │
└─────────────────────────────────────────────┘
```

## Token Lifecycle

```bash
┌─────────────────┐
│  Login Success  │
└────────┬────────┘
         │
         ├───────────────────────┬──────────────────────┐
         │                       │                      │
         ▼                       ▼                      ▼
┌─────────────────┐    ┌─────────────────┐   ┌──────────────────┐
│  Access Token   │    │  Refresh Token  │   │  Token Payload   │
│  Expires: 30min │    │  Expires: 7days │   │  - user_id       │
│  For API calls  │    │  For refresh    │   │  - tenant_id     │
└────────┬────────┘    └────────┬────────┘   │  - role          │
         │                      │             │  - exp           │
         │                      │             └──────────────────┘
         ▼                      │
┌─────────────────┐             │
│  Token Expired? │             │
└────────┬────────┘             │
         │                      │
    ┌────┴────┐                 │
    │   Yes   │                 │
    └────┬────┘                 │
         │                      │
         │  Use Refresh Token   │
         └──────────────────────┘
                │
                ▼
         ┌─────────────┐
         │  Get New    │
         │  Tokens     │
         └─────────────┘
```

## File Structure

```bash
app/
├── models/
│   ├── __init__.py (registers User & Tenant)
│   ├── general_model.py (base model)
│   ├── tenant.py (Tenant model)
│   └── user.py (User model + UserRole enum) ✨ NEW
│
├── schemas/
│   ├── tenant.py (Tenant schemas)
│   └── user.py (User schemas, Token, etc.) ✨ NEW
│
├── core/
│   ├── config.py (settings)
│   ├── security.py (password & JWT utils) ✨ NEW
│   └── deps.py (auth dependencies) ✨ NEW
│
├── api/v1/
│   ├── api.py (router aggregation)
│   └── endpoints/
│       ├── tenants.py (tenant CRUD)
│       ├── auth.py (register, login, refresh) ✨ NEW
│       └── users.py (user management) ✨ NEW
│
└── db/
    ├── database.py (engine & session)
    └── session.py (get_db dependency)
```

## Summary Statistics

- **Total Endpoints**: 16 (5 tenant + 5 auth + 6 user)
- **Protected Endpoints**: 6 (require authentication)
- **Role-Restricted**: 5 (require specific roles)
- **Authentication Methods**: JWT Bearer Token
- **Password Hashing**: Bcrypt
- **Token Types**: 2 (access + refresh)
- **User Roles**: 4 (Owner, Admin, Manager, Attendant)
- **Security Layers**: 5 (validation, auth, authz, isolation, ORM)
- **Supported Currencies**: 4 (USD, EUR, GBP, NGN - ISO 4217 compliant)
- **Email Verification**: Enabled with 24h token expiration

## Quick Start Commands

```bash
# 1. Create a tenant
curl -X POST http://localhost:8000/api/v1/tenants/ \
  -H "Content-Type: application/json" \
  -d '{"name":"My Company","domain":"mycompany.com"}'

# 2. Register a user
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"owner@mycompany.com","full_name":"John Doe","password":"SecurePass123","role":"owner","tenant_id":"<tenant_id>"}'

# 3. Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=owner@mycompany.com&password=SecurePass123"

# 4. Use access token
curl http://localhost:8000/api/v1/users/me \
  -H "Authorization: Bearer <access_token>"
```

## Testing Checklist

✅ User registration with validation
✅ Duplicate email detection
✅ Password hashing
✅ User login
✅ Token generation
✅ Token verification
✅ Role-based access control
✅ Tenant isolation
✅ Soft delete (GDPR)
✅ Inactive user blocking
✅ Refresh token flow
✅ Protected endpoints
✅ OpenAPI documentation
✅ Code style compliance (pycodestyle)
✅ Email verification with token expiration
✅ Multi-currency support (ISO 4217)
✅ Tax configuration per tenant

## Security & Compliance

### ISO 27001 Compliance

**Access Control (A.9)**
- JWT-based authentication with token expiration
- Role-based access control (RBAC) with 4 hierarchical roles
- Email verification tokens expire after 24 hours
- Verification tokens are cryptographically secure (secrets.token_urlsafe)
- Rate limiting on sensitive endpoints (3 resends/hour)

**Cryptography (A.10)**
- Passwords hashed using Bcrypt algorithm
- JWT tokens signed with HS256 algorithm
- Verification tokens use 32-byte URL-safe random strings
- All secrets stored in environment variables, not in code

**Operations Security (A.12)**
- Automatic logging of authentication events
- Token validation on every protected endpoint
- Inactive users blocked from authentication
- Soft delete for data retention and audit trails

### GDPR Compliance

**Right to Erasure (Art. 17)**
- Soft delete implementation for users (`is_active` flag)
- Verification tokens automatically cleared after use
- Token expiration ensures data minimization

**Data Minimization (Art. 5.1.c)**
- Verification tokens expire after 24 hours
- Tokens cleared immediately after successful verification
- Only necessary user fields stored

**Lawful Basis for Processing (Art. 6)**
- Tax information processed under legal obligation (Art. 6.1.c)
- Customer financial data processed under contract (Art. 6.1.b)
- Email verification for legitimate interest in security (Art. 6.1.f)

**Data Protection by Design (Art. 25)**
- Tenant isolation at database query level
- Foreign key constraints prevent orphaned records
- Input validation via Pydantic schemas
- Secure defaults (is_active=True, is_verified=False)

**Security of Processing (Art. 32)**
- Bcrypt password hashing (industry standard)
- JWT token-based authentication
- HTTPS recommended for production
- Rate limiting prevents brute force attacks

### Financial Data Security

**Multi-Currency Support (ISO 4217)**
- All currency codes follow ISO 4217 standard
- Supported currencies: USD, EUR, GBP, NGN
- Currency validation at schema level
- Database indexes on currency fields for performance

**Tax Data Handling**
- Tax rates stored with 2 decimal precision (Decimal 5,2)
- Tax labels support regional variations (VAT, GST, Sales Tax)
- Per-tenant tax configuration for regulatory compliance
- Nullable tax_rate supports tax-exempt organizations

**Sensitive Financial Fields**
- All monetary values use Decimal type (not Float) for precision
- Customer financial information isolated by tenant_id
- Invoice data protected by role-based permissions
- Audit trail via automatic timestamps (created_at, updated_at)

### Data Privacy Best Practices

**Personal Identifiable Information (PII)**
- Customer email, phone, address stored encrypted at rest (DB level)
- Email addresses used for authentication only
- No PII in logs or error messages
- User enumeration prevention in resend endpoint

**Token Security**
- Verification tokens single-use only
- Tokens indexed for efficient lookup but cleared after use
- Expired tokens rejected with clear error messages
- Token generation uses cryptographically secure randomness

**Rate Limiting**
- Verification endpoint: 10 requests/minute
- Resend endpoint: 3 requests/hour
- Login endpoint: Standard rate limiting via SlowAPI
- Prevents abuse and brute force attacks
