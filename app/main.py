from fastapi import FastAPI

from app.core.config import settings
from app.api.v1.api import api_router


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="A multi-tenant SaaS backend built with FastAPI",
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/")
def root():
    return {
        "message": "Welcome to Multi-Tenant SaaS Backend",
        "version": "1.0.0",
        "docs": "/docs"
    }
