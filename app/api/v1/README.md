# API Version 1 (`/app/api/v1`)

## Overview

This directory contains the implementation of API version 1 for the Multi-Tenant SaaS Backend. It includes router aggregation and all endpoint handlers organized by feature domain.

## Directory Structure

```bash
v1/
├── __init__.py     # Package initialization
├── api.py          # Main router that aggregates all endpoint routers
└── endpoints/      # Feature-specific endpoint implementations
    ├── __init__.py
    ├── auth.py      # Authentication & token management
    ├── tenants.py   # Tenant CRUD operations
    └── users.py     # User management with RBAC
```

## API Version Information

**Version:** 1.0
**Base Path:** `/api/v1`
**Status:** Active (Current)
**OpenAPI Spec:** <http://localhost:8000/api/v1/openapi.json>

## Router Aggregation (`api.py`)

The `api.py` file serves as the central router aggregator for all version 1 endpoints.

**Implementation:**

```python
from fastapi import APIRouter
from app.api.v1.endpoints import tenants, auth, users

api_router = APIRouter()

# Include feature routers with prefixes and tags
api_router.include_router(
    tenants.router,
    prefix="/tenants",
    tags=["tenants"]
)

api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["auth"]
)

api_router.include_router(
    users.router,
    prefix="/users",
    tags=["users"]
)
```

**Configuration:**

- Each feature router gets its own URL prefix
- OpenAPI tags group related endpoints in documentation
- Routers are independent and can be developed separately

**Router Inclusion in Main App:**

```python
# In app/main.py
from app.api.v1.api import api_router
from app.core.config import settings

app.include_router(api_router, prefix=settings.API_V1_STR)
# settings.API_V1_STR = "/api/v1"
```

## Endpoints Overview

### Authentication Endpoints (`/auth`)

**Purpose:** User authentication and token management

**Endpoints:**

- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login and receive tokens
- `POST /api/v1/auth/refresh` - Refresh access token

**Authentication:** Public endpoints (no auth required)

**Key Features:**

- JWT token generation
- Secure password hashing
- Token refresh mechanism
- Email uniqueness validation

**See:** [endpoints/README.md](endpoints/README.md#authentication-endpoints) for details.

### Tenant Endpoints (`/tenants`)

**Purpose:** Tenant (organization) lifecycle management

**Endpoints:**

- `POST /api/v1/tenants` - Create new tenant
- `GET /api/v1/tenants` - List all tenants
- `GET /api/v1/tenants/{tenant_id}` - Get tenant by ID
- `PUT /api/v1/tenants/{tenant_id}` - Update tenant
- `DELETE /api/v1/tenants/{tenant_id}` - Soft delete tenant

**Authentication:** Public for POST, varies for others

**Key Features:**

- Multi-tenant onboarding
- Domain uniqueness validation
- Soft deletion (GDPR compliance)
- Pagination support

**See:** [endpoints/README.md](endpoints/README.md#tenant-endpoints) for details.

### User Endpoints (`/users`)

**Purpose:** User management with role-based access control

**Endpoints:**

- `GET /api/v1/users/me` - Get current user
- `GET /api/v1/users` - List users (tenant-scoped)
- `GET /api/v1/users/{user_id}` - Get user by ID
- `PUT /api/v1/users/{user_id}` - Update user
- `DELETE /api/v1/users/{user_id}` - Soft delete user

**Authentication:** Required for all endpoints

**Authorization:**

- `/me` - Any authenticated user
- List/Get/Update - Admin or Owner
- Delete - Owner only

**Key Features:**

- Tenant isolation
- Role hierarchy enforcement
- Soft deletion
- User profile management

**See:** [endpoints/README.md](endpoints/README.md#user-endpoints) for details.

## API Design Principles

### RESTful Architecture

**Resource Naming:**

- Plural nouns for collections: `/users`, `/tenants`
- Singular identifiers: `/users/{user_id}`
- Special resources: `/users/me`

**HTTP Methods:**

- `GET` - Retrieve resources (idempotent, safe)
- `POST` - Create new resources
- `PUT` - Update resources (idempotent)
- `DELETE` - Remove resources (soft delete)

**Status Codes:**

- `200 OK` - Successful retrieval/update
- `201 Created` - Successful creation
- `400 Bad Request` - Invalid input
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - Resource doesn't exist
- `422 Unprocessable Entity` - Validation error

### Consistent Response Formats

**Single Resource:**

```json
{
  "id": "uuid",
  "email": "user@example.com",
  "full_name": "John Doe",
  "created_at": "2024-01-15T10:30:00",
  "updated_at": "2024-01-15T10:30:00"
}
```

**Collection:**

```json
[
  {
    "id": "uuid-1",
    "email": "user1@example.com"
  },
  {
    "id": "uuid-2",
    "email": "user2@example.com"
  }
]
```

**Error:**

```json
{
  "detail": "Error message"
}
```

### Multi-Tenant Isolation

All endpoints automatically enforce tenant isolation:

```python
# Current user's tenant_id is used to scope queries
@router.get("/users")
def list_users(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Only returns users from current_user's tenant
    return db.query(User).filter(
        User.tenant_id == current_user.tenant_id
    ).all()
```

**Isolation Benefits:**

- Prevents cross-tenant data access
- Simplifies endpoint logic
- Enhances security
- Automatic enforcement

## Security Implementation

### Authentication Layer

**JWT Token Flow:**

1. User logs in with credentials
2. System validates username/password
3. Generates access token (30 min) + refresh token (7 days)
4. Client includes token in subsequent requests
5. System validates token on each request

**Token Structure:**

```json
{
  "sub": "user-id",
  "tenant_id": "tenant-id",
  "role": "admin",
  "exp": 1234567890
}
```

### Authorization Layer

**Role Hierarchy:**

```bash
Owner > Admin > Manager > Attendant
```

**Permission Checks:**

```python
# Require specific role (includes hierarchy)
@router.delete("/users/{user_id}")
def delete_user(
    user_id: str,
    current_user: User = Depends(require_role(UserRole.OWNER))
):
    # Only owners can delete users
    pass
```

### Input Validation

**Pydantic Schemas:**

- Automatic type validation
- Field constraints (length, format)
- Email format validation
- Custom validators

**Example:**

```python
class UserCreate(BaseModel):
    email: EmailStr  # Validates email format
    password: str = Field(min_length=8)  # Min 8 characters
    full_name: str = Field(min_length=1, max_length=100)
```

## Dependency Injection

### Common Dependencies

**Database Session:**

```python
db: Session = Depends(get_db)
```

**Current User:**

```python
current_user: User = Depends(get_current_user)
```

**Role Requirement:**

```python
current_user: User = Depends(require_role(UserRole.ADMIN))
```

### Benefits

- Automatic execution
- Code reusability
- Easy testing (override dependencies)
- Clean endpoint logic

## Error Handling

### Standard Exceptions

```python
from fastapi import HTTPException

# Not Found
raise HTTPException(status_code=404, detail="User not found")

# Unauthorized
raise HTTPException(status_code=401, detail="Invalid credentials")

# Forbidden
raise HTTPException(status_code=403, detail="Insufficient permissions")

# Bad Request
raise HTTPException(status_code=400, detail="Email already registered")
```

### Database Errors

```python
from sqlalchemy.exc import IntegrityError

try:
    db.commit()
except IntegrityError as e:
    db.rollback()
    if "unique constraint" in str(e):
        raise HTTPException(status_code=400, detail="Resource already exists")
    raise
```

## Request/Response Flow

```bash
Client Request
      │
      ▼
┌─────────────────────┐
│ FastAPI Middleware  │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Input Validation   │
│  (Pydantic Schema)  │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│   Dependencies      │
│   - get_db()        │
│   - get_current_user│
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Endpoint Handler   │
│  (Business Logic)   │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Database Query     │
│  (Tenant-scoped)    │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Response Formatting │
│ (Pydantic Schema)   │
└──────────┬──────────┘
           │
           ▼
     JSON Response
```

## Testing

### Endpoint Tests

Located in `/tests/test_*.py`:

- `test_auth.py` - Authentication endpoint tests
- `test_users.py` - User management tests
- `test_tenants.py` - Tenant CRUD tests
- `test_tenant_isolation.py` - Multi-tenant isolation tests

**Example Test:**

```python
def test_create_user(client, test_tenant):
    response = client.post("/api/v1/auth/register", json={
        "email": "test@example.com",
        "full_name": "Test User",
        "password": "testpass123",
        "role": "admin",
        "tenant_id": test_tenant.id
    })
    assert response.status_code == 201
    assert response.json()["email"] == "test@example.com"
```

**See:** [/tests/README.md](../../tests/README.md) for comprehensive testing guide.

## Documentation

### OpenAPI/Swagger

**Access at:** <http://localhost:8000/docs>

**Features:**

- Interactive API explorer
- Try endpoints directly
- View request/response schemas
- Authentication support
- Auto-generated from code

### ReDoc

**Access at:** <http://localhost:8000/redoc>

**Features:**

- Clean, organized layout
- Better for reading documentation
- Printable format
- Search functionality

## Performance Optimization

### Pagination

```python
@router.get("/users")
def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=100),
    db: Session = Depends(get_db)
):
    return db.query(User).offset(skip).limit(limit).all()
```

### Query Optimization

- Index on tenant_id for fast filtering
- Limit result sets
- Avoid N+1 queries with eager loading
- Use selective column queries when possible

### Future Enhancements

- Response caching with Redis
- ETags for conditional requests
- Compression for large responses
- Rate limiting per tenant

## Versioning Strategy

### Current Approach

**URL-based versioning:**

- `/api/v1/...` - Current version
- `/api/v2/...` - Future version (when needed)

### When to Create v2

Breaking changes that warrant a new version:

- Changed response formats
- Removed endpoints
- Changed authentication mechanism
- Major structural changes

### Non-breaking Changes (Stay in v1)

- New endpoints
- New optional fields
- Bug fixes
- Performance improvements

## Future Endpoints (v1)

### Planned Features

**Invoice Management:**

```bash
POST   /api/v1/invoices
GET    /api/v1/invoices
GET    /api/v1/invoices/{id}
PUT    /api/v1/invoices/{id}
DELETE /api/v1/invoices/{id}
```

**Branch Management:**

```bash
POST   /api/v1/branches
GET    /api/v1/branches
GET    /api/v1/branches/{id}
PUT    /api/v1/branches/{id}
DELETE /api/v1/branches/{id}
```

**Analytics:**

```bash
GET /api/v1/analytics/revenue
GET /api/v1/analytics/invoices
GET /api/v1/analytics/users
```

**Exports:**

```bash
GET /api/v1/exports/invoices/csv
GET /api/v1/exports/invoices/json
```

## Related Documentation

- [Endpoints README](endpoints/README.md) - Detailed endpoint documentation
- [API Overview](../README.md) - API layer overview
- [Authentication](../../docs/authentication.md) - Auth implementation
- [API Structure](../../docs/API_STRUCTURE.md) - Visual API overview
- [Testing Guide](../../tests/README.md) - API testing

## License

MIT License - See [LICENSE](../../LICENSE) for details.
