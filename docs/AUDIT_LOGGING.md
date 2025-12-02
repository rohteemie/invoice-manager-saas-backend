# Audit Logging

## Overview

The audit logging system provides comprehensive tracking of critical operations for security, compliance, and debugging purposes. All audit logs are automatically captured and stored in the database with detailed context including user, tenant, IP address, user agent, and before/after state for changes.

## Features

### Automatic Logging

The following operations are automatically audited:

#### Authentication Events
- **User Login** (`LOGIN`) - Successful user authentication
- **Login Failed** (`LOGIN_FAILED`) - Failed login attempts with incorrect credentials
- **Token Refresh** (`TOKEN_REFRESH`) - JWT token refresh operations
- **Logout** (`LOGOUT`) - User logout events

#### User Management Events
- **User Created** (`USER_CREATED`) - New user registration
- **User Updated** (`USER_UPDATED`) - User profile updates
- **User Deleted** (`USER_DELETED`) - User soft deletion (deactivation)
- **User Role Changed** (`USER_ROLE_CHANGED`) - Changes to user roles (Owner, Admin, Manager, Attendant)
- **Password Changed** (`PASSWORD_CHANGED`) - Password update operations
- **Password Reset Requested** (`PASSWORD_RESET_REQUESTED`) - Password reset token generation
- **Password Reset Completed** (`PASSWORD_RESET_COMPLETED`) - Successful password reset

#### Tenant Management Events
- **Tenant Created** (`TENANT_CREATED`) - New tenant organization created
- **Tenant Updated** (`TENANT_UPDATED`) - Tenant configuration changes
- **Tenant Deleted** (`TENANT_DELETED`) - Tenant soft deletion

#### Invoice Management Events
- **Invoice Created** (`INVOICE_CREATED`) - New invoice creation
- **Invoice Updated** (`INVOICE_UPDATED`) - Invoice modifications
- **Invoice Deleted** (`INVOICE_DELETED`) - Invoice deletion
- **Invoice Status Changed** (`INVOICE_STATUS_CHANGED`) - Status transitions (Draft → Sent → Paid, etc.)

#### Data Export Events
- **Data Exported** (`DATA_EXPORTED`) - CSV/JSON data exports
- **Invoice PDF Generated** (`INVOICE_PDF_GENERATED`) - PDF generation for invoices

### Audit Log Data

Each audit log entry contains:

- **ID**: Unique identifier for the audit log
- **User ID**: ID of the user who performed the action (nullable for failed logins)
- **Tenant ID**: Associated tenant for multi-tenant isolation
- **Action**: Type of action performed (from AuditAction enum)
- **Resource Type**: Type of resource affected (User, Tenant, Invoice, Auth, Export)
- **Resource ID**: ID of the affected resource (nullable for general actions)
- **IP Address**: Client IP address (supports IPv4 and IPv6, handles proxy headers)
- **User Agent**: Browser/client user agent string
- **Changes**: JSON string containing before/after state for updates
- **Description**: Human-readable description of the action
- **Status**: Success or failure status
- **Created At**: Timestamp when the action occurred
- **Updated At**: Timestamp of last update

### API Endpoints

All audit log endpoints require **Admin role or higher** and enforce tenant isolation.

#### List Audit Logs
```
GET /api/v1/audit-logs/
```

Query Parameters:
- `skip` (int): Number of records to skip for pagination (default: 0)
- `limit` (int): Maximum number of records to return (default: 100, max: 1000)
- `user_id` (string): Filter by user ID
- `actions` (List[AuditAction]): Filter by action types (supports multiple)
- `resource_types` (List[ResourceType]): Filter by resource types (supports multiple)
- `resource_id` (string): Filter by resource ID
- `status` (string): Filter by status (success/failure)
- `start_date` (datetime): Filter by start date (ISO 8601 format)
- `end_date` (datetime): Filter by end date (ISO 8601 format)

**Multiple Filtering Support:**
- You can filter by multiple actions: `?actions=login&actions=login_failed`
- You can filter by multiple resource types: `?resource_types=user&resource_types=tenant`
- Multiple filters use OR logic within the same parameter, AND logic across different parameters

Response: Array of audit log objects, ordered by created_at descending (newest first)

#### Get Audit Log by ID
```
GET /api/v1/audit-logs/{audit_log_id}
```

Returns a specific audit log entry.

#### Get User Audit Logs
```
GET /api/v1/audit-logs/user/{user_id}
```

Returns all audit logs where the user was the actor or the resource.

Query Parameters: `actions` (supports multiple), `start_date`, `end_date`, `skip`, `limit`

#### Get Resource Audit Logs
```
GET /api/v1/audit-logs/resource/{resource_type}/{resource_id}
```

Returns all audit logs for a specific resource.

Query Parameters: `actions` (supports multiple), `start_date`, `end_date`, `skip`, `limit`

### Security & Compliance

#### Tenant Isolation
- All audit logs are strictly isolated by tenant
- Users can only access audit logs from their own tenant
- Tenant isolation is enforced at the database query level

#### IP Address Tracking
- Captures client IP address from request
- Supports proxy headers (X-Forwarded-For, X-Real-IP)
- Handles both IPv4 and IPv6 addresses

#### User Agent Tracking
- Records browser/client user agent for each action
- Useful for identifying suspicious activity or unauthorized access

#### Change Tracking
- For update operations, stores before/after state as JSON
- Enables complete audit trail for compliance requirements
- Particularly useful for role changes and sensitive data modifications

#### Role-Based Access
- Only Admin role and above can query audit logs
- Prevents unauthorized access to audit trail
- Maintains separation of duties for compliance

### Retention Policy

The audit log retention policy can be configured based on compliance requirements:

- **Default**: Logs are kept indefinitely
- **Recommended**: Implement automated archival after 90 days for performance
- **Compliance**: Retention period should match regulatory requirements (e.g., GDPR, SOX, HIPAA)

Future enhancements may include:
- Automated log archival to cold storage
- Configurable retention periods per tenant
- Log compression for older entries

### Best Practices

1. **Regular Review**: Periodically review audit logs for suspicious activity
2. **Alerting**: Set up alerts for critical events (failed logins, role changes, deletions)
3. **Monitoring**: Monitor audit log growth and implement archival strategy
4. **Compliance**: Ensure retention policy meets regulatory requirements
5. **Security**: Restrict audit log access to authorized personnel only
6. **Investigation**: Use audit logs for incident investigation and forensics

### Examples

#### View Recent Login Attempts (Multiple Actions)
```bash
# Get both successful and failed logins
GET /api/v1/audit-logs/?actions=login&actions=login_failed&limit=50

# Get only successful logins
GET /api/v1/audit-logs/?actions=login&limit=50
```

#### Track User Role Changes
```bash
GET /api/v1/audit-logs/?actions=user_role_changed
```

#### Monitor Authentication and User Changes
```bash
# Get all authentication-related events and user changes
GET /api/v1/audit-logs/?resource_types=auth&resource_types=user
```

#### Audit Trail for Specific Invoice
```bash
# Get all events for an invoice
GET /api/v1/audit-logs/resource/invoice/{invoice_id}

# Get only status changes and updates for an invoice
GET /api/v1/audit-logs/resource/invoice/{invoice_id}?actions=invoice_status_changed&actions=invoice_updated
```

#### Find All Actions by Specific User
```bash
GET /api/v1/audit-logs/user/{user_id}

# Filter to specific action types
GET /api/v1/audit-logs/user/{user_id}?actions=user_role_changed&actions=user_updated
```

#### Review Recent Failed Logins
```bash
GET /api/v1/audit-logs/?actions=login_failed&start_date=2024-01-01T00:00:00Z
```

#### Complex Multi-Filter Query
```bash
# Get all invoice and tenant events by a specific user in a date range
GET /api/v1/audit-logs/?user_id={user_id}&resource_types=invoice&resource_types=tenant&start_date=2024-01-01T00:00:00Z&end_date=2024-12-31T23:59:59Z
```

### Technical Implementation

The audit logging system is implemented using:

- **Model**: `app/models/audit_log.py` - SQLAlchemy model with composite indexes
- **Schema**: `app/schemas/audit_log.py` - Pydantic schemas for API responses
- **Service**: `app/services/audit_logger.py` - Service layer functions for creating audit logs
- **Endpoints**: `app/api/v1/endpoints/audit_logs.py` - REST API endpoints for querying logs
- **Migration**: `migrations/versions/add_audit_logs.py` - Database migration script

### Database Schema

The `audit_logs` table includes optimized indexes for common query patterns:

- Composite index on `(tenant_id, action)` for tenant-specific action queries
- Composite index on `(user_id, action)` for user-specific action queries
- Composite index on `(resource_type, resource_id)` for resource audit trails
- Index on `created_at` for time-based queries
- Individual indexes on foreign keys for join performance

### Performance Considerations

- Audit logging is asynchronous and does not block the main request flow
- Failed audit log creation logs an error but does not fail the main operation
- Indexes are optimized for common query patterns
- Pagination is enforced with sensible limits (max 1000 records per query)
- Consider implementing log archival for high-volume tenants

### Troubleshooting

**Problem**: Audit logs not being created
- Check database connectivity
- Verify audit_logs table exists (run migrations)
- Check application logs for audit_logger errors

**Problem**: Cannot query audit logs (403 Forbidden)
- Verify user has Admin role or higher
- Check tenant isolation is working correctly

**Problem**: Slow audit log queries
- Add pagination parameters (skip, limit)
- Use specific filters (action, resource_type, dates)
- Consider database index optimization
- Implement log archival for old data
