from app.models.general_model import Gen_Model, Base
from sqlalchemy import Column, String, Boolean, ForeignKey


class Client(Gen_Model, Base):
    """
    Client model for multi-tenant invoice management.

    Represents customers/clients to whom invoices are issued.
    Each client belongs to a specific tenant for data isolation.

    Attributes:
        name: Client's full name or company name
        email: Client's email address for communication
        phone: Client's phone number (optional)
        address: Client's physical address (optional)
        tax_id: Client's tax identification number (optional, GDPR-sensitive)
        tenant_id: Associated tenant for data isolation
        is_active: Soft delete flag for GDPR right-to-be-forgotten
    """
    __tablename__ = "clients"

    name = Column(String(200), nullable=False, index=True)
    email = Column(String(255), nullable=True, index=True)
    phone = Column(String(50), nullable=True)
    address = Column(String(500), nullable=True)
    tax_id = Column(String(100), nullable=True)
    tenant_id = Column(String(60), ForeignKey("tenants.id"), nullable=False,
                       index=True)
    is_active = Column(Boolean, default=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
