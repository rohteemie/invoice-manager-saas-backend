# AI Agent Prompt: Multi-Tenant Mobile App Login Implementation

**Copy this entire prompt and paste it into your AI agent for mobile app development**

---

## SYSTEM CONTEXT

You are a senior mobile app developer tasked with implementing a multi-tenant login feature for a mobile application (iOS/Android/React Native). The backend has been updated to support users who work for multiple organizations (tenants). Your task is to implement the login flow that handles both single-tenant and multi-tenant scenarios.

---

## PROJECT REQUIREMENTS

### Objective
Implement a multi-tenant login system in the mobile app where:
- Users can have email addresses that are unique per organization (not globally unique)
- Users can work for multiple organizations simultaneously
- Login flow should handle both single-tenant (direct to app) and multi-tenant (show selection screen) scenarios
- Maintain backward compatibility with existing single-tenant users

### Business Context
- **Target Users**: Users who work for multiple organizations
- **Example**: John can have email "john@example.com" at both "Acme Corp" and "TechCo"
- **User Experience**: Seamless login with optional tenant selection
- **Security**: Re-authentication required for tenant selection

---

## TECHNICAL SPECIFICATIONS

### Backend API Changes
The backend now provides TWO new/updated endpoints:

#### 1. LOGIN ENDPOINT (UPDATED)
**Endpoint**: `POST /api/v1/auth/login`

**Request Format**:
```json
{
  "username": "user@example.com",
  "password": "SecurePassword123!"
}
```

**Response Type A: Single Tenant User** (unchanged from before)
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800,
  "requires_password_change": false
}
```

**Response Type B: Multi-Tenant User** (NEW - when user belongs to 2+ tenants)
```json
{
  "requires_tenant_selection": true,
  "email": "user@example.com",
  "tenants": [
    {
      "tenant_id": "550e8400-e29b-41d4-a716-446655440000",
      "tenant_name": "Acme Corporation",
      "role": "owner"
    },
    {
      "tenant_id": "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
      "tenant_name": "TechStartup Inc",
      "role": "admin"
    }
  ],
  "message": "You belong to multiple organizations. Please select the one you want to access."
}
```

**Response Type C: Error** (invalid credentials)
```json
{
  "detail": "Incorrect email or password"
}
```
Status Code: 401

#### 2. SELECT TENANT ENDPOINT (NEW)
**Endpoint**: `POST /api/v1/auth/select-tenant`

**Request Format** (user selects tenant from UI):
```json
{
  "email": "user@example.com",
  "password": "SecurePassword123!",
  "tenant_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Response Format** (same as single-tenant login):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800,
  "requires_password_change": false
}
```

Status Code: 200
Error: 400 (invalid tenant) or 401 (wrong password)

---

## IMPLEMENTATION REQUIREMENTS

### 1. LOGIN SCREEN (Existing - Minor Update)
**No visual changes needed** - Keep existing UI as is.

**Code Logic Changes**:
```
1. User enters email and password
2. Call POST /api/v1/auth/login
3. Wait for response
4. IF response has "requires_tenant_selection" = true:
   - Parse tenant list
   - Navigate to TENANT SELECTION SCREEN (new)
5. ELSE:
   - Store access_token and refresh_token
   - Navigate to DASHBOARD
6. ON ERROR (401):
   - Show error message "Incorrect email or password"
```

### 2. TENANT SELECTION SCREEN (NEW)
**This screen is shown ONLY when user belongs to multiple tenants.**

**UI Elements Required**:
- Display title: "Select Your Organization"
- Display message from backend (or default: "You belong to multiple organizations. Please select the one you want to access.")
- List of organizations as selectable items. Each item should display:
  - Organization Name (e.g., "Acme Corporation")
  - User's Role in that org (e.g., "Owner")
  - Tenant ID (can be hidden but use it in backend call)
- A "Select" or "Continue" button for each organization (or single button after selection)
- Loading state while calling select-tenant endpoint
- Error message display if selection fails

**Example UI Layout**:
```
┌─────────────────────────────────┐
│  Select Your Organization       │
├─────────────────────────────────┤
│                                 │
│  ☐ Acme Corporation             │
│    Role: Owner                  │
│                                 │
│  ☐ TechStartup Inc              │
│    Role: Admin                  │
│                                 │
│           [CONTINUE]            │
│                                 │
└─────────────────────────────────┘
```

**Code Logic**:
```
1. Display tenant list from login response
2. User taps to select organization
3. User taps "Continue" button
4. Call POST /api/v1/auth/select-tenant with:
   {
     "email": stored_email,
     "password": stored_password,
     "tenant_id": selected_tenant_id
   }
5. Wait for response
6. IF success (200):
   - Store access_token and refresh_token
   - Clear stored password from memory for security
   - Navigate to DASHBOARD
7. IF error (401):
   - Show error message
   - Return to LOGIN screen for re-authentication
8. IF error (400):
   - Show error message
   - Return to TENANT SELECTION screen
```

**Important Security Note**: Store the password temporarily in memory ONLY during the login flow. Clear it immediately after successful authentication. DO NOT store password in persistent storage.

---

## DETAILED IMPLEMENTATION FLOW

### Flow Diagram
```
START
  ↓
LOGIN SCREEN
  ↓
User enters email/password
  ↓
API Call: POST /api/v1/auth/login
  ↓
┌─────────────────────────────────────────┐
│ DECISION: Response Type?                │
├─────────────────────────────────────────┤
│                                         │
├─ Token (success) ──────────────────────→ DASHBOARD
│                                         │
├─ MultiTenantResponse ───────────────────→ TENANT SELECTION
│                                         │
├─ Error (401) ─────────────────────────→ LOGIN (show error)
│                                         │
└─────────────────────────────────────────┘
                 ↑
                 │
        TENANT SELECTION SCREEN
                 │
            User selects org
                 │
        API Call: POST /api/v1/auth/select-tenant
                 │
        ┌────────┴────────┐
        │                 │
    Success (200)    Error (401 or 400)
        │                 │
        ↓                 ↓
   DASHBOARD         LOGIN/RETRY
```

---

## CODE EXAMPLE (TypeScript/React Native)

### Login Handler
```typescript
const handleLogin = async (email: string, password: string) => {
  setLoading(true);
  setError(null);

  try {
    const response = await fetch('/api/v1/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams({
        username: email,
        password: password
      }).toString()
    });

    if (!response.ok) {
      setError('Incorrect email or password');
      setLoading(false);
      return;
    }

    const data = await response.json();

    // Check for multi-tenant response
    if (data.requires_tenant_selection === true) {
      // Store email and password temporarily for tenant selection
      setStoredEmail(email);
      setStoredPassword(password);
      setTenants(data.tenants);
      setLoading(false);
      navigation.navigate('TenantSelection');
    } else {
      // Single tenant - proceed to dashboard
      await storeTokens(data.access_token, data.refresh_token);
      setLoading(false);
      navigation.navigate('Dashboard');
    }
  } catch (err) {
    setError('Network error. Please try again.');
    setLoading(false);
  }
};
```

### Tenant Selection Handler
```typescript
const handleTenantSelection = async (tenantId: string) => {
  setLoading(true);
  setError(null);

  try {
    const response = await fetch('/api/v1/auth/select-tenant', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        email: storedEmail,
        password: storedPassword,
        tenant_id: tenantId
      })
    });

    if (!response.ok) {
      const errorData = await response.json();
      setError(errorData.detail || 'Tenant selection failed');
      setLoading(false);
      return;
    }

    const data = await response.json();

    // Store tokens and clear temporary password
    await storeTokens(data.access_token, data.refresh_token);
    setStoredPassword(null); // Clear password from memory
    setLoading(false);

    navigation.reset({
      index: 0,
      routes: [{ name: 'Dashboard' }]
    });
  } catch (err) {
    setError('Network error. Please try again.');
    setLoading(false);
  }
};
```

### Token Storage (Secure)
```typescript
import * as SecureStore from 'expo-secure-store'; // For React Native

const storeTokens = async (accessToken: string, refreshToken: string) => {
  await SecureStore.setItemAsync('access_token', accessToken);
  await SecureStore.setItemAsync('refresh_token', refreshToken);
};

const getAccessToken = async () => {
  return await SecureStore.getItemAsync('access_token');
};

const clearTokens = async () => {
  await SecureStore.deleteItemAsync('access_token');
  await SecureStore.deleteItemAsync('refresh_token');
};
```

---

## TESTING REQUIREMENTS

### Test Cases to Implement

1. **Single-Tenant User Login**
   - Precondition: User exists in only one organization
   - Action: Enter credentials and login
   - Expected: Should show Token response and navigate to dashboard
   - ✓ Backward compatible (no changes for users)

2. **Multi-Tenant User Login**
   - Precondition: User exists in 2+ organizations
   - Action: Enter credentials and login
   - Expected: Should show MultiTenantLoginResponse with tenant list
   - Action: Select first organization
   - Expected: Should receive Token and navigate to dashboard
   - Action: Logout and login again, select second organization
   - Expected: Should receive Token for second organization and navigate to dashboard

3. **Invalid Credentials**
   - Precondition: None required
   - Action: Enter invalid password
   - Expected: Should show 401 error, display message "Incorrect email or password"
   - Action: Retry with correct credentials
   - Expected: Should succeed

4. **Network Error Handling**
   - Precondition: Network unavailable or backend unreachable
   - Action: Try to login
   - Expected: Should show network error message and allow retry

5. **Tenant Selection Timeout**
   - Precondition: User shown tenant selection screen
   - Action: Wait > 5 minutes without selecting tenant (optional implementation)
   - Expected: Should return to login screen and require re-authentication

6. **Invalid Tenant Selection**
   - Precondition: User in tenant selection with valid tenant list
   - Action: Somehow send invalid tenant_id to backend
   - Expected: Should show error "Invalid tenant selection"

7. **Password Change Enforcement**
   - Precondition: Backend returns requires_password_change = true
   - Action: Check login response
   - Expected: After dashboard load, show "Must Change Password" screen

### Manual Testing Steps
```
1. Test with single-tenant user:
   - Email: single@example.com
   - Password: TestPass123!
   - Expected: Direct to dashboard

2. Test with multi-tenant user:
   - Email: multi@example.com
   - Password: TestPass123!
   - Expected: Show tenant selection
   - Select first org
   - Expected: Dashboard loads for first org
   - Logout and repeat
   - Select second org
   - Expected: Dashboard loads for second org

3. Test invalid credentials:
   - Email: user@example.com
   - Password: wrong-password
   - Expected: Error message displayed

4. Test network error:
   - Disable network
   - Try to login
   - Expected: Error message with retry option
```

---

## SUCCESS CRITERIA

- [ ] Login screen accepts email/password as before (no changes)
- [ ] Single-tenant users can login directly to dashboard (backward compatible)
- [ ] Multi-tenant users see tenant selection screen after valid credentials
- [ ] Tenant selection screen displays:
  - [ ] Organization names
  - [ ] User roles in each organization
  - [ ] Selection mechanism (radio/tap/button)
- [ ] Selecting a tenant calls select-tenant endpoint correctly
- [ ] Tokens are stored securely after successful authentication
- [ ] Error messages displayed appropriately:
  - [ ] Invalid credentials → "Incorrect email or password"
  - [ ] Network error → "Network error. Please try again."
  - [ ] Invalid tenant → Error message from backend
- [ ] No passwords stored in persistent storage
- [ ] Token refresh mechanism works correctly
- [ ] Logout clears tokens and returns to login screen
- [ ] All scenarios tested and working

---

## KEY CONSTRAINTS & NOTES

1. **Password Storage**: Temporary password storage is acceptable ONLY in memory during the login flow. Clear immediately after authentication.

2. **Token Expiration**: Access tokens expire after 30 minutes (1800 seconds). Implement token refresh logic using refresh_token.

3. **Backward Compatibility**: Single-tenant users should NOT see any change in their login experience.

4. **Rate Limiting**: Backend has login rate limiting (10 attempts per minute). Handle 429 Too Many Requests errors gracefully.

5. **Email Case Sensitivity**: Email addresses are case-insensitive. Normalize to lowercase for consistency.

6. **Timeout Recommendation**: Implement 5-10 minute timeout for tenant selection screen to prevent users from being stuck there indefinitely.

7. **Accessibility**: Ensure tenant selection screen is accessible:
   - [ ] Clear labels for each organization
   - [ ] Proper contrast ratios
   - [ ] Screen reader support
   - [ ] Keyboard navigation

---

## DELIVERABLES

When implementation is complete, provide:

1. **Code Files**
   - Updated login screen component
   - New tenant selection screen component
   - Auth service/API client updates
   - Token storage/retrieval utilities

2. **Documentation**
   - Implementation notes explaining design choices
   - List of libraries used
   - Known limitations (if any)

3. **Test Results**
   - Screenshot/video of single-tenant login
   - Screenshot/video of multi-tenant login flow
   - Screenshot/video of error scenarios
   - Test case results

4. **Code Review Checklist**
   - Code follows project standards
   - No hardcoded credentials
   - Proper error handling
   - Accessible UI
   - Well-commented code

---

## REFERENCE DOCUMENTATION

The backend team has provided these documents:
- **FRONTEND_MULTI_TENANT_LOGIN_GUIDE.md** - Complete API and flow documentation
- **FRONTEND_QUICK_START.md** - Quick reference guide for developers
- **IMPLEMENTATION_STATUS.md** - Backend implementation details
- Live API Swagger: `/docs` endpoint on backend

---

## COMMUNICATION EXPECTATIONS

Upon completion:
1. Submit code for review by tech lead
2. Provide test execution evidence
3. Update app version number and changelog
4. Schedule UAT (User Acceptance Testing)
5. Prepare release notes for users

---

## QUESTIONS TO CLARIFY BEFORE STARTING

If any of the following are unclear, ask the TEAM before implementing:

1. What mobile framework is being used? (React Native, iOS native, Android native, Flutter, etc.)
2. What state management library? (Redux, MobX, Context API, etc.)
3. What HTTP client library? (axios, fetch, Dio, etc.)
4. What secure storage solution? (SecureStore, Keychain, etc.)
5. Are there existing design system components to use for UI?
6. What's the timeout preference for tenant selection screen?
7. Should tenant selection history be saved (quick-select next time)?

---

## FINAL SUMMARY

**Your Task**: Build a tenant-aware login system that:
- Maintains backward compatibility (single-tenant users unaffected)
- Handles multi-tenant logic smoothly
- Provides clear UX for tenant selection
- Stores credentials securely
- Handles errors gracefully

**Start Point**: FRONTEND_QUICK_START.md
**Deep Dive**: FRONTEND_MULTI_TENANT_LOGIN_GUIDE.md
**Time Estimate**: 5-7 days for full implementation + testing

Good luck! 🚀

