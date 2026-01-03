# Schemas Directory (`/app/schemas`)

## Overview

This directory contains Pydantic schemas (models) used for request validation and response serialization in the FastAPI application. Schemas ensure type safety, data validation, and automatic API documentation generation.

## Directory Structure

```bash
schemas/
├── __init__.py      # Schema exports
├── tenant.py        # Tenant-related schemas
├── user.py          # User-related schemas (authentication & management)
├── invoice.py       # Invoice and invoice item schemas
├── analytics.py     # Analytics and reporting schemas
├── audit_log.py     # Audit logging schemas
├── pagination.py    # Pagination response schemas
└── error.py         # Error response schemas
```

## Purpose of Schemas

Pydantic schemas serve multiple purposes in the application:

1. **Request Validation**: Validate incoming API request data
2. **Response Serialization**: Format database models for API responses
3. **Type Safety**: Provide compile-time and runtime type checking
4. **API Documentation**: Auto-generate OpenAPI/Swagger documentation
5. **Data Transformation**: Convert between different data representations

## Schema Patterns

### Base Schemas

Define common fields shared across create/update operations:

```python
class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    role: UserRole
```

### Create Schemas

Used for creating new resources (include required fields):

```python
class UserCreate(UserBase):
    password: str  # Only present during creation
    tenant_id: str
```

### Update Schemas

Used for updating existing resources (all fields optional):

```python
class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    role: Optional[UserRole] = None
```

### Database Schemas

Represent data as stored in the database:

```python
class UserInDB(UserBase):
    id: str
    tenant_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True  # Enable ORM mode
```

### Response Schemas

Used for API responses (exclude sensitive data):

```python
class User(UserInDB):
    pass  # Inherits all fields except password
```

## Tenant Schemas (`tenant.py`)

### TenantBase

Base schema with common tenant fields:

- `name`: String - Tenant name (1-100 characters)
- `domain`: Optional[String] - Unique domain identifier
- `plan_type`: String - Subscription plan (default: "free")
- `description`: Optional[String] - Tenant description (max 500 characters)

### TenantCreate

Schema for creating a new tenant:

- Inherits all fields from `TenantBase`
- All fields are required except `domain` and `description`

**Usage Example:**

```python
{
    "name": "Acme Corporation",
    "domain": "acme",
    "plan_type": "enterprise",
    "description": "Global manufacturing company"
}
```

### TenantUpdate

Schema for updating tenant information:

- All fields are optional
- Only provided fields will be updated

**Usage Example:**

```python
{
    "plan_type": "pro",
    "description": "Updated description"
}
```

### TenantInDB

Database representation of a tenant:

- Includes: id, is_active, created_at, updated_at
- Configured with `from_attributes = True` for SQLAlchemy compatibility

### Tenant

Public tenant schema for API responses:

- Inherits from `TenantInDB`
- Includes all tenant fields including metadata

## User Schemas (`user.py`)

### UserBase

Base schema with common user fields:

- `email`: EmailStr - Validated email address
- `full_name`: String - User's full name (1-100 characters)
- `role`: UserRole - Enum (owner, admin, manager, attendant)

### UserCreate

Schema for user registration:

- Inherits from `UserBase`
- `password`: String - Plain password (min 8 characters, max 100)
- `tenant_id`: String - Associated tenant UUID

**Validation Rules:**

- Email format validated automatically
- Password minimum length: 8 characters
- Full name cannot be empty

**Usage Example:**

```python
{
    "email": "admin@acme.com",
    "full_name": "Jane Admin",
    "password": "SecurePass123!",
    "role": "admin",
    "tenant_id": "tenant-uuid-here"
}
```

### UserUpdate

Schema for updating user information:

- All fields are optional
- `full_name`: Optional[String]
- `role`: Optional[UserRole]
- `is_active`: Optional[Boolean] - For soft deletion
- `is_verified`: Optional[Boolean] - For email verification

**Usage Example:**

```python
{
    "role": "manager",
    "is_verified": true
}
```

### UserInDB

Database representation with all fields:

- Includes: id, tenant_id, is_active, is_verified, timestamps
- Configured with `from_attributes = True`
- Excludes `hashed_password` from serialization

### User

Public user schema for API responses:

- Inherits from `UserInDB`
- Safe for external consumption (no password)

**Response Example:**

```python
{
    "id": "user-uuid",
    "email": "admin@acme.com",
    "full_name": "Jane Admin",
    "role": "admin",
    "tenant_id": "tenant-uuid",
    "is_active": true,
    "is_verified": true,
    "created_at": "2024-01-15T10:30:00",
    "updated_at": "2024-01-15T10:30:00"
}
```

### UserLogin

Schema for login credentials:

- `email`: EmailStr - User's email address
- `password`: String - Plain password

**Usage Example:**

```python
{
    "email": "admin@acme.com",
    "password": "SecurePass123!"
}
```

### Token

Schema for JWT token responses:

- `access_token`: String - JWT access token
- `refresh_token`: String - JWT refresh token
- `token_type`: String - Token type (default: "bearer")

**Response Example:**

```python
{
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
    "token_type": "bearer"
}
```

### TokenPayload

Internal schema for JWT token payload:

- `sub`: String - Subject (user_id)
- `tenant_id`: String - User's tenant ID
- `role`: String - User's role
- `exp`: int - Expiration timestamp

## Invoice Schemas (`invoice.py`)

Schemas for invoice management with multi-currency support and status lifecycle.

### Invoice

Main invoice schema with all fields:

- `id`: String - Invoice UUID
- `invoice_number`: String - Unique invoice number
- `tenant_id`: String - Tenant UUID
- `branch_id`: Optional[String] - Branch location identifier
- `customer_name`: String - Customer name
- `customer_email`: Optional[String] - Customer email
- `customer_phone`: Optional[String] - Customer phone
- `customer_address`: Optional[String] - Customer address
- `creator_id`: String - User who created the invoice
- `status`: InvoiceStatus - Current invoice status (draft/sent/paid/overdue)
- `issue_date`: String - Issue date
- `due_date`: Optional[String] - Payment due date
- `currency`: Currency - Invoice currency (USD/EUR/GBP/NGN)
- `subtotal`: Decimal - Subtotal before tax
- `tax_amount`: Decimal - Tax amount
- `discount_amount`: Decimal - Discount amount
- `total_amount`: Decimal - Final total
- `items`: List[InvoiceItem] - Invoice line items

### InvoiceCreate

Schema for creating new invoices:

- All required fields from Invoice
- Includes items list for creating invoice with line items
- Validates currency and tax calculations

### InvoiceItem

Line item schema:

- `description`: String - Item description
- `quantity`: Decimal - Quantity
- `unit_price`: Decimal - Price per unit
- `currency`: Currency - Item currency
- `total_price`: Decimal - Total (quantity × unit_price)

### InvoiceStatus

Status enum for invoice lifecycle:

- `DRAFT`: Initial state, can be edited
- `SENT`: Sent to customer, awaiting payment
- `PAID`: Payment received
- `OVERDUE`: Past due date, not paid

### Currency

Supported currencies:

- `USD`: US Dollar
- `EUR`: Euro
- `GBP`: British Pound
- `NGN`: Nigerian Naira

## Analytics Schemas (`analytics.py`)

Schemas for reporting and analytics endpoints.

### InvoiceSummary

Tenant-level invoice statistics:

- `total_invoices`: int - Total invoice count
- `draft_count`: int - Invoices in draft status
- `sent_count`: int - Invoices sent to customers
- `paid_count`: int - Paid invoices
- `overdue_count`: int - Overdue invoices
- `total_revenue`: Decimal - Total revenue (paid invoices)
- `pending_revenue`: Decimal - Revenue from unpaid invoices

### RevenueByStatus

Revenue breakdown by invoice status:

- `status`: String - Invoice status
- `count`: int - Number of invoices
- `total_amount`: Decimal - Total amount for this status

## Audit Log Schemas (`audit_log.py`)

Schemas for audit trail and activity tracking.

### AuditLog

Complete audit log entry:

- `id`: String - Audit log UUID
- `user_id`: Optional[String] - User who performed action
- `tenant_id`: Optional[String] - Associated tenant
- `action`: AuditAction - Action type (LOGIN, USER_CREATED, etc.)
- `resource_type`: ResourceType - Resource type (USER, TENANT, INVOICE)
- `resource_id`: Optional[String] - ID of affected resource
- `ip_address`: String - Client IP address
- `user_agent`: String - Client user agent
- `description`: String - Human-readable description
- `status`: String - Action status (success/failure)
- `created_at`: DateTime - Timestamp

### AuditAction

Enumeration of auditable actions including authentication events, user management, tenant management, invoice operations, and data exports.

### ResourceType

Enumeration of resource types: USER, TENANT, INVOICE, INVOICE_ITEM, AUTH, EXPORT.

## Pagination Schemas (`pagination.py`)

Generic pagination response wrapper.

### PaginatedResponse[T]

Generic paginated response:

- `items`: List[T] - Items in current page
- `total`: int - Total item count
- `page`: int - Current page number (1-indexed)
- `size`: int - Items per page
- `pages`: int - Total number of pages
- `has_next`: bool - Whether there is a next page
- `has_previous`: bool - Whether there is a previous page

Used for all list endpoints to provide consistent pagination.

## Error Schemas (`error.py`)

Standardized error response schemas.

### ErrorResponse

Standard error format:

- `detail`: String or Dict - Error message or validation errors
- `status_code`: int - HTTP status code
- `error_type`: String - Error type classification

Ensures consistent error responses across all endpoints.

## Validation Features

### Field Validation

**Email Validation:**

```python
from pydantic import EmailStr

email: EmailStr  # Automatically validates email format
```

**String Length:**

```python
from pydantic import Field

full_name: str = Field(..., min_length=1, max_length=100)
```

**Password Complexity:**

```python
password: str = Field(..., min_length=8, max_length=100)
```

### Custom Validators

Pydantic supports custom validators for complex validation logic:

```python
from pydantic import validator

class UserCreate(BaseModel):
    password: str

    @validator('password')
    def password_strength(cls, v):
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain uppercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain digit')
        return v
```

## ORM Mode Configuration

Schemas use `from_attributes = True` to work with SQLAlchemy models:

```python
class Config:
    from_attributes = True  # Enables ORM mode (Pydantic v2)
```

This allows:

- Automatic conversion from SQLAlchemy models to Pydantic schemas
- Attribute access instead of dictionary access
- Seamless integration with FastAPI response models

## Usage in Endpoints

### Request Validation

```python
@router.post("/users", response_model=User)
def create_user(user_in: UserCreate, db: Session = Depends(get_db)):
    # user_in is automatically validated
    hashed_password = get_password_hash(user_in.password)
    db_user = UserModel(**user_in.dict(exclude={'password'}),
                        hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    return db_user
```

### Response Serialization

```python
@router.get("/users/me", response_model=User)
def get_current_user(current_user: UserModel = Depends(get_current_user)):
    # UserModel is automatically converted to User schema
    return current_user
```

### Error Handling

Pydantic automatically returns 422 Unprocessable Entity for validation errors:

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

## API Documentation

Schemas automatically generate OpenAPI documentation with:

- Field descriptions
- Data types
- Validation rules
- Example values
- Required/optional indicators

**Example in Swagger UI:**

- Field names and types are displayed
- Validation constraints are documented
- Example requests/responses are auto-generated

## Best Practices

### 1. Separate Create and Update Schemas

```python
# Create: All required fields
class UserCreate(UserBase):
    password: str
    tenant_id: str

# Update: All optional fields
class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    role: Optional[UserRole] = None
```

### 2. Never Expose Passwords

```python
# ✅ Good: Password only in UserCreate
class UserCreate(BaseModel):
    password: str

# ❌ Bad: Password in response schema
class User(BaseModel):
    password: str  # Never do this!
```

### 3. Use Descriptive Field Names

```python
email: EmailStr = Field(..., description="User's email address")
```

### 4. Validate at Schema Level

```python
# Validation happens before reaching the endpoint
user_in: UserCreate  # Auto-validated
```

### 5. Reuse Base Schemas

```python
class UserBase(BaseModel):
    email: EmailStr
    full_name: str

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: str
```

## Schema Inheritance Hierarchy

```bash
BaseModel (Pydantic)
    │
    ├── TenantBase
    │   ├── TenantCreate
    │   ├── TenantUpdate
    │   └── TenantInDB
    │       └── Tenant
    │
    └── UserBase
        ├── UserCreate
        ├── UserUpdate
        └── UserInDB
            └── User
```

## Testing Schemas

Schemas are tested indirectly through API endpoint tests:

- Input validation tests in `/tests/test_auth.py`
- Response serialization tests in `/tests/test_users.py`
- Error handling tests for invalid data

## Future Schemas

Planned schemas for upcoming features:

- **Invoice Schemas**: InvoiceCreate, InvoiceUpdate, Invoice
- **Branch Schemas**: BranchCreate, BranchUpdate, Branch
- **Customer Schemas**: CustomerCreate, CustomerUpdate, Customer
- **Analytics Schemas**: RevenueReport, InvoiceMetrics
- **Pagination Schemas**: PaginatedResponse, PageParams

## Related Documentation

- [Models Documentation](../models/README.md) - SQLAlchemy ORM models
- [API Endpoints](../api/README.md) - How schemas are used in endpoints
- [Authentication](../../docs/authentication.md) - Auth-related schemas
- [Pydantic Documentation](https://docs.pydantic.dev/) - Official Pydantic docs

## License

MIT License - See [LICENSE](../../LICENSE) for details.
