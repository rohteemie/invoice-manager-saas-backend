# Email Verification System - Architecture and Implementation

## Overview

The Invoice Manager SaaS Backend features a production-ready email verification system built with modularity, reliability, and scalability as core principles. This document describes the architecture, implementation, and usage of the email verification system.

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

#### Implementation

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
            detail="Email verification required. "
                   "Please verify your email address to perform this action."
        )
    return current_user

# Usage in endpoints
@router.post("/invoices/", response_model=Invoice)
def create_invoice(
    invoice_in: InvoiceCreate,
    current_user: User = Depends(require_verified_email),
    db: Session = Depends(get_db)
):
    # Invoice creation logic
```

#### Enforcement Points

- ✅ Invoice creation
- ✅ Invoice sending via email
- 🔜 Payment processing (future)
- 🔜 API key generation (future)

#### Bypass Rules

- **Superadmins**: Always bypass verification requirement
- **Testing**: Mock email provider automatically used in test environment

### 4. Reminder System

Automated reminders are sent to users who haven't verified their email within 24 hours.

#### Reminder Task

```python
@celery_app.task(name='app.tasks.email_tasks.send_verification_reminders')
def send_verification_reminders():
    """Send reminders to unverified users (runs daily)."""
    # Find users:
    # - Unverified (is_verified = False)
    # - Active accounts (is_active = True)
    # - Token not expired
    # - Registered > 24 hours ago

    # Queue reminder emails asynchronously
```

#### Celery Beat Schedule

```python
celery_app.conf.beat_schedule = {
    'send-verification-reminders': {
        'task': 'app.tasks.email_tasks.send_verification_reminders',
        'schedule': 86400.0,  # Run once daily (24 hours)
    },
}
```

## Configuration

### Environment Variables

```bash
# Email Provider Selection
EMAIL_PROVIDER=sendgrid  # Options: sendgrid, mock

# SendGrid Configuration (for production)
SENDGRID_API_KEY=your-sendgrid-api-key
EMAILS_FROM=noreply@yourapp.com

# Email Verification Settings
EMAIL_VERIFICATION_BASE_URL=https://yourapp.com
EMAIL_VERIFICATION_TOKEN_EXPIRATION_HOURS=24

# Password Reset Settings
PASSWORD_RESET_TOKEN_EXPIRATION_MINUTES=30

# Celery/Redis (for async processing)
REDIS_URL=redis://localhost:6379/0
```

### Testing Configuration

For testing, the system automatically uses the Mock email provider:

```python
# conftest.py sets:
os.environ["EMAIL_PROVIDER"] = "mock"
os.environ["TESTING"] = "1"

# All Celery tasks are mocked in tests
# No actual emails are sent during testing
```

## API Reference

### Verification Endpoints

#### Verify Email

```http
POST /api/v1/auth/verify-email?token={verification_token}
```

**Success Response (200)**:
```json
{
  "message": "Email verified successfully",
  "email": "user@example.com",
  "is_verified": true
}
```

**Error Responses**:
- `400`: Invalid token, token expired, or already verified
- `429`: Rate limit exceeded (10/minute)

#### Resend Verification Email

```http
POST /api/v1/auth/resend-verification-email
Content-Type: application/json

{
  "email": "user@example.com"
}
```

**Success Response (200)**:
```json
{
  "message": "Verification email has been resent. Please check your inbox.",
  "email": "user@example.com"
}
```

**Error Responses**:
- `400`: Email already verified
- `429`: Rate limit exceeded (3/hour)

### User Endpoints

All user endpoints include `is_verified` in responses:

```json
{
  "id": "user-id",
  "email": "user@example.com",
  "full_name": "John Doe",
  "role": "owner",
  "tenant_id": "tenant-id",
  "is_active": true,
  "is_verified": false,  // ← Verification status
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

## Email Templates

### Verification Email

Professional HTML template with:
- Branded header with project name
- Clear call-to-action button
- Alternative text link
- Expiration warning (24 hours)
- Plain text fallback

### Reminder Email

Sent 24 hours after registration if still unverified:
- Friendly reminder tone
- Lists benefits of verification
- Same verification link
- Expiration notice

### Password Reset Email

Secure password reset with:
- Security warnings
- 30-minute expiration
- Security tips
- Plain text fallback

### Invoice Email

Professional invoice delivery:
- Customer greeting
- Invoice details
- PDF attachment
- Contact information

## Security Considerations

### Token Security

1. **Cryptographic Generation**: Uses `secrets.token_urlsafe(32)` for tokens
2. **URL-Safe Encoding**: Tokens safe for URL parameters
3. **Sufficient Length**: 32 bytes = 43 characters in base64
4. **Single-Use**: Tokens deleted after successful verification
5. **Expiration**: Configurable expiration (default 24 hours)
6. **Database Indexing**: Efficient token lookup with indexes

### Rate Limiting

- **Verify Endpoint**: 10 requests/minute per IP
- **Resend Endpoint**: 3 requests/hour per IP
- **Protection**: Prevents brute-force token guessing

### Email Privacy

- **Non-Enumeration**: Resend endpoint doesn't reveal if email exists
- **Generic Messages**: Same response for existing and non-existing emails
- **No User Info Leak**: Error messages don't expose user data

### Input Sanitization

All user-provided data is sanitized before use in emails:

```python
def sanitize_for_email(text: str) -> str:
    """Remove control characters and normalize whitespace."""
    # Removes: \x00-\x08, \x0B, \x0C, \x0E-\x1F, \x7F
    # Normalizes: Multiple spaces, newlines
    # Returns: Safe string for email content
```

## Testing

### Test Coverage

**19 Total Tests**:

**Email Verification Core (11 tests)**:
- Token generation and uniqueness
- Verification flow (valid, invalid, expired tokens)
- Resend functionality
- Already verified scenarios
- Login before/after verification

**Async Processing & Enforcement (8 tests)**:
- Async task invocation
- Verification enforcement for invoices
- Superadmin bypass
- User response includes verification status
- Email provider modularity
- Mock provider functionality

### Running Tests

```bash
# All email verification tests
pytest tests/test_email_verification.py -v

# Enforcement and async tests
pytest tests/test_email_verification_enforcement.py -v

# All tests
pytest tests/ -v
```

### Mocking in Tests

Celery tasks are automatically mocked in the test environment:

```python
# conftest.py provides mocked tasks
# No Redis/Celery required for testing
# No actual emails sent during tests
```

## Deployment Guide

### Production Setup

1. **Configure SendGrid**:
   ```bash
   export SENDGRID_API_KEY="your-api-key"
   export EMAILS_FROM="noreply@yourapp.com"
   export EMAIL_PROVIDER="sendgrid"
   ```

2. **Start Celery Worker**:
   ```bash
   celery -A app.core.celery_app worker --loglevel=info
   ```

3. **Start Celery Beat** (for reminders):
   ```bash
   celery -A app.core.celery_app beat --loglevel=info
   ```

4. **Configure Redis**:
   ```bash
   export REDIS_URL="redis://localhost:6379/0"
   ```

### Development Setup

1. **Use Mock Provider**:
   ```bash
   export EMAIL_PROVIDER="mock"
   ```

2. **Optional Celery** (runs inline):
   - Tasks execute synchronously in development
   - No Redis required
   - Emails logged to console

### Monitoring

Monitor email delivery through:
- **Celery Flower**: Task monitoring dashboard
- **SendGrid Dashboard**: Delivery statistics
- **Application Logs**: Task execution and failures
- **Sentry**: Error tracking (if configured)

## Adding New Email Providers

### Step 1: Implement Provider Class

```python
# app/services/email_provider.py

class MailgunEmailProvider(EmailProvider):
    def __init__(self, api_key: str, domain: str, from_email: str):
        self.api_key = api_key
        self.domain = domain
        self.from_email = from_email

    def validate_configuration(self) -> bool:
        return bool(self.api_key and self.domain and self.from_email)

    def send_email(self, to_email, subject, plain_text,
                   html_content=None, attachments=None, **kwargs):
        # Mailgun API implementation
        pass
```

### Step 2: Register in Factory

```python
def get_email_provider(provider_type: str, config: dict) -> EmailProvider:
    if provider_type == "mailgun":
        return MailgunEmailProvider(
            api_key=config.get("api_key"),
            domain=config.get("domain"),
            from_email=config.get("from_email")
        )
    # ... other providers
```

### Step 3: Update Configuration

```python
# Add settings in app/core/config.py
MAILGUN_API_KEY: Optional[str] = Field(None, ...)
MAILGUN_DOMAIN: Optional[str] = Field(None, ...)
```

## Troubleshooting

### Emails Not Sending

1. **Check Provider Configuration**:
   ```python
   provider = get_configured_email_provider()
   is_valid = provider.validate_configuration()
   ```

2. **Check Celery Worker**: Ensure worker is running
3. **Check Redis**: Verify Redis is accessible
4. **Check SendGrid API Key**: Verify key is valid
5. **Check Logs**: Look for error messages in application logs

### Tasks Not Processing

1. **Verify Celery Worker Running**: `celery -A app.core.celery_app worker`
2. **Check Redis Connection**: Test Redis connectivity
3. **Check Task Queue**: Use Flower dashboard
4. **Review Logs**: Check for task failures

### Verification Links Not Working

1. **Check Base URL**: Verify `EMAIL_VERIFICATION_BASE_URL` is correct
2. **Check Token Expiration**: Tokens expire after 24 hours
3. **Check Database**: Ensure token exists in database

## Best Practices

### For Developers

1. **Always Use Async Tasks**: Never send emails synchronously
2. **Handle Failures Gracefully**: Log errors, don't fail operations
3. **Test with Mock Provider**: Use mock provider in tests
4. **Sanitize Inputs**: Always sanitize user-provided data
5. **Monitor Tasks**: Use Celery Flower in production

### For Operators

1. **Monitor Email Delivery**: Track SendGrid delivery rates
2. **Set Up Alerts**: Alert on high failure rates
3. **Regular Testing**: Test email flow in staging
4. **Backup Provider**: Have backup email provider configured
5. **Rate Limit Tuning**: Adjust rate limits based on usage

## Migration from Synchronous to Async

If migrating from synchronous email sending:

1. **Update Imports**:
   ```python
   # Old
   from app.core.email import send_verification_email

   # New
   from app.tasks.email_tasks import send_verification_email_task
   ```

2. **Update Calls**:
   ```python
   # Old
   send_verification_email(email, token, full_name, base_url)

   # New
   send_verification_email_task.delay(email, token, full_name, base_url)
   ```

3. **Remove Blocking Logic**: Don't wait for email result
4. **Update Tests**: Mock Celery tasks in tests

## Conclusion

The email verification system provides a production-ready, modular, and scalable solution for email handling. Key benefits include:

- **Modularity**: Easy to switch providers or add new ones
- **Reliability**: Retry logic with exponential backoff
- **Performance**: Non-blocking async processing
- **Security**: Comprehensive security measures
- **Testability**: Complete test coverage with mocks
- **Maintainability**: Clean architecture and documentation

For additional help, see:
- [Frontend Integration Guide](FRONTEND_EMAIL_VERIFICATION.md)
- [API Documentation](API_STRUCTURE.md)
- [Security Guide](SECURITY.md)
