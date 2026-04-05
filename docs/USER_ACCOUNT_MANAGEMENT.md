# User Account Management Guide

## Overview

This document describes the user account management system in the multi-tenant SaaS backend, including role-based permissions, account deletion rules, and security policies.

## Table of Contents

1. [Role Hierarchy](#role-hierarchy)
2. [Account Management Rules](#account-management-rules)
3. [API Endpoints](#api-endpoints)
4. [Error Handling](#error-handling)
5. [Security Considerations](#security-considerations)
6. [Examples](#examples)

## Role Hierarchy

The system implements a four-tier role hierarchy:

```
OWNER (Highest)
  ↓
ADMIN
  ↓
MANAGER
  ↓
ATTENDANT (Lowest)
```

### Role Permissions

#### OWNER
- Full tenant/organization management
- **Exclusive ability** to manage users (create, read, update, delete)
- Can create users with ANY role, including other owners (co-owners) ✨ **NEW**
- Can upgrade/downgrade roles for non-owner users
- Can delete low-level users (Admin, Manager, Attendant)
- **Cannot** delete themselves
- **Cannot** delete other owners
- **Cannot** delete the organization
- All privileges of lower roles

#### ADMIN
- Full business operations access
- Manage invoices, reports, analytics
- **Cannot** manage users
- All privileges of Manager role

#### MANAGER
- Manage invoices and invoice lists
- View reports and analytics
- All privileges of Attendant role

#### ATTENDANT
- Create invoices
- View invoice inventory
- Basic operations only

## Account Management Rules

### User Creation Rules ✨ **NEW**

1. **Only owners can create user accounts**
   - Users are created via `POST /api/v1/users`
   - All roles can be assigned, including OWNER (for co-owners)
   - Users inherit the owner's tenant_id automatically

2. **Mandatory password change on first login**
   - All owner-created users have `must_change_password=true`
   - Login response includes `requires_password_change: true`
   - User must call `POST /api/v1/auth/force-change-password`
   - Password cannot be the same as the temporary password

3. **Pre-verified accounts**
   - Owner-created users are automatically marked as verified
   - No email verification required
   - Owners share temporary credentials out-of-band

4. **Co-owner support**
   - Owners can create additional owners (co-owners)
   - Useful for multi-partner businesses
   - Co-owners have identical privileges

### User Deletion Rules

1. **Only owners can delete user accounts**
   - Admins, Managers, and Attendants cannot delete any accounts
   - This ensures centralized control over user management

2. **Owners cannot delete themselves**
   - Self-deletion is prohibited to prevent accidental loss of admin access
   - Ensures at least one owner remains active in the organization

3. **Owners cannot delete other owners**
   - Prevents conflicts between co-owners
   - For owner account deletion, contact the technical team/developer organization

4. **Soft delete mechanism**
   - Users are marked as `is_active = False` instead of being removed from the database
   - Maintains audit trails and data integrity
   - GDPR-compliant right-to-be-forgotten implementation

### User Update Rules

1. **Only owners can update user information**
   - Non-owners cannot edit their own details
   - Non-owners cannot edit other users' details
   - This centralizes user management control

2. **Role change restrictions**
   - Owner role cannot be changed via API
   - Owner role cannot be assigned to any user via API
   - Prevents unauthorized privilege escalation

3. **Allowed updates for owners**
   - Full name
   - Role (except owner role)
   - Active status
   - Verification status

### Organization Deletion Rules

1. **Owners cannot delete their organization**
   - Organization deletion is a critical operation
   - Requires contacting the technical team/developer organization
   - Prevents accidental data loss

2. **System-level deletion only**
   - The delete tenant endpoint exists for administrative purposes
   - Should not be exposed to organization owners
   - Reserved for system administrators

## API Endpoints

### Create User ✨ **NEW**
```
POST /api/v1/users/
Authorization: Bearer <token>
Required Role: OWNER

Request Body:
{
  "email": "newuser@example.com",
  "full_name": "New User",
  "password": "TemporaryPassword123",
  "role": "manager"  // can be: owner, admin, manager, attendant
}

Response: 201 Created
{
  "id": "user-uuid",
  "email": "newuser@example.com",
  "full_name": "New User",
  "role": "manager",
  "tenant_id": "tenant-uuid",
  "is_active": true,
  "is_verified": true,
  "must_change_password": true,
  "created_at": "2024-01-01T00:00:00",
  "updated_at": "2024-01-01T00:00:00"
}

Error Responses:
- 400 Bad Request: Email already registered
- 401 Unauthorized: Missing or invalid token
- 403 Forbidden: Insufficient permissions (not an owner)
```

### List Users
```
GET /api/v1/users/
Authorization: Bearer <token>
Required Role: OWNER

Query Parameters:
- skip (int, optional): Number of records to skip (default: 0)
- limit (int, optional): Maximum number of records to return (default: 100)

Response: 200 OK
[
  {
    "id": "user-uuid",
    "email": "user@example.com",
    "full_name": "John Doe",
    "role": "admin",
    "tenant_id": "tenant-uuid",
    "is_active": true,
    "is_verified": true,
    "created_at": "2024-01-01T00:00:00",
    "updated_at": "2024-01-01T00:00:00"
  }
]

Error Responses:
- 401 Unauthorized: Missing or invalid token
- 403 Forbidden: Insufficient permissions (not an owner)
```

### Get User by ID
```
GET /api/v1/users/{user_id}
Authorization: Bearer <token>
Required Role: OWNER

Response: 200 OK
{
  "id": "user-uuid",
  "email": "user@example.com",
  "full_name": "John Doe",
  "role": "admin",
  "tenant_id": "tenant-uuid",
  "is_active": true,
  "is_verified": true,
  "created_at": "2024-01-01T00:00:00",
  "updated_at": "2024-01-01T00:00:00"
}

Error Responses:
- 401 Unauthorized: Missing or invalid token
- 403 Forbidden: Insufficient permissions (not an owner)
- 404 Not Found: User not found or belongs to different tenant
```

### Update User
```
PUT /api/v1/users/{user_id}
Authorization: Bearer <token>
Required Role: OWNER

Request Body:
{
  "full_name": "Jane Doe",  // optional
  "role": "manager",         // optional (cannot be "owner")
  "is_active": true,         // optional
  "is_verified": true        // optional
}

Response: 200 OK
{
  "id": "user-uuid",
  "email": "user@example.com",
  "full_name": "Jane Doe",
  "role": "manager",
  "tenant_id": "tenant-uuid",
  "is_active": true,
  "is_verified": true,
  "created_at": "2024-01-01T00:00:00",
  "updated_at": "2024-01-01T12:00:00"
}

Error Responses:
- 401 Unauthorized: Missing or invalid token
- 403 Forbidden: 
  - Insufficient permissions (not an owner)
  - Attempting to change owner role
  - Attempting to assign owner role
- 404 Not Found: User not found or belongs to different tenant
```

### Delete User
```
DELETE /api/v1/users/{user_id}
Authorization: Bearer <token>
Required Role: OWNER

Response: 200 OK
{
  "message": "User deactivated successfully"
}

Error Responses:
- 400 Bad Request: Attempting to delete own account
- 401 Unauthorized: Missing or invalid token
- 403 Forbidden: 
  - Insufficient permissions (not an owner)
  - Attempting to delete another owner
- 404 Not Found: User not found or belongs to different tenant
```

### Get Current User
```
GET /api/v1/users/me
Authorization: Bearer <token>
Required Role: Any authenticated user

Response: 200 OK
{
  "id": "user-uuid",
  "email": "user@example.com",
  "full_name": "John Doe",
  "role": "owner",
  "tenant_id": "tenant-uuid",
  "is_active": true,
  "is_verified": true,
  "created_at": "2024-01-01T00:00:00",
  "updated_at": "2024-01-01T00:00:00"
}

Error Responses:
- 401 Unauthorized: Missing or invalid token
- 403 Forbidden: User is inactive
```

## Error Handling

### HTTP Status Codes

- **200 OK**: Request successful
- **400 Bad Request**: Invalid request (e.g., trying to delete own account)
- **401 Unauthorized**: Missing or invalid authentication token
- **403 Forbidden**: Insufficient permissions or operation not allowed
- **404 Not Found**: Resource not found or not accessible

### Error Response Format

All error responses follow this format:

```json
{
  "detail": "Human-readable error message"
}
```

### Common Error Messages

| Error Message | Meaning | Solution |
|--------------|---------|----------|
| "Could not validate credentials" | Invalid or expired token | Re-authenticate and get a new token |
| "Inactive user" | User account has been deactivated | Contact organization owner for reactivation |
| "Insufficient permissions. Required role: owner" | User doesn't have owner role | Only owners can perform this action |
| "User not found" | User doesn't exist or belongs to different tenant | Verify user ID and tenant access |
| "Cannot delete your own account" | Owner attempting self-deletion | Have another owner delete your account if needed |
| "Cannot delete another owner account" | Owner attempting to delete another owner | Contact technical team for owner account deletion |
| "Owner role cannot be changed via API" | Attempting to change owner's role | Owner role changes require technical team intervention |
| "Cannot assign owner role via update API" | Attempting to assign owner role via PUT | Use POST /api/v1/users to create owners |

## Security Considerations

### Authentication & Authorization

1. **JWT Token-Based Authentication**
   - All endpoints require valid JWT bearer token
   - Tokens expire after 30 minutes
   - Refresh tokens valid for 7 days

2. **Role-Based Access Control (RBAC)**
   - Hierarchical role system enforces permissions
   - Higher roles inherit lower role permissions
   - Role checks performed at endpoint level

3. **Tenant Isolation**
   - All queries automatically filter by tenant_id
   - Users can only access resources within their tenant
   - Prevents cross-tenant data leakage

### Data Protection

1. **Soft Delete**
   - Users are deactivated, not permanently deleted
   - Maintains audit trail and referential integrity
   - Supports GDPR compliance

2. **Password Security**
   - Passwords never returned in API responses
   - Bcrypt hashing with salt
   - Cannot update password through user update endpoint

3. **Input Validation**
   - Pydantic schemas validate all inputs
   - SQL injection prevention via SQLAlchemy ORM
   - Email format validation

## Examples

### Example 1: Owner Listing All Users

```bash
# Request
curl -X GET "http://localhost:8000/api/v1/users/?skip=0&limit=10" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..."

# Response
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "owner@company.com",
    "full_name": "Company Owner",
    "role": "owner",
    "tenant_id": "660e8400-e29b-41d4-a716-446655440000",
    "is_active": true,
    "is_verified": true,
    "created_at": "2024-01-01T00:00:00",
    "updated_at": "2024-01-01T00:00:00"
  },
  {
    "id": "550e8400-e29b-41d4-a716-446655440001",
    "email": "admin@company.com",
    "full_name": "Company Admin",
    "role": "admin",
    "tenant_id": "660e8400-e29b-41d4-a716-446655440000",
    "is_active": true,
    "is_verified": true,
    "created_at": "2024-01-02T00:00:00",
    "updated_at": "2024-01-02T00:00:00"
  }
]
```

### Example 2: Owner Upgrading User Role

```bash
# Request
curl -X PUT "http://localhost:8000/api/v1/users/550e8400-e29b-41d4-a716-446655440002" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..." \
  -H "Content-Type: application/json" \
  -d '{
    "role": "manager"
  }'

# Response
{
  "id": "550e8400-e29b-41d4-a716-446655440002",
  "email": "user@company.com",
  "full_name": "Regular User",
  "role": "manager",
  "tenant_id": "660e8400-e29b-41d4-a716-446655440000",
  "is_active": true,
  "is_verified": true,
  "created_at": "2024-01-03T00:00:00",
  "updated_at": "2024-01-10T14:30:00"
}
```

### Example 3: Owner Deleting a User

```bash
# Request
curl -X DELETE "http://localhost:8000/api/v1/users/550e8400-e29b-41d4-a716-446655440002" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..."

# Response
{
  "message": "User deactivated successfully"
}
```

### Example 4: Non-Owner Attempting to Update User (Forbidden)

```bash
# Request (as admin)
curl -X PUT "http://localhost:8000/api/v1/users/550e8400-e29b-41d4-a716-446655440002" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..." \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "Updated Name"
  }'

# Response
HTTP/1.1 403 Forbidden
{
  "detail": "Insufficient permissions. Required role: owner"
}
```

### Example 5: Owner Attempting to Delete Themselves (Bad Request)

```bash
# Request
curl -X DELETE "http://localhost:8000/api/v1/users/550e8400-e29b-41d4-a716-446655440000" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..."

# Response
HTTP/1.1 400 Bad Request
{
  "detail": "Cannot delete your own account"
}
```

### Example 6: Owner Attempting to Delete Another Owner (Forbidden)

```bash
# Request
curl -X DELETE "http://localhost:8000/api/v1/users/550e8400-e29b-41d4-a716-446655440003" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..."

# Response (if user 550e8400-e29b-41d4-a716-446655440003 is an owner)
HTTP/1.1 403 Forbidden
{
  "detail": "Cannot delete another owner account"
}
```

## Troubleshooting

### Issue: "Insufficient permissions" when trying to manage users

**Cause**: Your account doesn't have the OWNER role.

**Solution**: Only users with the OWNER role can manage other users. Contact your organization owner if you need user management capabilities.

### Issue: "Cannot delete your own account"

**Cause**: You're attempting to delete your own owner account.

**Solution**: This is by design to prevent accidental loss of admin access. Have another owner delete your account, or contact the technical team.

### Issue: "Cannot delete another owner account"

**Cause**: You're attempting to delete another owner's account.

**Solution**: For security and governance, owner account deletions require technical team intervention. Contact the developer organization.

### Issue: User appears deleted but still shows in database

**Cause**: The system uses soft deletes.

**Solution**: This is expected behavior. Check the `is_active` field - it should be `false` for deleted users. This maintains audit trails and data integrity.

### Issue: "User not found" when accessing user from another organization

**Cause**: Tenant isolation is enforced.

**Solution**: Users can only access other users within their own organization/tenant. This is a security feature to prevent cross-tenant data access.

## Best Practices

1. **Owner Management**
   - Maintain at least 2 active owners per organization for redundancy
   - Regularly review user roles and permissions
   - Use the principle of least privilege when assigning roles

2. **Security**
   - Rotate JWT tokens regularly
   - Monitor user activity logs
   - Implement IP whitelisting for sensitive operations

3. **User Lifecycle**
   - Deactivate users instead of deleting when possible
   - Keep audit trails of all user management operations
   - Document reasons for role changes

4. **Integration**
   - Handle 403 errors gracefully in frontend applications
   - Implement proper error messaging for users
   - Cache role permissions in frontend to hide unavailable features

## Contact & Support

For issues requiring technical team intervention:
- Owner role assignment
- Owner account deletion
- Organization deletion
- Security incidents

Please contact the developer organization through your official support channels.
