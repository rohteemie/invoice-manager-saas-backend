# Invoicing Feature

**Latest Version**: 2.0 - Integrated Invoice & PDF Generation
**Last Updated**: 2025-11-10

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Invoice Data Model](#invoice-data-model)
3. [Invoice Lifecycle](#invoice-lifecycle)
4. [API Endpoints](#api-endpoints)
5. [PDF Generation](#pdf-generation)
6. [Multi-Currency & Tax Support](#multi-currency--tax-support)
7. [Role-Based Access Control](#role-based-access-control)
8. [Testing](#testing)
9. [Security & Compliance](#security--compliance)
10. [Troubleshooting](#troubleshooting)

---

## Overview

The invoicing feature enables organizations to create, manage, and distribute professional invoices with advanced capabilities including:

- Auto-generated invoice numbers with unique sequencing
- Complete invoice lifecycle management (Draft → Sent → Paid/Overdue)
- Multi-currency support with configurable tax rates
- Professional PDF generation with tenant branding
- Email distribution with a single click
- Comprehensive audit trails with creator tracking
- CSV/JSON export functionality
- Role-based access control with permission enforcement

**Key Features**:
- ✅ Auto-generated invoice numbers (format: `INV-YYYYMMDD-XXXX`)
- ✅ Multi-tenant isolation for data security
- ✅ Customer information tracking
- ✅ Line-item based invoicing
- ✅ Financial calculations (subtotal, tax, discount, total)
- ✅ Payment method tracking
- ✅ Multi-currency support (USD, EUR, GBP, NGN)
- ✅ Configurable tax rates per tenant
- ✅ Professional PDF generation (on-demand, no storage)
- ✅ Email delivery integration
- ✅ CSV/JSON export

---

## Invoice Data Model

### 1. Invoice Model (`app/models/invoice.py`)

**Table**: `invoices`

**Key Fields**:

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Primary key |
| `invoice_number` | String | Unique auto-generated number (e.g., INV-20251110-0001) |
| `tenant_id` | UUID | Foreign key to tenant (multi-tenant isolation) |
| `branch_id` | UUID | Optional branch reference |
| `customer_name` | String | Invoice recipient name |
| `customer_email` | Email | Customer email (for sending) |
| `customer_phone` | String | Customer contact number |
| `customer_address` | Text | Full customer address |
| `creator_id` | UUID | Foreign key to user who created invoice |
| `status` | Enum | Current lifecycle status |
| `issue_date` | Date | Invoice creation date |
| `due_date` | Date | Payment due date |
| `currency` | String | ISO 4217 currency code (USD, EUR, GBP, NGN) |
| `subtotal` | Decimal(10,2) | Sum of all line items |
| `tax_amount` | Decimal(10,2) | Calculated tax |
| `discount_amount` | Decimal(10,2) | Applied discount |
| `total_amount` | Decimal(10,2) | Final invoice total |
| `notes` | Text | Additional invoice notes |
| `payment_method` | Enum | Payment method (transfer, cash, pos, cheque, card, mobile_money, other) |
| `paid_at` | DateTime | Payment timestamp |
| `created_at` | DateTime | Creation timestamp |
| `updated_at` | DateTime | Last modification timestamp |

### 2. InvoiceItem Model (`app/models/invoice.py`)

**Table**: `invoice_items`

**Key Fields**:

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Primary key |
| `invoice_id` | UUID | Foreign key to invoice (cascade delete) |
| `description` | String | Line item description |
| `quantity` | Decimal(10,2) | Item quantity |
| `unit_price` | Decimal(10,2) | Price per unit |
| `total_price` | Decimal(10,2) | Calculated total (quantity × unit_price) |
| `created_at` | DateTime | Creation timestamp |
| `updated_at` | DateTime | Last modification timestamp |

### 3. Invoice Status Enum

```python
class InvoiceStatus(str, enum.Enum):
    DRAFT = "draft"        # Initial state, fully editable
    SENT = "sent"          # Sent to customer, still editable (via API)
    PAID = "paid"          # Payment received, no changes
    OVERDUE = "overdue"    # Past due date, no changes
```

---

## Invoice Lifecycle

### Status Flow

```
DRAFT ──────→ SENT ──────→ PAID
                 │
                 └──────→ OVERDUE ──────→ PAID
```

### Valid Transitions

| From | To | Conditions |
|------|-----|-----------|
| DRAFT | SENT | Must have at least one line item |
| SENT | PAID | Requires payment_method |
| SENT | OVERDUE | Automatic if due_date has passed |
| OVERDUE | PAID | Requires payment_method |

### Invalid Operations

- Cannot update SENT, PAID, or OVERDUE invoices
- Cannot delete non-DRAFT invoices
- Cannot resend PAID invoices

---

## API Endpoints

### Create Invoice

**Endpoint**: `POST /api/v1/invoices`

**Permission**: All authenticated users

**Request Body**:
```json
{
  "customer_name": "Acme Corp",
  "customer_email": "billing@acme.com",
  "customer_phone": "+1-555-0100",
  "customer_address": "123 Main St, City, State 12345",
  "issue_date": "2025-11-10",
  "due_date": "2025-12-10",
  "currency": "USD",
  "notes": "Net 30",
  "items": [
    {
      "description": "Consulting Services",
      "quantity": 40,
      "unit_price": 150.00
    },
    {
      "description": "Implementation",
      "quantity": 20,
      "unit_price": 200.00
    }
  ]
}
```

**Success Response (201 Created)**:
```json
{
  "id": "inv-uuid",
  "invoice_number": "INV-20251110-0042",
  "tenant_id": "tenant-uuid",
  "customer_name": "Acme Corp",
  "customer_email": "billing@acme.com",
  "status": "draft",
  "currency": "USD",
  "subtotal": 10000.00,
  "tax_amount": 0.00,
  "discount_amount": 0.00,
  "total_amount": 10000.00,
  "items": [
    {
      "description": "Consulting Services",
      "quantity": 40,
      "unit_price": 150.00,
      "total_price": 6000.00
    },
    {
      "description": "Implementation",
      "quantity": 20,
      "unit_price": 200.00,
      "total_price": 4000.00
    }
  ],
  "created_at": "2025-11-10T14:30:00Z",
  "updated_at": "2025-11-10T14:30:00Z"
}
```

### List Invoices

**Endpoint**: `GET /api/v1/invoices`

**Permission**: All authenticated users (tenant-scoped)

**Query Parameters**:
- `skip` (int): Pagination offset (default: 0)
- `limit` (int): Result limit (default: 50, max: 100)
- `status` (str): Filter by status (draft, sent, paid, overdue)

**Response (200 OK)**:
```json
{
  "items": [
    { /* invoice 1 */ },
    { /* invoice 2 */ }
  ],
  "total": 42,
  "skip": 0,
  "limit": 50
}
```

### Get Invoice Details

**Endpoint**: `GET /api/v1/invoices/{invoice_id}`

**Permission**: All authenticated users (tenant-scoped)

**Response (200 OK)**: Single invoice object (full details with items)

### Update Invoice

**Endpoint**: `PUT /api/v1/invoices/{invoice_id}`

**Permission**: Manager role and above

**Constraint**: Only DRAFT invoices can be updated

**Request Body**: Same as create (all updatable fields)

**Response (200 OK)**: Updated invoice object

### Change Invoice Status

**Endpoint**: `PATCH /api/v1/invoices/{invoice_id}/status`

**Permission**: Manager role and above

**Request Body**:
```json
{
  "status": "sent",
  "payment_method": null  // Required if status is "paid"
}
```

**Validation**:
- Enforces valid status transitions
- Requires `payment_method` if transitioning to PAID
- Cannot change PAID invoices

**Response (200 OK)**: Updated invoice

### Download Invoice PDF

**Endpoint**: `GET /api/v1/invoices/{invoice_id}/pdf`

**Permission**: All authenticated users (tenant-scoped)

**Response (200 OK)**:
```
Content-Type: application/pdf
Content-Disposition: inline; filename="invoice_INV-20251110-0001.pdf"

[PDF binary data]
```

**Features**:
- Generated on-demand (no file storage)
- Includes tenant branding/logo
- Multi-currency formatting
- Professional layout with headers/footers
- Page numbers and metadata

### Send Invoice Email

**Endpoint**: `POST /api/v1/invoices/{invoice_id}/send`

**Permission**: Manager role and above

**Behavior**:
1. Validates invoice is in DRAFT or SENT status
2. Sends email to `customer_email` with invoice details
3. Automatically transitions status DRAFT → SENT
4. Includes PDF attachment
5. Records send timestamp

**Request Body** (optional):
```json
{
  "include_pdf": true,
  "message": "Please find your invoice attached."
}
```

**Response (200 OK)**:
```json
{
  "message": "Invoice sent successfully",
  "sent_at": "2025-11-10T14:35:00Z"
}
```

### Delete Invoice

**Endpoint**: `DELETE /api/v1/invoices/{invoice_id}`

**Permission**: Admin role and above

**Constraint**: Only DRAFT invoices can be deleted

**Response (204 No Content)**: Success (no body)

### Export Invoices

**Endpoint**: `GET /api/v1/invoices/export/invoices`

**Permission**: Manager role and above

**Query Parameters**:
- `format` (str): csv or json (default: csv)
- `status` (str): Filter by status
- `start_date` (str): YYYY-MM-DD format
- `end_date` (str): YYYY-MM-DD format

**Response (200 OK)**:
- CSV: `text/csv` with file download
- JSON: `application/json` array of invoices

---

## PDF Generation

### Overview

Professional PDF documents are generated on-demand without storing files. Each PDF is created from current invoice data, ensuring they always reflect the latest information.

### Technology Stack

- **WeasyPrint 62.3+**: HTML/CSS → PDF conversion
- **Jinja2 3.1.2**: Template rendering
- **CSS Paged Media**: Print-optimized layout

### Architecture

```
API Request
    ↓
PDF Generator Service
    ├─ Fetch invoice from DB
    ├─ Prepare data for template
    ├─ Render Jinja2 template → HTML
    └─ Convert HTML → PDF (WeasyPrint)
    ↓
Stream Binary PDF Response
```

### Key Features

- ✅ **On-Demand**: Generated when requested
- ✅ **No Storage**: Not saved to disk
- ✅ **Real-Time Data**: Always reflects current state
- ✅ **Professional Design**: Print-optimized layout
- ✅ **Tenant Branding**: Includes company logo if configured
- ✅ **Multi-Currency**: Formats amounts correctly
- ✅ **Secure**: Tenant isolation enforced

### API Usage

**Example: cURL**
```bash
curl -X GET "http://localhost:8000/api/v1/invoices/{invoice_id}/pdf" \
  -H "Authorization: Bearer {access_token}" \
  --output invoice.pdf
```

**Example: Python**
```python
import requests

response = requests.get(
    f"http://localhost:8000/api/v1/invoices/{invoice_id}/pdf",
    headers={"Authorization": f"Bearer {access_token}"}
)

if response.status_code == 200:
    with open("invoice.pdf", "wb") as f:
        f.write(response.content)
```

**Example: JavaScript**
```javascript
fetch(`http://localhost:8000/api/v1/invoices/${invoiceId}/pdf`, {
  headers: { 'Authorization': `Bearer ${token}` }
})
  .then(r => r.blob())
  .then(blob => {
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'invoice.pdf';
    a.click();
  });
```

### Template Customization

**Location**: `app/templates/invoice.html`

**Customizable Sections**:
- Company branding (name, colors, logo)
- Invoice layout and spacing
- Font sizes and styling
- Page margins and header/footer

**Example CSS Customization**:
```css
@page {
    size: A4;
    margin: 1.5cm 2cm;
}

.company-name {
    color: #2563eb;  /* Brand color */
    font-size: 28px;
}
```

---

## Multi-Currency & Tax Support

### Supported Currencies

- **NGN**: Nigerian Naira (default)
- **USD**: US Dollar
- **EUR**: Euro
- **GBP**: British Pound

All currencies follow ISO 4217 standard (3-letter codes).

### Invoice Currency Selection

**Automatic (Default)**:
```json
POST /api/v1/invoices
{
  "customer_name": "John Doe",
  "items": [...]
  // currency not specified → uses tenant's default_currency
}
```

**Explicit**:
```json
POST /api/v1/invoices
{
  "customer_name": "John Doe",
  "currency": "EUR",
  "items": [...]
}
```

### Tenant Tax Configuration

**API**: `PUT /api/v1/tenants/{tenant_id}`

```json
{
  "default_currency": "GBP",
  "tax_rate": 20.00,
  "tax_label": "VAT"
}
```

**Fields**:
- `default_currency` (string): Default invoice currency (NGN, USD, EUR, GBP)
- `tax_rate` (decimal, optional): Tax percentage (0-100, e.g., 7.5)
- `tax_label` (string, optional): Tax name (e.g., "VAT", "GST", "Sales Tax")

**Tax-Exempt Organization**:
```json
{
  "default_currency": "USD",
  "tax_rate": null,
  "tax_label": null
}
```

### Tax Calculation

When creating an invoice, tax is automatically calculated:

```
Subtotal = Sum of (quantity × unit_price) for all items
Tax = Subtotal × (tenant.tax_rate / 100)
Discount = Invoice discount_amount
Total = Subtotal + Tax - Discount
```

Example:
```
Subtotal: $1,000.00
Tax Rate: 7.5%
Tax: $75.00
Discount: $0.00
Total: $1,075.00
```

### API Validation

- Currency codes validated against supported enum (NGN, USD, EUR, GBP)
- Input normalized to uppercase (EUR, eur, Eur → EUR)
- Invalid currencies return 422 Validation Error
- Tax rate: 0-100 (decimal, optional)

---

## Role-Based Access Control

### Permission Matrix

| Action | Attendant | Manager | Admin | Owner |
|--------|-----------|---------|-------|-------|
| Create | ✅ | ✅ | ✅ | ✅ |
| View (own tenant) | ✅ | ✅ | ✅ | ✅ |
| Update (DRAFT only) | ❌ | ✅ | ✅ | ✅ |
| Change Status | ❌ | ✅ | ✅ | ✅ |
| Delete (DRAFT only) | ❌ | ❌ | ✅ | ✅ |
| Download PDF | ✅ | ✅ | ✅ | ✅ |
| Send Email | ❌ | ✅ | ✅ | ✅ |
| Export | ❌ | ✅ | ✅ | ✅ |

**Notes**:
- All operations are tenant-scoped (users cannot access other tenants' invoices)
- Attendants have read-only access + can download PDFs
- Manager and above can modify and send invoices
- Only Admin and Owner can delete

---

## Testing

### Unit Tests

Located in `tests/test_invoices.py`:

**Test Coverage**:
- ✅ Invoice creation with validation
- ✅ Line item calculations
- ✅ Auto-generated invoice numbers
- ✅ Status transition validation
- ✅ RBAC enforcement
- ✅ Tenant isolation
- ✅ Pagination and filtering
- ✅ Error handling

**Run Tests**:
```bash
pytest tests/test_invoices.py -v
```

### PDF Integration Tests

Located in `tests/test_invoice_pdf.py`:

**Test Coverage**:
- ✅ PDF generation and download
- ✅ Authentication and authorization
- ✅ Tenant isolation
- ✅ Various invoice states
- ✅ Error scenarios

**Run Tests**:
```bash
pytest tests/test_invoice_pdf.py -v
```

### Multi-Currency Tests

Located in `tests/test_multi_currency_tax.py`:

**Test Coverage**:
- ✅ Currency support (NGN, USD, EUR, GBP)
- ✅ Tenant currency configuration
- ✅ Tax rate calculations
- ✅ Currency validation
- ✅ Invoice currency inheritance

**Run Tests**:
```bash
pytest tests/test_multi_currency_tax.py -v
```

### Run All Tests

```bash
pytest tests/test_invoices.py tests/test_invoice_pdf.py tests/test_multi_currency_tax.py -v
```

---

## Security & Compliance

### Data Security

- **Tenant Isolation**: All queries filtered by tenant_id at DB level
- **Authentication**: JWT required for all endpoints
- **Authorization**: RBAC enforced per operation
- **Encryption**: Passwords hashed, sensitive data encrypted in transit

### GDPR Compliance

- **Data Minimization**: Only required fields collected
- **Right to Access**: Users can view their invoices
- **Right to Erasure**: DRAFT invoices deletable by Admin+
- **Purpose Limitation**: Invoice data used only for invoicing
- **Data Portability**: CSV/JSON export available
- **Audit Trail**: All operations timestamped with creator tracking

### ISO 4217 Compliance

- All currency codes follow ISO 4217 standard
- Supported currencies: NGN, USD, EUR, GBP
- Case-insensitive validation with normalization

### Payment Security

- Payment methods validated against enum
- Sensitive payment info not stored in system
- Payment tracking via `paid_at` timestamp only

---

## Troubleshooting

### PDF Generation Issues

**WeasyPrint Installation**:
```bash
# Ubuntu/Debian
sudo apt-get install libpango-1.0-0 libpangocairo-1.0-0

# macOS
brew install pango
```

**Font/Rendering Issues**:
- Check WeasyPrint CSS support documentation
- Some CSS features not supported (use fallbacks)
- Test with simple invoices first

### Currency Validation Errors

```
422 Validation Error: value is not a valid enumeration member
```

**Solution**: Use supported currency codes:
- NGN (Nigerian Naira)
- USD (US Dollar)
- EUR (Euro)
- GBP (British Pound)

### Status Transition Errors

```
400 Bad Request: Invalid status transition
```

**Solution**: Verify valid transitions from current status:
- DRAFT → SENT
- SENT → PAID or OVERDUE
- OVERDUE → PAID
- PAID → (no transitions)

### Tenant Isolation Issues

**Problem**: Getting 404 or 403 errors

**Solution**:
1. Verify invoice belongs to your tenant
2. Check your JWT token is valid
3. Ensure you're using correct invoice_id
4. Use correct tenant context in request

---

## Future Enhancements

Potential improvements for future versions:

- [ ] Recurring invoices
- [ ] Invoice templates
- [ ] Multiple invoice variants (modern, classic, minimal)
- [ ] Digital signature integration
- [ ] QR code for online payment
- [ ] Automated dunning (overdue reminders)
- [ ] Multi-language PDF generation
- [ ] Custom invoice numbering schemes
- [ ] Payment gateway integration
- [ ] Batch invoice operations

