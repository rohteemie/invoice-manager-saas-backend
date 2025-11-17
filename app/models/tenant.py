from app.models.general_model import Gen_Model, Base
from sqlalchemy import Column, String, Boolean, Numeric


class Tenant(Gen_Model, Base):
    """
    Tenant model for multi-tenant architecture.

    Attributes:
        name: Tenant name
        domain: Unique tenant domain (optional)
        plan_type: Subscription plan type
        description: Tenant description (optional)
        is_active: Whether tenant is active
        default_currency: Default currency for invoices (NGN, USD, GBP, EUR)
        tax_rate: Default tax/VAT rate as percentage (0-100, tax-free nullable)
        tax_label: Label for tax (e.g., 'VAT', 'GST', 'Sales Tax', or None)
    """
    __tablename__ = "tenants"

    name = Column(String(100), nullable=False)
    domain = Column(String(100), nullable=True, unique=True)
    plan_type = Column(String(20), default="free")
    description = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True)
    default_currency = Column(String(3), default="USD", nullable=False)
    tax_rate = Column(Numeric(5, 2), nullable=True)
    tax_label = Column(String(50), nullable=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
