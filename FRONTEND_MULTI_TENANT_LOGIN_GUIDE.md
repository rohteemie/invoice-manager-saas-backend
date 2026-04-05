# Multi-Tenant Login Flow Implementation Guide

**For Mobile Frontend Engineers (iOS/Android/React Native)**

---

## Overview

The backend now supports **tenant-scoped email uniqueness**, meaning:
- Same email can exist in different organizations (tenants)
- Users can work for multiple organizations
- Login flow changes to support tenant selection when applicable

---

## API Changes

### 1. POST `/api/v1/auth/login` - Updated Behavior

#### Request (No Change)
```json
{
  "username": "user@example.com",
  "password": "SecurePassword123!"
}
```

#### Response: Single Tenant (User belongs to only one organization)
```json
{
  "access_token": "eyJhbGc...",
  "refresh_token": "eyJhbGc...",
  "token_type": "bearer",
  "expires_in": 1800,
  "requires_password_change": false
}
```
**Action**: Proceed to dashboard (existing behavior)

#### Response: Multiple Tenants (User belongs to multiple organizations)
```json
{
  "requires_tenant_selection": true,
  "email": "user@example.com",
  "tenants": [
    {
      "tenant_id": "org-uuid-1",
      "tenant_name": "Acme Corporation",
      "role": "owner"
    },
    {
      "tenant_id": "org-uuid-2",
      "tenant_name": "TechStartup Inc",
      "role": "admin"
    }
  ],
  "message": "You belong to multiple organizations. Please select the one you want to access."
}
```
**Action**: Show tenant selection screen (NEW)

#### Response: Error - Invalid Credentials
```json
{
  "detail": "Incorrect email or password"
}
```
**Status**: 401 Unauthorized

---

## New Endpoint: POST `/api/v1/auth/select-tenant`

**Purpose**: Complete login by selecting desired tenant

**Request** (After user selects tenant from UI):
```json
{
  "email": "user@example.com",
  "password": "SecurePassword123!",
  "tenant_id": "org-uuid-1"
}
```

**Response** (Same as single-tenant login):
```json
{
  "access_token": "eyJhbGc...",
  "refresh_token": "eyJhbGc...",
  "token_type": "bearer",
  "expires_in": 1800,
  "requires_password_change": false
}
```

**Status**: 200 OK

---

## Frontend Implementation Flow

### Login Flow Diagram

```
┌─────────────────────────────────────┐
│   Login Screen                      │
│  [Email Input]                      │
│  [Password Input]                   │
│  [Login Button]                     │
└────────────┬────────────────────────┘
             │
             ▼
    POST /api/v1/auth/login
             │
    ┌────────┴────────┐
    │                 │
    ▼                 ▼
401 Error         200 OK
    │                 │
    │          ┌──────┴──────┐
    │          │             │
    │    requires_tenant_    single_tenant
    │    selection=true      login
    │          │             │
    │          ▼             ▼
    │   Tenant Selection   Dashboard
    │   Screen              
    │          │
    │   User selects
    │   organization
    │          │
    │          ▼
    │  POST /api/v1/auth/select-tenant
    │          │
    │          ▼
    │       Dashboard
    │
    ▼
Show Error
Message
```

---

## Step-by-Step Implementation

### Step 1: Update Login Screen Logic

```typescript
// Pseudo-code for mobile app

async function handleLogin(email: string, password: string) {
  try {
    const response = await fetch('/api/v1/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams({
        username: email,
        password: password
      })
    });

    if (response.status === 401) {
      showErrorMessage('Incorrect email or password');
      return;
    }

    const data = await response.json();

    // NEW: Check if user has multiple tenants
    if (data.requires_tenant_selection === true) {
      // Show tenant selection screen
      navigateToTenantSelection(data.tenants, email, password);
    } else {
      // Single tenant - proceed as before
      saveTokens(data);
      navigateToDashboard();
    }
  } catch (error) {
    showErrorMessage('Login failed. Please try again.');
  }
}
```

### Step 2: Create Tenant Selection Screen

**Screen Components**:
- Header: "Choose Organization"
- List of tenants with:
  - Organization logo/icon
  - Organization name
  - User's role in that organization (e.g., "Owner", "Admin")
- "Select" button per organization
- "Cancel" button (go back to login)

**Example UI Layout** (React Native):
```jsx
<FlatList
  data={tenants}
  keyExtractor={(item) => item.tenant_id}
  renderItem={({ item }) => (
    <TouchableOpacity
      onPress={() => handleTenantSelect(item)}
      style={styles.tenantCard}
    >
      <Text style={styles.tenantName}>{item.tenant_name}</Text>
      <Text style={styles.userRole}>Role: {item.role}</Text>
      <TouchableOpacity
        onPress={() => completeLogin(item.tenant_id)}
        style={styles.selectButton}
      >
        <Text>Select</Text>
      </TouchableOpacity>
    </TouchableOpacity>
  )}
/>
```

### Step 3: Implement Tenant Selection Handler

```typescript
async function completeLogin(
  email: string,
  password: string,
  tenantId: string
) {
  try {
    const response = await fetch('/api/v1/auth/select-tenant', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        email: email,
        password: password,
        tenant_id: tenantId
      })
    });

    if (response.status !== 200) {
      showErrorMessage('Tenant selection failed');
      return;
    }

    const data = await response.json();
    
    // Save tokens and context
    saveTokens(data);
    saveSelectedTenant(tenantId);
    
    // Check if password change required
    if (data.requires_password_change === true) {
      navigateToPasswordChange();
    } else {
      navigateToDashboard();
    }
  } catch (error) {
    showErrorMessage('Failed to complete login');
  }
}
```

### Step 4: Store Selected Tenant Context

**In device storage** (AsyncStorage on React Native, SharedPreferences on Android, etc.):
```json
{
  "access_token": "...",
  "refresh_token": "...",
  "selected_tenant_id": "org-uuid-1",
  "user_email": "user@example.com"
}
```

**Use in subsequent requests**:
- Token already includes `tenant_id` in JWT payload
- Most endpoints automatically filter by tenant_id from token
- Some endpoints may need explicit tenant context in headers (backend will specify)

### Step 5: Handle Switch Tenant (Optional)

**In settings/profile screen**, add "Switch Organization" option:

```typescript
async function switchTenant(newTenantId: string) {
  // Re-authenticate with new tenant
  const { email, password } = getStoredCredentials(); // Or ask user again
  
  await completeLogin(email, password, newTenantId);
}
```

---

## Error Handling

### Invalid Credentials
```json
{
  "detail": "Incorrect email or password"
}
```
Status: 401  
Action: Show error message, stay on login screen

### Tenant Selection Timeout
- Add timeout handling for tenant selection screen
- Timeout after 5-10 minutes without selection
- Redirect to login screen with "Session expired" message

### Inactive Tenant
```json
{
  "detail": "Incorrect email or password"
}
```
Status: 401  
Action: Same as invalid credentials (doesn't leak which tenant inactive)

### Password Change Required
```json
{
  "requires_password_change": true
}
```
After login (single or multi-tenant):  
Action: Navigate to "Force Change Password" screen before dashboard

---

## Testing Checklist

- [ ] Login with single-tenant user → Proceeds to dashboard
- [ ] Login with multi-tenant user → Shows tenant selection screen
- [ ] Select tenant from list → Receives token and goes to dashboard
- [ ] Invalid email/password → Shows error, stays on login
- [ ] Tenant becomes inactive → Login fails gracefully
- [ ] Password change required → Shows password change screen
- [ ] Switch tenant feature works (if implemented)
- [ ] Tokens persist correctly in device storage
- [ ] Logout clears all stored data

---

## API Documentation

### Login Endpoint Details

**Endpoint**: `POST /api/v1/auth/login`  
**Rate Limit**: 10 requests per minute per IP  
**Progressive Throttling**: Applied on failed attempts

**Request Format**:
- Content-Type: `application/x-www-form-urlencoded`
- Fields: `username` (email), `password`

**Response Format**:
- Single tenant: Token response (access_token, refresh_token, etc.)
- Multi-tenant: TenantSelection response (requires_tenant_selection=true, list of tenants)

---

## Backward Compatibility

✅ **No breaking changes for single-tenant users**:
- Response structure remains identical
- Existing code continues to work
- Only adds new `requires_tenant_selection` field

✅ **Graceful degradation**:
- If backend returns empty tenant list (should not happen), treat as auth error
- If tenant selection endpoint fails, show error and return to login

---

## Security Considerations

1. **Password Storage**: Do NOT store plaintext passwords in device storage
   - Ask for password again when switching tenants
   - Use secure credential storage (Keychain on iOS, Keystore on Android)

2. **Token Security**: 
   - Store tokens in secure storage only
   - Clear tokens on logout
   - Don't log tokens in console/debugging

3. **Email in UI**: Safe to display (already entered by user)  
   - Don't leak this information in error messages beyond "incorrect credentials"

4. **Tenant List Information**: 
   - Only shown after successful password authentication
   - Tenant names are visible (this is expected UX)

---

## Questions & Support

For backend API clarification, refer to:
- `/docs` endpoint (Swagger UI) - Interactive API documentation
- `MULTI_TENANT_EMAIL_ANALYSIS.md` - Architecture explanation
- Backend team for specific endpoint behavior

---

## Summary of Changes

| Scenario | Before | After |
|----------|--------|-------|
| Single-tenant user | Login → Dashboard | Login → Dashboard (no change) |
| Multi-tenant user | ❌ Not supported | Login → Select Tenant → Dashboard |
| Email validation | Globally unique | Unique per tenant |
| Max login time | N/A | ~5-10 min (tenant selection) |
| Data isolation | Per token tenant_id | Per token tenant_id (no change) |
