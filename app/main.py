from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from contextlib import asynccontextmanager
from slowapi.errors import RateLimitExceeded
from sqlalchemy.exc import IntegrityError, OperationalError

from app.core.config import settings
from app.api.v1.api import api_router
from app.db.database import init_db
from app.core.sentry import init_sentry
from app.core.logging import LoggingMiddleware
from app.core.rate_limit import limiter, rate_limit_exceeded_handler
from app.core.rate_limit_middleware import RateLimitHeadersMiddleware
from app.core.metrics import metrics_endpoint
from app.core.exceptions import AppException
from app.core.exception_handlers import (
    app_exception_handler,
    http_exception_handler,
    validation_exception_handler,
    database_exception_handler,
    generic_exception_handler,
)


# OpenAPI tags metadata for better API documentation organization
tags_metadata = [
    {
        "name": "Root",
        "description": "Root and welcome endpoints providing basic API information.",
    },
    {
        "name": "Monitoring",
        "description": "Health check and metrics endpoints for monitoring and observability.",
    },
    {
        "name": "auth",
        "description": "Authentication and authorization endpoints including user registration, login, "
        "email verification, and password reset functionality.",
    },
    {
        "name": "tenants",
        "description": "Tenant (organization) management endpoints. Handles tenant CRUD operations, "
        "tenant registration with owner account, and tenant branding (logo management).",
    },
    {
        "name": "users",
        "description": "User management endpoints for CRUD operations on users within a tenant. "
        "Supports role-based access control and user profile management.",
    },
    {
        "name": "invoices",
        "description": "Invoice management endpoints supporting full CRUD operations, multi-currency invoices, "
        "PDF generation, email sending, status lifecycle management, and data export (CSV/JSON).",
    },
    {
        "name": "analytics",
        "description": "Analytics and reporting endpoints providing invoice summaries and revenue breakdowns "
        "for business intelligence and decision making.",
    },
    {
        "name": "audit-logs",
        "description": "Audit logging endpoints for tracking and querying user actions and system events. "
        "Provides comprehensive audit trails for compliance and security monitoring.",
    },
    {
        "name": "admin",
        "description": "Super Admin endpoints for platform-level administration. Allows cross-tenant operations, "
        "tenant suspension/reactivation, and platform-wide statistics. Restricted to Super Admin role only.",
    },
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    init_db()
    init_sentry()
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="""
    ## Multi-Tenant Invoice Management SaaS Backend

    A production-ready, scalable backend system for managing invoices across multiple tenants with complete data isolation.

    ### 🎯 Core Features

    * **🔐 Authentication & Security**
        - JWT-based authentication with access and refresh tokens
        - Email verification for new user accounts
        - Password reset functionality with secure token-based flow
        - Progressive login delay for brute-force protection (OWASP ASVS compliant)
        - Role-based access control (RBAC) with 5 role levels

    * **👥 Multi-Tenancy**
        - Complete tenant isolation at database level
        - Tenant branding with custom logo upload
        - Tenant suspension and reactivation
        - Soft delete for GDPR compliance

    * **📄 Invoice Management**
        - Full CRUD operations with draft, sent, paid, and overdue statuses
        - Multi-currency support (USD, EUR, GBP, NGN)
        - Configurable tax rates per tenant
        - PDF generation for invoices
        - Email sending for invoices
        - Branch and customer metadata tracking
        - CSV and JSON export capabilities

    * **📊 Analytics & Reporting**
        - Invoice summary statistics
        - Revenue breakdown by status
        - Tenant-scoped analytics

    * **🛡️ Platform Administration**
        - Super Admin role for platform-level management
        - Cross-tenant user and audit log visibility
        - Platform statistics and health monitoring

    * **📝 Audit Logging**
        - Comprehensive audit trail for all critical operations
        - User action tracking
        - Resource-specific audit log queries

    * **⚡ Performance & Reliability**
        - Redis caching for frequently accessed data
        - Background task processing with Celery
        - Tiered rate limiting by user role
        - Structured logging with Sentry integration
        - Health checks and Prometheus metrics
        - CI/CD with GitHub Actions

    ### 👤 User Roles

    - **Super Admin**: Platform-level access across all tenants
    - **Owner**: Full tenant management and user administration
    - **Admin**: User management and business operations
    - **Manager**: Invoice and inventory management
    - **Attendant**: Basic invoice creation and viewing

    ### 📚 Documentation

    For detailed documentation, visit:
    - **Interactive API Docs**: `/docs` (Swagger UI)
    - **Alternative Docs**: `/redoc` (ReDoc)
    - **GitHub Repository**: https://github.com/rohteemie/invoice-manager-saas-backend

    ### 🔗 API Endpoints Summary

    - **Authentication** (7): Registration, login, email verification, password reset
    - **Tenant Management** (9): CRUD operations, logo upload, tenant registration
    - **User Management** (5): User CRUD and profile management
    - **Invoice Management** (9): CRUD, PDF generation, email sending, exports
    - **Analytics** (2): Invoice summaries and revenue reports
    - **Audit Logs** (4): Comprehensive activity tracking and querying
    - **Super Admin** (7): Platform administration and cross-tenant operations
    - **Monitoring** (3): Health checks, metrics, root endpoint

    **Total Endpoints**: 46 (3 root/monitoring + 43 business API endpoints)

    ### 📖 API Version

    Current: **v1.0.0**

    ### 🔒 Security Notes

    All endpoints except public registration and login require JWT authentication via the `Authorization: Bearer <token>` header.
    Rate limiting is applied based on user role and endpoint type.
    """,
    version="1.0.0",
    contact={
        "name": "Rotimi Owolabi",
        "url": "https://github.com/rohteemie/invoice-manager-saas-backend",
        "email": "rotimijournal@outlook.com",
    },
    license_info={"name": "MIT License", "url": "https://opensource.org/licenses/MIT"},
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    openapi_tags=tags_metadata,
    redoc_url="/redoc",
    docs_url="/docs",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS or {"*"},
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add middleware
app.add_middleware(LoggingMiddleware)
app.add_middleware(RateLimitHeadersMiddleware)

# Add rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

# Add custom exception handlers for standardized error responses
app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(IntegrityError, database_exception_handler)
app.add_exception_handler(OperationalError, database_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# Routers
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get(
    "/",
    summary="API Root",
    description="Welcome endpoint providing basic API information and links to documentation.",
    tags=["Root"],
    response_description="API welcome message with version and documentation links",
)
def root():
    """
    Root endpoint of the Multi-Tenant SaaS Backend API.

    Returns basic API information including:
    - Welcome message
    - API version
    - Link to interactive documentation

    This endpoint is publicly accessible and requires no authentication.
    """
    return {
        "message": "Welcome to Multi-Tenant SaaS Backend",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc",
        "api_base": "/api/v1",
    }


@app.get(
    "/health",
    summary="Health Check",
    description="Health check endpoint for monitoring systems, load balancers, and orchestrators.",
    tags=["Monitoring"],
    response_description="Health status of the application",
)
def health_check():
    """
    Health check endpoint for monitoring and load balancers.

    Returns the current health status of the application including:
    - Health status (healthy/unhealthy)
    - Application version
    - Current environment (development/staging/production)

    This endpoint is publicly accessible and requires no authentication.
    Used by:
    - Kubernetes liveness/readiness probes
    - Load balancers for health checks
    - Monitoring systems (e.g., Prometheus, Datadog)
    """
    return {
        "status": "healthy",
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT,
    }


@app.get(
    "/metrics",
    summary="Prometheus Metrics",
    description="Prometheus-compatible metrics endpoint for performance monitoring and alerting.",
    tags=["Monitoring"],
    response_description="Application metrics in Prometheus text format",
)
def metrics():
    """
    Prometheus metrics endpoint for observability.

    Provides application performance metrics including:
    - Request counts and latencies
    - Error rates
    - Active connections
    - Custom business metrics

    This endpoint is publicly accessible but should be restricted to monitoring systems in production.
    Metrics are formatted in Prometheus text exposition format.

    Typically scraped by:
    - Prometheus server
    - Grafana Cloud
    - Other monitoring systems supporting Prometheus format
    """
    return metrics_endpoint()
