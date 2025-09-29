from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.db.session import get_db
from app.models.tenant import Tenant as TenantModel
from app.schemas.tenant import Tenant, TenantCreate, TenantUpdate

router = APIRouter()


@router.post("/", response_model=Tenant, status_code=201)
def create_tenant(
    tenant_in: TenantCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new tenant.
    """
    # Check if domain already exists, but only if domain is not None
    if tenant_in.domain is not None:
        existing_tenant = db.query(TenantModel).filter(
            TenantModel.domain == tenant_in.domain
        ).first()
        if existing_tenant:
            raise HTTPException(
                status_code=400,
                detail="A tenant with this domain already exists"
            )

    # Create new tenant
    try:
        db_tenant = TenantModel(**tenant_in.dict())
        db.add(db_tenant)
        db.commit()
        db.refresh(db_tenant)
        return db_tenant
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Failed to create tenant. Domain may already exist."
        )


@router.get("/", response_model=List[Tenant])
def list_tenants(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Get list of tenants.
    """
    tenants = db.query(TenantModel).offset(skip).limit(limit).all()
    return tenants


@router.get("/{tenant_id}", response_model=Tenant)
def get_tenant(
    tenant_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a specific tenant by ID.
    """
    tenant = db.query(TenantModel).filter(TenantModel.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return tenant


@router.put("/{tenant_id}", response_model=Tenant)
def update_tenant(
    tenant_id: int,
    tenant_update: TenantUpdate,
    db: Session = Depends(get_db)
):
    """
    Update a tenant.
    """
    tenant = db.query(TenantModel).filter(TenantModel.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    update_data = tenant_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(tenant, field, value)

    db.commit()
    db.refresh(tenant)
    return tenant


@router.delete("/{tenant_id}")
def delete_tenant(
    tenant_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete a tenant (soft delete by setting is_active to False).
    """
    tenant = db.query(TenantModel).filter(TenantModel.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    tenant.is_active = False
    db.commit()
    return {"message": "Tenant deactivated successfully"}
