# Password Reset Feature Documentation

## Overview

The password reset feature provides a secure, token-based flow for users who have forgotten their passwords. This implementation follows OWASP security best practices and is fully compliant with GDPR and ISO standards.

## Architecture

### Endpoints

#### 1. POST `/api/v1/auth/forgot-password`

Initiates the password reset process by sending a reset link to the user's email.

**Request Body:**
```json
{
  "email": "user@example.com"
}
```

**Response:** (200 OK - Always returns success to prevent email enumeration)
```json
{
  "message": "If the email exists in our system, a password reset link will be sent.",
  "email": "user@example.com"
}
```

**Rate Limit:** 3 requests per hour per IP

**Security Features:**
- Always returns success response (prevents email enumeration)
- Generates secure URL-safe random token (32 bytes)
- Sets token expiration to 30 minutes
- Stores token hash in database
- Logs all password reset requests for audit
- Password reset tokens are only issued for verified accounts

---

#### 2. POST `/api/v1/auth/reset-password`

Validates the reset token and updates the user's password.

**Request Body:**
```json
{
  "token": "secure-reset-token-from-email",
  "new_password": "NewSecurePassword123"
}
```

**Response:** (200 OK)
```json
{
  "message": "Password has been reset successfully. You can now log in with your new password.",
  "email": "user@example.com"
}
```

**Error Responses:**
- 400 Bad Request - Invalid or expired token
- 403 Forbidden - User account is inactive
- 422 Validation Error - Password doesn't meet requirements

**Rate Limit:** 5 requests per hour per IP

**Validation:**
- Token must be valid and not expired
- Token must exist in database
- Password must be at least 8 characters
- User account must be active
- User account must be verified
- Token is invalidated after successful reset

---

## Database Schema

### User Model Extensions

Two new fields added to the `users` table:

```python
reset_password_token = Column(String(255), nullable=True, index=True)
reset_password_token_expires_at = Column(DateTime, nullable=True)
```

**Migration File:** `migrations/versions/add_password_reset_tokens.py`

---

## Email Template

The password reset email includes:

- **Plain Text Version:** For email clients that don't support HTML
- **HTML Version:** Professionally styled with security tips
- **Reset Link:** Unique, time-limited URL to reset password
- **Security Warnings:** Advice on password security best practices
- **Expiration Notice:** Clear indication that link expires in 30 minutes

**Email Provider:** SendGrid Web API v3

---

## Security Features

### 1. Token Generation
- Uses `secrets.token_urlsafe(32)` for cryptographically secure random tokens
- 32-byte tokens provide ~2^256 possible values
- Tokens are URL-safe (no special characters that need encoding)

### 2. Token Storage
- Stored as plain text (not hashed) for validation
- Indexed for fast lookup
- Automatically cleared after use or expiration

### 3. Token Expiration
- Default: 30 minutes (configurable via `PASSWORD_RESET_TOKEN_EXPIRATION_MINUTES`)
- Enforced both at database level and in application logic
- Expired tokens are rejected and cleared from database

### 4. Email Enumeration Prevention
- Always returns success message regardless of email existence
- Prevents attackers from discovering valid user emails
- Logs attempts for security monitoring

### 5. Rate Limiting
- Forgot password: 3 requests/hour (prevents spam)
- Reset password: 5 requests/hour (allows legitimate retries)
- IP-based rate limiting via SlowAPI

### 6. Audit Logging
- All password reset requests logged with user email and tenant ID
- Successful password resets logged separately
- Failed attempts logged for security monitoring
- Includes timestamp and IP address

### 7. Password Security
- Minimum 8 characters required
- Passwords hashed using bcrypt (cost factor 12)
- Old password immediately invalidated
- User can login with new password immediately

---

## Configuration

Add to `.env` file:

```bash
# Password reset token expiration in minutes (default: 30 minutes)
PASSWORD_RESET_TOKEN_EXPIRATION_MINUTES=30

# SendGrid email configuration
SENDGRID_API_KEY=your-sendgrid-api-key-here
EMAILS_FROM=noreply@yourapp.com
EMAIL_VERIFICATION_BASE_URL=https://yourapp.com
```

---

## Testing

### Test Coverage

The implementation includes 16 comprehensive tests:

1. **Forgot Password Tests:**
   - Existing user email
   - Non-existent email (security)
   - Invalid email format
   - Inactive user account
   - Token generation verification
   - Test mode link exposure

2. **Reset Password Tests:**
   - Valid token
   - Invalid token
   - Expired token
   - Short password (validation)
   - Inactive user
   - Login with new password
   - Cannot login with old password
   - Token cannot be reused

3. **Integration Tests:**
   - Full password reset flow
   - Password strength validation

### Running Tests

```bash
# Run password reset tests only
python -m pytest tests/test_password_reset.py -v

# Run all auth tests
python -m pytest tests/ -k "auth" -v

# Run full test suite
python -m pytest tests/ -v
```

---

## Usage Example

### 1. User Requests Password Reset

**Frontend:**
```javascript
const response = await fetch('/api/v1/auth/forgot-password', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    email: 'user@example.com'
  })
});

const data = await response.json();
console.log(data.message);
// "If the email exists in our system, a password reset link will be sent."
```

**Backend Actions:**
1. Validates email format
2. Looks up user by email
3. Generates secure reset token
4. Stores token with 30-minute expiration
5. Sends email with reset link
6. Logs request for audit

---

### 2. User Clicks Reset Link

Email contains link: `https://yourapp.com/reset-password?token=abc123...`

---

### 3. User Submits New Password

**Frontend:**
```javascript
const urlParams = new URLSearchParams(window.location.search);
const token = urlParams.get('token');

const response = await fetch('/api/v1/auth/reset-password', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    token: token,
    new_password: 'NewSecurePassword123'
  })
});

const data = await response.json();
if (response.ok) {
  console.log(data.message);
  // "Password has been reset successfully. You can now log in with your new password."
  // Redirect to login page
}
```

**Backend Actions:**
1. Validates token exists and not expired
2. Validates password meets requirements
3. Hashes new password with bcrypt
4. Updates user password
5. Invalidates reset token
6. Logs successful reset
7. Returns success message

---

## Error Handling

### Common Error Scenarios

#### 1. Token Expired
```json
{
  "detail": "Reset token has expired. Please request a new password reset."
}
```
**HTTP Status:** 400 Bad Request

#### 2. Invalid Token
```json
{
  "detail": "Invalid or expired reset token"
}
```
**HTTP Status:** 400 Bad Request

#### 3. Inactive Account
```json
{
  "detail": "User account is inactive"
}
```
**HTTP Status:** 403 Forbidden

#### 4. Weak Password
```json
{
  "detail": [
    {
      "loc": ["body", "new_password"],
      "msg": "ensure this value has at least 8 characters",
      "type": "value_error.any_str.min_length"
    }
  ]
}
```
**HTTP Status:** 422 Validation Error

---

## Compliance

### GDPR Compliance
- Uses email as primary identifier (not personal data)
- Password reset tokens automatically expire
- Audit logs track all password reset attempts
- Users can request password reset at any time

### ISO 27001 Compliance
- Secure token generation
- Time-limited access tokens
- Comprehensive audit logging
- Password strength requirements
- Rate limiting to prevent abuse

### OWASP Best Practices
- Prevents email enumeration
- Uses secure random token generation
- Implements proper token expiration
- Includes rate limiting
- Logs security events
- Validates all input
- Uses bcrypt for password hashing

---

## Monitoring & Maintenance

### Audit Log Examples

**Successful Reset Request:**
```
INFO - Password reset requested for user: user@example.com (tenant: abc-123)
```

**Successful Password Reset:**
```
INFO - Password successfully reset for user: user@example.com (tenant: abc-123)
```

**Failed Reset (Non-existent Email):**
```
INFO - Password reset requested for non-existent email: fake@example.com
```

**Failed Reset (Inactive User):**
```
WARNING - Password reset requested for inactive user: inactive@example.com
```

### Metrics to Monitor

1. **Password Reset Request Rate**
   - Track requests per hour/day
   - Alert on unusual spikes (possible attack)

2. **Token Expiration Rate**
   - Monitor how many tokens expire unused
   - May indicate email delivery issues

3. **Failed Reset Attempts**
   - Track invalid/expired token usage
   - May indicate brute force attempts

4. **Success Rate**
   - Monitor successful resets vs requests
   - Should be high for legitimate users

---

## Troubleshooting

### User Not Receiving Email

**Possible Causes:**
1. Email in spam folder
2. SendGrid API key not configured
3. Email address not in database
4. SendGrid account issues

**Solutions:**
1. Check SendGrid dashboard for delivery status
2. Verify SENDGRID_API_KEY in environment
3. Check application logs for email sending errors
4. Verify EMAILS_FROM is verified in SendGrid

### Token Expired Too Quickly

**Possible Causes:**
1. User took longer than 30 minutes
2. Clock skew between servers

**Solutions:**
1. Increase `PASSWORD_RESET_TOKEN_EXPIRATION_MINUTES`
2. Ensure server clocks are synchronized

### Rate Limit Hit

**Possible Causes:**
1. Legitimate user making multiple requests
2. Automated attack

**Solutions:**
1. Whitelist trusted IPs
2. Increase rate limit for forgot-password
3. Monitor logs for abuse patterns

---

## Future Enhancements

Potential improvements for future versions:

1. **Multi-Factor Authentication**
   - Require 2FA before allowing password reset
   - Send verification code to phone

2. **Password History**
   - Prevent reuse of last N passwords
   - Store password hashes with timestamp

3. **Security Questions**
   - Additional verification step
   - Fallback for email access issues

4. **Account Recovery**
   - Alternative recovery methods
   - Admin-assisted recovery flow

5. **Token Throttling**
   - Limit number of active tokens per user
   - Prevent token generation spam

6. **Email Templates**
   - Customizable templates per tenant
   - Internationalization support

---

## API Reference

For complete API documentation, see [API_STRUCTURE.md](./API_STRUCTURE.md)

For security considerations, see [SECURITY.md](./SECURITY.md)

For authentication flow, see [authentication.md](./authentication.md)
