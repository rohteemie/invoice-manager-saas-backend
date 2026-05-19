import logging
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi import Request, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func
from app.db.session import get_db
from app.models.tenant import Tenant as TenantModel
from app.models.user import User as UserModel, UserRole
from app.schemas.tenant import Tenant, TenantCreate
from app.schemas.tenant import TenantRegister, TenantWithOwner
from app.schemas.tenant import SuperAdminTenantUpdate
from app.schemas.pagination import PaginatedResponse, create_paginated_response
from app.core.security import get_password_hash, generate_verification_token
from app.core.config import settings
from app.core.deps import require_role, get_current_active_user
from app.core.deps import require_superadmin
from app.services.file_upload import get_file_upload_service, FileUploadError
from app.services.audit_logger import log_tenant_event
from app.models.audit_log import AuditAction
from app.tasks.email_tasks import send_verification_email_task

router = APIRouter()
logger = logging.getLogger(__name__)
DEFAULT_EMAIL_BASE_URL = "http://localhost:5173"
VERIFICATION_EMAIL_QUEUE_MAX_ATTEMPTS = 3


def queue_verification_email_with_retry(
    email: str,
    token: str,
    full_name: str
) -> dict:
    """
    Queue verification email with broker-level retry attempts.
    """
    payload = {
        "email": email,
        "token": token,
        "full_name": full_name,
        "base_url": settings.EMAIL_VERIFICATION_BASE_URL or DEFAULT_EMAIL_BASE_URL
    }

    for attempt in range(1, VERIFICATION_EMAIL_QUEUE_MAX_ATTEMPTS + 1):
        try:
            send_verification_email_task.delay(**payload)
            return {
                "status": "queued",
                "message": "Verification email has been queued for delivery."
            }
        except Exception as exc:
            logger.warning(
                (
                    "Failed to queue verification email for %s "
                    "(attempt %s/%s): %s"
                ),
                email,
                attempt,
                VERIFICATION_EMAIL_QUEUE_MAX_ATTEMPTS,
                str(exc)
            )

    logger.error(
        "Verification email queueing failed after %s attempts for %s",
        VERIFICATION_EMAIL_QUEUE_MAX_ATTEMPTS,
        email
    )
    raise RuntimeError(
        "Verification email delivery could not be queued for tenant "
        "registration."
    )


@router.post("/", response_model=Tenant, status_code=201)
def create_tenant(
    tenant_in: TenantCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new tenant.

    Requires at least one unique identifier:
    domain or business_registration_number.

    Currency Configuration:
    - default_currency: Required field, defaults to 'NGN' if not specified
    - Supported currencies: NGN, USD, GBP, EUR
    - All invoices created for this tenant will use this currency
    """
    # Validate that at least one unique identifier is provided
    if not tenant_in.domain and not tenant_in.business_registration_number:
        raise HTTPException(
            status_code=400,
            detail=(
                "Either domain or business_registration_number "
                "must be provided"
            )
        )

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

    # Check if business_registration_number already exists
    if tenant_in.business_registration_number is not None:
        existing_tenant = db.query(TenantModel).filter(
            TenantModel.business_registration_number
            == tenant_in.business_registration_number
        ).first()
        if existing_tenant:
            raise HTTPException(
                status_code=400,
                detail=(
                    "A tenant with this business registration number "
                    "already exists"
                )
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
            detail=(
                "Failed to create tenant. Domain or business registration "
                "number may already exist."
            )
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

    Requires at least one unique identifier:
    domain or business_registration_number.

    Currency Configuration:
    - default_currency: Required field, defaults to 'NGN' if not specified
    - Supported currencies: NGN, USD, GBP, EUR
    - All invoices created will use this currency
    """
    # Validate that at least one unique identifier is provided
    if (
        not tenant_register.domain
        and not tenant_register.business_registration_number
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                "Either domain or business_registration_number "
                "must be provided"
            )
        )

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

    # Check if business_registration_number already exists
    if tenant_register.business_registration_number is not None:
        existing_tenant = db.query(TenantModel).filter(
            TenantModel.business_registration_number
            == tenant_register.business_registration_number
        ).first()
        if existing_tenant:
            raise HTTPException(
                status_code=400,
                detail=(
                    "A tenant with this business registration number "
                    "already exists"
                )
            )

    # Check if owner email already exists
    existing_user = db.query(UserModel).filter(
        func.lower(UserModel.email) == tenant_register.owner.email.lower()
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
        db.flush()

        verification_email = queue_verification_email_with_retry(
            email=db_owner.email,
            token=verification_token,
            full_name=db_owner.full_name
        )

        db.commit()
        db.refresh(db_tenant)
        db.refresh(db_owner)

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
            },
            "verification_email": verification_email
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
    except RuntimeError:
        db.rollback()
        raise HTTPException(
            status_code=503,
            detail=(
                "Unable to complete tenant registration because the "
                "verification email could not be queued. Please try again."
            )
        )


@router.get("/", response_model=PaginatedResponse[Tenant])
def list_tenants(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Get list of tenants.

    Returns paginated response with metadata:
    - items: List of tenants
    - total: Total count of tenants
    - page: Current page number
    - size: Items per page
    - pages: Total number of pages
    - has_next: Whether there is a next page
    - has_previous: Whether there is a previous page
    """
    query = db.query(TenantModel)

    # Get total count
    total = query.count()

    # Get paginated items
    tenants = query.offset(skip).limit(limit).all()

    return create_paginated_response(
        items=tenants,
        total=total,
        skip=skip,
        limit=limit
    )


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
    tenant_update: SuperAdminTenantUpdate,
    request: Request,
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update a tenant.

    Permissions:
    - Super Admins: Can update all fields including plan_type and default_currency
    - Tenant Owners: Can update their own tenant details
      (except plan_type and default_currency)
    """
    tenant = db.query(TenantModel).filter(TenantModel.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    # Verify authentication and permissions
    if not current_user.is_superadmin:
        # Check ownership
        active_owner = db.query(UserModel).filter(
            UserModel.id == current_user.id,
            UserModel.tenant_id == tenant.id,
            UserModel.role == UserRole.OWNER,
            UserModel.is_active.is_(True)
        ).first()
        if not active_owner:
            raise HTTPException(
                status_code=403,
                detail="You don't have permission to update this tenant"
            )

        # Check for restricted fields (plan_type)
        if (
            tenant_update.plan_type is not None
            and tenant_update.plan_type != tenant.plan_type
        ):
            raise HTTPException(
                status_code=403,
                detail="Only super admins can change the plan type"
            )

        # Check for restricted fields (default_currency)
        if (
            tenant_update.default_currency is not None
            and tenant_update.default_currency != tenant.default_currency
        ):
            raise HTTPException(
                status_code=403,
                detail="Only super admins can change the default currency"
            )

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

    # Check for business_registration_number uniqueness if being updated
    if (
        "business_registration_number" in update_data
        and update_data["business_registration_number"] is not None
    ):
        new_brn = update_data["business_registration_number"]
        if new_brn != tenant.business_registration_number:
            existing_tenant = db.query(TenantModel).filter(
                TenantModel.business_registration_number == new_brn,
                TenantModel.id != tenant_id
            ).first()
            if existing_tenant:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "A tenant with this business registration number "
                        "already exists"
                    )
                )

    # Ensure at least one unique identifier remains after the update
    final_domain = update_data.get("domain", tenant.domain)
    final_business_registration_number = update_data.get(
        "business_registration_number",
        tenant.business_registration_number,
    )
    if final_domain is None and final_business_registration_number is None:
        raise HTTPException(
            status_code=400,
            detail=(
                "Tenant must have at least one unique identifier: "
                "domain or business_registration_number"
            ),
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
    request: Request,
    current_user: UserModel = Depends(require_superadmin),
    db: Session = Depends(get_db)
):
    """
    Delete a tenant (soft delete by setting is_active to False).

    Requires SuperAdmin authentication.
    Organization deletion requires contacting the technical team/developer.
    """
    tenant = db.query(TenantModel).filter(TenantModel.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    if not tenant.is_active:
        raise HTTPException(status_code=400, detail="Tenant already inactive")

    tenant.is_active = False
    db.commit()

    # Log tenant deletion
    log_tenant_event(
        db=db,
        request=request,
        action=AuditAction.TENANT_DELETED,
        resource_id=tenant.id,
        tenant_id=tenant.id,
        description=f"Tenant {tenant.name} deactivated by superadmin"
    )

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
