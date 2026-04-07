# User Authentication & Authorization Documentation

## Overview

This document describes the JWT-based authentication and role-based access control (RBAC) implementation for the Multi-Tenant SaaS backend.

## User Model

The User model implements the following attributes:

- **id**: UUID primary key
- **email**: Unique email address (used as username for login)
- **full_name**: User's full name
- **hashed_password**: Bcrypt-hashed password for secure storage (ISO 27001: A.10)
- **role**: User role enum (Owner, Admin, Manager, Attendant)
- **tenant_id**: Foreign key to Tenant model for data isolation
- **is_active**: Boolean flag for soft delete (GDPR-compliant: Art. 17)
- **is_verified**: Boolean flag for email verification status
- **is_superadmin**: Boolean flag for platform-level Super Admin access ✨ **NEW**
- **verification_token**: Cryptographically secure token for email verification (nullable, indexed)
- **verification_token_expires_at**: Token expiration timestamp (nullable, 24h default - GDPR: Data minimization)
- **reset_password_token**: Secure token for password reset (nullable, indexed) ✨ **NEW**
- **reset_password_token_expires_at**: Reset token expiration (nullable, 30min default) ✨ **NEW**
- **must_change_password**: Boolean flag requiring password change on first login (for owner-created users) ✨ **NEW**
- **created_at**: Timestamp of user creation (GDPR: Audit trail)
- **updated_at**: Timestamp of last update (GDPR: Audit trail)

### Email Verification Fields (Security)

**verification_token** (String, 255 chars, nullable, indexed)
- Generated using `secrets.token_urlsafe(32)` for cryptographic security
- 43-character URL-safe token (32 bytes base64-encoded)
- Indexed for efficient lookup during verification
- Single-use: cleared immediately after successful verification
- **Security compliance**: ISO 27001 A.9 (Access Control)

**verification_token_expires_at** (DateTime, nullable)
- Default expiration: 24 hours from generation (configurable)
- Prevents indefinite token validity
- Automatically cleared after verification
- **Privacy compliance**: GDPR Art. 5.1.c (Data Minimization)

### Password Reset Fields (Security) ✨ **NEW**

**reset_password_token** (String, 255 chars, nullable, indexed)
- Generated using `secrets.token_urlsafe(32)` for cryptographic security
- 43-character URL-safe token (32 bytes base64-encoded)
- Indexed for efficient lookup during password reset
- Single-use: cleared immediately after successful reset
- **Security compliance**: ISO 27001 A.9 (Access Control)

**reset_password_token_expires_at** (DateTime, nullable)
- Default expiration: 30 minutes from generation (configurable)
- Short expiration window for security
- Automatically cleared after password reset
- **Privacy compliance**: GDPR Art. 5.1.c (Data Minimization)

## User Roles

The system implements a hierarchical role-based access control:

0. **Super Admin** (Platform-level privileges) ✨ **NEW**
   - Not tied to any specific tenant (tenant_id = null)
   - Full access to all tenants and platform resources
   - Can suspend/reactivate tenants
   - View all users across all tenants
   - Access platform-wide audit logs and statistics
   - Bypasses all tenant-level role checks
   - Dedicated `/admin/*` endpoints

1. **Owner** (Highest tenant-level privileges)
   - Full access to all tenant resources
   - Can manage all users in the tenant
   - Can delete users (soft delete)
   - Can manage subscriptions and billing

2. **Admin**
   - Manage users within the tenant
   - Full access to business operations
   - Cannot manage owners

3. **Manager**
   - Manage inventory and sales
   - View reports and analytics
   - Limited user management

4. **Attendant** (Lowest privileges)
   - Record sales and transactions
   - View inventory
   - No administrative rights

## Authentication Endpoints

### Register Superadmin (Superadmin Only)

**POST** `/api/v1/auth/register`

Register a new superadmin user. **Requires SUPERADMIN authentication.**

⚠️ **Important:** This endpoint is restricted to superadmin users only.
- For new organization registration: Use `POST /api/v1/tenants/register`
- For adding users to existing tenant: Use `POST /api/v1/users` (Owner only)

**Request Body:**

```json
{
  "email": "superadmin@example.com",
  "full_name": "Platform Admin",
  "password": "SecurePassword123",
  "is_superadmin": true,
  "role": "attendant"
}
```

> **Note:** The `role` field is accepted but superadmin accounts are platform-level
> and do not belong to any tenant. The `is_superadmin` flag must be `true`; omitting
> it or setting it to `false` will result in a 400 error.

**Response:** User object without password

**Error Responses:**
- 401 Unauthorized: Not authenticated as superadmin
- 400 Bad Request: `is_superadmin` must be true
- 400 Bad Request: Superadmins cannot have `tenant_id`

### Login

**POST** `/api/v1/auth/login`

Authenticate user and receive JWT tokens.

**Security Features:** ✨ **NEW**
- Progressive login delay (throttling) prevents brute-force attacks
- Constant-time responses to prevent account enumeration
- Comprehensive audit logging for security monitoring
- See [LOGIN_THROTTLING.md](LOGIN_THROTTLING.md) for details

**Request Body (Form Data):**

```bash
username=user@example.com
password=SecurePassword123
```

**Response:**

```json
{
  "access_token": "eyJhbGc...",
  "refresh_token": "eyJhbGc...",
  "token_type": "bearer",
  "expires_in": 1800,
  "requires_password_change": false
}
```

**Note:** When `requires_password_change` is `true`, the user must call `POST /api/v1/auth/force-change-password` before accessing the system. This occurs for users created by an owner.

**Security Behavior:**

- **1-3 failed attempts**: No delay (normal user mistakes)
- **4-5 failed attempts**: 2-second delay (deter automated tools)
- **6-8 failed attempts**: 30-second delay (significant slowdown)
- **9+ failed attempts**: 15-minute cooldown (long delay)
- **Successful login**: Clears all failure counters
- **All failures**: Return same generic error "Incorrect email or password"

### Refresh Token

**POST** `/api/v1/auth/refresh`

Get new access and refresh tokens using a valid refresh token.

**Request Body:**

```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response:** New token pair

> **Security Note:** The refresh token is sent in the request body (not as a query parameter) to prevent token exposure in server logs, browser history, and proxy logs.

### Email Verification ✨ **NEW**

**POST** `/api/v1/auth/verify-email`

Verify user's email address using a verification token sent during registration.

**Request Body:**

```json
{
  "token": "verification-token-from-email"
}
```

**Response:**

```json
{
  "message": "Email verified successfully. You can now log in.",
  "email": "user@example.com"
}
```

**Features:**
- Tokens expire after 24 hours (configurable)
- Single-use tokens (deleted after verification)
- Cryptographically secure token generation
- User must verify email before full account access

### Resend Verification Email ✨ **NEW**

**POST** `/api/v1/auth/resend-verification-email`

Request a new verification email if the original token expired or was lost.

**Request Body:**

```json
{
  "email": "user@example.com"
}
```

**Response:**

```json
{
  "message": "Verification email has been resent. Please check your inbox.",
  "email": "user@example.com"
}
```

**Features:**
- Rate limited: 3 requests per hour per IP
- Generates new token (invalidates old one)
- Works for already-registered users only
- Returns success even if email doesn't exist (prevents email enumeration)

### Forgot Password ✨ **NEW**

**POST** `/api/v1/auth/forgot-password`

Request a password reset link via email.

**Request Body:**

```json
{
  "email": "user@example.com"
}
```

**Response:**

```json
{
  "message": "If the email exists in our system, a password reset link will be sent.",
  "email": "user@example.com"
}
```

**Features:**
- Rate limited: 3 requests per hour per IP
- Reset tokens expire after 30 minutes
- Always returns success response (prevents email enumeration)
- Secure token generation using `secrets.token_urlsafe(32)`
- All requests are logged for audit purposes

### Reset Password ✨ **NEW**

**POST** `/api/v1/auth/reset-password`

Reset user password using a valid reset token.

**Request Body:**

```json
{
  "token": "reset-token-from-email",
  "new_password": "NewSecurePassword123"
}
```

**Response:**

```json
{
  "message": "Password has been reset successfully. You can now log in with your new password.",
  "email": "user@example.com"
}
```

**Features:**
- Rate limited: 5 requests per hour per IP
- Token must be valid and not expired
- Password must meet security requirements (min 8 characters)
- Token is invalidated immediately after successful reset
- User account must be active

**Error Responses:**
- 400 Bad Request - Invalid or expired token
- 403 Forbidden - User account is inactive
- 422 Validation Error - Password doesn't meet requirements

### Force Change Password ✨ **NEW**

**POST** `/api/v1/auth/force-change-password`

Change password for users who were created by an owner and must change their temporary password on first login.

**Headers:**

```bash
Authorization: Bearer {access_token}
```

**Request Body:**

```json
{
  "current_password": "TemporaryPassword123",
  "new_password": "MyNewSecurePassword456"
}
```

**Response:**

```json
{
  "message": "Password changed successfully. You can now access the system with your new password.",
  "email": "user@example.com"
}
```

**Features:**
- Validates current (temporary) password
- Ensures new password is different from current
- Clears `must_change_password` flag upon success
- Logs password change for audit trail
- Rate limited: 5 requests per minute

**Error Responses:**
- 401 Unauthorized - Invalid token or incorrect current password
- 400 Bad Request - New password same as current
- 403 Forbidden - User account is inactive
- 404 Not Found - User not found

## User Management Endpoints

All user management endpoints require authentication.

### Get Current User

**GET** `/api/v1/users/me`

Get information about the currently authenticated user.

**Headers:**

```bash
Authorization: Bearer {access_token}
```

### List Users

**GET** `/api/v1/users/`

List all users in the current tenant. Requires Admin or Owner role.

**Query Parameters:**

- `skip`: Number of records to skip (default: 0)
- `limit`: Maximum number of records (default: 100)

### Get User by ID

**GET** `/api/v1/users/{user_id}`

Get a specific user by ID. Requires Admin or Owner role.

### Update User

**PUT** `/api/v1/users/{user_id}`

Update user information. Requires Admin or Owner role.

**Request Body:**

```json
{
  "full_name": "Updated Name",
  "role": "manager",
  "is_active": true,
  "is_verified": true
}
```

### Delete User (Soft Delete)

**DELETE** `/api/v1/users/{user_id}`

Deactivate a user (GDPR-compliant soft delete). Requires Owner role.

## Security Features

### Password Security

- Passwords are hashed using bcrypt
- Minimum password length: 8 characters
- Passwords are never stored in plain text
- Passwords are never returned in API responses

### JWT Tokens

- Access tokens expire in 30 minutes (configurable)
- Refresh tokens expire in 7 days (configurable)
- Tokens include user ID, tenant ID, and role
- Tokens are signed with a secret key

### Data Isolation

- All user queries are automatically filtered by tenant_id
- Users can only access data from their own tenant
- Cross-tenant access is prevented at the database level

### GDPR Compliance

- Soft delete implementation (right-to-be-forgotten)
- User data can be deactivated instead of permanently deleted
- Audit trail is maintained for compliance
- Email is the only personal identifier

## Role-Based Access Control (RBAC)

The `require_role()` dependency factory enables role-based access control:

```python
from app.core.deps import require_role
from app.models.user import UserRole

@router.get("/admin-only")
def admin_endpoint(
    current_user = Depends(require_role(UserRole.ADMIN))
):
    # Only accessible by Admin and Owner roles
    pass
```

Role hierarchy ensures that higher roles can access lower-role endpoints:

- Owner can access Admin, Manager, and Attendant endpoints
- Admin can access Manager and Attendant endpoints
- Manager can access Attendant endpoints
- Attendant can only access Attendant endpoints

## Configuration

Authentication settings are configured in `.env`:

```env
SECRET_KEY=your-secret-key-here
ACCESS_TOKEN_EXPIRATION=30  # minutes
REFRESH_TOKEN_EXPIRATION=10080  # minutes (7 days)
```

⚠️ **Security Note:** Always use a strong, unique SECRET_KEY in production and never commit it to version control.

## Testing the Authentication Flow

### 1. Register Tenant with Owner Account (Recommended)

This creates a tenant and the first owner in a single operation:

```bash
curl -X POST http://localhost:8000/api/v1/tenants/register \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_name": "My Company",
    "owner_email": "owner@mycompany.com",
    "owner_full_name": "John Doe",
    "owner_password": "SecurePassword123"
  }'
```

### 2. Login

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=owner@mycompany.com&password=SecurePassword123"
```

### 3. Create Additional User (Owner only)

Owners can create users within their tenant:

```bash
curl -X POST http://localhost:8000/api/v1/users/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer {access_token}" \
  -d '{
    "email": "staff@mycompany.com",
    "full_name": "Staff Member",
    "password": "TempPassword123",
    "role": "manager"
  }'
```

Note: New users must change their password on first login.

### 4. Force Password Change (New Users)

Users created by an owner must change their password:

```bash
curl -X POST http://localhost:8000/api/v1/auth/force-change-password \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer {access_token}" \
  -d '{
    "current_password": "TempPassword123",
    "new_password": "MyNewSecurePassword456"
  }'
```

### 5. Use the Access Token

```bash
curl -X GET http://localhost:8000/api/v1/users/me \
  -H "Authorization: Bearer {access_token}"
```

## Error Handling

### Common Error Responses

- **401 Unauthorized**: Invalid or expired token
- **403 Forbidden**: Insufficient permissions or inactive user
- **404 Not Found**: User or resource not found
- **400 Bad Request**: Invalid input data

### Example Error Response

```json
{
  "detail": "Could not validate credentials"
}
```

## Best Practices

1. **Token Management**
   - Store tokens securely (e.g., httpOnly cookies)
   - Implement token refresh before expiration
   - Clear tokens on logout

2. **Password Management**
   - Enforce strong password requirements
   - Implement password reset functionality
   - Consider implementing rate limiting on login attempts

3. **Role Assignment**
   - Start with the least privileged role (Attendant)
   - Promote users as needed
   - Regularly audit user permissions

4. **Data Privacy**
   - Never log passwords or tokens
   - Implement proper audit logging
   - Handle personal data according to GDPR requirements

## Future Enhancements

- [x] Email verification workflow ✨ **COMPLETED**
- [x] Password reset functionality ✨ **COMPLETED**
- [x] Rate limiting on authentication endpoints ✨ **COMPLETED**
- [x] Audit logging for security events ✨ **COMPLETED**
- [x] Account lockout after failed login attempts (Progressive delay) ✨ **COMPLETED**
- [ ] Two-factor authentication (2FA)
- [ ] OAuth2 social login integration
