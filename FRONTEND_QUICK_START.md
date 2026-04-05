# Frontend Engineer Quick Start Guide

**For**: Mobile App Developers (iOS/Android/React Native)
**Date**: April 3, 2026
**Status**: Ready for Implementation

---

## 📖 **Primary Document to Read**

### **→ [FRONTEND_MULTI_TENANT_LOGIN_GUIDE.md](FRONTEND_MULTI_TENANT_LOGIN_GUIDE.md)**

This is **THE** document for frontend implementation. It contains:
- ✅ Complete API changes documentation
- ✅ Request/response examples (single vs multi-tenant)
- ✅ Step-by-step implementation guide
- ✅ UI/UX flow diagrams
- ✅ Error handling guide
- ✅ Testing checklist
- ✅ Security considerations

**Time to Read**: ~15-20 minutes
**Critical Sections**: Login Flow, API Changes, Implementation Code

---

## 🎯 **What Changed (Quick Summary)**

### Before (Old Behavior)
```
User Email Login → Direct to Dashboard
```

### After (New Behavior)
```
User Email Login
    ↓
Check how many tenants user belongs to
    ├─ 1 tenant? → Direct to Dashboard (unchanged)
    └─ 2+ tenants? → Show Tenant Selection Screen → Dashboard
```

---

## 🔑 **Key API Endpoints**

### 1. Login Endpoint (Updated)
```
POST /api/v1/auth/login
```

**Same request as before**:
```json
{
  "username": "user@example.com",
  "password": "Password123!"
}
```

**Response changed - can now return 2 types**:

**Type A: Single Tenant** (unchanged)
```json
{
  "access_token": "...",
  "refresh_token": "...",
  "token_type": "bearer",
  "expires_in": 1800,
  "requires_password_change": false
}
```

**Type B: Multiple Tenants** (NEW)
```json
{
  "requires_tenant_selection": true,
  "email": "user@example.com",
  "tenants": [
    {
      "tenant_id": "org-uuid-1",
      "tenant_name": "Acme Corp",
      "role": "owner"
    },
    {
      "tenant_id": "org-uuid-2",
      "tenant_name": "TechCo",
      "role": "admin"
    }
  ],
  "message": "You belong to multiple organizations. Please select the one you want to access."
}
```

### 2. New Tenant Selection Endpoint (NEW)
```
POST /api/v1/auth/select-tenant
```

**Request**:
```json
{
  "email": "user@example.com",
  "password": "Password123!",
  "tenant_id": "org-uuid-1"
}
```

**Response** (same as single tenant login):
```json
{
  "access_token": "...",
  "refresh_token": "...",
  "token_type": "bearer",
  "expires_in": 1800,
  "requires_password_change": false
}
```

---

## 💻 **Implementation Code Example (TypeScript)**

### Login Handler
```typescript
async handleLogin(email: string, password: string) {
  const response = await api.post('/api/v1/auth/login', {
    username: email,
    password: password
  });

  // Check if requires_tenant_selection is present
  if (response.data.requires_tenant_selection === true) {
    // Multiple tenants - show selection screen
    this.showTenantSelectionScreen(response.data.tenants, email);
  } else {
    // Single tenant or error - proceed as normal
    this.storeTokens(response.data);
    this.navigateToDashboard();
  }
}
```

### Tenant Selection Handler (NEW)
```typescript
async handleTenantSelection(
  email: string,
  password: string,
  selectedTenantId: string
) {
  const response = await api.post('/api/v1/auth/select-tenant', {
    email: email,
    password: password,
    tenant_id: selectedTenantId
  });

  // Store tokens and navigate to dashboard
  this.storeTokens(response.data);
  this.navigateToDashboard();
}
```

---

## 📋 **Implementation Checklist**

- [ ] Read FRONTEND_MULTI_TENANT_LOGIN_GUIDE.md completely
- [ ] Update login endpoint response handling
  - [ ] Add check for `requires_tenant_selection` field
  - [ ] Parse tenant list if multi-tenant response
- [ ] Create tenant selection screen UI
  - [ ] Display list of tenants
  - [ ] Show organization name and user role
  - [ ] Add selection button
- [ ] Implement select-tenant endpoint call
- [ ] Update navigation logic
  - [ ] Single tenant: Direct to dashboard
  - [ ] Multi-tenant: Show selection first
- [ ] Add error handling for:
  - [ ] Invalid credentials
  - [ ] Tenant selection timeout (if applicable)
  - [ ] Network errors
- [ ] Test with:
  - [ ] Single-tenant user (should work as before)
  - [ ] Multi-tenant user (should show selection)
  - [ ] Invalid credentials (should show error)
- [ ] Update app version and release notes

---

## 🔍 **Backend Schemas (What to Expect)**

### Token Response
```typescript
interface Token {
  access_token: string;
  refresh_token: string;
  token_type: "bearer";
  expires_in: number;
  requires_password_change: boolean;
}
```

### Multi-Tenant Login Response
```typescript
interface MultiTenantLoginResponse {
  requires_tenant_selection: true;
  email: string;
  tenants: TenantOption[];
  message: string;
}

interface TenantOption {
  tenant_id: string;
  tenant_name: string;
  role: "owner" | "admin" | "manager" | "attendant";
}
```

### Select Tenant Request
```typescript
interface SelectTenantRequest {
  email: string;
  password: string;
  tenant_id: string;
}
```

---

## ⚠️ **Important Notes**

1. **Password Re-authentication**: The select-tenant endpoint requires the user to re-enter their password for security. This is intentional.

2. **Timeout Handling**: Users should not be able to select a tenant forever. Implement a reasonable timeout (5-10 minutes) before forcing re-login.

3. **Error Handling**: Both endpoints can return standard HTTP errors:
   - `401`: Invalid credentials
   - `400`: Bad request (missing fields)
   - `404`: Tenant not found

4. **Backward Compatibility**: Single-tenant users will not see any change. The token response is identical.

5. **Token Storage**: Store both `access_token` and `refresh_token`. Use access_token for API calls, refresh_token to get new tokens when expired.

---

## 🧪 **Testing Scenarios**

### Scenario 1: Single Tenant User
- Login with single-tenant user credentials
- **Expected**: Receive Token response, go to dashboard
- **Your App**: Direct navigation to dashboard (no changes needed)

### Scenario 2: Multi-Tenant User
- Login with multi-tenant user credentials
- **Expected**: Receive MultiTenantLoginResponse with tenant list
- **Your App**: Show tenant selection screen
- Select tenant and call select-tenant endpoint
- **Expected**: Receive Token response
- **Your App**: Navigate to dashboard

### Scenario 3: Invalid Credentials
- Login with wrong password
- **Expected**: 401 Unauthorized with message
- **Your App**: Show error message to user

---

## 📞 **API Documentation**

Backend has updated Swagger/OpenAPI documentation at:
```
https://your-backend-url/docs
```

Or manually test with curl:
```bash
# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user@example.com&password=Password123!"

# Select Tenant
curl -X POST http://localhost:8000/api/v1/auth/select-tenant \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "Password123!",
    "tenant_id": "org-uuid-1"
  }'
```

---

## 🚀 **Implementation Timeline**

1. **Phase 1 (Day 1)**: Read documentation, understand flow
2. **Phase 2 (Day 2-3)**: Implement login endpoint updates
3. **Phase 3 (Day 3-4)**: Create tenant selection UI
4. **Phase 4 (Day 4-5)**: Implement select-tenant endpoint
5. **Phase 5 (Day 5-6)**: Testing and bug fixes
6. **Phase 6 (Day 6-7)**: Code review and deployment

---

## ✅ **Sign-Off Checklist**

- [ ] Understand the multi-tenant login flow
- [ ] Can implement login endpoint changes
- [ ] Can create tenant selection UI
- [ ] Can implement select-tenant endpoint
- [ ] Know error handling approach
- [ ] Ready to test end-to-end

---

## 📚 **Reference Documents**

| Document | Purpose | Who Should Read |
|----------|---------|-----------------|
| **FRONTEND_MULTI_TENANT_LOGIN_GUIDE.md** ⭐ | Implementation guide | Frontend Engineers |
| IMPLEMENTATION_STATUS.md | Technical checklist | Backend/DevOps |
| VERIFICATION_REPORT.md | Compliance & verification | Tech Lead/QA |
| TESTING_TENANT_SCOPED_EMAIL.md | Test suite details | QA/Backend |
| PROJECT_COMPLETION_SUMMARY.md | Project overview | Project Manager |

---

**Next Action**: Open [FRONTEND_MULTI_TENANT_LOGIN_GUIDE.md](FRONTEND_MULTI_TENANT_LOGIN_GUIDE.md) and start implementing!
