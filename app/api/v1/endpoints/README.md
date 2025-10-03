# Endpoints Directory (`/app/api/v1/endpoints`)

## Overview

This directory contains individual endpoint handlers for the Multi-Tenant SaaS Backend API v1. Each file implements a specific feature domain with related endpoints.

## Directory Structure

```
endpoints/
├── __init__.py     # Package initialization
├── auth.py         # Authentication & token management endpoints
├── tenants.py      # Tenant CRUD endpoints
└── users.py        # User management endpoints with RBAC
```

## Endpoint Files

### Authentication Endpoints (`auth.py`)

**Purpose:** Handle user authentication, registration, and token management.

**Tag:** `auth`

**Endpoints:**

#### POST `/api/v1/auth/register`
Register a new user account.

**Authentication:** Not required (public)

**Request Body:**
```json
{
  "email": "user@example.com",
  "full_name": "John Doe",
  "password": "SecurePass123",
  "role": "admin",
  "tenant_id": "tenant-uuid-here"
}
```

**Validation:**
- Email must be valid format
- Email must be unique
- Password minimum 8 characters
- Full name 1-100 characters
- Role must be valid UserRole enum
- Tenant ID must exist

**Response (201 Created):**
```json
{
  "id": "user-uuid",
  "email": "user@example.com",
  "full_name": "John Doe",
  "role": "admin",
  "tenant_id": "tenant-uuid-here",
  "is_active": true,
  "is_verified": false,
  "created_at": "2024-01-15T10:30:00",
  "updated_at": "2024-01-15T10:30:00"
}
```

**Error Responses:**
- `400 Bad Request` - Email already registered
- `422 Unprocessable Entity` - Validation error

**Security:**
- Password is hashed with bcrypt before storage
- Password never returned in response
- User created with default `is_verified=False`

---

#### POST `/api/v1/auth/login`
Authenticate user and receive JWT tokens.

**Authentication:** Not required (public)

**Request (Form Data):**
```
username=user@example.com
password=SecurePass123
```

**Note:** Uses OAuth2 password flow (form data, not JSON)

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Token Contents:**
- **Access Token**: Contains user_id, tenant_id, role (expires in 30 min)
- **Refresh Token**: Contains user_id only (expires in 7 days)

**Error Responses:**
- `401 Unauthorized` - Invalid credentials
- `401 Unauthorized` - User is inactive

**Security:**
- Verifies password with bcrypt
- Checks user is active
- Returns tokens only on successful auth

**Usage:**
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user@example.com&password=SecurePass123"
```

---

#### POST `/api/v1/auth/refresh`
Refresh access token using refresh token.

**Authentication:** Not required (uses refresh token)

**Request Body:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Error Responses:**
- `401 Unauthorized` - Invalid or expired refresh token
- `401 Unauthorized` - User not found or inactive

**Security:**
- Validates refresh token signature
- Checks token expiration
- Verifies user still exists and is active
- Generates new access token with current user data

---

### Tenant Endpoints (`tenants.py`)

**Purpose:** Manage tenant (organization) lifecycle.

**Tag:** `tenants`

**Endpoints:**

#### POST `/api/v1/tenants`
Create a new tenant (organization).

**Authentication:** Not required (public registration)

**Request Body:**
```json
{
  "name": "Acme Corporation",
  "domain": "acme",
  "plan_type": "enterprise",
  "description": "Global manufacturing company"
}
```

**Validation:**
- Name: 1-100 characters (required)
- Domain: Unique, optional
- Plan type: Default "free"
- Description: Max 500 characters, optional

**Response (201 Created):**
```json
{
  "id": "tenant-uuid",
  "name": "Acme Corporation",
  "domain": "acme",
  "plan_type": "enterprise",
  "description": "Global manufacturing company",
  "is_active": true,
  "created_at": "2024-01-15T10:30:00",
  "updated_at": "2024-01-15T10:30:00"
}
```

**Error Responses:**
- `400 Bad Request` - Domain already exists
- `422 Unprocessable Entity` - Validation error

---

#### GET `/api/v1/tenants`
List all tenants with pagination.

**Authentication:** Varies by implementation

**Query Parameters:**
- `skip`: Offset for pagination (default: 0)
- `limit`: Number of results (default: 100, max: 100)

**Response (200 OK):**
```json
[
  {
    "id": "tenant-uuid-1",
    "name": "Acme Corporation",
    "domain": "acme",
    "plan_type": "enterprise"
  },
  {
    "id": "tenant-uuid-2",
    "name": "Tech Startup",
    "domain": "techstartup",
    "plan_type": "pro"
  }
]
```

**Usage:**
```bash
curl http://localhost:8000/api/v1/tenants?skip=0&limit=10
```

---

#### GET `/api/v1/tenants/{tenant_id}`
Get tenant by ID.

**Authentication:** Varies by implementation

**Path Parameters:**
- `tenant_id`: UUID of the tenant

**Response (200 OK):**
```json
{
  "id": "tenant-uuid",
  "name": "Acme Corporation",
  "domain": "acme",
  "plan_type": "enterprise",
  "description": "Global manufacturing company",
  "is_active": true,
  "created_at": "2024-01-15T10:30:00",
  "updated_at": "2024-01-15T10:30:00"
}
```

**Error Responses:**
- `404 Not Found` - Tenant doesn't exist

---

#### PUT `/api/v1/tenants/{tenant_id}`
Update tenant information.

**Authentication:** Varies by implementation

**Path Parameters:**
- `tenant_id`: UUID of the tenant

**Request Body (all fields optional):**
```json
{
  "name": "Acme Corp (Updated)",
  "plan_type": "pro",
  "description": "Updated description"
}
```

**Response (200 OK):**
```json
{
  "id": "tenant-uuid",
  "name": "Acme Corp (Updated)",
  "domain": "acme",
  "plan_type": "pro",
  "description": "Updated description",
  "is_active": true,
  "created_at": "2024-01-15T10:30:00",
  "updated_at": "2024-01-15T11:00:00"
}
```

**Error Responses:**
- `404 Not Found` - Tenant doesn't exist
- `400 Bad Request` - Domain already exists

---

#### DELETE `/api/v1/tenants/{tenant_id}`
Soft delete a tenant.

**Authentication:** Varies by implementation

**Path Parameters:**
- `tenant_id`: UUID of the tenant

**Response (200 OK):**
```json
{
  "id": "tenant-uuid",
  "name": "Acme Corporation",
  "is_active": false,
  "updated_at": "2024-01-15T12:00:00"
}
```

**Note:** Soft delete sets `is_active=False` (GDPR compliance)

**Error Responses:**
- `404 Not Found` - Tenant doesn't exist

---

### User Endpoints (`users.py`)

**Purpose:** Manage users within tenants with role-based access control.

**Tag:** `users`

**All endpoints require authentication via JWT Bearer token.**

#### GET `/api/v1/users/me`
Get current authenticated user's information.

**Authentication:** Required (any authenticated user)

**Authorization:** Any authenticated user

**Request Headers:**
```
Authorization: Bearer {access_token}
```

**Response (200 OK):**
```json
{
  "id": "user-uuid",
  "email": "user@example.com",
  "full_name": "John Doe",
  "role": "admin",
  "tenant_id": "tenant-uuid",
  "is_active": true,
  "is_verified": true,
  "created_at": "2024-01-15T10:30:00",
  "updated_at": "2024-01-15T10:30:00"
}
```

**Error Responses:**
- `401 Unauthorized` - Invalid or missing token

---

#### GET `/api/v1/users`
List users in current user's tenant.

**Authentication:** Required

**Authorization:** Admin or Owner only

**Query Parameters:**
- `skip`: Offset for pagination (default: 0)
- `limit`: Number of results (default: 100, max: 100)

**Response (200 OK):**
```json
[
  {
    "id": "user-uuid-1",
    "email": "admin@acme.com",
    "full_name": "Admin User",
    "role": "admin",
    "tenant_id": "tenant-uuid"
  },
  {
    "id": "user-uuid-2",
    "email": "manager@acme.com",
    "full_name": "Manager User",
    "role": "manager",
    "tenant_id": "tenant-uuid"
  }
]
```

**Tenant Isolation:** Automatically filters to current user's tenant

**Error Responses:**
- `401 Unauthorized` - Invalid or missing token
- `403 Forbidden` - Insufficient permissions (not Admin or Owner)

---

#### GET `/api/v1/users/{user_id}`
Get user by ID (within current tenant).

**Authentication:** Required

**Authorization:** Admin or Owner only

**Path Parameters:**
- `user_id`: UUID of the user

**Response (200 OK):**
```json
{
  "id": "user-uuid",
  "email": "user@example.com",
  "full_name": "John Doe",
  "role": "manager",
  "tenant_id": "tenant-uuid",
  "is_active": true,
  "is_verified": true,
  "created_at": "2024-01-15T10:30:00",
  "updated_at": "2024-01-15T10:30:00"
}
```

**Tenant Isolation:** Returns 404 if user belongs to different tenant

**Error Responses:**
- `401 Unauthorized` - Invalid or missing token
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - User not found in current tenant

---

#### PUT `/api/v1/users/{user_id}`
Update user information.

**Authentication:** Required

**Authorization:** Admin or Owner only

**Path Parameters:**
- `user_id`: UUID of the user

**Request Body (all fields optional):**
```json
{
  "full_name": "Jane Doe (Updated)",
  "role": "admin",
  "is_verified": true
}
```

**Response (200 OK):**
```json
{
  "id": "user-uuid",
  "email": "user@example.com",
  "full_name": "Jane Doe (Updated)",
  "role": "admin",
  "tenant_id": "tenant-uuid",
  "is_active": true,
  "is_verified": true,
  "created_at": "2024-01-15T10:30:00",
  "updated_at": "2024-01-15T13:00:00"
}
```

**Tenant Isolation:** Can only update users in current tenant

**Error Responses:**
- `401 Unauthorized` - Invalid or missing token
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - User not found in current tenant

---

#### DELETE `/api/v1/users/{user_id}`
Soft delete a user.

**Authentication:** Required

**Authorization:** Owner only

**Path Parameters:**
- `user_id`: UUID of the user

**Response (200 OK):**
```json
{
  "id": "user-uuid",
  "email": "user@example.com",
  "full_name": "John Doe",
  "is_active": false,
  "updated_at": "2024-01-15T14:00:00"
}
```

**Note:** Soft delete sets `is_active=False` (GDPR right-to-be-forgotten)

**Tenant Isolation:** Can only delete users in current tenant

**Error Responses:**
- `401 Unauthorized` - Invalid or missing token
- `403 Forbidden` - Insufficient permissions (not Owner)
- `404 Not Found` - User not found in current tenant

---

## Common Patterns

### Authentication Header

All protected endpoints require:
```
Authorization: Bearer {access_token}
```

**Example:**
```bash
curl -H "Authorization: Bearer eyJhbGc..." \
  http://localhost:8000/api/v1/users/me
```

### Tenant Isolation

All user-related queries are automatically scoped to the authenticated user's tenant:

```python
# In endpoint handler
@router.get("/users")
def list_users(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Automatically filtered by tenant
    users = db.query(User).filter(
        User.tenant_id == current_user.tenant_id
    ).all()
    return users
```

### Soft Deletion

Instead of hard deletes, we use soft deletion:
- Set `is_active = False`
- Preserves audit trails
- GDPR compliant (right-to-be-forgotten)
- Can be hard-deleted later if needed

### Error Handling

Consistent error responses across all endpoints:

```python
# Not Found
raise HTTPException(status_code=404, detail="User not found")

# Unauthorized
raise HTTPException(status_code=401, detail="Invalid credentials")

# Forbidden
raise HTTPException(status_code=403, detail="Insufficient permissions")

# Bad Request
raise HTTPException(status_code=400, detail="Email already exists")
```

## Role-Based Access Control

### Role Hierarchy

```
Owner > Admin > Manager > Attendant
```

### Permission Matrix

| Endpoint | Attendant | Manager | Admin | Owner |
|----------|-----------|---------|-------|-------|
| GET /users/me | ✅ | ✅ | ✅ | ✅ |
| GET /users | ❌ | ❌ | ✅ | ✅ |
| GET /users/{id} | ❌ | ❌ | ✅ | ✅ |
| PUT /users/{id} | ❌ | ❌ | ✅ | ✅ |
| DELETE /users/{id} | ❌ | ❌ | ❌ | ✅ |

### Implementation

```python
from app.core.deps import require_role
from app.models.user import UserRole

@router.delete("/users/{user_id}")
def delete_user(
    user_id: str,
    current_user: User = Depends(require_role(UserRole.OWNER)),
    db: Session = Depends(get_db)
):
    # Only owners can access this endpoint
    pass
```

## Testing

Each endpoint is thoroughly tested in `/tests`:

**Test Files:**
- `test_auth.py` - Authentication endpoint tests
- `test_users.py` - User management tests
- `test_tenants.py` - Tenant CRUD tests
- `test_tenant_isolation.py` - Multi-tenant isolation tests

**Example Test:**
```python
def test_list_users_as_admin(client, admin_auth_headers):
    response = client.get(
        "/api/v1/users",
        headers=admin_auth_headers
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)
```

**See:** [/tests/README.md](../../../tests/README.md) for comprehensive testing guide.

## Related Documentation

- [API v1 Overview](../README.md) - API version documentation
- [API Layer](../../README.md) - API architecture
- [Authentication Guide](../../../docs/authentication.md) - Detailed auth flow
- [Models](../../models/README.md) - Data models
- [Schemas](../../schemas/README.md) - Request/response validation

## Future Endpoints

Planned endpoints for upcoming features:

### Invoice Management
- POST `/api/v1/invoices`
- GET `/api/v1/invoices`
- GET `/api/v1/invoices/{id}`
- PUT `/api/v1/invoices/{id}`
- DELETE `/api/v1/invoices/{id}`

### Branch Management
- POST `/api/v1/branches`
- GET `/api/v1/branches`

### Analytics
- GET `/api/v1/analytics/revenue`
- GET `/api/v1/analytics/invoices`

## License

MIT License - See [LICENSE](../../../LICENSE) for details.
