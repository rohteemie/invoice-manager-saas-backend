# Email Verification Testing Guide

This guide provides step-by-step instructions for testing the email verification feature from end to end.

## Prerequisites

- The application is running on `http://localhost:8000`
- You have curl, jq, or Python installed for testing

## Quick Test with Python

Run this complete test script:

```bash
cd /home/runner/work/multi-tenant-saas-backend/multi-tenant-saas-backend
python << 'PYTHON_SCRIPT'
import requests
import json
import time

BASE_URL = "http://localhost:8000"
timestamp = int(time.time())

print("=== Email Verification End-to-End Test ===\n")

# Step 1: Create tenant with owner
print("Step 1: Creating a test tenant...")
tenant_data = {
    "name": f"Email Test Tenant {timestamp}",
    "domain": f"emailtest-{timestamp}.com",
    "description": "Test tenant for email verification",
    "owner": {
        "email": f"emailtest{timestamp}@example.com",
        "full_name": "Email Test User",
        "password": "SecurePassword123"
    }
}

response = requests.post(f"{BASE_URL}/api/v1/tenants/register", json=tenant_data)
if response.status_code == 201:
    tenant_result = response.json()
    owner_email = tenant_result["owner"]["email"]
    is_verified = tenant_result["owner"]["is_verified"]
    print(f"✓ Tenant created successfully")
    print(f"✓ Owner Email: {owner_email}")
    print(f"✓ Initial verification status: {is_verified}")
    
    # Step 2: Request verification
    print("\nStep 2: Requesting verification email...")
    verify_request = requests.post(
        f"{BASE_URL}/api/v1/auth/send-verification-email",
        params={"email": owner_email}
    )
    if verify_request.status_code == 200:
        verify_result = verify_request.json()
        verification_token = verify_result["verification_token"]
        print(f"✓ Verification token received")
        
        # Step 3: Verify email
        print("\nStep 3: Verifying email with token...")
        verify_response = requests.post(
            f"{BASE_URL}/api/v1/auth/verify-email",
            params={"token": verification_token}
        )
        if verify_response.status_code == 200:
            print("✓ Email verified successfully!")
            
            # Step 4: Try again (should be idempotent)
            print("\nStep 4: Verifying again (should be idempotent)...")
            verify_again = requests.post(
                f"{BASE_URL}/api/v1/auth/verify-email",
                params={"token": verification_token}
            )
            if "already verified" in verify_again.json().get("message", "").lower():
                print("✓ Correctly identified as already verified")
                
                # Step 5: Test invalid token
                print("\nStep 5: Testing with invalid token...")
                invalid_response = requests.post(
                    f"{BASE_URL}/api/v1/auth/verify-email",
                    params={"token": "invalid_token_123"}
                )
                if invalid_response.status_code == 400:
                    print("✓ Correctly rejected invalid token")
                    print("\n=== ✅ All Tests Passed Successfully ===")
                else:
                    print("❌ Invalid token should have been rejected")
            else:
                print("❌ Should have identified as already verified")
        else:
            print(f"❌ Verification failed: {verify_response.text}")
    else:
        print(f"❌ Failed to request verification: {verify_request.text}")
else:
    print(f"❌ Failed to create tenant: {response.text}")
PYTHON_SCRIPT
```

## Quick Test with cURL

```bash
# 1. Create tenant
RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/tenants/register \
  -H "Content-Type: application/json" \
  -d "{
    \"name\": \"Test Company $(date +%s)\",
    \"domain\": \"test-$(date +%s).com\",
    \"owner\": {
      \"email\": \"test-$(date +%s)@example.com\",
      \"full_name\": \"Test User\",
      \"password\": \"SecurePass123\"
    }
  }")

echo "Tenant created:"
echo "$RESPONSE" | jq

# 2. Extract email
EMAIL=$(echo "$RESPONSE" | jq -r '.owner.email')
echo "Owner email: $EMAIL"

# 3. Request verification
VERIFY_RESPONSE=$(curl -s -X POST "http://localhost:8000/api/v1/auth/send-verification-email?email=$EMAIL")
echo "Verification response:"
echo "$VERIFY_RESPONSE" | jq

# 4. Extract token
TOKEN=$(echo "$VERIFY_RESPONSE" | jq -r '.verification_token')
echo "Token: ${TOKEN:0:50}..."

# 5. Verify email
VERIFY_RESULT=$(curl -s -X POST "http://localhost:8000/api/v1/auth/verify-email?token=$TOKEN")
echo "Verify result:"
echo "$VERIFY_RESULT" | jq
```

## Running Automated Tests

```bash
# Run all email verification tests
pytest tests/test_email_verification.py -v

# Run specific test
pytest tests/test_email_verification.py::test_full_email_verification_workflow -v

# Run with detailed output
pytest tests/test_email_verification.py -vv -s

# Run all tests to ensure no regression
pytest tests/ -v
```

## Testing Scenarios

### Scenario 1: New User Registration and Verification

**Expected Flow:**
1. User registers → `is_verified: false`
2. Request verification → receives token
3. Verify with token → `is_verified: true`

### Scenario 2: Already Verified User

**Expected Flow:**
1. Request verification for verified user → Error: "Email already verified"

### Scenario 3: Invalid Token

**Expected Flow:**
1. Verify with invalid token → Error: "Invalid or expired verification token"

### Scenario 4: Expired Token

**Expected Flow:**
1. Wait 24+ hours
2. Verify with old token → Error: "Invalid or expired verification token"

### Scenario 5: Non-existent User

**Expected Flow:**
1. Request verification for non-existent email → Error: "User not found"

## Checking Verification Status

After verifying, you can check the user's status:

```bash
# Login
LOGIN_RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=$EMAIL&password=SecurePass123")

ACCESS_TOKEN=$(echo "$LOGIN_RESPONSE" | jq -r '.access_token')

# Get user profile
curl -X GET http://localhost:8000/api/v1/users/me \
  -H "Authorization: Bearer $ACCESS_TOKEN" | jq
```

## Interactive Testing with Swagger UI

1. Start the server: `uvicorn app.main:app --reload`
2. Open browser: http://localhost:8000/docs
3. Find the auth section
4. Test endpoints interactively

## Expected Test Results

When all tests pass, you should see:

```
tests/test_email_verification.py::test_send_verification_email_success PASSED
tests/test_email_verification.py::test_send_verification_email_already_verified PASSED
tests/test_email_verification.py::test_send_verification_email_nonexistent_user PASSED
tests/test_email_verification.py::test_verify_email_success PASSED
tests/test_email_verification.py::test_verify_email_already_verified PASSED
tests/test_email_verification.py::test_verify_email_invalid_token PASSED
tests/test_email_verification.py::test_verify_email_expired_token PASSED
tests/test_email_verification.py::test_verify_email_wrong_token_type PASSED
tests/test_email_verification.py::test_email_verification_token_creation_and_verification PASSED
tests/test_email_verification.py::test_verify_email_for_nonexistent_user PASSED
tests/test_email_verification.py::test_full_email_verification_workflow PASSED
tests/test_email_verification.py::test_verification_token_cannot_be_reused_maliciously PASSED

12 passed
```

## Troubleshooting

**Problem**: Server not responding
- **Solution**: Check if server is running with `curl http://localhost:8000/health`

**Problem**: "User not found" error
- **Solution**: Make sure you're using the correct email from the registration response

**Problem**: Token validation fails immediately
- **Solution**: Verify SECRET_KEY is set in .env file

**Problem**: Rate limit errors
- **Solution**: Wait for rate limit window to reset or restart server

## Documentation References

- [Full Documentation](docs/email_verification.md)
- [Quick Reference](docs/email_verification_quickstart.md)
- [Implementation Summary](docs/EMAIL_VERIFICATION_SUMMARY.md)
- [API Documentation](http://localhost:8000/docs)

## Success Criteria

✅ Can create a new user with `is_verified: false`
✅ Can request verification email and receive token
✅ Can verify email with token
✅ User status changes to `is_verified: true`
✅ Cannot verify already verified email
✅ Invalid tokens are rejected
✅ Expired tokens are rejected
✅ All 12 tests pass
✅ No security vulnerabilities found
✅ No regression in existing tests

---

**Last Updated**: November 3, 2024
**Status**: All tests passing ✅
