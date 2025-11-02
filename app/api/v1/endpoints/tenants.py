from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.db.session import get_db
from app.models.tenant import Tenant as TenantModel
from app.models.user import User as UserModel, UserRole
from app.schemas.tenant import (
    Tenant, TenantCreate, TenantUpdate, TenantRegister, TenantWithOwner
)
from app.core.security import get_password_hash, generate_verification_token
from app.core.email import send_verification_email
from app.core.config import settings

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
        db_tenant = TenantModel(**tenant_in.model_dump())
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


@router.post("/register", response_model=TenantWithOwner, status_code=201)
def register_tenant_with_owner(
    tenant_register: TenantRegister,
    db: Session = Depends(get_db)
):
    """
    Create a new tenant with its first owner user in a single transaction.

    This endpoint simplifies the onboarding process by creating both
    a tenant and its owner user atomically. This ensures:
    - No tenant exists without an owner
    - No dangling users without a tenant
    - Consistent data state
    """
    # Check if tenant domain already exists, but only if domain is not None
    if tenant_register.domain is not None:
        existing_tenant = db.query(TenantModel).filter(
            TenantModel.domain == tenant_register.domain
        ).first()
        if existing_tenant:
            raise HTTPException(
                status_code=400,
                detail="A tenant with this domain already exists"
            )

    # Check if owner email already exists
    existing_user = db.query(UserModel).filter(
        UserModel.email == tenant_register.owner.email
    ).first()
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="A user with this email already exists"
        )

    # Create tenant and owner in a transaction
    try:
        # Create tenant
        tenant_data = tenant_register.model_dump(exclude={'owner'})
        db_tenant = TenantModel(**tenant_data)
        db.add(db_tenant)
        db.flush()  # Flush to get tenant.id without committing

        # Generate verification token
        verification_token = generate_verification_token()

        # Create owner user
        hashed_password = get_password_hash(tenant_register.owner.password)
        db_owner = UserModel(
            email=tenant_register.owner.email,
            full_name=tenant_register.owner.full_name,
            hashed_password=hashed_password,
            role=UserRole.OWNER,
            tenant_id=db_tenant.id,
            is_active=True,
            is_verified=False,
            verification_token=verification_token
        )
        db.add(db_owner)

        # Commit both together
        db.commit()
        db.refresh(db_tenant)
        db.refresh(db_owner)

        # Send verification email
        send_verification_email(
            email=db_owner.email,
            token=verification_token,
            full_name=db_owner.full_name,
            base_url=settings.EMAIL_VERIFICATION_BASE_URL
        )

        # Return combined response
        return {
            "tenant": db_tenant,
            "owner": {
                "id": db_owner.id,
                "email": db_owner.email,
                "full_name": db_owner.full_name,
                "role": db_owner.role.value,
                "tenant_id": db_owner.tenant_id,
                "is_active": db_owner.is_active,
                "is_verified": db_owner.is_verified,
                "created_at": db_owner.created_at,
                "updated_at": db_owner.updated_at
            }
        }
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=(
                "Failed to create tenant and owner. "
                "Domain or email may already exist."
            )
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
    tenant_id: str,
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
    tenant_id: str,
    tenant_update: TenantUpdate,
    db: Session = Depends(get_db)
):
    """
    Update a tenant.
    """
    tenant = db.query(TenantModel).filter(TenantModel.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    update_data = tenant_update.model_dump(exclude_unset=True)
    # Check for domain uniqueness if domain is being updated
    if "domain" in update_data and update_data["domain"] is not None:
        new_domain = update_data["domain"]
        if new_domain != tenant.domain:
            existing_tenant = db.query(TenantModel).filter(
                TenantModel.domain == new_domain,
                TenantModel.id != tenant_id
            ).first()
            if existing_tenant:
                raise HTTPException(
                    status_code=400,
                    detail="A tenant with this domain already exists"
                )
    for field, value in update_data.items():
        setattr(tenant, field, value)

    db.commit()
    db.refresh(tenant)
    return tenant


@router.delete("/{tenant_id}")
def delete_tenant(
    tenant_id: str,
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
