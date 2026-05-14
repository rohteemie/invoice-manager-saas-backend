# Bug Report: Multi-Tenant SaaS Backend

**Date**: May 14, 2026
**Status**: Critical Issues Found
**Severity Levels**: 🔴 Critical, 🟠 High, 🟡 Medium, 🟢 Low

---

## 1. 🔴 CRITICAL BUGS

### 1.1 Debug Print Statements in Production Code
**File**: [app/api/v1/endpoints/auth.py](app/api/v1/endpoints/auth.py#L808-L809)
**Lines**: 808-809
**Issue**: Debug print statements left in `forgot_password()` endpoint that expose password reset tokens to stdout/logs

```python
# LINES 808-809 (PRODUCTION CODE - SHOULD BE REMOVED)
print("______________TOKEN________________")
print(reset_token)  # ⚠️ SECURITY RISK: Token exposed in logs/stdout
```

**Impact**:
- Password reset tokens exposed in application logs
- Tokens visible in container logs
- Potential token compromise

**Fix**: Remove the print statements immediately

---

### 1.2 Incomplete Email Verification Logging Code
**File**: [app/api/v1/endpoints/auth.py](app/api/v1/endpoints/auth.py#L666-L671)
**Lines**: 666-671
**Issue**: Incomplete/commented-out logging code in `verify_email()` endpoint

```python
# Optionally, log the verification event
# log_auth_event(
#     db=db,
#     request=request,
#     action=AuditAction.EMAIL_VERIFIED,
#     user_id=user.id,
#     tenant_id=user.tenant_id,
#     description=  # ← INCOMPLETE! Missing description parameter
```

**Impact**:
- Email verification events not logged to audit trail
- Compliance gap: Cannot track when users verified emails
- Inconsistent logging across authentication flows

**Fix**: Complete the logging code or remove comments

---

### 1.3 Missing Tenant Ownership Validation in Owner-Created Users
**File**: [app/api/v1/endpoints/users.py](app/api/v1/endpoints/users.py#L30-L90)
**Lines**: 30-90
**Issue**: No validation that an owner cannot create users for a different tenant

```python
@router.post("/", response_model=User, status_code=status.HTTP_201_CREATED)
def create_user(
    user_in: OwnerUserCreate,
    current_user: UserModel = Depends(require_role(UserRole.OWNER)),
    db: Session = Depends(get_db)
):
    # ✓ Checks if current_user is superadmin (good)
    if current_user.is_superadmin:
        raise HTTPException(...)

    # ✓ Validates email doesn't exist in tenant (good)
    existing_user = db.query(UserModel).filter(
        func.lower(UserModel.email) == user_in.email.lower(),
        UserModel.tenant_id == current_user.tenant_id  # Uses current tenant
    ).first()

    # ✓ Creates user with current_user.tenant_id (good)
    new_user = UserModel(
        ...
        tenant_id=current_user.tenant_id,
        ...
    )
```

**Analysis**: This is actually SECURE. The code correctly associates created users with `current_user.tenant_id` and validates against that tenant. No issue found here.

---

### 1.4 Password Reset Token Can Be Used After Email Verification
**File**: [app/api/v1/endpoints/auth.py](app/api/v1/endpoints/auth.py#L700-L850)
**Issue**: No email verification enforcement before allowing password reset

**Scenario**:
1. New tenant owner created via `/tenants/register` - NOT verified (`is_verified=False`)
2. User immediately calls `/forgot-password` with their email
3. Backend generates reset token without checking if user is verified
4. User can reset password and access system WITHOUT verifying email

**Impact**:
- Email verification enforcement bypassed
- Users can use password reset flow instead of email verification
- Contradicts requirement: "Email verification is mandatory"

**Fix**: Add email verification check in `reset_password()` endpoint:
```python
if not user.is_verified:
    return success_message  # Don't allow reset if not verified
```

---

### 1.5 No Validation of User Email Format in Multi-Tenant Login
**File**: [app/api/v1/endpoints/auth.py](app/api/v1/endpoints/auth.py#L755-L760)
**Issue**: Email case handling inconsistency in `resend_verification_email()`

```python
# In resend_verification_email() - DOES NOT lowercase email
user = db.query(UserModel).filter(
    UserModel.email == resend_request.email  # ← Case-sensitive comparison!
).first()

# But in login() - DOES lowercase email
users = db.query(UserModel).filter(
    UserModel.email.ilike(email)  # ← Case-insensitive via ilike()
).first()
```

**Impact**:
- User with email "John@Example.com" created via tenant registration
- Cannot resend verification with "john@example.com" (different case)
- Confusing UX, potential account access issues

**Fix**: Ensure consistent case-insensitive comparison in all email queries

---

### 1.6 Race Condition in User Email Uniqueness Check
**File**: [app/api/v1/endpoints/users.py](app/api/v1/endpoints/users.py#L50-L60)
**Issue**: TOCTOU (Time-of-Check-Time-of-Use) vulnerability in email uniqueness

```python
# Check if email already exists
existing_user = db.query(UserModel).filter(...).first()
if existing_user:
    raise HTTPException(...)

# Create user - RACE CONDITION WINDOW
new_user = UserModel(
    email=user_in.email.lower(),
    ...
)
db.add(new_user)
db.commit()  # ← Can fail here if another request creates same email
```

**Impact**:
- Concurrent requests can create duplicate emails
- Unique constraint violation throws 500 error instead of 400
- Poor error handling and UX

**Fix**: Rely on database unique constraint and catch `IntegrityError`:
```python
try:
    db.add(new_user)
    db.commit()
except IntegrityError:
    db.rollback()
    raise HTTPException(status_code=400, detail="Email already exists")
```

---

### 1.7 Unverified Email Users Gain Full System Access
**File**: [app/api/v1/endpoints/auth.py](app/api/v1/endpoints/auth.py#L750-L850)
**Issue**: Tenant owner created via `/tenants/register` is not verified but can access system

```python
# In register_tenant_with_owner()
db_owner = UserModel(
    email=tenant_register.owner.email,
    ...
    is_verified=False,  # ← Not verified initially
    verification_token=verification_token,
    ...
)

# But in login, the endpoint does NOT check is_verified
# Any endpoint that calls get_current_user() allows unverified users
@router.get("/me")
def get_current_user_info(
    current_user: UserModel = Depends(get_current_user)  # Allows unverified!
):
    return current_user
```

**Impact**:
- Unverified users can access all endpoints
- Email verification is not enforced
- Security: Unverified accounts could be compromised

**Fix**: Check `is_verified` in `get_current_user()` or add middleware

---

## 2. 🟠 HIGH PRIORITY ISSUES

### 2.1 No Error Handling for Celery Task Failures
**File**: [app/api/v1/endpoints/tenants.py](app/api/v1/endpoints/tenants.py#L180-L195)
**Issue**: Email sending task failures are silently swallowed

```python
try:
    send_verification_email_task.delay(...)
except Exception as e:
    logger.warning("Failed to queue verification email...")
    # ✓ Doesn't fail registration, which is good
    # ✗ But user has no way to know email wasn't sent
```

**Impact**:
- Tenant owner never receives verification email
- Owner tries to verify but token doesn't exist in inbox
- No feedback mechanism to retry

**Fix**: Return warning in response or implement retry logic

---

### 2.2 Missing Rate Limit on Admin Endpoints
**File**: [app/api/v1/endpoints/admin.py](app/api/v1/endpoints/admin.py#L1-L100)
**Issue**: Tenant suspension and user management endpoints lack rate limiting

**Endpoints without rate limits:**
- `PUT /api/v1/admin/tenants/{tenant_id}/suspend` - Can suspend tenant repeatedly
- User/Tenant listing endpoints - No pagination limits enforced

**Impact**:
- DoS vulnerability: Attacker can spam tenant suspensions
- Rate limit protection missing for critical operations

**Fix**: Add `@limiter.limit()` decorator to all admin endpoints

---

### 2.3 Insufficient Tenant Isolation in Tenant Updates
**File**: [app/api/v1/endpoints/tenants.py](app/api/v1/endpoints/tenants.py#L325-L360)
**Issue**: Owner can update tenant they don't fully own

```python
def update_tenant(..., current_user, ...):
    tenant = db.query(TenantModel).filter(TenantModel.id == tenant_id).first()

    if not current_user.is_superadmin:
        # Check ownership
        if (current_user.tenant_id != tenant_id
            or current_user.role != UserRole.OWNER):
            raise HTTPException(...)
```

**Current Logic**: Only checks if `current_user.role == OWNER`, doesn't verify if there could be multiple owners where one shouldn't be updating

**Impact**: Low security impact but potential for confusion with co-owners

---

### 2.4 Long String Truncation Issues in Error Messages
**File**: [app/api/v1/endpoints/auth.py](app/api/v1/endpoints/auth.py#L656-L658)
**Issue**: Multi-line string escape in error messages

```python
detail="Email is already verified.\
    You can now log in to your account."
# ✗ Creates: "Email is already verified.    You can now log in..."
# ✓ Should be: "Email is already verified. You can now log in..."
```

**Impact**: Minor - Spacing issues in error responses

---

## 3. 🟡 MEDIUM PRIORITY ISSUES

### 3.1 Missing Email Verification Requirement in Critical Flows
**File**: Multiple files
**Issue**: No enforcement of `is_verified` before:
- Creating invoices
- Sending emails
- Accessing reports
- Making API calls

**Impact**:
- Unverified users can perform critical actions
- Business logic vulnerability

**Fix**: Add `@require_verified_email` to sensitive endpoints (already defined in `deps.py` but not used)

---

### 3.2 Password Change Flag Not Enforced in Multi-Tenant Selection
**File**: [app/api/v1/endpoints/auth.py](app/api/v1/endpoints/auth.py#L500-L530)
**Issue**: User with `must_change_password=True` can call `/select-tenant` and bypass forced password change

```python
# In select_tenant()
# Returns tokens even if user.must_change_password == True
return {
    "access_token": access_token,
    "requires_password_change": user.must_change_password  # ← Only advisory
}
```

**Impact**:
- Forced password change can be bypassed via tenant selection
- Temporary passwords remain active indefinitely

**Fix**: Reject login if `must_change_password=True` before generating tokens

---

### 3.3 Superadmin Email Verification Not Enforced
**File**: [app/api/v1/endpoints/auth.py](app/api/v1/endpoints/auth.py#L40-L120)
**Issue**: Superadmin users created via `/auth/register` can bypass email verification

```python
db_user = UserModel(
    ...
    is_verified=False,  # Not verified
    verification_token=verification_token,
    is_superadmin=True,
)
# No subsequent check that superadmin must verify before accessing platform
```

**Impact**: Superadmins can access platform without email verification

---

### 3.4 No Transaction Rollback on Email Send Failure
**File**: [app/api/v1/endpoints/tenants.py](app/api/v1/endpoints/tenants.py#L175-L195)
**Issue**: In `register_tenant_with_owner()`, if email fails to send, user is still created

```python
db.commit()  # ← User and tenant created
# ... then ...
try:
    send_verification_email_task.delay(...)  # ← Can fail after commit
except Exception as e:
    logger.warning(...)  # ← Silently ignored
```

**Impact**:
- Tenant and owner created but owner never receives verification email
- Orphaned accounts in system
- Owner cannot verify and access system

**Fix**: Either send email before committing or implement email retry logic

---

## 4. 🟢 LOW PRIORITY ISSUES

### 4.1 Unused Dependency Import
**File**: [app/api/v1/endpoints/auth.py](app/api/v1/endpoints/auth.py#L1-L40)
**Issue**: Some imports may be unused

**Fix**: Run `pylint` or `isort` to clean up imports

---

### 4.2 Inconsistent Error Message Formatting
**Files**: Multiple
**Issue**: Some error messages use periods, some don't

**Example**:
```python
"User not found"  # No period
"Email already registered."  # With period
```

**Fix**: Standardize error message formatting

---

### 4.3 Missing Response Status Code on Delete Success
**File**: [app/api/v1/endpoints/users.py](app/api/v1/endpoints/users.py#L320)
**Issue**: User delete returns 200 without explicit status_code

```python
@router.delete("/{user_id}")
def delete_user(...):  # ← Should specify status_code=204
    ...
    return {"message": "User deactivated successfully"}
```

**Fix**: Add `status_code=status.HTTP_204_NO_CONTENT` to decorator

---

## Summary of Bugs by Category

| Category | Count | Severity |
|----------|-------|----------|
| Security Issues | 5 | 🔴 Critical |
| Validation Issues | 3 | 🔴 Critical |
| Email/Verification | 4 | 🔴 Critical + 🟠 High |
| Race Conditions | 1 | 🔴 Critical |
| Error Handling | 2 | 🟠 High |
| Rate Limiting | 1 | 🟠 High |
| Data Isolation | 1 | 🟠 High |
| Email Enforcement | 1 | 🟡 Medium |
| Multi-tenant Flow | 1 | 🟡 Medium |
| Code Quality | 2 | 🟢 Low |

---

## Immediate Actions Required

Before MVP production deployment, fix these 🔴 CRITICAL issues:

1. ✅ **Remove debug print statements** from `forgot_password()` - Takes 2 minutes
2. ✅ **Complete email verification logging** - Takes 5 minutes
3. ✅ **Enforce email verification** before password reset - Takes 10 minutes
4. ✅ **Fix email case sensitivity** in all queries - Takes 15 minutes
5. ✅ **Add IntegrityError handling** for race conditions - Takes 20 minutes
6. ✅ **Enforce email verification** in login flow - Takes 15 minutes
7. ✅ **Block password-change-required users** from tenant selection - Takes 10 minutes

**Total Time to Fix**: ~75 minutes

