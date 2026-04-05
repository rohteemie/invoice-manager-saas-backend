# Super Admin Role & Platform Management

## Overview

The Super Admin role provides platform-level access for managing the entire SaaS platform across all tenants. Unlike tenant-scoped roles (Owner, Admin, Manager, Attendant), Super Admins have global control capabilities.

## Key Features

### Super Admin Characteristics

- **Platform-Level Access**: Not tied to any specific tenant (tenant_id = null)
- **Bypasses Role Checks**: Automatically granted access to all tenant-level operations
- **Dedicated Endpoints**: Exclusive access to `/admin/*` routes
- **Global Visibility**: Can view and manage all tenants, users, and audit logs

### Database Schema Changes

**User Model Updates:**
- Added `is_superadmin` boolean field (default: False, indexed)
- Made `tenant_id` nullable for Super Admin users
- Migration: `add_superadmin_field_and_nullable_tenant.py`

**Token Payload Updates:**
- JWT tokens now include `is_superadmin` flag
- Used for authentication and authorization checks

## API Endpoints

All Super Admin endpoints require the `is_superadmin=True` flag. Accessing these endpoints with a normal user account results in a `403 Forbidden` response.

### Tenant Management

#### List All Tenants
```
GET /api/v1/admin/tenants
```
Query parameters:
- `skip` (int): Pagination offset (default: 0)
- `limit` (int): Results per page (max: 1000, default: 100)
- `is_active` (bool): Filter by active status

#### Get Tenant Details
```
GET /api/v1/admin/tenants/{tenant_id}
```

#### Suspend Tenant
```
PUT /api/v1/admin/tenants/{tenant_id}/suspend
```
Sets tenant's `is_active` to False and logs the action.

#### Reactivate Tenant
```
PUT /api/v1/admin/tenants/{tenant_id}/reactivate
```
Sets tenant's `is_active` to True and logs the action.

### User Management

#### List All Users
```
GET /api/v1/admin/users
```
Query parameters:
- `skip` (int): Pagination offset (default: 0)
- `limit` (int): Results per page (max: 1000, default: 100)
- `tenant_id` (string): Filter by tenant
- `is_active` (bool): Filter by active status
- `is_superadmin` (bool): Filter by superadmin status

### Audit Logs

#### List Platform-Wide Audit Logs
```
GET /api/v1/admin/audit-logs
```
Query parameters:
- `skip` (int): Pagination offset (default: 0)
- `limit` (int): Results per page (max: 1000, default: 100)
- `tenant_id` (string): Filter by tenant
- `user_id` (string): Filter by user
- `action` (string): Filter by action type

### Platform Statistics

#### Get Platform Stats
```
GET /api/v1/admin/stats
```
Returns aggregated statistics:
- `total_tenants`: Total number of tenants
- `active_tenants`: Number of active tenants
- `suspended_tenants`: Number of suspended tenants
- `total_users`: Total number of users
- `active_users`: Number of active users
- `inactive_users`: Number of inactive users
- `superadmins_count`: Number of super admin users

## Creating a Super Admin

### Registration
```bash
POST /api/v1/auth/register
Content-Type: application/json

{
  "email": "admin@platform.com",
  "full_name": "Platform Administrator",
  "password": "SecurePassword123",
  "role": "attendant",
  "tenant_id": null,
  "is_superadmin": true
}
```

**Note**: For security, consider implementing additional verification for super admin registration in production (e.g., require invitation codes, multi-factor authentication, or manual approval).

### Login
Super Admins log in using the standard login endpoint:
```bash
POST /api/v1/auth/login
Content-Type: application/x-www-form-urlencoded

username=admin@platform.com&password=SecurePassword123
```

The returned JWT token will include `"is_superadmin": true` in the payload.

## Security Considerations

### Access Control
1. **Dependency Injection**: The `require_superadmin` dependency is used to protect all admin endpoints
2. **Token Validation**: JWT tokens are verified to contain `is_superadmin: true`
3. **Role Bypass**: Super Admins automatically bypass tenant-level role checks via updated `require_role` logic

### Implementation Details

**deps.py - Access Control:**
```python
def require_superadmin(
    current_user: User = Depends(get_current_user)
) -> User:
    if not current_user.is_superadmin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super admin access required"
        )
    return current_user
```

**Role Check Update:**
```python
def role_checker(current_user: User = Depends(get_current_user)) -> User:
    # Superadmins bypass all role checks
    if current_user.is_superadmin:
        return current_user
    # ... rest of role hierarchy check
```

### Audit Logging
All Super Admin actions are logged in the audit log system:
- Tenant suspensions/reactivations
- Cross-tenant data access
- Platform-wide operations

### Production Recommendations
1. **Limit Super Admin Accounts**: Create only necessary super admin accounts
2. **Strong Authentication**: Enforce strong passwords and consider MFA
3. **Monitoring**: Set up alerts for super admin activities
4. **Audit Trails**: Regularly review super admin audit logs
5. **Separate Registration**: Consider a separate, secured registration process for super admins

## Testing

The implementation includes comprehensive test coverage in `tests/test_superadmin.py`:

- Access control (403 for non-superadmins)
- Tenant management (suspend/reactivate)
- Cross-tenant user viewing
- Audit log access
- Platform statistics
- Pagination and filtering
- JWT token validation
- Registration validation

Run tests:
```bash
pytest tests/test_superadmin.py -v
```

## Example Usage

### Scenario: Monitor Platform Activity

1. **Login as Super Admin**
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@platform.com&password=SecurePassword123"
```

2. **View Platform Statistics**
```bash
curl -X GET http://localhost:8000/api/v1/admin/stats \
  -H "Authorization: Bearer {access_token}"
```

3. **List All Tenants**
```bash
curl -X GET http://localhost:8000/api/v1/admin/tenants?limit=50 \
  -H "Authorization: Bearer {access_token}"
```

4. **Suspend a Problematic Tenant**
```bash
curl -X PUT http://localhost:8000/api/v1/admin/tenants/{tenant_id}/suspend \
  -H "Authorization: Bearer {access_token}"
```

5. **Review Audit Logs**
```bash
curl -X GET http://localhost:8000/api/v1/admin/audit-logs?action=tenant_updated \
  -H "Authorization: Bearer {access_token}"
```

## Migration Guide

To apply the database changes:

```bash
# Apply migration
alembic upgrade head
```

The migration adds:
- `is_superadmin` column to users table (default: False)
- Index on `is_superadmin` for query performance
- Makes `tenant_id` nullable (SQLite compatibility handled)

## Future Enhancements

Potential additions to Super Admin functionality:
- Subscription/plan management endpoints
- Billing and payment oversight
- System-wide configuration management
- Advanced analytics and reporting
- Tenant resource usage monitoring
- Automated tenant lifecycle management
