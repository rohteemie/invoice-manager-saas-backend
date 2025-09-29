from fastapi import APIRouter

from app.api.v1.endpoints import tenants

api_router = APIRouter()
api_router.include_router(tenants.router, prefix="/tenants", tags=["tenants"])
