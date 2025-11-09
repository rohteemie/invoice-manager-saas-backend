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
