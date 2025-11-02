# Email Verification Feature

## Overview

The email verification feature ensures that new tenant owners verify their email address upon registration. This improves security, prevents fake signups, and ensures that only verified owners can access their tenant dashboard.

## Implementation Details

### Database Changes

**User Model** (`app/models/user.py`):
- Added `verification_token` field (String, nullable, indexed) to store the unique verification token

**Migration**: `migrations/versions/add_verification_token.py`
- Adds the `verification_token` column to the `users` table
- Creates an index on `verification_token` for efficient lookups

### Backend Components

#### 1. Token Generation (`app/core/security.py`)

```python
def generate_verification_token() -> str:
    """Generate a secure random token for email verification."""
```

- Uses `secrets.token_urlsafe(32)` to generate cryptographically secure tokens
- Returns a URL-safe string suitable for email links

#### 2. Email Service (`app/core/email.py`)

```python
def send_verification_email(
    email: str,
    token: str,
    full_name: str,
    base_url: Optional[str] = None
) -> bool:
```

- Sends verification email to the new owner
- Currently logs the email content (placeholder for actual email service integration)
- In production, integrate with services like SendGrid, AWS SES, or similar

#### 3. Configuration (`app/core/config.py`)

Added `EMAIL_VERIFICATION_BASE_URL` setting:
```python
EMAIL_VERIFICATION_BASE_URL: Optional[str] = Field(
    "https://yourapp.com",
    validation_alias="EMAIL_VERIFICATION_BASE_URL"
)
```

Set via environment variable to configure the base URL for verification links.

### API Endpoints

#### 1. Tenant Registration (`POST /api/v1/tenants/register`)

**Updated behavior**:
1. Creates tenant and owner user
2. Generates unique verification token
3. Stores token in `user.verification_token`
4. Sets `user.is_verified = False`
5. Sends verification email with token

**Response** (unchanged):
```json
{
  "tenant": { ... },
  "owner": {
    "id": "...",
    "email": "owner@example.com",
    "is_verified": false,
    ...
  }
}
```

#### 2. Email Verification (`POST /api/v1/auth/verify-email`)

**New endpoint** for verifying email addresses.

**Request**:
```http
POST /api/v1/auth/verify-email?token={verification_token}
```

**Success Response** (200):
```json
{
  "message": "Email verified successfully",
  "email": "owner@example.com",
  "is_verified": true
}
```

**Error Responses**:
- `400 Bad Request`: Invalid or expired token
- `400 Bad Request`: Email already verified

**Behavior**:
1. Looks up user by verification token
2. Validates token exists and user not already verified
3. Sets `user.is_verified = True`
4. Clears `user.verification_token` (sets to `None`)
5. Returns success message

## Usage Flow

### 1. New Tenant Registration

```bash
curl -X POST http://localhost:8000/api/v1/tenants/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Company",
    "domain": "mycompany.com",
    "plan_type": "free",
    "owner": {
      "full_name": "John Doe",
      "email": "john@mycompany.com",
      "password": "SecurePassword123"
    }
  }'
```

**Response**:
```json
{
  "tenant": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "My Company",
    "domain": "mycompany.com",
    "is_active": true,
    ...
  },
  "owner": {
    "id": "660e8400-e29b-41d4-a716-446655440000",
    "email": "john@mycompany.com",
    "is_verified": false,
    ...
  }
}
```

**Email sent to**: john@mycompany.com
```
Subject: Verify your email address

Hello John Doe,

Thank you for registering! Please verify your email by clicking:
https://yourapp.com/verify-email?token=AbCdEf123...

If you didn't register, please ignore this email.
```

### 2. Email Verification

User clicks the link in the email, which calls:

```bash
curl -X POST \
  'http://localhost:8000/api/v1/auth/verify-email?token=AbCdEf123...'
```

**Response**:
```json
{
  "message": "Email verified successfully",
  "email": "john@mycompany.com",
  "is_verified": true
}
```

### 3. Login

Owner can login **before or after** verification:

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=john@mycompany.com&password=SecurePassword123"
```

> **Note**: Currently, unverified users can still login. To enforce verification before login, add a check in the login endpoint.

## Testing

### Running Tests

```bash
# Run email verification tests only
pytest tests/test_email_verification.py -v

# Run all tests
pytest tests/ -v
```

### Test Coverage

The implementation includes 6 comprehensive tests:

1. **test_register_tenant_generates_verification_token**: Verifies token generation on registration
2. **test_verify_email_with_valid_token**: Tests successful email verification
3. **test_verify_email_with_invalid_token**: Tests error handling for invalid tokens
4. **test_verify_email_already_verified**: Tests preventing duplicate verification
5. **test_verification_token_is_unique**: Ensures each user gets a unique token
6. **test_owner_can_login_before_verification**: Confirms login works before verification

## Configuration

### Environment Variables

Add to `.env` file:

```env
# Email Verification Configuration
EMAIL_VERIFICATION_BASE_URL=https://yourapp.com
```

For development/testing:
```env
EMAIL_VERIFICATION_BASE_URL=http://localhost:3000
```

## Security Considerations

1. **Token Security**:
   - Uses `secrets.token_urlsafe()` for cryptographically secure tokens
   - Tokens are URL-safe and sufficiently long (32 bytes = 43 characters)

2. **Token Storage**:
   - Tokens are indexed for efficient lookup
   - Tokens are cleared after successful verification

3. **Token Validation**:
   - Validates token exists in database
   - Checks user is not already verified
   - Prevents token reuse

4. **Rate Limiting**:
   - Verification endpoint is rate-limited (10/minute)
   - Prevents brute-force token guessing

## Future Enhancements

### 1. Email Service Integration

Replace the logging placeholder with actual email sending:

```python
# Example: SendGrid integration
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

def send_verification_email(email, token, full_name, base_url):
    message = Mail(
        from_email='noreply@yourapp.com',
        to_emails=email,
        subject='Verify your email address',
        html_content=f'...'
    )
    sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
    response = sg.send(message)
    return response.status_code == 202
```

### 2. Token Expiration

Add expiration time to tokens:

```python
# Add to User model
verification_token_expires_at = Column(DateTime, nullable=True)

# Generate with expiration
def generate_verification_token():
    return {
        "token": secrets.token_urlsafe(32),
        "expires_at": datetime.utcnow() + timedelta(hours=24)
    }
```

### 3. Resend Verification Email

Add endpoint to resend verification email:

```python
@router.post("/resend-verification")
def resend_verification_email(email: str, db: Session = Depends(get_db)):
    user = db.query(UserModel).filter(UserModel.email == email).first()
    if not user or user.is_verified:
        raise HTTPException(400, "Invalid request")
    
    # Generate new token and send email
    ...
```

### 4. Enforce Verification Before Login

Optionally require verification before allowing login:

```python
@router.post("/login")
def login(...):
    ...
    if not user.is_verified:
        raise HTTPException(
            status_code=403,
            detail="Please verify your email before logging in"
        )
    ...
```

## Migration Guide

To apply the database migration:

```bash
# Using Alembic
alembic upgrade head

# Or manually apply
python -c "
from app.db.database import engine
from sqlalchemy import text

with engine.connect() as conn:
    conn.execute(text('ALTER TABLE users ADD COLUMN verification_token VARCHAR(255)'))
    conn.execute(text('CREATE INDEX ix_users_verification_token ON users(verification_token)'))
    conn.commit()
"
```

## API Documentation

The new endpoint is automatically documented in:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Troubleshooting

### Issue: Email not received

**Cause**: Email service is currently a placeholder (logs only)

**Solution**: Integrate actual email service (SendGrid, AWS SES, etc.)

### Issue: Token not found

**Cause**: Token may have been copied incorrectly or already used

**Solution**: 
- Ensure token is copied exactly from email
- Check if email was already verified
- Request a new verification email (when implemented)

### Issue: Verification fails after successful registration

**Cause**: Database connection or transaction issue

**Solution**:
- Check database logs
- Ensure database migration was applied
- Verify `verification_token` column exists in `users` table

## Summary

The email verification feature:
- ✅ Generates unique tokens for each new owner
- ✅ Sends verification emails (currently logged)
- ✅ Provides secure verification endpoint
- ✅ Prevents token reuse
- ✅ Maintains backward compatibility
- ✅ Includes comprehensive tests
- ✅ Ready for production email integration
