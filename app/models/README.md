# Models Directory (`/app/models`)

## Overview

This directory contains SQLAlchemy ORM models that define the database schema for the Multi-Tenant SaaS Backend. These models represent the core data structures and relationships in the application.

## Directory Structure

```
models/
├── __init__.py           # Model registration and imports
├── general_model.py      # Base model with common fields
├── tenant.py             # Tenant model for multi-tenancy
└── user.py               # User model with RBAC
```

## Models

### Base Model (`general_model.py`)

The `Gen_Model` class provides common fields and functionality for all models:

**Common Fields:**
- `id`: String (UUID) - Primary key
- `created_at`: DateTime - Timestamp of record creation
- `updated_at`: DateTime - Timestamp of last update

**Features:**
- Automatic UUID generation for new records
- Automatic timestamp management
- Consistent field naming across all models
- Base class for SQLAlchemy declarative base

**Usage:**
```python
from app.models.general_model import Gen_Model, Base

class MyModel(Gen_Model, Base):
    __tablename__ = "my_table"
    # Additional fields...
```

### Tenant Model (`tenant.py`)

Represents organizations/companies in the multi-tenant architecture.

**Table:** `tenants`

**Fields:**
- `id`: String (UUID) - Primary key (inherited from Gen_Model)
- `name`: String(100) - Tenant name (required)
- `domain`: String(100) - Unique domain identifier (optional, unique)
- `plan_type`: String(20) - Subscription plan (default: "free")
- `description`: String(500) - Tenant description (optional)
- `is_active`: Boolean - Soft delete flag (default: True)
- `created_at`: DateTime - Creation timestamp (inherited)
- `updated_at`: DateTime - Update timestamp (inherited)

**Constraints:**
- Unique domain for each tenant
- NOT NULL on name field

**Use Cases:**
- Tenant onboarding and management
- Subscription plan tracking
- Tenant isolation and data segregation
- Soft deletion for GDPR compliance

**Example:**
```python
from app.models.tenant import Tenant

tenant = Tenant(
    name="Acme Corporation",
    domain="acme",
    plan_type="enterprise",
    description="Global manufacturing company"
)
```

### User Model (`user.py`)

Represents users within tenants with role-based access control.

**Table:** `users`

**Fields:**
- `id`: String (UUID) - Primary key (inherited from Gen_Model)
- `email`: String(255) - Unique email address (indexed)
- `full_name`: String(100) - User's full name (required)
- `hashed_password`: String(255) - Bcrypt hashed password (required)
- `role`: Enum(UserRole) - User role for RBAC (default: ATTENDANT)
- `tenant_id`: String(60) - Foreign key to tenants table (indexed)
- `is_active`: Boolean - Soft delete flag (default: True)
- `is_verified`: Boolean - Email verification status (default: False)
- `created_at`: DateTime - Creation timestamp (inherited)
- `updated_at`: DateTime - Update timestamp (inherited)

**UserRole Enum:**
```python
class UserRole(str, enum.Enum):
    OWNER = "owner"        # Full tenant management
    ADMIN = "admin"        # User and business management
    MANAGER = "manager"    # Invoice and inventory management
    ATTENDANT = "attendant"  # Basic operations only
```

**Relationships:**
- `tenant_id` → Foreign key to `tenants.id`
- Users belong to exactly one tenant (data isolation)

**Constraints:**
- Unique email address globally
- NOT NULL on email, full_name, hashed_password, role, tenant_id
- Foreign key constraint to tenants table
- Indexed on email and tenant_id for performance

**Security Features:**
- Password hashing with bcrypt (never store plain text)
- Soft deletion with `is_active` flag (GDPR compliance)
- Email verification support with `is_verified`
- Tenant isolation via foreign key

**Use Cases:**
- User authentication and authorization
- Role-based access control
- User management within tenants
- Audit trails and activity tracking

**Example:**
```python
from app.models.user import User, UserRole
from app.core.security import get_password_hash

user = User(
    email="admin@acme.com",
    full_name="Jane Admin",
    hashed_password=get_password_hash("secure_password"),
    role=UserRole.ADMIN,
    tenant_id="tenant-uuid-here"
)
```

## Database Relationships

```
┌─────────────────────┐
│      Tenants        │
│  (Organizations)    │
├─────────────────────┤
│ id (PK)             │
│ name                │
│ domain (unique)     │
│ plan_type           │
│ is_active           │
└──────────┬──────────┘
           │
           │ 1:N
           │
┌──────────▼──────────┐
│       Users         │
│   (Employees)       │
├─────────────────────┤
│ id (PK)             │
│ email (unique)      │
│ full_name           │
│ hashed_password     │
│ role (enum)         │
│ tenant_id (FK)      │
│ is_active           │
│ is_verified         │
└─────────────────────┘
```

## Data Isolation Strategy

### Tenant Isolation
- All user records include a `tenant_id` foreign key
- API queries filter by authenticated user's `tenant_id`
- Cross-tenant access is prevented at the application layer
- Database constraints ensure referential integrity

### Security Considerations
- Foreign key constraints prevent orphaned records
- Soft deletes preserve data for audit purposes
- Indexed fields optimize tenant-scoped queries
- Role hierarchy enforced at application layer

## Common Patterns

### Creating a New Model

1. Inherit from `Gen_Model` and `Base`:
```python
from app.models.general_model import Gen_Model, Base
from sqlalchemy import Column, String, ForeignKey

class MyModel(Gen_Model, Base):
    __tablename__ = "my_table"
    
    name = Column(String(100), nullable=False)
    tenant_id = Column(String(60), ForeignKey("tenants.id"), nullable=False)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
```

2. Register in `__init__.py`:
```python
from app.models.my_model import MyModel
```

3. Database will auto-create table on next startup

### Querying with Tenant Isolation

```python
# Get all users for a specific tenant
users = db.query(User).filter(User.tenant_id == current_tenant_id).all()

# Get specific user within tenant
user = db.query(User).filter(
    User.id == user_id,
    User.tenant_id == current_tenant_id
).first()
```

### Soft Deletion

```python
# Soft delete a user
user.is_active = False
db.commit()

# Query only active records
active_users = db.query(User).filter(
    User.tenant_id == tenant_id,
    User.is_active == True
).all()
```

## Model Registration

All models are registered in `__init__.py` to ensure they are discovered by SQLAlchemy:

```python
from app.models.general_model import Base
from app.models.tenant import Tenant
from app.models.user import User

# Models are now registered and available for import
```

## Database Initialization

Models are automatically synchronized with the database on application startup via `app.db.database.init_db()`:

```python
from app.models.general_model import Base
from app.db.database import engine

Base.metadata.create_all(bind=engine)
```

## Migration Strategy

### Current Approach
- SQLAlchemy auto-creates tables on startup
- Suitable for development and testing
- Schema changes require manual database cleanup

### Future Approach (Planned)
- Alembic migrations for production
- Version-controlled schema changes
- Safe migrations with rollback support
- Zero-downtime deployments

## GDPR Compliance

### Right to be Forgotten
- Soft deletion with `is_active` flag
- Preserves audit trails while removing user access
- Can be hard-deleted after retention period

### Data Minimization
- Only essential fields are stored
- No sensitive data beyond hashed passwords
- Email used as primary identifier

### Audit Trails
- `created_at` and `updated_at` timestamps on all records
- Future: Audit log model for tracking changes

## Performance Considerations

### Indexes
- Primary keys (id) are automatically indexed
- Email field indexed for fast user lookups
- `tenant_id` indexed for efficient tenant-scoped queries

### Query Optimization
- Use select queries with appropriate filters
- Avoid N+1 queries with eager loading (when needed)
- Limit result sets with pagination

## Testing

Models are tested in `/tests/test_tenants.py` and `/tests/test_users.py`:
- CRUD operations
- Constraint validation
- Relationship integrity
- Soft deletion behavior

See [/tests/README.md](../../tests/README.md) for testing documentation.

## Related Documentation

- [Database Configuration](../db/README.md)
- [Schemas Documentation](../schemas/README.md)
- [API Endpoints](../api/README.md)
- [ERD Diagram](../../docs/erd_diagram.png)

## Future Models

Planned models for upcoming features:

- **Invoice**: Core business entity for invoice management
- **InvoiceItem**: Line items within invoices
- **Branch**: Physical locations within a tenant
- **Customer**: Customer information for invoices
- **AuditLog**: Tracking user actions for compliance
- **Subscription**: Detailed subscription management

## License

MIT License - See [LICENSE](../../LICENSE) for details.
