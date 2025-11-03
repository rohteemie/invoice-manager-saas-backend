# Email Verification Quick Reference Guide

## Quick Start

### 1. Register a User (Will be Unverified)
```bash
curl -X POST http://localhost:8000/api/v1/tenants/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Company",
    "domain": "mycompany.com",
    "description": "My company description",
    "owner": {
      "email": "owner@mycompany.com",
      "full_name": "Company Owner",
      "password": "SecurePass123"
    }
  }'
```

**Response includes**: `is_verified: false`

### 2. Request Verification Email
```bash
curl -X POST "http://localhost:8000/api/v1/auth/send-verification-email?email=owner@mycompany.com"
```

**Response**: Returns a verification token (in production, this would be emailed)

### 3. Verify Email
```bash
curl -X POST "http://localhost:8000/api/v1/auth/verify-email?token=YOUR_TOKEN_HERE"
```

**Response**: `"message": "Email verified successfully"`

## API Endpoints

| Endpoint | Method | Rate Limit | Description |
|----------|--------|------------|-------------|
| `/api/v1/auth/send-verification-email` | POST | 3/hour | Send verification token |
| `/api/v1/auth/verify-email` | POST | 10/hour | Verify email with token |

## Common Responses

### Success: Email Verification Sent (200)
```json
{
  "message": "Verification email sent",
  "verification_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "note": "In production, this token would be sent via email"
}
```

### Success: Email Verified (200)
```json
{
  "message": "Email verified successfully",
  "email": "user@example.com"
}
```

### Success: Already Verified (200)
```json
{
  "message": "Email already verified"
}
```

### Error: User Not Found (404)
```json
{
  "detail": "User not found"
}
```

### Error: Already Verified (400)
```json
{
  "detail": "Email already verified"
}
```

### Error: Invalid/Expired Token (400)
```json
{
  "detail": "Invalid or expired verification token"
}
```

### Error: Rate Limit (429)
```json
{
  "detail": "Rate limit exceeded"
}
```

## Testing with cURL

### Complete Workflow
```bash
# 1. Create tenant + owner
RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/tenants/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Company",
    "domain": "testcompany.com",
    "description": "Test",
    "owner": {
      "email": "test@example.com",
      "full_name": "Test User",
      "password": "SecurePass123"
    }
  }')

# 2. Extract email
EMAIL=$(echo "$RESPONSE" | jq -r '.owner.email')
echo "Email: $EMAIL"

# 3. Request verification
VERIFY_RESPONSE=$(curl -s -X POST "http://localhost:8000/api/v1/auth/send-verification-email?email=$EMAIL")

# 4. Extract token
TOKEN=$(echo "$VERIFY_RESPONSE" | jq -r '.verification_token')
echo "Token: ${TOKEN:0:50}..."

# 5. Verify email
curl -X POST "http://localhost:8000/api/v1/auth/verify-email?token=$TOKEN" | jq
```

## Testing with Python

```python
import requests

BASE_URL = "http://localhost:8000"

# 1. Create tenant
response = requests.post(
    f"{BASE_URL}/api/v1/tenants/register",
    json={
        "name": "Test Company",
        "domain": "testcompany.com",
        "description": "Test",
        "owner": {
            "email": "test@example.com",
            "full_name": "Test User",
            "password": "SecurePass123"
        }
    }
)
tenant_data = response.json()
email = tenant_data["owner"]["email"]

# 2. Request verification
verify_req = requests.post(
    f"{BASE_URL}/api/v1/auth/send-verification-email",
    params={"email": email}
)
token = verify_req.json()["verification_token"]

# 3. Verify email
verify_res = requests.post(
    f"{BASE_URL}/api/v1/auth/verify-email",
    params={"token": token}
)
print(verify_res.json())
```

## Running Tests

```bash
# Run all email verification tests
pytest tests/test_email_verification.py -v

# Run specific test
pytest tests/test_email_verification.py::test_full_email_verification_workflow -v

# Run with coverage
pytest tests/test_email_verification.py --cov=app -v
```

## Token Details

- **Algorithm**: HS256 (HMAC with SHA-256)
- **Expiration**: 24 hours
- **Type**: `email_verification`
- **Payload**: Contains email in `sub` field

## Security Features

✅ JWT-based tokens with expiration
✅ Rate limiting (3 requests/hour for send, 10/hour for verify)
✅ Token type validation
✅ Idempotent verification (safe to call multiple times)
✅ Database transaction safety

## Production Checklist

Before deploying to production:

- [ ] Configure email service (SendGrid, AWS SES, etc.)
- [ ] Update `send_verification_email` to send actual emails
- [ ] Remove token from API response
- [ ] Set up frontend verification page
- [ ] Update FRONTEND_URL in environment variables
- [ ] Test email delivery
- [ ] Monitor rate limits
- [ ] Set up Sentry for error tracking

## Documentation Links

- [Full Documentation](../docs/email_verification.md)
- [API Documentation](http://localhost:8000/docs)
- [Test Suite](../tests/test_email_verification.py)

## Need Help?

- Check the [full documentation](../docs/email_verification.md)
- View API docs at `/docs` or `/redoc`
- Run the test suite for examples
- Check server logs for detailed error messages
