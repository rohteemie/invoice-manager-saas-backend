# Section 2: User Management - Frontend Checklist

## Summary of Backend Changes

The following backend changes have been made for Section 2 (User Management):

### 2.1 User Creation (Owner-Controlled)

**Changes Made:**
- `POST /api/v1/auth/register` now requires **SUPERADMIN authentication** and is only for creating other superadmins
- New endpoint `POST /api/v1/users` for owners to create users within their tenant
- Regular users cannot self-register to existing tenants

**Frontend Tasks:**

- [ ] **Remove public registration for existing tenants**
  - If you have a "Join Organization" or similar feature that calls `/auth/register`, this must be removed or reworked
  - Users should be invited/created by the organization owner

- [ ] **Update Admin Panel - User Creation**
  - Add a "Create User" form in the admin panel for owners only
  - Required fields: `email`, `full_name`, `password`, `role`
  - Role dropdown should NOT include "owner" option
  - Call `POST /api/v1/users` with owner's auth token

- [ ] **Implement User Invite Flow (Optional Enhancement)**
  - Instead of owner entering password, generate temp password and email to new user
  - Or implement email invite link system

---

### 2.2 Password Change on First Login

**Changes Made:**
- Login response now includes `requires_password_change: boolean` field
- New endpoint `POST /api/v1/auth/force-change-password` for changing password
- Users created by owners have `must_change_password: true`

**Frontend Tasks:**

- [ ] **Check login response for `requires_password_change`**
  - After successful login, check if `response.requires_password_change === true`
  ```javascript
  const loginResponse = await api.login(email, password);
  if (loginResponse.requires_password_change) {
    // Redirect to password change page
    navigate('/change-password');
  } else {
    // Proceed to dashboard
    navigate('/dashboard');
  }
  ```

- [ ] **Create Password Change Page**
  - Required fields: `current_password`, `new_password`, `confirm_new_password`
  - Call `POST /api/v1/auth/force-change-password` with:
    ```json
    {
      "current_password": "temp123",
      "new_password": "NewSecure456@"
    }
    ```
  - Include Bearer token in Authorization header

- [ ] **Handle Error Messages**
  - "Incorrect current password" - Show validation error
  - "New password must be different from current password" - Show validation error

- [ ] **After successful password change**
  - Redirect user to login page OR automatically log them in with new credentials
  - Show success toast/notification

---

### 2.3 User Deletion

**Status:** Already implemented - Owner only can delete users (soft delete)

**Frontend Tasks:**

- [ ] **Verify delete button only shows for owners**
  - Check current user role before showing delete action
  - Admin, Manager, Attendant should NOT see delete button

---

## API Endpoint Summary

| Endpoint | Method | Auth Required | Role Required | Description |
|----------|--------|---------------|---------------|-------------|
| `/api/v1/auth/register` | POST | Yes | SUPERADMIN | Create new superadmin only |
| `/api/v1/tenants/register` | POST | No | - | Create new tenant + owner (onboarding) |
| `/api/v1/users` | POST | Yes | OWNER | Owner creates user in their tenant |
| `/api/v1/auth/login` | POST | No | - | Returns `requires_password_change` flag |
| `/api/v1/auth/force-change-password` | POST | Yes | Any | Change password, clears flag |

## Error Response Examples

### Creating user with owner role (from POST /users):
```json
{
  "status": "error",
  "message": "Cannot create user with OWNER role"
}
```

### Creating non-superadmin via /auth/register:
```json
{
  "status": "error",
  "message": "This endpoint is for superadmin creation only. Use POST /api/v1/tenants/register for new organizations or POST /api/v1/users for adding users to a tenant."
}
```

### Wrong current password during force change:
```json
{
  "status": "error",
  "message": "Incorrect current password"
}
```

---

## Testing Checklist

- [ ] Owner can create new users (non-owner roles only)
- [ ] Admin/Manager/Attendant cannot access user creation
- [ ] New user created by owner must change password on first login
- [ ] Password change flow works correctly
- [ ] Cannot set same password as current when changing
- [ ] Public registration is no longer available for existing tenants
- [ ] New tenant registration still works (creates tenant + owner)
