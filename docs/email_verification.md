# Email Verification Feature Documentation

## Overview

The email verification feature provides a secure mechanism to verify user email addresses during registration. This feature uses JWT tokens with a 24-hour expiration to ensure email ownership before granting full access to the system.

## Features

- ✅ Secure JWT-based email verification tokens (24-hour expiration)
- ✅ Email verification status tracking in user profile
- ✅ Protection against duplicate verification requests
- ✅ Rate limiting to prevent abuse
- ✅ Comprehensive test coverage (12 tests)

## Architecture

### Database Schema

The `users` table includes an `is_verified` boolean field:

```python
is_verified = Column(Boolean, default=False)
```

When a user registers, `is_verified` is set to `False` by default. After email verification, it becomes `True`.

### Security Implementation

Email verification tokens are implemented using JWT (JSON Web Tokens) with the following properties:

- **Algorithm**: HS256
- **Expiration**: 24 hours
- **Token Type**: `email_verification`
- **Payload**: Contains the user's email address in the `sub` field

## API Endpoints

### 1. Send Verification Email

**Endpoint**: `POST /api/v1/auth/send-verification-email`

**Rate Limit**: 3 requests per hour per IP

**Query Parameters**:
- `email` (string, required): The user's email address

**Description**: Generates and returns a verification token for the specified email address.

**Success Response** (200):
```json
{
  "message": "Verification email sent",
  "verification_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "note": "In production, this token would be sent via email"
}
```

**Error Responses**:
- `404 Not Found`: User not found
- `400 Bad Request`: Email already verified
- `429 Too Many Requests`: Rate limit exceeded

**Example Request**:
```bash
curl -X POST "http://localhost:8000/api/v1/auth/send-verification-email?email=user@example.com"
```

### 2. Verify Email

**Endpoint**: `POST /api/v1/auth/verify-email`

**Rate Limit**: 10 requests per hour per IP

**Query Parameters**:
- `token` (string, required): The verification token received via email

**Description**: Verifies the email address using the provided token and marks the user as verified.

**Success Response** (200):
```json
{
  "message": "Email verified successfully",
  "email": "user@example.com"
}
```

**Error Responses**:
- `400 Bad Request`: Invalid or expired verification token
- `404 Not Found`: User not found
- `429 Too Many Requests`: Rate limit exceeded

**Example Request**:
```bash
curl -X POST "http://localhost:8000/api/v1/auth/verify-email?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

## Testing Guide

### Running the Test Suite

The email verification feature includes comprehensive tests covering all scenarios:

```bash
# Run all email verification tests
pytest tests/test_email_verification.py -v

# Run a specific test
pytest tests/test_email_verification.py::test_full_email_verification_workflow -v

# Run with coverage
pytest tests/test_email_verification.py --cov=app.api.v1.endpoints.auth --cov=app.core.security -v
```

### Test Coverage

The test suite includes 12 tests covering:

1. ✅ Successful verification email sending
2. ✅ Already verified user handling
3. ✅ Non-existent user handling
4. ✅ Successful email verification
5. ✅ Already verified email re-verification
6. ✅ Invalid token rejection
7. ✅ Expired token rejection
8. ✅ Wrong token type rejection
9. ✅ Token creation and verification
10. ✅ Non-existent user verification attempt
11. ✅ Full end-to-end workflow
12. ✅ Token security and idempotency

## Manual Testing Instructions

### End-to-End Manual Testing

Follow these steps to manually test the email verification feature:

#### Step 1: Register a New User

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "testuser@example.com",
    "full_name": "Test User",
    "password": "SecurePass123",
    "role": "attendant",
    "tenant_id": "YOUR_TENANT_ID"
  }'
```

**Expected Response**: User created with `is_verified: false`

```json
{
  "email": "testuser@example.com",
  "full_name": "Test User",
  "role": "attendant",
  "tenant_id": "...",
  "is_verified": false,
  "is_active": true,
  "id": "...",
  "created_at": "2024-11-03T...",
  "updated_at": "2024-11-03T..."
}
```

#### Step 2: Request Verification Email

```bash
curl -X POST "http://localhost:8000/api/v1/auth/send-verification-email?email=testuser@example.com"
```

**Expected Response**: Verification token generated

```json
{
  "message": "Verification email sent",
  "verification_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0dXNlckBleGFtcGxlLmNvbSIsInR5cGUiOiJlbWFpbF92ZXJpZmljYXRpb24iLCJleHAiOjE3MzA3MzQyMTV9.example_signature",
  "note": "In production, this token would be sent via email"
}
```

**Note**: Copy the `verification_token` value for the next step.

#### Step 3: Verify Email Address

```bash
curl -X POST "http://localhost:8000/api/v1/auth/verify-email?token=YOUR_VERIFICATION_TOKEN"
```

Replace `YOUR_VERIFICATION_TOKEN` with the token from Step 2.

**Expected Response**: Email verified successfully

```json
{
  "message": "Email verified successfully",
  "email": "testuser@example.com"
}
```

#### Step 4: Verify User Status

Login to verify the user can access the system:

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=testuser@example.com&password=SecurePass123"
```

Then fetch the user profile to confirm verification status:

```bash
curl -X GET http://localhost:8000/api/v1/users/me \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**Expected Response**: User profile shows `is_verified: true`

### Testing Error Scenarios

#### Test 1: Already Verified Email

Try requesting verification for an already verified email:

```bash
curl -X POST "http://localhost:8000/api/v1/auth/send-verification-email?email=testuser@example.com"
```

**Expected Response**: `400 Bad Request` with message "Email already verified"

#### Test 2: Invalid Token

Try verifying with an invalid token:

```bash
curl -X POST "http://localhost:8000/api/v1/auth/verify-email?token=invalid_token_123"
```

**Expected Response**: `400 Bad Request` with message "Invalid or expired verification token"

#### Test 3: Non-existent User

Try requesting verification for a non-existent email:

```bash
curl -X POST "http://localhost:8000/api/v1/auth/send-verification-email?email=nonexistent@example.com"
```

**Expected Response**: `404 Not Found` with message "User not found"

#### Test 4: Expired Token

Wait 24+ hours after generating a token, then try to use it:

```bash
curl -X POST "http://localhost:8000/api/v1/auth/verify-email?token=EXPIRED_TOKEN"
```

**Expected Response**: `400 Bad Request` with message "Invalid or expired verification token"

## Interactive Testing with Swagger UI

You can also test the email verification feature using the built-in Swagger UI:

1. Start the application:
   ```bash
   uvicorn app.main:app --reload
   ```

2. Open your browser and navigate to:
   ```
   http://localhost:8000/docs
   ```

3. Find the **auth** section and expand the email verification endpoints:
   - `POST /api/v1/auth/send-verification-email`
   - `POST /api/v1/auth/verify-email`

4. Click "Try it out" and follow the workflow described in the manual testing section above.

## Production Deployment Considerations

### Email Service Integration

In production, the verification token should be sent via email rather than returned in the API response. To implement this:

1. **Configure an email service** (e.g., SendGrid, AWS SES, Mailgun)
2. **Update the `send_verification_email` endpoint** to:
   ```python
   # Instead of returning the token
   # Send it via email
   send_email(
       to=email,
       subject="Verify your email address",
       body=f"Click here to verify: {FRONTEND_URL}/verify?token={verification_token}"
   )
   ```
3. **Remove the token from the response** for security

### Environment Variables

Add these to your `.env` file:

```env
# Email Configuration
EMAIL_SERVICE_API_KEY=your_email_service_api_key
EMAIL_FROM_ADDRESS=noreply@yourdomain.com
EMAIL_FROM_NAME=Your App Name
FRONTEND_URL=https://your-frontend-url.com
```

### Security Best Practices

1. **HTTPS Only**: Always use HTTPS in production
2. **Rate Limiting**: The endpoints are already rate-limited (3/hour for send, 10/hour for verify)
3. **Token Expiration**: Tokens expire after 24 hours
4. **One-Time Use**: While tokens can be verified multiple times (idempotent), once verified, new verification requests are rejected
5. **Email Validation**: Email format is validated using Pydantic's EmailStr

## Troubleshooting

### Common Issues

**Issue**: "Email already verified" error when testing
- **Solution**: Use a different email address or manually set `is_verified=False` in the database

**Issue**: Token validation fails immediately
- **Solution**: Verify that `SECRET_KEY` in `.env` matches the one used to generate tokens

**Issue**: Rate limit errors during testing
- **Solution**: Wait for the rate limit window to reset or restart the server to clear Redis cache

**Issue**: "User not found" when verifying
- **Solution**: Ensure the email in the token matches an existing user in the database

## Integration with Existing Features

### User Registration Flow

```
1. User registers → is_verified = False
2. System sends verification email (returns token in dev mode)
3. User clicks verification link
4. System verifies token and sets is_verified = True
5. User can now fully access the system
```

### Current Implementation Status

- ✅ User model has `is_verified` field
- ✅ Token generation and validation
- ✅ Verification endpoints
- ✅ Rate limiting
- ✅ Comprehensive tests
- ⚠️ Email sending (mocked - returns token in response)
- ℹ️ Login does NOT currently require email verification (design choice for backward compatibility)

### Future Enhancements

1. **Email Service Integration**: Replace token return with actual email sending
2. **Verification Required Login**: Optionally require email verification before allowing login
3. **Resend Verification**: Add explicit endpoint to resend verification email
4. **Verification Reminder**: Send reminder emails for unverified accounts after X days
5. **Email Change Verification**: Require verification when users update their email address

## Code References

### Key Files

- **Security Functions**: `/app/core/security.py`
  - `create_email_verification_token()`
  - `verify_email_verification_token()`

- **API Endpoints**: `/app/api/v1/endpoints/auth.py`
  - `POST /send-verification-email`
  - `POST /verify-email`

- **User Model**: `/app/models/user.py`
  - `is_verified` field

- **Tests**: `/tests/test_email_verification.py`
  - Comprehensive test suite

## Support

For questions or issues:
1. Check this documentation
2. Review the test suite for examples
3. Check the API documentation at `/docs`
4. Open an issue on the GitHub repository

## Changelog

### Version 1.0.0 (2024-11-03)
- Initial implementation of email verification feature
- Added JWT-based verification tokens
- Implemented rate-limited endpoints
- Created comprehensive test suite (12 tests)
- Added documentation and manual testing guide
