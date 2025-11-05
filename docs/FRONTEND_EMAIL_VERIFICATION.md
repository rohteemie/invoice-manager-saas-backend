# Email Verification API - Frontend Integration Guide

## Overview

This guide provides everything you need to integrate the email verification feature into the frontend application. The feature ensures that new tenant owners verify their email address upon registration.

## Quick Start

### 1. User Registration Flow

When a new tenant owner registers, they will receive a verification email. The frontend should:

1. Display a success message after registration
2. Prompt the user to check their email
3. Provide a way to resend the verification email if needed

### 2. Email Verification Flow

When the user clicks the link in the verification email, they will be redirected to your frontend with a token parameter:

```
http://localhost:5173/verify-email?token=AbCdEf123...
```

Your frontend should extract the token and call the verification endpoint.

---

## API Endpoints

### 1. Register Tenant (Includes Email Verification)

**Endpoint:** `POST /api/v1/tenants/register`

**Description:** Register a new tenant and owner. Automatically generates and sends a verification email.

**Request Body:**
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

**Success Response (201 Created):**
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

**Frontend UI Recommendation:**
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

---

### 2. Verify Email

**Endpoint:** `POST /api/v1/auth/verify-email?token={token}`

**Description:** Verify the user's email address using the token from the verification email.

**Query Parameters:**
- `token` (required): The verification token from the email

**Success Response (200 OK):**
```json
{
  "message": "Email verified successfully",
  "email": "john@acme.com",
  "is_verified": true
}
```

**Error Responses:**

1. **Invalid or Expired Token (400 Bad Request):**
```json
{
  "detail": "Invalid or expired verification token"
}
```

2. **Token Expired (400 Bad Request):**
```json
{
  "detail": "Verification token has expired. Please request a new verification email."
}
```

3. **Already Verified (400 Bad Request):**
```json
{
  "detail": "Email is already verified. You can now log in to your account."
}
```

**Frontend Implementation Example:**

```typescript
// verify-email page component
async function verifyEmail(token: string) {
  try {
    const response = await fetch(
      `${API_BASE_URL}/api/v1/auth/verify-email?token=${token}`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      }
    );

    if (response.ok) {
      const data = await response.json();
      // Show success message and redirect to login
      showSuccessMessage(data.message);
      setTimeout(() => {
        router.push('/login');
      }, 2000);
    } else {
      const error = await response.json();
      // Show error message
      showErrorMessage(error.detail);
      
      // If token expired, show resend button
      if (error.detail.includes('expired')) {
        setShowResendButton(true);
      }
    }
  } catch (error) {
    showErrorMessage('Failed to verify email. Please try again.');
  }
}
```

**Frontend UI Recommendation:**

Success State:
```jsx
<SuccessPage>
  <CheckIcon />
  <h1>Email Verified!</h1>
  <p>Your email has been successfully verified.</p>
  <p>Redirecting to login...</p>
</SuccessPage>
```

Error State:
```jsx
<ErrorPage>
  <WarningIcon />
  <h1>Verification Failed</h1>
  <p>{errorMessage}</p>
  {showResendButton && (
    <Button onClick={handleResendEmail}>
      Request New Verification Email
    </Button>
  )}
  <Link to="/login">Go to Login</Link>
</ErrorPage>
```

---

### 3. Resend Verification Email

**Endpoint:** `POST /api/v1/auth/resend-verification-email`

**Description:** Request a new verification email. Rate limited to 3 requests per hour.

**Request Body:**
```json
{
  "email": "john@acme.com"
}
```

**Success Response (200 OK):**
```json
{
  "message": "Verification email has been resent. Please check your inbox.",
  "email": "john@acme.com"
}
```

**For non-existent email (200 OK - doesn't reveal if email exists):**
```json
{
  "message": "If the email exists in our system, a verification email will be sent.",
  "email": "john@acme.com"
}
```

**Error Response (400 Bad Request - Already Verified):**
```json
{
  "detail": "Email is already verified. You can log in to your account."
}
```

**Error Response (429 Too Many Requests - Rate Limited):**
```json
{
  "detail": "Too many requests. Please wait before requesting another verification email."
}
```

**Frontend Implementation Example:**

```typescript
async function resendVerificationEmail(email: string) {
  try {
    const response = await fetch(
      `${API_BASE_URL}/api/v1/auth/resend-verification-email`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email }),
      }
    );

    if (response.ok) {
      const data = await response.json();
      showSuccessMessage(data.message);
    } else if (response.status === 429) {
      showErrorMessage('Too many requests. Please wait before trying again.');
    } else {
      const error = await response.json();
      showErrorMessage(error.detail);
    }
  } catch (error) {
    showErrorMessage('Failed to resend verification email.');
  }
}
```

**Frontend UI Recommendation:**

```jsx
<ResendEmailForm>
  <h2>Resend Verification Email</h2>
  <p>Enter your email address to receive a new verification link.</p>
  
  <Input
    type="email"
    value={email}
    onChange={(e) => setEmail(e.target.value)}
    placeholder="your@email.com"
  />
  
  <Button onClick={() => resendVerificationEmail(email)}>
    Send Verification Email
  </Button>
  
  <Info>
    ⚠️ Rate limited to 3 requests per hour
  </Info>
</ResendEmailForm>
```

---

## Complete Frontend Flow

### Registration Flow

```
User fills registration form
    ↓
POST /api/v1/tenants/register
    ↓
Show success message
    ↓
Prompt user to check email
    ↓
[Optional] Provide resend button
```

### Verification Flow

```
User clicks link in email
    ↓
Frontend extracts token from URL
    ↓
POST /api/v1/auth/verify-email?token={token}
    ↓
If success: Show success → Redirect to login
    ↓
If error: Show error message
    ↓
If expired: Show resend button
```

### Resend Flow

```
User clicks "Resend verification email"
    ↓
User enters email address
    ↓
POST /api/v1/auth/resend-verification-email
    ↓
Show confirmation message
    ↓
Prompt user to check email
```

---

## Error Handling

### Common Error Scenarios

1. **Invalid Token**
   - HTTP 400
   - Message: "Invalid or expired verification token"
   - Action: Show error, provide resend button

2. **Expired Token**
   - HTTP 400
   - Message: "Verification token has expired. Please request a new verification email."
   - Action: Show error, provide resend button

3. **Already Verified**
   - HTTP 400
   - Message: "Email is already verified. You can now log in to your account."
   - Action: Show message, redirect to login

4. **Rate Limit Exceeded**
   - HTTP 429
   - Message: "Too many requests..."
   - Action: Show error, disable resend button temporarily

---

## Security Considerations

1. **Token Expiration**: Verification tokens expire after 24 hours
2. **Single Use**: Tokens are deleted after successful verification
3. **Rate Limiting**: 
   - Verification endpoint: 10 requests per minute
   - Resend endpoint: 3 requests per hour
4. **Email Privacy**: Resend endpoint doesn't reveal if email exists

---

## Configuration

### Environment Variables

The backend uses these environment variables (relevant for frontend integration):

```env
EMAIL_VERIFICATION_BASE_URL=http://localhost:5173
EMAIL_VERIFICATION_TOKEN_EXPIRATION_HOURS=24
```

Make sure your frontend URL matches the `EMAIL_VERIFICATION_BASE_URL` setting on the backend.

---

## Testing

### Manual Testing Checklist

- [ ] Register new tenant
- [ ] Receive verification email
- [ ] Click verification link
- [ ] Verify email successfully
- [ ] Try to verify again (should fail - already verified)
- [ ] Request new verification email
- [ ] Verify with new token
- [ ] Test expired token (manual expiry in DB)
- [ ] Test rate limiting on resend

### Test Email Credentials

For development, the backend may log email content to console instead of sending actual emails. Check with your backend team for the current email service configuration.

---

## API Response Schemas

### TenantRegistrationResponse

```typescript
interface TenantRegistrationResponse {
  tenant: {
    id: string;
    name: string;
    domain: string;
    plan_type: string;
    is_active: boolean;
    created_at: string;
    updated_at: string;
  };
  owner: {
    id: string;
    email: string;
    full_name: string;
    role: string;
    tenant_id: string;
    is_active: boolean;
    is_verified: boolean;
    created_at: string;
    updated_at: string;
  };
}
```

### EmailVerificationResponse

```typescript
interface EmailVerificationResponse {
  message: string;
  email: string;
  is_verified: boolean;
}
```

### ResendVerificationResponse

```typescript
interface ResendVerificationResponse {
  message: string;
  email: string;
}
```

### ErrorResponse

```typescript
interface ErrorResponse {
  detail: string;
}
```

---

## React/Next.js Example

Complete example for a Next.js app:

```typescript
// pages/verify-email.tsx
import { useEffect, useState } from 'react';
import { useRouter } from 'next/router';

export default function VerifyEmailPage() {
  const router = useRouter();
  const { token } = router.query;
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading');
  const [message, setMessage] = useState('');

  useEffect(() => {
    if (token) {
      verifyEmail(token as string);
    }
  }, [token]);

  async function verifyEmail(token: string) {
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/v1/auth/verify-email?token=${token}`,
        { method: 'POST' }
      );

      const data = await response.json();

      if (response.ok) {
        setStatus('success');
        setMessage(data.message);
        setTimeout(() => router.push('/login'), 3000);
      } else {
        setStatus('error');
        setMessage(data.detail);
      }
    } catch (error) {
      setStatus('error');
      setMessage('Failed to verify email. Please try again.');
    }
  }

  if (status === 'loading') {
    return <div>Verifying your email...</div>;
  }

  if (status === 'success') {
    return (
      <div>
        <h1>✓ Email Verified!</h1>
        <p>{message}</p>
        <p>Redirecting to login...</p>
      </div>
    );
  }

  return (
    <div>
      <h1>⚠️ Verification Failed</h1>
      <p>{message}</p>
      <button onClick={() => router.push('/resend-verification')}>
        Request New Verification Email
      </button>
    </div>
  );
}
```

---

## Support

For backend API issues or questions:
- Check the API documentation at `/docs` (Swagger UI)
- Review the backend README
- Contact the backend team

For frontend integration help:
- Refer to this guide
- Check the example implementations above
- Test with the provided endpoints
