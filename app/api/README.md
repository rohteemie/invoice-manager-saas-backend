# API Directory (`/app/api`)

## Overview

This directory contains all API routing and endpoint definitions for the Multi-Tenant SaaS Backend. The API is versioned and organized by feature domain for maintainability and scalability.

## Directory Structure

```
api/
├── __init__.py     # Package initialization
└── v1/             # API Version 1
    ├── __init__.py
    ├── api.py      # Main router aggregation
    └── endpoints/  # Feature-specific endpoint handlers
        ├── __init__.py
        ├── auth.py      # Authentication endpoints
        ├── tenants.py   # Tenant management endpoints
        └── users.py     # User management endpoints
```

## API Versioning

The application uses URL-based versioning for backward compatibility:

**Current Version:** v1 (prefix: `/api/v1`)

**Version Strategy:**
- Breaking changes require a new version
- Non-breaking changes added to current version
- Old versions deprecated gracefully
- Clear migration paths documented

**Example URLs:**
```
/api/v1/auth/login
/api/v1/tenants
/api/v1/users/me
```

## Router Aggregation (`v1/api.py`)

The main API router aggregates all feature routers:

```python
from fastapi import APIRouter
from app.api.v1.endpoints import tenants, auth, users

api_router = APIRouter()
api_router.include_router(tenants.router, prefix="/tenants", tags=["tenants"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
```

**Router Configuration:**
- `prefix`: URL prefix for all routes in the router
- `tags`: OpenAPI tags for documentation grouping

**Included in main app:**
```python
# In app/main.py
app.include_router(api_router, prefix=settings.API_V1_STR)
```

## API Endpoints

### Authentication (`endpoints/auth.py`)

**Tag:** `auth`

Handles user authentication and token management.

#### POST `/api/v1/auth/register`
Register a new user account.

**Request Body:**
```json
{
  "email": "user@example.com",
  "full_name": "John Doe",
  "password": "SecurePass123",
  "role": "admin",
  "tenant_id": "tenant-uuid"
}
```

**Response:** User object (without password)
**Status Codes:** 201 Created, 400 Bad Request

#### POST `/api/v1/auth/login`
Authenticate user and receive JWT tokens.

**Request (Form Data):**
```
username=user@example.com
password=SecurePass123
```

**Response:**
```json
{
  "access_token": "eyJhbGc...",
  "refresh_token": "eyJhbGc...",
  "token_type": "bearer"
}
```

**Status Codes:** 200 OK, 401 Unauthorized

#### POST `/api/v1/auth/refresh`
Refresh access token using refresh token.

**Request:**
```json
{
  "refresh_token": "eyJhbGc..."
}
```

**Response:**
```json
{
  "access_token": "eyJhbGc...",
  "token_type": "bearer"
}
```

**Status Codes:** 200 OK, 401 Unauthorized

**See:** [endpoints/README.md](v1/endpoints/README.md) for detailed endpoint documentation.

### Tenant Management (`endpoints/tenants.py`)

**Tag:** `tenants`

Manages tenant (organization) lifecycle.

#### POST `/api/v1/tenants`
Create a new tenant.

**Authentication:** Not required (public registration)

#### GET `/api/v1/tenants`
List all tenants (paginated).

**Query Parameters:**
- `skip`: Offset (default: 0)
- `limit`: Page size (default: 100)

#### GET `/api/v1/tenants/{tenant_id}`
Get tenant by ID.

#### PUT `/api/v1/tenants/{tenant_id}`
Update tenant information.

#### DELETE `/api/v1/tenants/{tenant_id}`
Soft delete a tenant.

**See:** [endpoints/README.md](v1/endpoints/README.md) for detailed endpoint documentation.

### User Management (`endpoints/users.py`)

**Tag:** `users`

Manages users within tenants with role-based access control.

#### GET `/api/v1/users/me`
Get current authenticated user.

**Authentication:** Required
**Authorization:** Any authenticated user

#### GET `/api/v1/users`
List users in current user's tenant.

**Authentication:** Required
**Authorization:** Admin or Owner

#### GET `/api/v1/users/{user_id}`
Get user by ID (tenant-scoped).

**Authentication:** Required
**Authorization:** Admin or Owner

#### PUT `/api/v1/users/{user_id}`
Update user information.

**Authentication:** Required
**Authorization:** Admin or Owner

#### DELETE `/api/v1/users/{user_id}`
Soft delete a user.

**Authentication:** Required
**Authorization:** Owner only

**See:** [endpoints/README.md](v1/endpoints/README.md) for detailed endpoint documentation.

## API Design Patterns

### RESTful Design

**Resource-Based URLs:**
```
/api/v1/tenants          # Collection
/api/v1/tenants/{id}     # Specific resource
/api/v1/users/me         # Special resource
```

**HTTP Methods:**
- `GET`: Retrieve resources
- `POST`: Create new resources
- `PUT`: Update resources (full replacement)
- `PATCH`: Partial update (not yet implemented)
- `DELETE`: Soft delete resources

### Response Formats

**Success Response:**
```json
{
  "id": "uuid",
  "field": "value",
  "created_at": "2024-01-15T10:30:00",
  "updated_at": "2024-01-15T10:30:00"
}
```

**Error Response:**
```json
{
  "detail": "Error message here"
}
```

**Validation Error:**
```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "value is not a valid email address",
      "type": "value_error.email"
    }
  ]
}
```

### Status Codes

**Success:**
- `200 OK`: Successful GET, PUT, DELETE
- `201 Created`: Successful POST
- `204 No Content`: Successful DELETE (no body)

**Client Errors:**
- `400 Bad Request`: Invalid input data
- `401 Unauthorized`: Missing or invalid authentication
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `422 Unprocessable Entity`: Validation error

**Server Errors:**
- `500 Internal Server Error`: Unexpected error

## Authentication & Authorization

### Authentication Flow

1. **Public Endpoints** (no auth required):
   - POST `/api/v1/auth/register`
   - POST `/api/v1/auth/login`
   - POST `/api/v1/tenants`

2. **Protected Endpoints** (JWT required):
   - All other endpoints require `Authorization: Bearer {token}`

### Authorization Levels

**Any Authenticated User:**
- GET `/api/v1/users/me`

**Admin or Owner:**
- GET `/api/v1/users`
- GET `/api/v1/users/{id}`
- PUT `/api/v1/users/{id}`

**Owner Only:**
- DELETE `/api/v1/users/{id}`

### Tenant Isolation

All endpoints automatically scope queries to the authenticated user's tenant:

```python
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

## API Documentation

### Interactive Documentation

**Swagger UI:** http://localhost:8000/docs
- Interactive API explorer
- Try out endpoints
- View request/response schemas
- Authentication support

**ReDoc:** http://localhost:8000/redoc
- Clean, organized documentation
- Better for reading
- Printable format

### OpenAPI Specification

**JSON Format:** http://localhost:8000/api/v1/openapi.json

**Features:**
- Complete API specification
- Machine-readable format
- Client generation support
- Integration with tools (Postman, Insomnia)

## Request Validation

All requests are validated using Pydantic schemas:

**Automatic Validation:**
- Type checking
- Required fields
- Field constraints (length, format)
- Enum validation
- Email format
- UUID format

**Example:**
```python
@router.post("/users", response_model=User)
def create_user(
    user_in: UserCreate,  # Automatically validated
    db: Session = Depends(get_db)
):
    # user_in is guaranteed to be valid
    pass
```

## Error Handling

### Standard Error Responses

```python
from fastapi import HTTPException

# Not Found
raise HTTPException(
    status_code=404,
    detail="User not found"
)

# Unauthorized
raise HTTPException(
    status_code=401,
    detail="Invalid credentials"
)

# Forbidden
raise HTTPException(
    status_code=403,
    detail="Insufficient permissions"
)
```

### Database Errors

```python
from sqlalchemy.exc import IntegrityError

try:
    db.add(db_user)
    db.commit()
except IntegrityError:
    db.rollback()
    raise HTTPException(
        status_code=400,
        detail="User already exists"
    )
```

## Testing

### Endpoint Testing

```python
def test_create_user(client):
    response = client.post("/api/v1/users", json={
        "email": "test@example.com",
        "full_name": "Test User",
        "password": "testpass",
        "tenant_id": "tenant-id"
    })
    assert response.status_code == 201
    assert response.json()["email"] == "test@example.com"
```

### Authentication Testing

```python
def test_protected_endpoint(client, auth_headers):
    response = client.get(
        "/api/v1/users/me",
        headers=auth_headers
    )
    assert response.status_code == 200
```

**See:** [/tests/README.md](../../tests/README.md) for comprehensive testing documentation.

## Performance Considerations

### Pagination

Implement pagination for list endpoints:

```python
@router.get("/users")
def list_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    users = db.query(User).offset(skip).limit(limit).all()
    return users
```

### Caching (Planned)

- Redis caching for frequently accessed data
- Cache invalidation on updates
- Cache keys include tenant_id

### Rate Limiting (Planned)

- Per-tenant rate limits
- Token bucket algorithm
- Redis for distributed rate limiting

## Security Best Practices

### Input Validation
- ✅ All inputs validated with Pydantic
- ✅ SQL injection prevention via ORM
- ✅ XSS prevention via JSON responses

### Authentication
- ✅ JWT tokens for stateless auth
- ✅ Secure password hashing (bcrypt)
- ✅ Token expiration
- ✅ HTTPS required in production

### Authorization
- ✅ Role-based access control
- ✅ Tenant isolation enforced
- ✅ Principle of least privilege

## Future API Features

### Planned Endpoints

**Invoice Management:**
- POST `/api/v1/invoices`
- GET `/api/v1/invoices`
- GET `/api/v1/invoices/{id}`
- PUT `/api/v1/invoices/{id}`
- DELETE `/api/v1/invoices/{id}`

**Analytics:**
- GET `/api/v1/analytics/revenue`
- GET `/api/v1/analytics/invoices`

**Exports:**
- GET `/api/v1/exports/invoices/csv`
- GET `/api/v1/exports/invoices/json`

### API v2 (Future)

Breaking changes will be introduced in v2:
- GraphQL support
- WebSocket endpoints for real-time updates
- Improved pagination (cursor-based)
- Enhanced filtering and sorting

## Related Documentation

- [Endpoints Documentation](v1/endpoints/README.md) - Detailed endpoint specs
- [Authentication Guide](../../docs/authentication.md) - Auth implementation details
- [API Structure](../../docs/API_STRUCTURE.md) - Visual API overview
- [Models](../models/README.md) - Data models
- [Schemas](../schemas/README.md) - Request/response validation

## License

MIT License - See [LICENSE](../../LICENSE) for details.
