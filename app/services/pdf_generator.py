"""
PDF Generator Service for Invoice Documents.

This service handles on-demand PDF generation for invoices using
WeasyPrint and Jinja2 templates. PDFs are generated in-memory without
storage to maintain database as single source of truth.
"""

from pathlib import Path
from typing import Optional
from decimal import Decimal
from datetime import datetime, timezone
from jinja2 import Environment, FileSystemLoader, TemplateNotFound
from weasyprint import HTML
from weasyprint.text.fonts import FontConfiguration

from app.models.invoice import Invoice, InvoiceStatus


class PDFGenerationError(Exception):
    """Custom exception for PDF generation errors."""
    pass


class PDFGenerator:
    """
    PDF Generator for invoice documents.

    Handles template rendering and PDF conversion using WeasyPrint
    with Jinja2 templates.

    Attributes:
        template_dir: Path to template directory
        env: Jinja2 environment for template rendering
        font_config: WeasyPrint font configuration
    """

    def __init__(self, template_dir: Optional[Path] = None):
        """
        Initialize PDF Generator.

        Args:
            template_dir: Custom template directory path.
                         Defaults to app/templates
        """
        if template_dir is None:
            # Get the app/templates directory
            base_dir = Path(__file__).resolve().parent.parent
            template_dir = base_dir / "templates"

        if not template_dir.exists():
            raise PDFGenerationError(
                f"Template directory not found: {template_dir}"
            )

        self.template_dir = template_dir
        self.env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            autoescape=True
        )

        # Configure fonts for WeasyPrint
        self.font_config = FontConfiguration()

    def _prepare_invoice_data(
        self,
        invoice: Invoice,
        tenant=None,
        creator=None
    ) -> dict:
        """
        Prepare invoice data for template rendering.

        Args:
            invoice: Invoice model instance
            tenant: Optional Tenant model instance for branding
            creator: Optional User model instance for creator name

        Returns:
            Dictionary with formatted invoice data
        """
        # Get currency symbol based on invoice currency
        currency_symbols = {
            "USD": "$",
            "GBP": "£",
            "EUR": "€",
            "NGN": "₦"
        }
        currency_code = invoice.currency.value if hasattr(
            invoice.currency, 'value'
        ) else str(invoice.currency)
        currency_symbol = currency_symbols.get(currency_code, "$")

        # Format monetary values
        def format_money(value: Decimal) -> str:
            return f"{currency_symbol}{value:,.2f}"

        # Format dates
        def format_date(date_str: Optional[str]) -> str:
            if not date_str:
                return "N/A"
            try:
                date_obj = datetime.fromisoformat(date_str)
                return date_obj.strftime("%B %d, %Y")
            except (ValueError, TypeError):
                return date_str

        # Prepare items data
        items_data = []
        for item in invoice.items:
            items_data.append({
                "description": item.description,
                "quantity": float(item.quantity),
                "unit_price": format_money(item.unit_price),
                "total_price": format_money(item.total_price)
            })

        # Determine if we should show draft watermark
        is_draft = invoice.status == InvoiceStatus.DRAFT
        show_draft_watermark = is_draft
        if tenant and hasattr(tenant, 'draft_watermark_enabled'):
            # Only show if tenant has enabled it (or default True)
            show_draft_watermark = (
                is_draft
                and (tenant.draft_watermark_enabled is not False)
            )

        # Prepare invoice data
        data = {
            "invoice_number": invoice.invoice_number,
            "issue_date": format_date(invoice.issue_date),
            "due_date": format_date(invoice.due_date),
            "status": invoice.status.value.upper(),
            "customer": {
                "name": invoice.customer_name,
                "email": invoice.customer_email or "N/A",
                "phone": invoice.customer_phone or "N/A",
                "address": invoice.customer_address or "N/A"
            },
            "items": items_data,
            "subtotal": format_money(invoice.subtotal),
            "tax_amount": format_money(invoice.tax_amount),
            "discount_amount": format_money(invoice.discount_amount),
            "total_amount": format_money(invoice.total_amount),
            "notes": invoice.notes or "",
            "payment_method": invoice.payment_method or "N/A",
            "paid_at": format_date(invoice.paid_at) if invoice.paid_at else "N/A",  # noqa: E501
            "generated_at": datetime.now(timezone.utc).strftime(
                "%B %d, %Y at %I:%M %p"
            ),
            "tenant": None,
            "logo_url": None,
            # PDF Customization defaults
            "primary_color": "#2563eb",
            "secondary_color": "#1e40af",
            "custom_footer": None,
            "show_draft_watermark": show_draft_watermark,
            "creator_name": None
        }

        # Add creator name if provided
        if creator and hasattr(creator, 'full_name'):
            data["creator_name"] = creator.full_name

        # Add tenant information if provided
        if tenant:
            data["tenant"] = {
                "name": tenant.name,
                "address": tenant.address or "N/A",
                "phone": tenant.phone or "N/A",
                "email": tenant.email or "N/A",
                "tax_label": tenant.tax_label or "Tax"
            }
            # Convert logo_url to absolute path for WeasyPrint
            if tenant.logo_url:
                from pathlib import Path
                base_dir = Path(__file__).resolve().parent.parent
                logo_path = base_dir / tenant.logo_url
                if logo_path.exists():
                    data["logo_url"] = str(logo_path)

            # Apply tenant PDF customization
            if hasattr(tenant, 'primary_color') and tenant.primary_color:
                data["primary_color"] = tenant.primary_color
            if hasattr(tenant, 'secondary_color') and tenant.secondary_color:
                data["secondary_color"] = tenant.secondary_color
            if hasattr(tenant, 'custom_footer') and tenant.custom_footer:
                data["custom_footer"] = tenant.custom_footer

        return data

    def generate_invoice_pdf(
        self,
        invoice: Invoice,
        tenant=None,
        creator=None
    ) -> bytes:
        """
        Generate PDF for an invoice.

        Args:
            invoice: Invoice model instance with loaded relationships
            tenant: Optional Tenant model instance for branding
            creator: Optional User model instance for creator name

        Returns:
            PDF file content as bytes

        Raises:
            PDFGenerationError: If template not found or PDF generation fails
        """
        try:
            # Load template
            template = self.env.get_template("invoice.html")
        except TemplateNotFound as e:
            raise PDFGenerationError(
                f"Invoice template not found: {e}"
            )

        # Prepare data
        invoice_data = self._prepare_invoice_data(invoice, tenant, creator)

        # Render HTML
        try:
            html_content = template.render(**invoice_data)
        except Exception as e:
            raise PDFGenerationError(
                f"Template rendering failed: {str(e)}"
            )

        # Generate PDF
        try:
            html_doc = HTML(string=html_content)
            pdf_bytes = html_doc.write_pdf(font_config=self.font_config)
            return pdf_bytes
        except Exception as e:
            raise PDFGenerationError(
                f"PDF generation failed: {str(e)}"
            )


# Create singleton instance
_pdf_generator: Optional[PDFGenerator] = None


def get_pdf_generator() -> PDFGenerator:
    """
    Get or create PDF Generator singleton instance.

    Returns:
        PDFGenerator instance
    """
    global _pdf_generator
    if _pdf_generator is None:
        _pdf_generator = PDFGenerator()
    return _pdf_generator
