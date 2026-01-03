from typing import List
from fastapi import (
    APIRouter, Depends, HTTPException, UploadFile, File, Request
)
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.db.session import get_db
from app.models.tenant import Tenant as TenantModel
from app.models.user import User as UserModel, UserRole
from app.schemas.tenant import (
    Tenant, TenantCreate, TenantUpdate, TenantRegister, TenantWithOwner
)
from app.core.security import get_password_hash, generate_verification_token
from app.core.config import settings
from app.core.deps import require_role
from app.services.file_upload import get_file_upload_service, FileUploadError
from app.services.audit_logger import log_tenant_event
from app.models.audit_log import AuditAction
from app.tasks.email_tasks import send_verification_email_task

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

        # Generate verification token with expiration
        verification_token, token_expires_at = generate_verification_token()

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
            verification_token=verification_token,
            verification_token_expires_at=token_expires_at
        )
        db.add(db_owner)

        # Commit both together
        db.commit()
        db.refresh(db_tenant)
        db.refresh(db_owner)

        # Send verification email asynchronously
        try:
            send_verification_email_task.delay(
                email=db_owner.email,
                token=verification_token,
                full_name=db_owner.full_name,
                base_url=(
                    settings.EMAIL_VERIFICATION_BASE_URL
                    or "http://localhost:5173"
                ),
            )
        except Exception as e:
            # Log but don't fail registration if email fails
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(
                "Failed to queue verification email for %s: %s",
                db_owner.email, str(e)
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
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Update a tenant.
    """
    tenant = db.query(TenantModel).filter(TenantModel.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    update_data = tenant_update.model_dump(exclude_unset=True)

    # Track changes for audit
    changes = {}
    for field, value in update_data.items():
        if hasattr(tenant, field):
            old_value = getattr(tenant, field)
            if old_value != value:
                changes[field] = {"before": old_value, "after": value}

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

    # Log tenant update
    if changes:
        log_tenant_event(
            db=db,
            request=request,
            action=AuditAction.TENANT_UPDATED,
            resource_id=tenant.id,
            tenant_id=tenant.id,
            changes=changes,
            description=f"Tenant {tenant.name} updated"
        )

    return tenant


@router.delete("/{tenant_id}")
def delete_tenant(
    tenant_id: str,
    db: Session = Depends(get_db)
):
    """
    Delete a tenant (soft delete by setting is_active to False).

    Note: This endpoint should not be accessible to organization owners.
    Organization deletion requires contacting the technical team/developer
    organization. This endpoint exists for administrative/system-level
    operations only.
    """
    tenant = db.query(TenantModel).filter(TenantModel.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    tenant.is_active = False
    db.commit()
    return {"message": "Tenant deactivated successfully"}


@router.post("/{tenant_id}/logo", response_model=Tenant)
def upload_tenant_logo(
    tenant_id: str,
    file: UploadFile = File(...),
    current_user: UserModel = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    """
    Upload a logo for a tenant.

    Permissions: Admin and Owner roles only.

    Requirements:
    - File types: PNG, JPG, JPEG, SVG only
    - Maximum file size: 2MB

    The uploaded logo will be used in branded invoices and reports.
    """
    # Check if tenant exists
    tenant = db.query(TenantModel).filter(TenantModel.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    # Verify user has access to this tenant
    if (
        current_user.tenant_id != tenant_id
        and current_user.role != UserRole.OWNER
    ):
        raise HTTPException(
            status_code=403,
            detail="You don't have permission to upload logo for this tenant"
        )

    # Upload and save file
    try:
        file_service = get_file_upload_service()
        logo_url = file_service.save_logo(tenant_id, file)

        # Update tenant with logo URL
        tenant.logo_url = logo_url
        db.commit()
        db.refresh(tenant)

        return tenant
    except FileUploadError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to upload logo: {str(e)}"
        )


@router.get("/{tenant_id}/logo")
def get_tenant_logo(
    tenant_id: str,
    db: Session = Depends(get_db)
):
    """
    Retrieve the logo file for a tenant.

    Returns the logo image file if it exists, or a 404 error if not found.
    """
    # Check if tenant exists
    tenant = db.query(TenantModel).filter(TenantModel.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    # Check if tenant has a logo
    if not tenant.logo_url:
        raise HTTPException(
            status_code=404,
            detail="Tenant does not have a logo"
        )

    # Get logo file path
    file_service = get_file_upload_service()
    logo_path = file_service.get_logo_path(tenant.logo_url)

    if not logo_path:
        raise HTTPException(
            status_code=404,
            detail="Logo file not found"
        )

    # Return file
    return FileResponse(
        path=logo_path,
        media_type="image/png",  # Will be auto-detected by FileResponse
        filename=f"tenant_{tenant_id}_logo{logo_path.suffix}"
    )


@router.delete("/{tenant_id}/logo", response_model=Tenant)
def delete_tenant_logo(
    tenant_id: str,
    current_user: UserModel = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    """
    Delete the logo for a tenant.

    Permissions: Admin and Owner roles only.
    """
    # Check if tenant exists
    tenant = db.query(TenantModel).filter(TenantModel.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    # Verify user has access to this tenant
    if (
        current_user.tenant_id != tenant_id
        and current_user.role != UserRole.OWNER
    ):
        raise HTTPException(
            status_code=403,
            detail=(
                "You don't have permission to "
                "delete logo for this tenant"
            )
        )

    # Delete logo file
    if tenant.logo_url:
        file_service = get_file_upload_service()
        file_service.delete_logo(tenant_id)

        # Update tenant
        tenant.logo_url = None
        db.commit()
        db.refresh(tenant)

    return tenant
