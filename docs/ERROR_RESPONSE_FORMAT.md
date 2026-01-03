# Standardized Error Response Format

## Overview

All API error responses now follow a consistent, standardized format to make client-side error handling predictable and reliable.

## Error Response Schema

All errors return a JSON object with the following structure:

```json
{
  "error": "ErrorType",
  "message": "Human-readable error message",
  "code": "MACHINE_READABLE_CODE",
  "details": [  // Optional, present for validation errors
    {
      "field": "field_name",
      "message": "Specific field error message",
      "code": "FIELD_ERROR_CODE"
    }
  ],
  "request_id": "unique-request-id-for-tracking"
}
```

### Fields

- **error** (string): The type/category of error (e.g., "ValidationError", "HTTPException", "DatabaseError")
- **message** (string): A human-readable error message suitable for display
- **code** (string): A machine-readable error code in UPPER_SNAKE_CASE format for client-side error handling
- **details** (array, optional): Additional error details, particularly for validation errors
- **request_id** (string): A unique identifier for this request, useful for debugging and support

## Common Error Codes

### Authentication & Authorization
- `UNAUTHORIZED` (401): Authentication required or token invalid
- `FORBIDDEN` (403): User lacks required permissions
- `INVALID_CREDENTIALS` (401): Login failed due to incorrect credentials

### Validation
- `VALIDATION_ERROR` (422): Request data failed validation
- `INVALID_EMAIL` (422): Email format is invalid
- `INVALID_INPUT` (422): Input data is malformed

### Resources
- `NOT_FOUND` (404): Requested resource does not exist
- `USER_NOT_FOUND` (404): Specific user not found
- `INVOICE_NOT_FOUND` (404): Specific invoice not found
- `TENANT_NOT_FOUND` (404): Specific tenant not found

### Conflicts
- `CONFLICT` (409): Resource conflict (e.g., duplicate entry)
- `DUPLICATE_ENTRY` (409): Resource already exists
- `INVALID_REFERENCE` (409): Referenced resource does not exist

### Server Errors
- `DATABASE_ERROR` (500): Database operation failed
- `INTERNAL_SERVER_ERROR` (500): Unexpected server error
- `EXTERNAL_SERVICE_ERROR` (503): External service unavailable

### Rate Limiting
- `RATE_LIMIT_EXCEEDED` (429): Too many requests

## Examples

### 1. Validation Error
**Request:**
```bash
POST /api/v1/auth/register
{
  "email": "invalid-email",
  "password": "short"
}
```

**Response (422):**
```json
{
  "error": "ValidationError",
  "message": "Request validation failed",
  "code": "VALIDATION_ERROR",
  "details": [
    {
      "field": "email",
      "message": "value is not a valid email address",
      "code": "VALUE_ERROR"
    },
    {
      "field": "password",
      "message": "ensure this value has at least 8 characters",
      "code": "VALUE_ERROR"
    }
  ],
  "request_id": "abc-123-def-456"
}
```

### 2. Authentication Error
**Request:**
```bash
GET /api/v1/users/me
# No Authorization header
```

**Response (401):**
```json
{
  "error": "HTTPException",
  "message": "Not authenticated",
  "code": "UNAUTHORIZED",
  "request_id": "xyz-789-uvw-012"
}
```

### 3. Not Found Error
**Request:**
```bash
GET /api/v1/invoices/non-existent-id
```

**Response (404):**
```json
{
  "error": "HTTPException",
  "message": "Invoice not found",
  "code": "NOT_FOUND",
  "request_id": "mno-345-pqr-678"
}
```

### 4. Permission Error
**Request:**
```bash
GET /api/v1/admin/tenants
# User does not have admin role
```

**Response (403):**
```json
{
  "error": "HTTPException",
  "message": "Insufficient permissions. Required role: admin",
  "code": "FORBIDDEN",
  "request_id": "stu-901-vwx-234"
}
```

### 5. Duplicate Entry Error
**Request:**
```bash
POST /api/v1/auth/register
{
  "email": "existing@example.com",
  ...
}
```

**Response (409):**
```json
{
  "error": "DatabaseError",
  "message": "A record with this information already exists",
  "code": "DUPLICATE_ENTRY",
  "request_id": "ghi-567-jkl-890"
}
```

## Client-Side Error Handling

### JavaScript/TypeScript Example

```typescript
interface ApiError {
  error: string;
  message: string;
  code: string;
  details?: Array<{
    field?: string;
    message: string;
    code?: string;
  }>;
  request_id: string;
}

async function handleApiCall() {
  try {
    const response = await fetch('/api/v1/invoices');
    
    if (!response.ok) {
      const error: ApiError = await response.json();
      
      // Handle specific error codes
      switch (error.code) {
        case 'UNAUTHORIZED':
          // Redirect to login
          window.location.href = '/login';
          break;
          
        case 'VALIDATION_ERROR':
          // Display validation errors to user
          error.details?.forEach(detail => {
            showFieldError(detail.field, detail.message);
          });
          break;
          
        case 'NOT_FOUND':
          // Show not found message
          showNotification(error.message, 'error');
          break;
          
        default:
          // Generic error handling
          showNotification(error.message, 'error');
          console.error(`Error ${error.code}:`, error.message, error.request_id);
      }
      
      return;
    }
    
    const data = await response.json();
    // Process successful response
    
  } catch (err) {
    // Handle network errors
    showNotification('Network error occurred', 'error');
  }
}
```

### Python Example

```python
import requests
from typing import Optional, List, Dict, Any

class ApiError:
    def __init__(self, response_data: Dict[str, Any]):
        self.error = response_data.get('error')
        self.message = response_data.get('message')
        self.code = response_data.get('code')
        self.details = response_data.get('details', [])
        self.request_id = response_data.get('request_id')

def handle_api_call():
    try:
        response = requests.post(
            'https://api.example.com/api/v1/invoices',
            json={'customer_name': 'Test'},
            headers={'Authorization': 'Bearer token'}
        )
        
        if not response.ok:
            error = ApiError(response.json())
            
            # Handle specific error codes
            if error.code == 'VALIDATION_ERROR':
                for detail in error.details:
                    print(f"Validation error in {detail.get('field')}: {detail.get('message')}")
            
            elif error.code == 'UNAUTHORIZED':
                # Re-authenticate
                pass
            
            else:
                print(f"Error: {error.message} (ID: {error.request_id})")
            
            return None
        
        return response.json()
        
    except requests.RequestException as e:
        print(f"Network error: {e}")
        return None
```

## Benefits

1. **Consistency**: All errors follow the same format, making client-side handling predictable
2. **Machine-Readable**: Error codes enable programmatic error handling
3. **Human-Friendly**: Messages are suitable for display to end users
4. **Debuggable**: Request IDs enable easy tracking and debugging
5. **Detailed**: Validation errors include field-level details
6. **Secure**: Internal implementation details are hidden in production

## Migration Notes

### From Old Format

**Before:**
```json
{
  "detail": "Email already registered"
}
```

**After:**
```json
{
  "error": "HTTPException",
  "message": "Email already registered",
  "code": "BAD_REQUEST",
  "request_id": "..."
}
```

### Key Changes
- `detail` → `message` (for error messages)
- Added `error` field (error type)
- Added `code` field (machine-readable code)
- Added `request_id` field (for tracking)
- Added `details` array (for validation errors with field-level info)

## Security Considerations

1. **Production Mode**: In production, internal error details (like database errors) are hidden from clients
2. **Development Mode**: More detailed error information is provided in development for debugging
3. **No Information Leakage**: Error messages are carefully crafted to avoid exposing sensitive information
4. **Request IDs**: All errors include request IDs for support and debugging without exposing system internals
