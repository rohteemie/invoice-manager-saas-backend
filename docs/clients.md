# Client Management API Documentation

## Overview

The Client Management API provides endpoints for creating and managing clients (customers) within a multi-tenant SaaS environment. Each client is isolated to a specific tenant, ensuring data privacy and security.

## Client Model

### Attributes

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | String (UUID) | Auto-generated | Unique identifier for the client |
| `name` | String (200) | Yes | Client's full name or company name |
| `email` | String (Email) | No | Client's email address for communication |
| `phone` | String (50) | No | Client's phone number |
| `address` | String (500) | No | Client's physical address |
| `tax_id` | String (100) | No | Client's tax identification number (GDPR-sensitive) |
| `tenant_id` | String (UUID) | Yes | Associated tenant for data isolation |
| `is_active` | Boolean | Auto (True) | Soft delete flag for GDPR compliance |
| `created_at` | DateTime | Auto-generated | Timestamp when the client was created |
| `updated_at` | DateTime | Auto-generated | Timestamp when the client was last updated |

### Database Schema

```sql
CREATE TABLE clients (
    id VARCHAR(60) PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    email VARCHAR(255),
    phone VARCHAR(50),
    address VARCHAR(500),
    tax_id VARCHAR(100),
    tenant_id VARCHAR(60) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    FOREIGN KEY (tenant_id) REFERENCES tenants(id)
);

CREATE INDEX idx_clients_name ON clients(name);
CREATE INDEX idx_clients_email ON clients(email);
CREATE INDEX idx_clients_tenant_id ON clients(tenant_id);
```

## API Endpoints

### Base URL
```
/api/v1/clients
```

### Authentication
All endpoints require JWT authentication. Include the access token in the Authorization header:
```
Authorization: Bearer <access_token>
```

---

### 1. Create Client

**Endpoint:** `POST /api/v1/clients/`

**Required Role:** Admin or Owner

**Description:** Create a new client for the authenticated user's tenant.

**Request Body:**
```json
{
  "name": "Acme Corporation",
  "email": "contact@acme.com",
  "phone": "+1234567890",
  "address": "123 Main St, City, State 12345",
  "tax_id": "TAX-123456",
  "tenant_id": "tenant-uuid-here"
}
```

**Required Fields:**
- `name` (1-200 characters)
- `tenant_id` (must match authenticated user's tenant)

**Optional Fields:**
- `email` (valid email format)
- `phone` (max 50 characters)
- `address` (max 500 characters)
- `tax_id` (max 100 characters)

**Success Response (201 Created):**
```json
{
  "id": "client-uuid-here",
  "name": "Acme Corporation",
  "email": "contact@acme.com",
  "phone": "+1234567890",
  "address": "123 Main St, City, State 12345",
  "tax_id": "TAX-123456",
  "tenant_id": "tenant-uuid-here",
  "is_active": true,
  "created_at": "2024-01-15T10:30:00.000000",
  "updated_at": "2024-01-15T10:30:00.000000"
}
```

**Error Responses:**

- **400 Bad Request** - Duplicate email in tenant
```json
{
  "detail": "A client with this email already exists in your tenant"
}
```

- **403 Forbidden** - Attempting to create for another tenant
```json
{
  "detail": "Cannot create client for another tenant"
}
```

- **422 Unprocessable Entity** - Validation error
```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "value is not a valid email address",
      "type": "value_error.email"
    }
  ]
}
```

**Example cURL:**
```bash
curl -X POST "http://localhost:8000/api/v1/clients/" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Acme Corporation",
    "email": "contact@acme.com",
    "phone": "+1234567890",
    "tenant_id": "YOUR_TENANT_ID"
  }'
```

---

### 2. List Clients

**Endpoint:** `GET /api/v1/clients/`

**Required Role:** Admin or Owner

**Description:** Retrieve a paginated list of active clients for the authenticated user's tenant.

**Query Parameters:**
- `skip` (integer, default: 0) - Number of records to skip for pagination
- `limit` (integer, default: 100, max: 100) - Maximum number of records to return

**Success Response (200 OK):**
```json
[
  {
    "id": "client-1-uuid",
    "name": "Acme Corporation",
    "email": "contact@acme.com",
    "phone": "+1234567890",
    "address": "123 Main St, City, State 12345",
    "tax_id": "TAX-123456",
    "tenant_id": "tenant-uuid-here",
    "is_active": true,
    "created_at": "2024-01-15T10:30:00.000000",
    "updated_at": "2024-01-15T10:30:00.000000"
  },
  {
    "id": "client-2-uuid",
    "name": "Tech Solutions Inc",
    "email": "info@techsolutions.com",
    "phone": "+9876543210",
    "address": "456 Tech Ave, Silicon Valley, CA",
    "tax_id": "TAX-654321",
    "tenant_id": "tenant-uuid-here",
    "is_active": true,
    "created_at": "2024-01-16T14:20:00.000000",
    "updated_at": "2024-01-16T14:20:00.000000"
  }
]
```

**Example cURL:**
```bash
curl -X GET "http://localhost:8000/api/v1/clients/?skip=0&limit=10" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

---

### 3. Get Client by ID

**Endpoint:** `GET /api/v1/clients/{client_id}`

**Required Role:** Admin or Owner

**Description:** Retrieve a specific client by ID from the authenticated user's tenant.

**Path Parameters:**
- `client_id` (string) - The unique identifier of the client

**Success Response (200 OK):**
```json
{
  "id": "client-uuid-here",
  "name": "Acme Corporation",
  "email": "contact@acme.com",
  "phone": "+1234567890",
  "address": "123 Main St, City, State 12345",
  "tax_id": "TAX-123456",
  "tenant_id": "tenant-uuid-here",
  "is_active": true,
  "created_at": "2024-01-15T10:30:00.000000",
  "updated_at": "2024-01-15T10:30:00.000000"
}
```

**Error Responses:**

- **404 Not Found** - Client doesn't exist or belongs to another tenant
```json
{
  "detail": "Client not found"
}
```

**Example cURL:**
```bash
curl -X GET "http://localhost:8000/api/v1/clients/client-uuid-here" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

---

### 4. Update Client

**Endpoint:** `PUT /api/v1/clients/{client_id}`

**Required Role:** Admin or Owner

**Description:** Update client information. Supports partial updates.

**Path Parameters:**
- `client_id` (string) - The unique identifier of the client

**Request Body (all fields optional):**
```json
{
  "name": "Acme Corp (Updated)",
  "email": "newemail@acme.com",
  "phone": "+1111111111",
  "address": "789 New Address",
  "tax_id": "TAX-NEW-123",
  "is_active": true
}
```

**Success Response (200 OK):**
```json
{
  "id": "client-uuid-here",
  "name": "Acme Corp (Updated)",
  "email": "newemail@acme.com",
  "phone": "+1111111111",
  "address": "789 New Address",
  "tax_id": "TAX-NEW-123",
  "tenant_id": "tenant-uuid-here",
  "is_active": true,
  "created_at": "2024-01-15T10:30:00.000000",
  "updated_at": "2024-01-15T11:45:00.000000"
}
```

**Error Responses:**

- **400 Bad Request** - Duplicate email in tenant
```json
{
  "detail": "A client with this email already exists in your tenant"
}
```

- **404 Not Found** - Client doesn't exist or belongs to another tenant
```json
{
  "detail": "Client not found"
}
```

**Example cURL (Partial Update):**
```bash
curl -X PUT "http://localhost:8000/api/v1/clients/client-uuid-here" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "+1111111111"
  }'
```

---

### 5. Delete Client (Soft Delete)

**Endpoint:** `DELETE /api/v1/clients/{client_id}`

**Required Role:** Owner only

**Description:** Soft delete a client by setting `is_active` to `false`. This maintains audit trails and complies with GDPR right-to-be-forgotten requirements.

**Path Parameters:**
- `client_id` (string) - The unique identifier of the client

**Success Response (200 OK):**
```json
{
  "message": "Client deactivated successfully"
}
```

**Error Responses:**

- **403 Forbidden** - Admin users cannot delete clients
```json
{
  "detail": "User does not have required role"
}
```

- **404 Not Found** - Client doesn't exist or belongs to another tenant
```json
{
  "detail": "Client not found"
}
```

**Example cURL:**
```bash
curl -X DELETE "http://localhost:8000/api/v1/clients/client-uuid-here" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

---

## Role-Based Access Control

| Endpoint | Owner | Admin | Manager | Attendant |
|----------|-------|-------|---------|-----------|
| Create Client | ✅ | ✅ | ❌ | ❌ |
| List Clients | ✅ | ✅ | ❌ | ❌ |
| Get Client | ✅ | ✅ | ❌ | ❌ |
| Update Client | ✅ | ✅ | ❌ | ❌ |
| Delete Client | ✅ | ❌ | ❌ | ❌ |

## Data Isolation

All client operations enforce strict tenant isolation:

- Users can only create clients for their own tenant
- Users can only view/update/delete clients from their own tenant
- Cross-tenant access attempts return 404 Not Found
- Client listings are automatically filtered by tenant

## GDPR Compliance

### Right to be Forgotten
The delete endpoint implements soft deletion by setting `is_active` to `false`:
- Maintains audit trail
- Allows data recovery if needed
- Complies with GDPR requirements
- Deactivated clients are excluded from listing

### Data Minimization
The client model only collects essential information:
- Name is the only required field
- Email, phone, address, and tax_id are optional
- No unnecessary personal data collection

### Sensitive Data
- `tax_id` field is marked as GDPR-sensitive
- Proper access controls via RBAC
- Data encrypted at rest and in transit

## Validation Rules

### Name
- Required field
- Minimum length: 1 character
- Maximum length: 200 characters

### Email
- Optional field
- Must be valid email format if provided
- Must be unique within the tenant

### Phone
- Optional field
- Maximum length: 50 characters

### Address
- Optional field
- Maximum length: 500 characters

### Tax ID
- Optional field
- Maximum length: 100 characters

## Error Handling

### Common HTTP Status Codes

- **200 OK** - Successful GET, PUT, or DELETE request
- **201 Created** - Successful client creation
- **400 Bad Request** - Duplicate email or invalid request
- **401 Unauthorized** - Missing or invalid authentication token
- **403 Forbidden** - Insufficient permissions or cross-tenant access
- **404 Not Found** - Client not found
- **422 Unprocessable Entity** - Validation error in request body

## Testing

The client management API is covered by 28 comprehensive tests:

- **CRUD Operations**: Create, read, update, delete functionality
- **RBAC**: Role-based access control for all roles
- **Tenant Isolation**: Cross-tenant access prevention
- **Validation**: Email format, required fields, field lengths
- **Soft Delete**: GDPR-compliant deletion
- **Edge Cases**: Duplicate emails, non-existent clients, pagination

Run tests with:
```bash
pytest tests/test_clients.py -v
```

## Examples

### Creating a Client (Python)
```python
import requests

headers = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json"
}

client_data = {
    "name": "Acme Corporation",
    "email": "contact@acme.com",
    "phone": "+1234567890",
    "tenant_id": tenant_id
}

response = requests.post(
    "http://localhost:8000/api/v1/clients/",
    headers=headers,
    json=client_data
)

if response.status_code == 201:
    client = response.json()
    print(f"Created client: {client['id']}")
```

### Updating a Client (JavaScript)
```javascript
const updateClient = async (clientId, updates) => {
  const response = await fetch(`http://localhost:8000/api/v1/clients/${clientId}`, {
    method: 'PUT',
    headers: {
      'Authorization': `Bearer ${accessToken}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(updates)
  });

  if (response.ok) {
    const client = await response.json();
    console.log('Updated client:', client);
  }
};

// Update only the phone number
await updateClient('client-uuid', { phone: '+9999999999' });
```

### Listing Clients with Pagination (Python)
```python
def get_all_clients(base_url, access_token):
    headers = {"Authorization": f"Bearer {access_token}"}
    skip = 0
    limit = 10
    all_clients = []
    
    while True:
        response = requests.get(
            f"{base_url}/api/v1/clients/?skip={skip}&limit={limit}",
            headers=headers
        )
        clients = response.json()
        
        if not clients:
            break
            
        all_clients.extend(clients)
        skip += limit
    
    return all_clients
```

## Best Practices

1. **Always validate tenant_id**: Ensure the client is being created for the correct tenant
2. **Use email for communication**: Store client emails for invoice delivery
3. **Soft delete only**: Never hard delete clients to maintain audit trails
4. **Paginate large lists**: Use skip and limit parameters for performance
5. **Handle duplicates**: Check for unique email addresses within tenants
6. **Secure sensitive data**: Treat tax_id as GDPR-sensitive information
7. **Test thoroughly**: Verify tenant isolation and RBAC in all operations

## Future Enhancements

Planned improvements for the client management system:

- Client search and filtering by name, email, or tax ID
- Client tags or categories for better organization
- Client-specific notes or metadata
- Integration with invoice generation
- Client activity history and audit logs
- Bulk import/export of clients
- Client status management (active, suspended, archived)
