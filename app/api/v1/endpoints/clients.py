"""
Client management endpoints with role-based access control.
Supports CRUD operations with tenant-aware data isolation.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.client import Client as ClientModel
from app.models.user import User as UserModel, UserRole
from app.schemas.client import Client, ClientCreate, ClientUpdate
from app.core.deps import get_current_user, require_role

router = APIRouter()


@router.post("/", response_model=Client, status_code=status.HTTP_201_CREATED)
def create_client(
    client_in: ClientCreate,
    current_user: UserModel = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    """
    Create a new client.

    - Requires Admin or Owner role
    - Enforces tenant isolation (client must belong to user's tenant)
    - Returns the created client
    """
    # Ensure the client is being created for the current user's tenant
    if client_in.tenant_id != current_user.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot create client for another tenant"
        )

    # Check for duplicate email within the same tenant
    if client_in.email:
        existing_client = db.query(ClientModel).filter(
            ClientModel.email == client_in.email,
            ClientModel.tenant_id == current_user.tenant_id,
            ClientModel.is_active == True  # noqa: E712
        ).first()
        if existing_client:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A client with this email already exists in your tenant"
            )

    db_client = ClientModel(**client_in.model_dump())
    db.add(db_client)
    db.commit()
    db.refresh(db_client)
    return db_client


@router.get("/", response_model=List[Client])
def list_clients(
    skip: int = 0,
    limit: int = 100,
    current_user: UserModel = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    """
    List all clients in the current tenant.

    - Requires Admin or Owner role
    - Returns only clients from same tenant (data isolation)
    - Supports pagination
    - Only returns active clients by default
    """
    clients = db.query(ClientModel).filter(
        ClientModel.tenant_id == current_user.tenant_id,
        ClientModel.is_active == True  # noqa: E712
    ).offset(skip).limit(limit).all()
    return clients


@router.get("/{client_id}", response_model=Client)
def get_client(
    client_id: str,
    current_user: UserModel = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    """
    Get a specific client by ID.

    - Requires Admin or Owner role
    - Enforces tenant-based access control
    - Returns 404 if client not found or belongs to another tenant
    """
    client = db.query(ClientModel).filter(
        ClientModel.id == client_id,
        ClientModel.tenant_id == current_user.tenant_id
    ).first()

    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found"
        )
    return client


@router.put("/{client_id}", response_model=Client)
def update_client(
    client_id: str,
    client_update: ClientUpdate,
    current_user: UserModel = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    """
    Update client information.

    - Requires Admin or Owner role
    - Enforces tenant-based access control
    - Partial updates supported
    - Cannot update tenant_id
    """
    client = db.query(ClientModel).filter(
        ClientModel.id == client_id,
        ClientModel.tenant_id == current_user.tenant_id
    ).first()

    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found"
        )

    # Check for duplicate email if email is being updated
    update_data = client_update.model_dump(exclude_unset=True)
    if "email" in update_data and update_data["email"]:
        existing_client = db.query(ClientModel).filter(
            ClientModel.email == update_data["email"],
            ClientModel.tenant_id == current_user.tenant_id,
            ClientModel.id != client_id,
            ClientModel.is_active == True  # noqa: E712
        ).first()
        if existing_client:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A client with this email already exists in your tenant"
            )

    for field, value in update_data.items():
        setattr(client, field, value)

    db.commit()
    db.refresh(client)
    return client


@router.delete("/{client_id}")
def delete_client(
    client_id: str,
    current_user: UserModel = Depends(require_role(UserRole.OWNER)),
    db: Session = Depends(get_db)
):
    """
    Soft delete a client (GDPR-compliant right-to-be-forgotten).

    - Requires Owner role
    - Sets is_active to False instead of hard delete
    - Enforces tenant-based access control
    - Maintains audit trail
    """
    client = db.query(ClientModel).filter(
        ClientModel.id == client_id,
        ClientModel.tenant_id == current_user.tenant_id
    ).first()

    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found"
        )

    client.is_active = False
    db.commit()
    return {"message": "Client deactivated successfully"}
