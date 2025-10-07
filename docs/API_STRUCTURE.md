# API Structure Overview

## Authentication & User Management API

This document provides a visual overview of the implemented API structure.

```bash
Multi-Tenant SaaS Backend API
│
├── / (Root)
│   └── GET - Welcome message
│
├── /api/v1/tenants (Tenant Management)
│   ├── POST   - Create new tenant
│   ├── GET    - List all tenants (paginated)
│   ├── GET    /{tenant_id} - Get tenant by ID
│   ├── PUT    /{tenant_id} - Update tenant
│   └── DELETE /{tenant_id} - Soft delete tenant
│
├── /api/v1/auth (Authentication)
│   ├── POST /register - Register new user
│   ├── POST /login    - Login and get tokens
│   └── POST /refresh  - Refresh access token
│
└── /api/v1/users (User Management)
    ├── GET    /me - Get current user info (Authenticated)
    ├── GET    /   - List users in tenant (Admin+)
    ├── GET    /{user_id} - Get user by ID (Admin+)
    ├── PUT    /{user_id} - Update user (Admin+)
    └── DELETE /{user_id} - Soft delete user (Owner)
```

## Role Hierarchy

```bash
┌─────────────────────────────────────┐
│            OWNER                    │
│  - Full tenant management           │
│  - Delete users                     │
│  - All admin privileges             │
└─────────────┬───────────────────────┘
              │
┌─────────────▼───────────────────────┐
│            ADMIN                    │
│  - Manage users                     │
│  - Full business operations         │
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
┌──────────────────┐
│     Tenant       │
│  - id (PK)       │
│  - name          │
│  - domain        │
│  - plan_type     │
│  - is_active     │
└────────┬─────────┘
         │
         │ 1:N
         │
         ▼
┌──────────────────┐
│      User        │
│  - id (PK)       │
│  - email         │
│  - full_name     │
│  - hashed_pass   │
│  - role (enum)   │
│  - tenant_id(FK) │◄── Foreign Key
│  - is_active     │
│  - is_verified   │
└──────────────────┘
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

- **Total Endpoints**: 14 (5 tenant + 3 auth + 6 user)
- **Protected Endpoints**: 6 (require authentication)
- **Role-Restricted**: 5 (require specific roles)
- **Authentication Methods**: JWT Bearer Token
- **Password Hashing**: Bcrypt
- **Token Types**: 2 (access + refresh)
- **User Roles**: 4 (Owner, Admin, Manager, Attendant)
- **Security Layers**: 5 (validation, auth, authz, isolation, ORM)

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
