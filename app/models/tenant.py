from app.models.general_model import Gen_Model, Base
from sqlalchemy import Column, String, Boolean, Numeric, Text, Integer


class Tenant(Gen_Model, Base):
    """
    Tenant model for multi-tenant architecture.

    Attributes:
        name: Tenant name
        domain: Unique tenant domain (optional)
        business_registration_number: Unique business registration number (optional)
        plan_type: Subscription plan type (only super admin can modify)
        description: Tenant description (optional)
        is_active: Whether tenant is active
        default_currency: Default currency for invoices (NGN, USD, GBP, EUR)
        tax_rate: Default tax/VAT rate as percentage (0-100, tax-free nullable)
        tax_label: Label for tax (e.g., 'VAT', 'GST', 'Sales Tax', or None)
        logo_url: URL/path to tenant logo for branded invoices (optional)
        address: Tenant business address for invoices (optional)
        phone: Tenant contact phone number (optional)
        email: Tenant contact email for invoices (optional)
        invoice_number_prefix: Custom prefix for invoice numbers
            (default: 'INV')
        invoice_number_format: Format string for invoice numbers
            (default: '{prefix}-{date}-{sequence:04d}')
        invoice_number_sequence: Atomic counter for invoice numbering
            (default: 0)
        primary_color: Primary brand color for PDF (hex, default: '#2563eb')
        secondary_color: Secondary brand color for PDF (hex, default: '#1e40af')
        custom_footer: Custom footer text for invoices (optional)
        draft_watermark_enabled: Whether to show DRAFT watermark (default: True)
    """
    __tablename__ = "tenants"

    name = Column(String(100), nullable=False)
    domain = Column(String(100), nullable=True, unique=True)
    business_registration_number = Column(String(100), nullable=True, unique=True)
    plan_type = Column(String(20), default="Standard")
    description = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True)
    default_currency = Column(String(3), default="NGN", nullable=False)
    tax_rate = Column(Numeric(5, 2), nullable=True)
    tax_label = Column(String(50), nullable=True)
    logo_url = Column(String(500), nullable=True)
    address = Column(Text, nullable=True)
    phone = Column(String(20), nullable=True)
    email = Column(String(255), nullable=True)
    invoice_number_prefix = Column(
        String(20), default="INV", nullable=False
    )
    invoice_number_format = Column(
        String(100),
        default="{prefix}-{date}-{sequence:04d}",
        nullable=False
    )
    invoice_number_sequence = Column(Integer, default=0, nullable=False)
    # PDF Customization fields
    primary_color = Column(String(7), default="#2563eb", nullable=False)
    secondary_color = Column(String(7), default="#1e40af", nullable=False)
    custom_footer = Column(Text, nullable=True)
    draft_watermark_enabled = Column(Boolean, default=True, nullable=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
