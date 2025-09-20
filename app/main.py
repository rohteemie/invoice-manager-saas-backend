from fastapi import FastAPI

from app.core.config import settings
from app.core.database import engine
from app.models import tenant  # Import models to ensure they're registered
from app.api.v1.api import api_router

# Create database tables
tenant.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.project_name,
    description="A multi-tenant SaaS backend built with FastAPI",
    version="1.0.0",
    openapi_url=f"{settings.api_v1_str}/openapi.json"
)

# Include API router
app.include_router(api_router, prefix=settings.api_v1_str)


@app.get("/")
def root():
    return {
        "message": "Welcome to Multi-Tenant SaaS Backend",
        "version": "1.0.0",
        "docs": "/docs"
    }
