# 🖼️ Tenant Branding & Logo Management

## Overview

The Multi-Tenant SaaS Backend supports tenant branding through customizable logos and contact information. Each organization can upload their logo and add their business details, which are automatically included in generated invoices and reports.

This feature enhances the professional appearance of invoices and provides a personalized experience for each tenant's customers.

---

## Features

### Tenant Logo Upload
- Upload custom logos for branded invoices
- Supported formats: PNG, JPG, JPEG, SVG
- Maximum file size: 2MB
- Automatic file validation and storage
- Logo appears in invoice PDF header

### Tenant Contact Information
- Business name
- Physical address
- Phone number
- Contact email
- All information displayed on invoices

### Branded Invoices
- Tenant logo in invoice header
- Tenant contact details displayed prominently
- Custom tax labels (e.g., VAT, GST, Sales Tax)
- Professional, personalized appearance

---

## API Endpoints

### Upload Tenant Logo

**Endpoint:** `POST /api/v1/tenants/{tenant_id}/logo`

**Permissions:** Owner and Admin roles only

**Request:**
```http
POST /api/v1/tenants/{tenant_id}/logo
Authorization: Bearer {access_token}
Content-Type: multipart/form-data

file: [image file]
```

**Response:**
```json
{
  "id": "tenant-uuid",
  "name": "Acme Corporation",
  "logo_url": "uploads/logos/tenant-uuid.png",
  "address": "123 Business St, City, Country",
  "phone": "+1234567890",
  "email": "contact@acme.com",
  ...
}
```

**Validation Rules:**
- File types: PNG, JPG, JPEG, SVG only
- Maximum file size: 2MB
- Only one logo per tenant (uploading new logo replaces old one)

**Example (cURL):**
```bash
curl -X POST http://localhost:8000/api/v1/tenants/{tenant_id}/logo \
  -H "Authorization: Bearer {access_token}" \
  -F "file=@/path/to/logo.png"
```

**Example (Python requests):**
```python
import requests

url = "http://localhost:8000/api/v1/tenants/{tenant_id}/logo"
headers = {"Authorization": "Bearer {access_token}"}
files = {"file": open("logo.png", "rb")}

response = requests.post(url, headers=headers, files=files)
print(response.json())
```

---

### Retrieve Tenant Logo

**Endpoint:** `GET /api/v1/tenants/{tenant_id}/logo`

**Permissions:** Public (no authentication required)

**Request:**
```http
GET /api/v1/tenants/{tenant_id}/logo
```

**Response:**
- Returns the image file directly
- Content-Type: image/png, image/jpeg, or image/svg+xml
- 404 error if tenant has no logo

**Example (cURL):**
```bash
curl -X GET http://localhost:8000/api/v1/tenants/{tenant_id}/logo \
  -o logo.png
```

---

### Delete Tenant Logo

**Endpoint:** `DELETE /api/v1/tenants/{tenant_id}/logo`

**Permissions:** Owner and Admin roles only

**Request:**
```http
DELETE /api/v1/tenants/{tenant_id}/logo
Authorization: Bearer {access_token}
```

**Response:**
```json
{
  "id": "tenant-uuid",
  "name": "Acme Corporation",
  "logo_url": null,
  ...
}
```

**Example (cURL):**
```bash
curl -X DELETE http://localhost:8000/api/v1/tenants/{tenant_id}/logo \
  -H "Authorization: Bearer {access_token}"
```

---

## Setting Tenant Contact Information

Update tenant contact details using the existing tenant update endpoint:

**Endpoint:** `PUT /api/v1/tenants/{tenant_id}`

**Request:**
```json
{
  "name": "Acme Corporation",
  "address": "123 Business Street, Suite 100, City, State, ZIP, Country",
  "phone": "+1 (555) 123-4567",
  "email": "contact@acme.com",
  "tax_label": "VAT"
}
```

**Response:**
```json
{
  "id": "tenant-uuid",
  "name": "Acme Corporation",
  "address": "123 Business Street, Suite 100, City, State, ZIP, Country",
  "phone": "+1 (555) 123-4567",
  "email": "contact@acme.com",
  "tax_label": "VAT",
  "logo_url": "uploads/logos/tenant-uuid.png",
  ...
}
```

---

## Invoice Branding Behavior

### With Logo and Contact Info
When a tenant has uploaded a logo and added contact information:
- Logo appears in the invoice header
- Tenant name, address, phone, and email are displayed
- Custom tax label is used (e.g., "VAT" instead of "Tax")
- Professional, branded appearance

### With Contact Info Only
When a tenant has contact information but no logo:
- Tenant information is displayed without logo
- Invoice remains professional and personalized
- Company name and details are prominent

### Without Branding
When a tenant has neither logo nor contact info:
- Generic header is displayed
- Default "Multi-Tenant SaaS" branding
- Standard "Tax" label is used

---

## Storage Configuration

### Local Storage (Default)
- Logos are stored in `uploads/logos/` directory
- File naming: `{tenant_id}.{extension}`
- Files are automatically cleaned up when replaced

### File Structure
```
uploads/
└── logos/
    ├── tenant-uuid-1.png
    ├── tenant-uuid-2.jpg
    └── tenant-uuid-3.svg
```

### Cloud Storage (Future Enhancement)
For production deployments, consider migrating to cloud storage:
- AWS S3
- Google Cloud Storage
- Azure Blob Storage

Update the `FileUploadService` class to integrate with your preferred cloud provider.

---

## Security Considerations

### File Validation
✅ **File Extension Validation**
- Only `.png`, `.jpg`, `.jpeg`, `.svg` allowed
- Case-insensitive checking

✅ **MIME Type Validation**
- Validates actual file content type
- Prevents extension spoofing

✅ **File Size Limits**
- Maximum 2MB per file
- Prevents DoS attacks via large files

✅ **Access Control**
- Upload/delete: Admin and Owner roles only
- Prevents unauthorized modifications

### Best Practices
1. **Regular Cleanup**: Periodically review and clean up unused logo files
2. **Backup**: Include `uploads/` directory in backup strategy
3. **Monitoring**: Track upload frequency and storage usage
4. **Rate Limiting**: API endpoints are rate-limited to prevent abuse
5. **Input Sanitization**: All file inputs are validated and sanitized

---

## Error Handling

### Common Errors

**400 Bad Request - Invalid File Extension**
```json
{
  "detail": "Invalid file extension. Allowed: .png, .jpg, .jpeg, .svg"
}
```

**400 Bad Request - Invalid File Type**
```json
{
  "detail": "Invalid file type. Allowed: PNG, JPG, JPEG, SVG"
}
```

**400 Bad Request - File Too Large**
```json
{
  "detail": "File size exceeds maximum allowed size of 2.0MB"
}
```

**401 Unauthorized**
```json
{
  "detail": "Not authenticated"
}
```

**403 Forbidden**
```json
{
  "detail": "You don't have permission to upload logo for this tenant"
}
```

**404 Not Found - Tenant**
```json
{
  "detail": "Tenant not found"
}
```

**404 Not Found - Logo**
```json
{
  "detail": "Tenant does not have a logo"
}
```

---

## Integration Examples

### Complete Branding Setup

```python
import requests

# 1. Update tenant contact information
tenant_data = {
    "name": "Acme Corporation",
    "address": "123 Business St, Suite 100, San Francisco, CA 94105",
    "phone": "+1 (415) 555-1234",
    "email": "billing@acme.com",
    "tax_label": "Sales Tax"
}

response = requests.put(
    f"http://localhost:8000/api/v1/tenants/{tenant_id}",
    json=tenant_data,
    headers={"Authorization": f"Bearer {access_token}"}
)
print("Tenant updated:", response.json())

# 2. Upload logo
with open("acme_logo.png", "rb") as logo_file:
    files = {"file": logo_file}
    response = requests.post(
        f"http://localhost:8000/api/v1/tenants/{tenant_id}/logo",
        files=files,
        headers={"Authorization": f"Bearer {access_token}"}
    )
print("Logo uploaded:", response.json())

# 3. Generate branded invoice
invoice_data = {
    "customer_name": "Client Company",
    "customer_email": "client@example.com",
    "issue_date": "2024-01-15",
    "due_date": "2024-02-15",
    "items": [
        {
            "description": "Professional Services",
            "quantity": 10,
            "unit_price": 150.00
        }
    ]
}

response = requests.post(
    "http://localhost:8000/api/v1/invoices/",
    json=invoice_data,
    headers={"Authorization": f"Bearer {access_token}"}
)
invoice = response.json()

# 4. Download branded PDF
pdf_response = requests.get(
    f"http://localhost:8000/api/v1/invoices/{invoice['id']}/pdf",
    headers={"Authorization": f"Bearer {access_token}"}
)

with open("branded_invoice.pdf", "wb") as pdf_file:
    pdf_file.write(pdf_response.content)
print("Branded invoice saved!")
```

---

## Testing

### Unit Tests
Run logo upload tests:
```bash
pytest tests/test_tenant_logo.py -v
```

### Manual Testing

1. **Upload a logo:**
```bash
curl -X POST http://localhost:8000/api/v1/tenants/{tenant_id}/logo \
  -H "Authorization: Bearer {token}" \
  -F "file=@logo.png"
```

2. **Retrieve the logo:**
```bash
curl -X GET http://localhost:8000/api/v1/tenants/{tenant_id}/logo \
  -o downloaded_logo.png
```

3. **Generate invoice and check branding:**
```bash
# Create invoice
curl -X POST http://localhost:8000/api/v1/invoices/ \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{...invoice data...}'

# Download PDF
curl -X GET http://localhost:8000/api/v1/invoices/{invoice_id}/pdf \
  -H "Authorization: Bearer {token}" \
  -o invoice.pdf
```

---

## Troubleshooting

### Logo Not Appearing in PDF

**Possible Causes:**
1. Logo file path is incorrect
2. Logo file was deleted manually
3. Permissions issue reading file

**Solution:**
- Check that `uploads/logos/` directory exists
- Verify logo file exists at the path in `tenant.logo_url`
- Ensure proper file permissions

### Upload Fails with 500 Error

**Possible Causes:**
1. Disk space full
2. Permission issues writing to `uploads/logos/`
3. Invalid file format

**Solution:**
- Check available disk space
- Verify directory permissions: `chmod 755 uploads/logos/`
- Validate file format before upload

---

## Future Enhancements

### Planned Features
- [ ] Cloud storage integration (S3, GCS, Azure)
- [ ] Logo image optimization and resizing
- [ ] Multiple logo variants (header, email, PDF)
- [ ] Custom color schemes for invoices
- [ ] Watermark support
- [ ] Logo preview before upload
- [ ] Batch logo upload for multiple tenants
- [ ] Logo usage analytics

### Migration Path
When ready to migrate to cloud storage:
1. Choose cloud provider
2. Update `FileUploadService` to use cloud SDK
3. Migrate existing logos to cloud storage
4. Update `logo_url` paths in database
5. Update PDF generator to fetch from cloud URLs

---

## Related Documentation

- [Invoice Management](INVOICE_IMPLEMENTATION.md)
- [PDF Generation](PDF_GENERATION.md)
- [Authentication](authentication.md)
- [API Structure](API_STRUCTURE.md)

---

## Support

For questions or issues related to tenant branding:
- Review this documentation
- Check test files: `tests/test_tenant_logo.py`
- Open an issue on GitHub

---

**Last Updated:** November 2024  
**Version:** 1.0
