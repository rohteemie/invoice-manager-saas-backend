# Core Directory (`/app/core`)

## Overview

This directory contains core application utilities and configurations that are used throughout the application. It houses essential functionality for security, configuration management, and dependency injection.

## Directory Structure

```bash
core/
├── config.py     # Application configuration and settings
├── deps.py       # Dependency injection functions
└── security.py   # Security utilities (JWT, password hashing)
```

## Modules

### Configuration (`config.py`)

Manages application configuration using Pydantic Settings for environment variable management.

**Key Configuration:**

- `PROJECT_NAME`: Application name for documentation
- `API_V1_STR`: API version prefix (default: "/api/v1")
- `DATABASE_URL`: Database connection string
- `SECRET_KEY`: Secret key for JWT token signing
- `ACCESS_TOKEN_EXPIRE_MINUTES`: Token expiration time (default: 30 minutes)
- `REFRESH_TOKEN_EXPIRE_DAYS`: Refresh token expiration (default: 7 days)
- `ALGORITHM`: JWT algorithm (default: "HS256")

**Usage:**

```python
from app.core.config import settings

# Access configuration
database_url = settings.DATABASE_URL
token_expire = settings.ACCESS_TOKEN_EXPIRE_MINUTES
```

**Environment Variables:**
Create a `.env` file with:

```env
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///./app.db
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

**Features:**

- Type-safe configuration
- Automatic environment variable loading
- Default values for optional settings
- Validation of required settings

### Security (`security.py`)

Provides security utilities following OWASP best practices.

#### Password Management

**Password Hashing:**

```python
from app.core.security import get_password_hash

hashed = get_password_hash("user_password")
# Returns bcrypt hashed password
```

**Password Verification:**

```python
from app.core.security import verify_password

is_valid = verify_password("plain_password", hashed_password)
# Returns True if password matches
```

**Implementation Details:**

- Uses `bcrypt` algorithm for secure password hashing
- Automatic salt generation
- Configurable work factor (cost)
- Resistant to rainbow table attacks

#### JWT Token Management

**Access Token Creation:**

```python
from app.core.security import create_access_token
from datetime import timedelta

token_data = {
    "sub": user.id,
    "tenant_id": user.tenant_id,
    "role": user.role
}

access_token = create_access_token(
    data=token_data,
    expires_delta=timedelta(minutes=30)
)
```

**Refresh Token Creation:**

```python
from app.core.security import create_refresh_token

refresh_token = create_refresh_token(
    data={"sub": user.id},
    expires_delta=timedelta(days=7)
)
```

**Token Decoding:**

```python
from app.core.security import decode_token

payload = decode_token(token_string)
# Returns: {"sub": "user-id", "tenant_id": "tenant-id", "role": "admin", "exp": 1234567890}
```

**Token Features:**

- JWT (JSON Web Tokens) for stateless authentication
- Configurable expiration times
- Role and tenant information embedded in token
- Signature verification for security
- Automatic expiration handling

**Security Considerations:**

- Tokens are signed with SECRET_KEY
- Cannot be tampered with without detection
- Include expiration timestamp (exp claim)
- Should be transmitted over HTTPS only

### Dependencies (`deps.py`)

Provides dependency injection functions for FastAPI endpoints.

#### Database Session Dependency

**get_db:**

```python
from app.core.deps import get_db
from fastapi import Depends

@router.get("/users")
def list_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    return users
```

**Features:**

- Yields database session for each request
- Automatically closes session after request
- Thread-safe scoped sessions
- Handles connection pooling

#### Authentication Dependencies

**get_current_user:**

```python
from app.core.deps import get_current_user
from fastapi import Depends

@router.get("/users/me")
def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user
```

**Flow:**

1. Extracts JWT token from Authorization header
2. Validates and decodes token
3. Queries database for user by ID
4. Verifies user is active
5. Returns user object

**Raises:**

- `401 Unauthorized` - Invalid or missing token
- `401 Unauthorized` - User not found or inactive

**get_current_active_user:**

```python
from app.core.deps import get_current_active_user

@router.get("/protected")
def protected_route(user: User = Depends(get_current_active_user)):
    # User is guaranteed to be active
    return {"message": "Access granted"}
```

Additional validation on top of `get_current_user`:

- Ensures user.is_active == True
- Raises 401 if user is deactivated

#### Role-Based Dependencies

**require_role:**

```python
from app.core.deps import require_role
from app.models.user import UserRole

# Owner only endpoint
@router.delete("/users/{user_id}")
def delete_user(
    user_id: str,
    current_user: User = Depends(require_role(UserRole.OWNER))
):
    # Only owners can access this
    pass
```

**Role Hierarchy:**

1. **Owner** - Full access (includes Admin privileges)
2. **Admin** - User management (includes Manager privileges)
3. **Manager** - Invoice/inventory management (includes Attendant privileges)
4. **Attendant** - Basic operations only

**Implementation:**

```python
def require_role(required_role: UserRole):
    def role_checker(current_user: User = Depends(get_current_user)):
        if not has_role(current_user, required_role):
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return current_user
    return role_checker
```

**has_role Function:**

```python
def has_role(user: User, required_role: UserRole) -> bool:
    """Check if user has required role (includes hierarchy)"""
    role_hierarchy = {
        UserRole.OWNER: [UserRole.OWNER, UserRole.ADMIN, UserRole.MANAGER, UserRole.ATTENDANT],
        UserRole.ADMIN: [UserRole.ADMIN, UserRole.MANAGER, UserRole.ATTENDANT],
        UserRole.MANAGER: [UserRole.MANAGER, UserRole.ATTENDANT],
        UserRole.ATTENDANT: [UserRole.ATTENDANT]
    }
    return required_role in role_hierarchy.get(user.role, [])
```

## Security Architecture

### Authentication Flow

```bash
1. User Login
   └─> Validate credentials
       └─> Generate JWT tokens
           └─> Return access + refresh tokens

2. Protected Request
   └─> Extract Bearer token
       └─> Verify signature
           └─> Check expiration
               └─> Load user from DB
                   └─> Verify active status
                       └─> Grant access
```

### Authorization Flow

```bash
1. Request to Protected Endpoint
   └─> Authenticate user (get_current_user)
       └─> Check role requirements (require_role)
           └─> Verify role hierarchy
               └─> Grant/Deny access
```

### Token Security

**Access Token:**

- Short-lived (30 minutes default)
- Contains user ID, tenant ID, and role
- Used for API authentication
- Cannot be revoked (stateless)

**Refresh Token:**

- Long-lived (7 days default)
- Contains only user ID
- Used to obtain new access tokens
- Should be stored securely

**Best Practices:**

- Access tokens in memory only
- Refresh tokens in httpOnly cookies
- Always use HTTPS in production
- Rotate refresh tokens on use

## Dependency Injection Pattern

FastAPI's dependency injection system provides:

### 1. Automatic Execution

```python
# Dependency is automatically called
def endpoint(db: Session = Depends(get_db)):
    pass
```

### 2. Nested Dependencies

```python
# Dependencies can depend on other dependencies
def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    pass
```

### 3. Reusability

```python
# Same dependency used across multiple endpoints
@router.get("/users", dependencies=[Depends(get_current_user)])
@router.post("/users", dependencies=[Depends(get_current_user)])
```

### 4. Testing

```python
# Dependencies can be overridden in tests
app.dependency_overrides[get_db] = override_get_db
```

## Usage Examples

### Secure Endpoint Example

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.deps import get_db, require_role
from app.models.user import UserRole, User

router = APIRouter()

@router.get("/admin/users")
def list_all_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN))
):
    """Only admins and owners can access this endpoint"""
    users = db.query(User).filter(
        User.tenant_id == current_user.tenant_id
    ).all()
    return users
```

### Multi-Tenant Query Example

```python
from app.core.deps import get_current_user

@router.get("/invoices")
def get_invoices(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Automatically filtered by user's tenant"""
    invoices = db.query(Invoice).filter(
        Invoice.tenant_id == current_user.tenant_id
    ).all()
    return invoices
```

### Password Update Example

```python
from app.core.security import verify_password, get_password_hash

@router.put("/users/me/password")
def update_password(
    old_password: str,
    new_password: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not verify_password(old_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect password")

    current_user.hashed_password = get_password_hash(new_password)
    db.commit()
    return {"message": "Password updated successfully"}
```

## Configuration Best Practices

### Environment-Specific Settings

**Development (.env.dev):**

```env
DATABASE_URL=sqlite:///./dev.db
SECRET_KEY=dev-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES=1440  # 24 hours for development
```

**Production (.env.prod):**

```env
DATABASE_URL=postgresql://user:pass@localhost/prod_db
SECRET_KEY=very-secure-production-key
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### Secret Key Generation

```bash
# Generate secure secret key
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Security Checklist

- ✅ Use strong SECRET_KEY in production
- ✅ Set appropriate token expiration times
- ✅ Enable HTTPS in production
- ✅ Store passwords as hashed only
- ✅ Validate user input with Pydantic
- ✅ Implement rate limiting (planned)
- ✅ Enable CORS appropriately
- ✅ Use environment variables for secrets

## Testing

### Testing Dependencies

```python
from app.core.deps import get_db

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
```

### Testing Authentication

```python
from app.core.security import create_access_token

def test_protected_endpoint():
    token = create_access_token(data={"sub": user.id})
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/protected", headers=headers)
    assert response.status_code == 200
```

## Related Documentation

- [API Endpoints](../api/README.md) - Using dependencies in endpoints
- [Authentication Guide](../../docs/authentication.md) - Detailed auth flow
- [Models](../models/README.md) - User and Tenant models
- [Testing](../../tests/README.md) - Testing with dependencies

## Future Enhancements

- **Rate Limiting**: Token bucket or sliding window
- **Email Verification**: Email confirmation tokens
- **Password Reset**: Secure password reset flow
- **OAuth2 Integration**: Social login support
- **API Key Authentication**: Alternative to JWT for services
- **Audit Logging**: Dependency for automatic action logging

## License

MIT License - See [LICENSE](../../LICENSE) for details.
