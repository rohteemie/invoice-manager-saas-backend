# Endpoints Directory (`/app/api/v1/endpoints`)

## Overview

This directory contains individual endpoint handlers for the Multi-Tenant SaaS Backend API v1. Each file implements a specific feature domain with related endpoints.

## Directory Structure

```
endpoints/
├── __init__.py     # Package initialization
├── auth.py         # Authentication & token management endpoints
├── tenants.py      # Tenant CRUD endpoints
├── users.py        # User management endpoints with RBAC
└── invoices.py     # Invoice CRUD and lifecycle endpoints
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
  "description": "Updated description",
  "plan_type": "pro"
}

**Note on plan_type:**
- Regular users (Owners) CANNOT update `plan_type`
- Super Admins CAN update `plan_type`
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
- `403 Forbidden` - Not authorized to update plan_type (Regular users)

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

### Invoice Endpoints (`invoices.py`)

**Purpose:** Manage invoices with lifecycle states and tenant isolation.

**Tag:** `invoices`

**Endpoints:**

#### POST `/api/v1/invoices`
Create a new invoice.

**Authentication:** Required (any authenticated user)

**Request Body:**
```json
{
  "customer_name": "John Doe",
  "customer_email": "john@example.com",
  "customer_phone": "+1234567890",
  "customer_address": "123 Main St, City, Country",
  "branch_id": "branch-uuid",
  "issue_date": "2024-01-15",
  "due_date": "2024-02-15",
  "notes": "Payment terms: Net 30",
  "items": [
    {
      "description": "Product A",
      "quantity": 2,
      "unit_price": 100.00
    },
    {
      "description": "Service B",
      "quantity": 1,
      "unit_price": 50.00
    }
  ]
}
```

**Response (201 Created):**
```json
{
  "id": "invoice-uuid",
  "invoice_number": "INV-20240115-0001",
  "tenant_id": "tenant-uuid",
  "creator_id": "user-uuid",
  "customer_name": "John Doe",
  "customer_email": "john@example.com",
  "status": "draft",
  "subtotal": 250.00,
  "tax_amount": 0.00,
  "discount_amount": 0.00,
  "total_amount": 250.00,
  "items": [
    {
      "id": "item-uuid-1",
      "description": "Product A",
      "quantity": 2,
      "unit_price": 100.00,
      "total_price": 200.00
    },
    {
      "id": "item-uuid-2",
      "description": "Service B",
      "quantity": 1,
      "unit_price": 50.00,
      "total_price": 50.00
    }
  ],
  "created_at": "2024-01-15T10:00:00",
  "updated_at": "2024-01-15T10:00:00"
}
```

#### GET `/api/v1/invoices`
List invoices for current tenant.

**Authentication:** Required

**Query Parameters:**
- `skip` (int): Pagination offset (default: 0)
- `limit` (int): Results per page (default: 100, max: 100)
- `status` (string): Filter by status (draft, sent, paid, overdue)

**Response (200 OK):**
```json
[
  {
    "id": "invoice-uuid",
    "invoice_number": "INV-20240115-0001",
    "customer_name": "John Doe",
    "status": "draft",
    "total_amount": 250.00,
    ...
  }
]
```

#### GET `/api/v1/invoices/{invoice_id}`
Get a specific invoice.

**Authentication:** Required

**Response (200 OK):** Invoice object with items

**Tenant Isolation:** Returns 404 if invoice belongs to different tenant

#### PUT `/api/v1/invoices/{invoice_id}`
Update an invoice.

**Authentication:** Required (Manager role or higher)

**Permissions:** `MANAGER`, `ADMIN`, `OWNER`

**Constraints:** Only DRAFT invoices can be updated

**Request Body:**
```json
{
  "customer_name": "Updated Name",
  "notes": "Updated notes",
  "items": [
    {
      "description": "New Item",
      "quantity": 3,
      "unit_price": 75.00
    }
  ]
}
```

**Note:** Updating items replaces all existing items

#### PATCH `/api/v1/invoices/{invoice_id}/status`
Update invoice status (lifecycle management).

**Authentication:** Required (Manager role or higher)

**Permissions:** `MANAGER`, `ADMIN`, `OWNER`

**Request Body:**
```json
{
  "status": "sent"
}
```

**For PAID status:**
```json
{
  "status": "paid",
  "payment_method": "Credit Card"
}
```

**Valid Status Transitions:**
- `DRAFT` → `SENT`
- `SENT` → `PAID`, `OVERDUE`
- `OVERDUE` → `PAID`
- `PAID` → (no transitions allowed)

**Response (200 OK):** Updated invoice object

**Error Responses:**
- `400 Bad Request` - Invalid status transition
- `400 Bad Request` - Missing payment_method for PAID status
- `403 Forbidden` - Insufficient permissions

#### DELETE `/api/v1/invoices/{invoice_id}`
Delete an invoice.

**Authentication:** Required (Admin role or higher)

**Permissions:** `ADMIN`, `OWNER`

**Constraints:** Only DRAFT invoices can be deleted

**Response (200 OK):**
```json
{
  "message": "Invoice deleted successfully"
}
```

**Error Responses:**
- `400 Bad Request` - Cannot delete non-DRAFT invoice
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - Invoice not found

#### GET `/api/v1/invoices/export/invoices`
Export invoices in CSV or JSON format.

**Authentication:** Required (any authenticated user)

**Query Parameters:**
- `format` (string): Export format - `csv` or `json` (default: `csv`)
- `status` (string): Filter by status (draft, sent, paid, overdue) - optional
- `start_date` (string): Filter invoices created on or after this date (ISO 8601) - optional
- `end_date` (string): Filter invoices created on or before this date (ISO 8601) - optional

**Response (200 OK):**

Content-Type depends on format:
- CSV: `text/csv`
- JSON: `application/json`

**Response Headers:**
- `Content-Disposition: attachment; filename=invoices_YYYYMMDD_HHMMSS.{csv|json}`

**CSV Format:**
```csv
Invoice Number,Customer Name,Customer Email,Status,Issue Date,Due Date,Subtotal,Tax Amount,Discount Amount,Total Amount,Payment Method,Paid At,Created At
INV-20240115-0001,John Doe,john@example.com,draft,2024-01-15,2024-02-15,250.00,0.00,0.00,250.00,,,2024-01-15T10:00:00
INV-20240115-0002,Jane Smith,jane@example.com,paid,2024-01-16,2024-02-16,500.00,0.00,0.00,500.00,Credit Card,2024-01-20T15:30:00,2024-01-16T11:00:00
```

**JSON Format:**
```json
[
  {
    "invoice_number": "INV-20240115-0001",
    "customer_name": "John Doe",
    "customer_email": "john@example.com",
    "customer_phone": "+1234567890",
    "customer_address": "123 Main St",
    "status": "draft",
    "issue_date": "2024-01-15",
    "due_date": "2024-02-15",
    "subtotal": 250.00,
    "tax_amount": 0.00,
    "discount_amount": 0.00,
    "total_amount": 250.00,
    "payment_method": null,
    "paid_at": null,
    "created_at": "2024-01-15T10:00:00",
    "items": [
      {
        "description": "Product A",
        "quantity": 2.0,
        "unit_price": 100.0,
        "total_price": 200.0
      },
      {
        "description": "Service B",
        "quantity": 1.0,
        "unit_price": 50.0,
        "total_price": 50.0
      }
    ]
  }
]
```

**Use Cases:**
- Finance teams can export to CSV for analysis in Excel
- Integration with external systems using JSON format
- Filtered exports for specific reporting periods or statuses

**Examples:**

Export all invoices as CSV (default):
```bash
curl -H "Authorization: Bearer {token}" \
  "http://localhost:8000/api/v1/invoices/export/invoices"
```

Export PAID invoices as JSON:
```bash
curl -H "Authorization: Bearer {token}" \
  "http://localhost:8000/api/v1/invoices/export/invoices?format=json&status=paid"
```

Export invoices for date range:
```bash
curl -H "Authorization: Bearer {token}" \
  "http://localhost:8000/api/v1/invoices/export/invoices?start_date=2024-01-01&end_date=2024-01-31"
```

**Tenant Isolation:** Only exports invoices belonging to the authenticated user's tenant

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
| POST /invoices | ✅ | ✅ | ✅ | ✅ |
| GET /invoices | ✅ | ✅ | ✅ | ✅ |
| GET /invoices/{id} | ✅ | ✅ | ✅ | ✅ |
| PUT /invoices/{id} | ❌ | ✅ | ✅ | ✅ |
| PATCH /invoices/{id}/status | ❌ | ✅ | ✅ | ✅ |
| DELETE /invoices/{id} | ❌ | ❌ | ✅ | ✅ |

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

### Branch Management
- POST `/api/v1/branches`
- GET `/api/v1/branches`
- GET `/api/v1/branches/{id}`
- PUT `/api/v1/branches/{id}`
- DELETE `/api/v1/branches/{id}`

### Analytics
- GET `/api/v1/analytics/revenue`
- GET `/api/v1/analytics/invoices`
- GET `/api/v1/analytics/overdue`

### Customer Management
- POST `/api/v1/customers`
- GET `/api/v1/customers`
- GET `/api/v1/customers/{id}`

## License

MIT License - See [LICENSE](../../../LICENSE) for details.
