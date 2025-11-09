# Invoice PDF Generation Feature

## Overview

The Invoice PDF Generation feature provides on-demand PDF document generation for invoices without storing the files themselves. This ensures that the database remains the single source of truth and PDFs are always generated with the most current data.

## Features

- **On-Demand Generation**: PDFs are generated in real-time when requested
- **No Storage Required**: PDFs are not stored on disk, reducing storage costs
- **Professional Design**: High-quality, print-optimized PDF documents
- **Template-Based**: Uses Jinja2 templates for easy customization
- **Multi-Tenant Safe**: Respects tenant isolation boundaries
- **Fast & Efficient**: Asynchronous generation using WeasyPrint

## Technical Implementation

### Technology Stack

- **WeasyPrint 62.3+**: HTML/CSS to PDF conversion with high fidelity
- **Jinja2 3.1.2**: Template engine for rendering invoice data
- **CSS Paged Media**: Professional page layout with headers, footers, and page numbers

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    API Endpoint Layer                        │
│         GET /api/v1/invoices/{invoice_id}/pdf               │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                  PDF Generator Service                       │
│  - Fetch invoice data from database                         │
│  - Prepare and format data for template                     │
│  - Render Jinja2 template to HTML                           │
│  - Convert HTML to PDF using WeasyPrint                     │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    Database Layer                            │
│  - Invoice data with line items                             │
│  - Customer information                                      │
│  - Payment details                                           │
└─────────────────────────────────────────────────────────────┘
```

## API Documentation

### Endpoint

```
GET /api/v1/invoices/{invoice_id}/pdf
```

### Authentication

Requires JWT Bearer token authentication.

### Permissions

All authenticated users can download invoices for their own tenant.

### Request

**Path Parameters:**
- `invoice_id` (string, required): The unique identifier of the invoice

**Headers:**
- `Authorization: Bearer {access_token}` (required)

### Response

**Success Response (200 OK):**

```
Content-Type: application/pdf
Content-Disposition: inline; filename="invoice_INV-20240115-0001.pdf"

[PDF binary data]
```

**Error Responses:**

- `401 Unauthorized`: Missing or invalid authentication token
- `404 Not Found`: Invoice not found or belongs to different tenant
- `500 Internal Server Error`: PDF generation failed

### Example Usage

#### cURL

```bash
curl -X GET "http://localhost:8000/api/v1/invoices/{invoice_id}/pdf" \
  -H "Authorization: Bearer {access_token}" \
  --output invoice.pdf
```

#### Python (requests)

```python
import requests

url = "http://localhost:8000/api/v1/invoices/{invoice_id}/pdf"
headers = {"Authorization": f"Bearer {access_token}"}

response = requests.get(url, headers=headers)

if response.status_code == 200:
    with open("invoice.pdf", "wb") as f:
        f.write(response.content)
    print("PDF downloaded successfully")
else:
    print(f"Error: {response.status_code}")
```

#### JavaScript (fetch)

```javascript
const invoiceId = 'your-invoice-id';
const token = 'your-access-token';

fetch(`http://localhost:8000/api/v1/invoices/${invoiceId}/pdf`, {
  headers: {
    'Authorization': `Bearer ${token}`
  }
})
  .then(response => response.blob())
  .then(blob => {
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'invoice.pdf';
    a.click();
  });
```

## Postman Testing

### Setup

1. **Import Collection**: Create a new request in Postman
2. **Set URL**: `GET {{base_url}}/api/v1/invoices/{{invoice_id}}/pdf`
3. **Add Variables**:
   - `base_url`: `http://localhost:8000/api/v1`
   - `invoice_id`: The ID of an existing invoice
4. **Authentication**:
   - Type: Bearer Token
   - Token: Your JWT access token

### Test Steps

1. **Create an Invoice** (if you don't have one):
   ```
   POST {{base_url}}/invoices
   Body: {
     "customer_name": "John Doe",
     "customer_email": "john@example.com",
     "issue_date": "2024-01-15",
     "items": [
       {
         "description": "Product A",
         "quantity": 2,
         "unit_price": 100.00
       }
     ]
   }
   ```
   Save the returned `id` as `invoice_id` variable.

2. **Download PDF**:
   ```
   GET {{base_url}}/invoices/{{invoice_id}}/pdf
   ```
   
3. **Verify Response**:
   - Status: `200 OK`
   - Headers: `Content-Type: application/pdf`
   - Body: PDF binary data

4. **Save PDF**:
   - In Postman, click "Save Response" → "Save to a file"
   - Open the saved PDF to verify content

### Automated Tests in Postman

Add this script to the Tests tab:

```javascript
pm.test("Status code is 200", function () {
    pm.response.to.have.status(200);
});

pm.test("Content-Type is application/pdf", function () {
    pm.response.to.have.header("Content-Type", "application/pdf");
});

pm.test("Content-Disposition header exists", function () {
    pm.response.to.have.header("Content-Disposition");
});

pm.test("Response has PDF content", function () {
    const responseBody = pm.response.text();
    pm.expect(responseBody).to.include("%PDF");
});
```

## PDF Template Customization

The PDF template is located at `app/templates/invoice.html`. You can customize:

### Branding

```html
<div class="company-name">Your Company Name</div>
<div class="company-tagline">Your Tagline</div>
```

### Colors

```css
/* Main brand color */
.invoice-header {
    border-bottom: 3px solid #2563eb; /* Change this */
}

.company-name {
    color: #2563eb; /* Change this */
}
```

### Layout

The template uses CSS Paged Media for print optimization:

```css
@page {
    size: A4;  /* Change to Letter, Legal, etc. */
    margin: 1.5cm 2cm;  /* Adjust margins */
}
```

## Error Handling

The PDF generation service includes comprehensive error handling:

### Template Not Found

```python
PDFGenerationError: Invoice template not found: invoice.html
```
**Solution**: Ensure `app/templates/invoice.html` exists

### Template Rendering Error

```python
PDFGenerationError: Template rendering failed: {error_details}
```
**Solution**: Check template syntax and variable names

### PDF Generation Error

```python
PDFGenerationError: PDF generation failed: {error_details}
```
**Solution**: Check WeasyPrint installation and HTML validity

## Performance Considerations

### Generation Time

- Average: 200-500ms per invoice
- Depends on:
  - Number of line items
  - Template complexity
  - System resources

### Optimization Tips

1. **Caching**: Consider caching PDFs for frequently accessed invoices
2. **Async Processing**: For bulk operations, use background tasks
3. **Template Optimization**: Keep templates simple and efficient
4. **Font Loading**: System fonts are faster than custom fonts

## Security

### Access Control

- ✅ JWT authentication required
- ✅ Tenant isolation enforced
- ✅ User can only access their tenant's invoices

### Data Sanitization

- ✅ Jinja2 auto-escaping enabled
- ✅ HTML special characters escaped
- ✅ No SQL injection possible (ORM used)

### Privacy

- ✅ No PDFs stored on disk
- ✅ No logging of sensitive invoice data
- ✅ Temporary data cleaned up automatically

## Testing

### Unit Tests

Located in `tests/test_pdf_generator.py`:

```bash
pytest tests/test_pdf_generator.py -v
```

Tests cover:
- PDF generator initialization
- Data preparation and formatting
- Template rendering
- PDF generation with various data
- Error handling

### Integration Tests

Located in `tests/test_invoice_pdf.py`:

```bash
pytest tests/test_invoice_pdf.py -v
```

Tests cover:
- End-to-end PDF download flow
- Authentication and authorization
- Tenant isolation
- Various invoice states (draft, paid, etc.)
- Edge cases and error scenarios

### Run All PDF Tests

```bash
pytest tests/test_pdf_generator.py tests/test_invoice_pdf.py -v
```

## Troubleshooting

### WeasyPrint Installation Issues

If you encounter font or rendering issues:

```bash
# Ubuntu/Debian
sudo apt-get install libpango-1.0-0 libpangocairo-1.0-0

# macOS
brew install pango

# Windows
# Usually works out of the box with pip install
```

### PDF Not Generating

1. Check logs for specific error messages
2. Verify template exists: `ls app/templates/invoice.html`
3. Test with a simple invoice first
4. Ensure all dependencies are installed: `pip install -r requirements.txt`

### Styling Issues

1. Use browser dev tools to test HTML/CSS
2. Check WeasyPrint CSS support: [docs](https://doc.courtbouillon.org/weasyprint/)
3. Some CSS features aren't supported in PDF rendering

## Future Enhancements

Potential improvements for future versions:

- [ ] Multiple template themes (modern, classic, minimal)
- [ ] Custom logo upload support
- [ ] Multi-currency formatting
- [ ] QR code for online payment
- [ ] Digital signature integration
- [ ] PDF/A compliance for archival
- [ ] Watermark support for draft invoices
- [ ] Batch PDF generation endpoint
- [ ] Email delivery integration

## Support

For issues or questions:

1. Check this documentation
2. Review test files for usage examples
3. Check application logs for errors
4. Create an issue in the repository

## License

This feature is part of the Multi-Tenant SaaS Backend project and follows the same MIT License.
