from fastapi import APIRouter

from app.api.v1.endpoints import (
    tenants, auth, users, invoices, analytics, audit_logs
)

api_router = APIRouter()
api_router.include_router(tenants.router, prefix="/tenants", tags=["tenants"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(invoices.router, prefix="/invoices",
                          tags=["invoices"])
api_router.include_router(analytics.router, prefix="/analytics",
                          tags=["analytics"])
api_router.include_router(audit_logs.router, prefix="/audit-logs",
                          tags=["audit-logs"])
