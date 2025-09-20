from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class TenantBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Tenant name")
    domain: str = Field(..., min_length=3, max_length=100, description="Unique tenant domain")
    description: Optional[str] = Field(None, max_length=500, description="Tenant description")


class TenantCreate(TenantBase):
    pass


class TenantUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    is_active: Optional[bool] = None


class TenantInDB(TenantBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class Tenant(TenantInDB):
    pass
