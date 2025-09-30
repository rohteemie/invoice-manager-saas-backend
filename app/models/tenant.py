from app.models.general_model import Gen_Model, Base
from sqlalchemy import Column, String, Boolean


class Tenant(Gen_Model, Base):
    """
    Tenant model for multi-tenant architecture.
    """
    __tablename__ = "tenants"

    name = Column(String(100), nullable=False)
    domain = Column(String(100), nullable=True, unique=True)
    plan_type = Column(String(20), default="free")
    description = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
