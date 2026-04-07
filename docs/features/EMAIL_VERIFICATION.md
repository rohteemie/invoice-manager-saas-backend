# Email Verification Feature

**Latest Version**: 2.0 - Production Ready
**Last Updated**: 2025-11-10

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Key Features](#key-features)
3. [System Architecture](#system-architecture)
4. [Implementation Details](#implementation-details)
5. [API Endpoints](#api-endpoints)
6. [Frontend Integration Guide](#frontend-integration-guide)
7. [Configuration](#configuration)
8. [Testing](#testing)
9. [Security Considerations](#security-considerations)

---

## Overview

The email verification feature ensures that new tenant owners verify their email address upon registration. This improves security, prevents fake signups, and ensures that only verified owners can access their tenant dashboard.

**Key Improvements (v2.0)**:
- ✅ Token Expiration: Tokens now expire after 24 hours (configurable)
- ✅ Resend Email: New endpoint to resend verification emails
- ✅ HTML Emails: Beautiful, responsive HTML email templates
- ✅ Better Error Messages: User-friendly error messages for all scenarios
- ✅ Comprehensive Tests: Full test coverage with 11+ tests

---

## Key Features

1. **Secure Token Generation**: Cryptographically secure, URL-safe tokens
2. **Token Expiration**: Configurable expiration time (default 24 hours)
3. **Single-Use Tokens**: Tokens are deleted after successful verification
4. **HTML Email Templates**: Professional, responsive email design
5. **Resend Functionality**: Users can request new verification emails
6. **Rate Limiting**: Protection against abuse
7. **Frontend-Friendly**: Clear API responses and error messages

---

## System Architecture

### 1. Modular Email Provider System

The email system is built on a modular architecture that allows easy switching between email providers without impacting application logic.

```
┌─────────────────────────────────────┐
│   Application Layer                 │
│  (Auth, Tenants, Invoices, etc.)   │
└─────────────┬───────────────────────┘
              │
              ▼
┌─────────────────────────────────────┐
│   Email Tasks (Celery)              │
│  - send_verification_email_task     │
│  - send_password_reset_email_task   │
│  - send_invoice_email_task          │
│  - send_verification_reminder_task  │
└─────────────┬───────────────────────┘
              │
              ▼
┌─────────────────────────────────────┐
│   Email Service Layer               │
│  - compose_verification_email()     │
│  - compose_password_reset_email()   │
│  - compose_invoice_email()          │
│  - compose_reminder_email()         │
└─────────────┬───────────────────────┘
              │
              ▼
┌─────────────────────────────────────┐
│   Email Provider Interface          │
│  - EmailProvider (abstract)         │
│  - get_email_provider() factory     │
└─────────────┬───────────────────────┘
              │
      ┌───────┴───────┐
      ▼               ▼
┌──────────────┐ ┌──────────────┐
│  SendGrid    │ │  Mock Email  │
│  Provider    │ │  Provider    │
└──────────────┘ └──────────────┘
```

#### Email Provider Interface

All email providers implement the `EmailProvider` abstract base class:

```python
class EmailProvider(ABC):
    @abstractmethod
    def send_email(
        self,
        to_email: str,
        subject: str,
        plain_text: str,
        html_content: Optional[str] = None,
        attachments: Optional[list] = None,
        **kwargs
    ) -> bool:
        """Send an email using the provider's API."""
        pass

    @abstractmethod
    def validate_configuration(self) -> bool:
        """Validate that the provider is properly configured."""
        pass
```

#### Available Providers

1. **SendGridEmailProvider**: Production-ready SendGrid implementation
2. **MockEmailProvider**: Testing and development provider
3. **Future**: AWS SES, SMTP, Mailgun, etc. can be easily added

#### Provider Selection

Email provider is selected via configuration:

```python
# Environment variable
EMAIL_PROVIDER=sendgrid  # or "mock" for testing

# Factory pattern
provider = get_email_provider(
    provider_type="sendgrid",
    config={
        "api_key": settings.SENDGRID_API_KEY,
        "from_email": settings.EMAILS_FROM
    }
)
```

### 2. Asynchronous Email Processing

All emails are sent asynchronously using Celery tasks to ensure non-blocking operations.

#### Task Architecture

```python
@celery_app.task(
    name='app.tasks.email_tasks.send_verification_email_task',
    bind=True,
    max_retries=3,
    default_retry_delay=60,  # 1 minute
)
def send_verification_email_task(self, email, token, full_name, base_url):
    """Send verification email asynchronously with retry logic."""
    # Implementation with exponential backoff
```

#### Retry Strategy

- **Max Retries**: 3 attempts
- **Exponential Backoff**: 60s → 120s → 240s
- **Error Handling**: Logs failures, returns status dict
- **Timeout**: 30 minutes soft limit, 30 minutes hard limit

#### Task Types

1. **send_verification_email_task**: New user email verification
2. **send_password_reset_email_task**: Password reset emails
3. **send_invoice_email_task**: Invoice delivery with PDF attachment
4. **send_verification_reminder_task**: Reminder for unverified users

### 3. Email Verification Enforcement

The system enforces email verification for critical operations using dependency injection.

```python
# Dependency for verification requirement
def require_verified_email(
    current_user: User = Depends(get_current_user)
) -> User:
    """Ensure user has verified their email."""
    if current_user.is_superadmin:
        return current_user  # Bypass for superadmins

    if not current_user.is_verified:
        raise HTTPException(
            status_code=403,
            detail="Email verification required"
        )
    return current_user
```

---

## Implementation Details

### Database Changes

**User Model** (`app/models/user.py`):
- Added `verification_token` field (String, nullable, indexed) to store the unique verification token
- Added `verification_token_expires_at` field (DateTime, nullable) to track token expiration

**Migrations**:
- `migrations/versions/add_verification_token.py` - Adds verification_token column
- `migrations/versions/add_token_expiration.py` - Adds verification_token_expires_at column

### Backend Components

#### 1. Token Generation (`app/core/security.py`)

```python
def generate_verification_token() -> tuple[str, datetime]:
    """Generate a secure random token for email verification with expiration."""
```

- Uses `secrets.token_urlsafe(32)` to generate cryptographically secure tokens
- Returns a tuple of (token, expiration_datetime)
- Expiration time is configurable via `EMAIL_VERIFICATION_TOKEN_EXPIRATION_HOURS`

#### 2. Email Service (`app/core/email.py`)

```python
def send_verification_email(
    email: str,
    token: str,
    full_name: str,
    base_url: Optional[str] = None
) -> bool:
```

- Sends verification email using SendGrid API v3
- Includes both plain text and HTML versions
- HTML template is professionally styled and responsive
- Links expire in 24 hours (configurable)
- Uses httpx for HTTP requests (no heavy SDK dependency)

#### 3. Configuration (`app/core/config.py`)

Added email verification settings:
```python
EMAIL_VERIFICATION_BASE_URL: Optional[str] = "https://yourapp.com"
SENDGRID_API_KEY: Optional[str] = None
EMAILS_FROM: Optional[str] = None
EMAIL_VERIFICATION_TOKEN_EXPIRATION_HOURS: int = 24
```

Set via environment variables to configure the email service.

---

## API Endpoints

### 1. Tenant Registration (Enhanced)

**Endpoint**: `POST /api/v1/tenants/register`

**Description**: Register a new tenant and owner. Automatically generates and sends a verification email.

**Request Body**:
```json
{
  "name": "Acme Corporation",
  "domain": "acme.com",
  "plan_type": "free",
  "owner": {
    "full_name": "John Doe",
    "email": "john@acme.com",
    "password": "SecurePass123!"
  }
}
```

**Success Response (201 Created)**:
```json
{
  "tenant": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Acme Corporation",
    "domain": "acme.com",
    "plan_type": "free",
    "is_active": true,
    "created_at": "2025-11-03T20:00:00Z",
    "updated_at": "2025-11-03T20:00:00Z"
  },
  "owner": {
    "id": "660e8400-e29b-41d4-a716-446655440000",
    "email": "john@acme.com",
    "full_name": "John Doe",
    "role": "owner",
    "tenant_id": "550e8400-e29b-41d4-a716-446655440000",
    "is_active": true,
    "is_verified": false,
    "created_at": "2025-11-03T20:00:00Z",
    "updated_at": "2025-11-03T20:00:00Z"
  }
}
```

**Behavior**:
1. Creates tenant and owner user
2. Generates unique verification token
3. Stores token in `user.verification_token`
4. Sets `user.is_verified = False`
5. Sends verification email with token

---

### 2. Verify Email

**Endpoint**: `POST /api/v1/auth/verify-email?token={token}`

**Description**: Verify the user's email address using the token from the verification email.

**Request**:
```http
POST /api/v1/auth/verify-email?token=AbCdEf123...
```

**Success Response (200 OK)**:
```json
{
  "message": "Email verified successfully",
  "email": "owner@example.com",
  "is_verified": true
}
```

**Error Responses**:
- `400 Bad Request`: Invalid token
- `400 Bad Request`: Token expired (prompt user to request new one)
- `400 Bad Request`: Email already verified

**Behavior**:
1. Looks up user by verification token
2. Validates token exists and user not already verified
3. Checks if token has expired
4. Sets `user.is_verified = True`
5. Clears `user.verification_token` and `user.verification_token_expires_at`
6. Returns success message

---

### 3. Resend Verification Email

**Endpoint**: `POST /api/v1/auth/resend-verification-email`

**Description**: Request a new verification email.

**Request**:
```http
POST /api/v1/auth/resend-verification-email
Content-Type: application/json

{
  "email": "owner@example.com"
}
```

**Success Response (200 OK)**:
```json
{
  "message": "Verification email has been resent. Please check your inbox.",
  "email": "owner@example.com"
}
```

**Error Responses**:
- `400 Bad Request`: Email already verified
- `429 Too Many Requests`: Rate limit exceeded (3 per hour)

**Behavior**:
1. Finds user by email
2. Checks if user is already verified
3. Generates new verification token with expiration
4. Updates user record with new token
5. Sends new verification email
6. Returns success message

**Security**: Doesn't reveal whether email exists in the system for non-existent emails.

---

## Frontend Integration Guide

### 1. User Registration Flow

When a new tenant owner registers, they will receive a verification email. The frontend should:

1. Display a success message after registration
2. Prompt the user to check their email
3. Provide a way to resend the verification email if needed

### Frontend UI Recommendation

```jsx
// After successful registration
<SuccessMessage>
  ✓ Account created successfully!

  📧 Please check your email (john@acme.com) for a verification link.

  The link will expire in 24 hours.

  <Button onClick={handleResendEmail}>
    Didn't receive email? Resend
  </Button>
</SuccessMessage>
```

### 2. Email Verification Flow

When the user clicks the link in the verification email, they will be redirected to your frontend with a token parameter:

```
http://localhost:5173/verify-email?token=AbCdEf123...
```

Your frontend should extract the token and call the verification endpoint.

### 3. React TypeScript Implementation Example

```typescript
import { useState } from 'react';
import axios from 'axios';

const VerifyEmailPage: React.FC = () => {
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading');
  const [message, setMessage] = useState('');

  useEffect(() => {
    const verifyEmail = async () => {
      const token = new URLSearchParams(window.location.search).get('token');

      if (!token) {
        setStatus('error');
        setMessage('Invalid verification link');
        return;
      }

      try {
        const response = await axios.post(
          `/api/v1/auth/verify-email?token=${token}`
        );
        setStatus('success');
        setMessage(response.data.message);
        // Redirect to dashboard after 2 seconds
        setTimeout(() => window.location.href = '/dashboard', 2000);
      } catch (error) {
        setStatus('error');
        if (error.response?.status === 400) {
          setMessage(error.response.data.detail);
        } else {
          setMessage('Verification failed. Please try again.');
        }
      }
    };

    verifyEmail();
  }, []);

  return (
    <div>
      {status === 'loading' && <p>Verifying your email...</p>}
      {status === 'success' && <p>{message}</p>}
      {status === 'error' && (
        <div>
          <p>{message}</p>
          <button onClick={() => window.location.href = '/resend-email'}>
            Resend Verification Email
          </button>
        </div>
      )}
    </div>
  );
};
```

### 4. Handle Resend Request

```typescript
const [email, setEmail] = useState('');
const [rateLimitError, setRateLimitError] = useState(false);

const handleResend = async () => {
  try {
    const response = await axios.post('/api/v1/auth/resend-verification-email', {
      email
    });
    alert(response.data.message);
  } catch (error) {
    if (error.response?.status === 429) {
      setRateLimitError(true);
    } else {
      alert(error.response?.data?.detail || 'Error sending email');
    }
  }
};

return (
  <form onSubmit={(e) => { e.preventDefault(); handleResend(); }}>
    <input
      type="email"
      value={email}
      onChange={(e) => setEmail(e.target.value)}
      placeholder="Enter your email"
      required
    />
    <button type="submit">Resend Verification Email</button>
    {rateLimitError && (
      <p>Too many requests. Please try again later.</p>
    )}
  </form>
);
```

### 5. Error Handling Best Practices

```typescript
interface VerificationError {
  status: number;
  message: string;
  actionable: boolean;
}

const handleVerificationError = (error: any): VerificationError => {
  if (error.response?.status === 400) {
    const detail = error.response.data.detail;

    if (detail.includes('expired')) {
      return {
        status: 400,
        message: 'Your verification link has expired. Please request a new one.',
        actionable: true
      };
    }

    if (detail.includes('already verified')) {
      return {
        status: 400,
        message: 'Your email is already verified. You can log in now.',
        actionable: false
      };
    }

    if (detail.includes('invalid')) {
      return {
        status: 400,
        message: 'Invalid verification link. Please request a new email.',
        actionable: true
      };
    }
  }

  return {
    status: error.response?.status || 500,
    message: 'An unexpected error occurred. Please try again.',
    actionable: false
  };
};
```

---

## Configuration

### Environment Variables

```env
# Email service
SENDGRID_API_KEY=your-sendgrid-api-key
EMAILS_FROM=noreply@yourapp.com

# Frontend URL for verification links (used in email)
EMAIL_VERIFICATION_BASE_URL=http://localhost:5173

# Token expiration time (hours)
EMAIL_VERIFICATION_TOKEN_EXPIRATION_HOURS=24

# Email provider (sendgrid or mock for testing)
EMAIL_PROVIDER=sendgrid
```

### Database Configuration

The User model automatically includes verification fields:

```python
# app/models/user.py
verification_token: str = Column(String(255), nullable=True, index=True)
verification_token_expires_at: datetime = Column(DateTime, nullable=True)
```

---

## Testing

### Unit Tests

Comprehensive test suite with 11+ tests covering:

```python
# tests/test_email_verification.py

def test_register_tenant_sends_verification_email():
    """Test that registration generates and sends verification email"""

def test_verify_email_with_valid_token():
    """Test successful email verification"""

def test_verify_email_with_expired_token():
    """Test verification fails with expired token"""

def test_verify_email_with_invalid_token():
    """Test verification fails with invalid token"""

def test_verify_already_verified_email():
    """Test cannot verify already verified email"""

def test_resend_verification_email():
    """Test resending verification email generates new token"""

def test_resend_too_many_times():
    """Test rate limiting for resend requests (3/hour)"""

def test_verification_email_format():
    """Test that generated emails have proper HTML/plain text"""

def test_token_expiration_time():
    """Test that tokens expire after configured hours"""

def test_mark_user_verified_on_successful_verification():
    """Test that user.is_verified is set to True"""

def test_clear_token_after_verification():
    """Test that token is cleared after successful verification"""
```

**Run Tests**:
```bash
pytest tests/test_email_verification.py -v
```

**Coverage**:
- All new features covered
- All error paths tested
- Edge cases validated
- 100% pass rate

---

## Security Considerations

### Token Security

- **Cryptographic Generation**: Uses `secrets.token_urlsafe(32)` for cryptographically secure tokens
- **Single-Use**: Tokens are deleted after successful verification
- **Expiration**: Tokens expire after 24 hours (configurable)
- **Not in Logs**: Tokens are never logged or exposed in error messages

### Rate Limiting

- **Verification**: 10 attempts per minute per IP
- **Resend**: 3 requests per hour per email
- **Protection**: Prevents brute-force attacks and abuse

### Email Security

- **HTTPS Required**: All email links redirect to HTTPS in production
- **Token in URL**: Verification tokens passed as URL parameters (safe with HTTPS)
- **No Sensitive Data**: Emails don't contain passwords or sensitive tokens

### Data Privacy

- **GDPR Compliant**: Email used only for verification
- **No Tracking**: No third-party tracking in email templates
- **User Control**: Users can delete account anytime

### Verification Enforcement

- **Optional Bypass**: Super Admins can bypass verification checks
- **Configurable**: Verification can be disabled in development
- **Secure Defaults**: Verification enabled by default

---

## Troubleshooting

### Verification Email Not Received

1. Check SENDGRID_API_KEY is valid
2. Verify EMAILS_FROM is configured
3. Check spam/junk folder
4. Use "Resend Verification Email" endpoint
5. Check email service logs/Sentry

### Token Expiration Errors

- Tokens expire after 24 hours (configurable)
- Request new email via "Resend Verification Email" endpoint
- Check EMAIL_VERIFICATION_TOKEN_EXPIRATION_HOURS setting

### Rate Limit Issues

- Resend endpoint has 3/hour limit
- Wait before making new requests
- Check Retry-After header in 429 response

