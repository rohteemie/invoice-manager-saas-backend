"""
Unit tests for PDF Generator Service.

Tests the PDF generation functionality, template rendering,
and error handling for invoice PDFs.
"""
from pathlib import Path
from decimal import Decimal

import pytest
from app.services.pdf_generator import (
    PDFGenerator,
    PDFGenerationError,
    get_pdf_generator
)
from app.models.invoice import Invoice, InvoiceItem, InvoiceStatus


class MockTenant:
    """Mock tenant for testing PDF customization."""

    def __init__(
        self,
        name="Test Company",
        address="123 Test St",
        phone="+1234567890",
        email="contact@test.com",
        tax_label="VAT",
        logo_url=None,
        primary_color="#2563eb",
        secondary_color="#1e40af",
        custom_footer=None,
        draft_watermark_enabled=True
    ):
        self.name = name
        self.address = address
        self.phone = phone
        self.email = email
        self.tax_label = tax_label
        self.logo_url = logo_url
        self.primary_color = primary_color
        self.secondary_color = secondary_color
        self.custom_footer = custom_footer
        self.draft_watermark_enabled = draft_watermark_enabled


class MockUser:
    """Mock user for testing creator name on PDF."""

    def __init__(self, full_name="John Smith"):
        self.full_name = full_name


@pytest.fixture
def sample_invoice():
    """Create a sample invoice with items for testing."""
    invoice = Invoice(
        id="test-invoice-1",
        invoice_number="INV-20240115-0001",
        tenant_id="test-tenant",
        creator_id="test-user",
        customer_name="John Doe",
        customer_email="john@example.com",
        customer_phone="+1234567890",
        customer_address="123 Main St, City, Country",
        status=InvoiceStatus.SENT,
        issue_date="2024-01-15",
        due_date="2024-02-15",
        subtotal=Decimal("250.00"),
        tax_amount=Decimal("25.00"),
        discount_amount=Decimal("0.00"),
        total_amount=Decimal("275.00"),
        notes="Please pay on time",
        payment_method=None,
        paid_at=None
    )

    # Add invoice items
    invoice.items = [
        InvoiceItem(
            id="item-1",
            invoice_id=invoice.id,
            description="Product A",
            quantity=Decimal("2.00"),
            unit_price=Decimal("100.00"),
            total_price=Decimal("200.00")
        ),
        InvoiceItem(
            id="item-2",
            invoice_id=invoice.id,
            description="Product B",
            quantity=Decimal("1.00"),
            unit_price=Decimal("50.00"),
            total_price=Decimal("50.00")
        )
    ]

    return invoice


@pytest.fixture
def pdf_generator():
    """Get PDF generator instance."""
    return get_pdf_generator()


def test_pdf_generator_initialization():
    """Test PDF generator can be initialized."""
    generator = PDFGenerator()
    assert generator is not None
    assert generator.template_dir.exists()
    assert generator.env is not None
    assert generator.font_config is not None


def test_pdf_generator_singleton():
    """Test that get_pdf_generator returns singleton instance."""
    gen1 = get_pdf_generator()
    gen2 = get_pdf_generator()
    assert gen1 is gen2


def test_prepare_invoice_data(pdf_generator, sample_invoice):
    """Test invoice data preparation for template rendering."""
    data = pdf_generator._prepare_invoice_data(sample_invoice)

    assert data["invoice_number"] == "INV-20240115-0001"
    assert data["status"] == "SENT"
    assert data["customer"]["name"] == "John Doe"
    assert data["customer"]["email"] == "john@example.com"
    assert data["subtotal"] == "$250.00"
    assert data["total_amount"] == "$275.00"
    assert len(data["items"]) == 2
    assert data["items"][0]["description"] == "Product A"
    assert data["items"][0]["quantity"] == 2.0
    assert data["items"][0]["unit_price"] == "$100.00"


def test_prepare_invoice_data_with_minimal_fields(pdf_generator):
    """Test data preparation with minimal invoice fields."""
    invoice = Invoice(
        id="test-invoice-2",
        invoice_number="INV-20240116-0002",
        tenant_id="test-tenant",
        creator_id="test-user",
        customer_name="Jane Doe",
        customer_email=None,
        customer_phone=None,
        customer_address=None,
        status=InvoiceStatus.DRAFT,
        issue_date="2024-01-16",
        due_date=None,
        subtotal=Decimal("100.00"),
        tax_amount=Decimal("0.00"),
        discount_amount=Decimal("0.00"),
        total_amount=Decimal("100.00"),
        notes=None,
        payment_method=None,
        paid_at=None
    )
    invoice.items = []

    data = pdf_generator._prepare_invoice_data(invoice)

    assert data["customer"]["email"] == "N/A"
    assert data["customer"]["phone"] == "N/A"
    assert data["customer"]["address"] == "N/A"
    assert data["due_date"] == "N/A"
    assert data["notes"] == ""


def test_generate_invoice_pdf_success(pdf_generator, sample_invoice):
    """Test successful PDF generation."""
    pdf_bytes = pdf_generator.generate_invoice_pdf(sample_invoice)

    assert pdf_bytes is not None
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 0
    # Check PDF header
    assert pdf_bytes[:4] == b'%PDF'


def test_generate_invoice_pdf_with_paid_invoice(pdf_generator):
    """Test PDF generation for a paid invoice."""
    invoice = Invoice(
        id="test-invoice-3",
        invoice_number="INV-20240117-0003",
        tenant_id="test-tenant",
        creator_id="test-user",
        customer_name="Alice Smith",
        customer_email="alice@example.com",
        customer_phone="+9876543210",
        customer_address="456 Oak Ave, Town, Country",
        status=InvoiceStatus.PAID,
        issue_date="2024-01-17",
        due_date="2024-02-17",
        subtotal=Decimal("500.00"),
        tax_amount=Decimal("50.00"),
        discount_amount=Decimal("25.00"),
        total_amount=Decimal("525.00"),
        notes="Thank you for your business",
        payment_method="Credit Card",
        paid_at="2024-01-20"
    )
    invoice.items = [
        InvoiceItem(
            id="item-3",
            invoice_id=invoice.id,
            description="Service Fee",
            quantity=Decimal("1.00"),
            unit_price=Decimal("500.00"),
            total_price=Decimal("500.00")
        )
    ]

    pdf_bytes = pdf_generator.generate_invoice_pdf(invoice)

    assert pdf_bytes is not None
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 0


def test_invalid_template_directory():
    """Test initialization with invalid template directory."""
    with pytest.raises(PDFGenerationError) as exc_info:
        PDFGenerator(template_dir=Path("/nonexistent/path"))

    assert "Template directory not found" in str(exc_info.value)


def test_generate_pdf_handles_special_characters(pdf_generator):
    """Test PDF generation with special characters in data."""
    invoice = Invoice(
        id="test-invoice-4",
        invoice_number="INV-20240118-0004",
        tenant_id="test-tenant",
        creator_id="test-user",
        customer_name="José García & Sons Ltd.",
        customer_email="jose@example.com",
        customer_phone="+1-555-1234",
        customer_address="123 O'Brien St, Café District",
        status=InvoiceStatus.DRAFT,
        issue_date="2024-01-18",
        due_date="2024-02-18",
        subtotal=Decimal("100.00"),
        tax_amount=Decimal("0.00"),
        discount_amount=Decimal("0.00"),
        total_amount=Decimal("100.00"),
        notes="Special characters: €, £, ñ, <>&",
        payment_method=None,
        paid_at=None
    )
    invoice.items = [
        InvoiceItem(
            id="item-4",
            invoice_id=invoice.id,
            description="Product with <special> & \"chars\"",
            quantity=Decimal("1.00"),
            unit_price=Decimal("100.00"),
            total_price=Decimal("100.00")
        )
    ]

    pdf_bytes = pdf_generator.generate_invoice_pdf(invoice)

    assert pdf_bytes is not None
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 0


def test_prepare_invoice_data_with_custom_colors(pdf_generator, sample_invoice):
    """Test that custom colors are applied from tenant settings."""
    tenant = MockTenant(
        primary_color="#ff5500",
        secondary_color="#003366"
    )

    data = pdf_generator._prepare_invoice_data(sample_invoice, tenant)

    assert data["primary_color"] == "#ff5500"
    assert data["secondary_color"] == "#003366"


def test_prepare_invoice_data_with_custom_footer(pdf_generator, sample_invoice):
    """Test that custom footer is applied from tenant settings."""
    tenant = MockTenant(
        custom_footer="Custom company footer text - All rights reserved."
    )

    data = pdf_generator._prepare_invoice_data(sample_invoice, tenant)

    assert data["custom_footer"] == (
        "Custom company footer text - All rights reserved."
    )


def test_prepare_invoice_data_with_creator_name(pdf_generator, sample_invoice):
    """Test that creator name is included in data."""
    creator = MockUser(full_name="Jane Manager")

    data = pdf_generator._prepare_invoice_data(
        sample_invoice, tenant=None, creator=creator
    )

    assert data["creator_name"] == "Jane Manager"


def test_draft_watermark_enabled_for_draft_invoice(pdf_generator):
    """Test that draft watermark is shown for draft invoices by default."""
    invoice = Invoice(
        id="test-invoice-5",
        invoice_number="INV-20240119-0005",
        tenant_id="test-tenant",
        creator_id="test-user",
        customer_name="Test Customer",
        status=InvoiceStatus.DRAFT,
        issue_date="2024-01-19",
        subtotal=Decimal("100.00"),
        tax_amount=Decimal("0.00"),
        discount_amount=Decimal("0.00"),
        total_amount=Decimal("100.00")
    )
    invoice.items = []

    data = pdf_generator._prepare_invoice_data(invoice)

    assert data["show_draft_watermark"] is True


def test_draft_watermark_not_shown_for_sent_invoice(pdf_generator):
    """Test that draft watermark is not shown for non-draft invoices."""
    invoice = Invoice(
        id="test-invoice-6",
        invoice_number="INV-20240119-0006",
        tenant_id="test-tenant",
        creator_id="test-user",
        customer_name="Test Customer",
        status=InvoiceStatus.SENT,
        issue_date="2024-01-19",
        subtotal=Decimal("100.00"),
        tax_amount=Decimal("0.00"),
        discount_amount=Decimal("0.00"),
        total_amount=Decimal("100.00")
    )
    invoice.items = []

    data = pdf_generator._prepare_invoice_data(invoice)

    assert data["show_draft_watermark"] is False


def test_draft_watermark_disabled_by_tenant(pdf_generator):
    """Test that draft watermark can be disabled by tenant setting."""
    invoice = Invoice(
        id="test-invoice-7",
        invoice_number="INV-20240119-0007",
        tenant_id="test-tenant",
        creator_id="test-user",
        customer_name="Test Customer",
        status=InvoiceStatus.DRAFT,
        issue_date="2024-01-19",
        subtotal=Decimal("100.00"),
        tax_amount=Decimal("0.00"),
        discount_amount=Decimal("0.00"),
        total_amount=Decimal("100.00")
    )
    invoice.items = []

    tenant = MockTenant(draft_watermark_enabled=False)

    data = pdf_generator._prepare_invoice_data(invoice, tenant)

    assert data["show_draft_watermark"] is False


def test_generate_pdf_with_all_customizations(pdf_generator, sample_invoice):
    """Test PDF generation with all customization options."""
    tenant = MockTenant(
        name="Custom Company",
        primary_color="#e63946",
        secondary_color="#1d3557",
        custom_footer="Payment terms: Net 30 days",
        draft_watermark_enabled=True
    )
    creator = MockUser(full_name="Sales Rep")

    pdf_bytes = pdf_generator.generate_invoice_pdf(
        sample_invoice, tenant, creator
    )

    assert pdf_bytes is not None
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 0
    assert pdf_bytes[:4] == b'%PDF'


def test_generate_pdf_draft_with_watermark(pdf_generator):
    """Test PDF generation for draft invoice includes watermark."""
    invoice = Invoice(
        id="test-invoice-8",
        invoice_number="INV-20240120-0008",
        tenant_id="test-tenant",
        creator_id="test-user",
        customer_name="Draft Customer",
        status=InvoiceStatus.DRAFT,
        issue_date="2024-01-20",
        subtotal=Decimal("100.00"),
        tax_amount=Decimal("0.00"),
        discount_amount=Decimal("0.00"),
        total_amount=Decimal("100.00")
    )
    invoice.items = [
        InvoiceItem(
            id="item-8",
            invoice_id=invoice.id,
            description="Draft Product",
            quantity=Decimal("1.00"),
            unit_price=Decimal("100.00"),
            total_price=Decimal("100.00")
        )
    ]

    tenant = MockTenant(draft_watermark_enabled=True)

    pdf_bytes = pdf_generator.generate_invoice_pdf(invoice, tenant)

    assert pdf_bytes is not None
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 0
    assert pdf_bytes[:4] == b'%PDF'


def test_prepare_invoice_data_defaults(pdf_generator, sample_invoice):
    """Test that default customization values are set."""
    data = pdf_generator._prepare_invoice_data(sample_invoice)

    # Check default values are set
    assert data["primary_color"] == "#2563eb"
    assert data["secondary_color"] == "#1e40af"
    assert data["custom_footer"] is None
    assert data["creator_name"] is None


def test_invalid_hex_colors_fallback_to_defaults(pdf_generator, sample_invoice):
    """Test that invalid hex colors fall back to defaults."""
    tenant = MockTenant(
        primary_color="invalid-color",
        secondary_color="123456"  # Missing #
    )

    data = pdf_generator._prepare_invoice_data(sample_invoice, tenant)

    # Invalid colors should fall back to defaults
    assert data["primary_color"] == "#2563eb"
    assert data["secondary_color"] == "#1e40af"


def test_valid_hex_colors_accepted(pdf_generator, sample_invoice):
    """Test that valid hex colors are accepted."""
    tenant = MockTenant(
        primary_color="#FF5500",
        secondary_color="#aabbcc"
    )

    data = pdf_generator._prepare_invoice_data(sample_invoice, tenant)

    assert data["primary_color"] == "#FF5500"
    assert data["secondary_color"] == "#aabbcc"
