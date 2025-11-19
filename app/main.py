from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from slowapi.errors import RateLimitExceeded

from app.core.config import settings
from app.api.v1.api import api_router
from app.db.database import init_db
from app.core.sentry import init_sentry
from app.core.logging import LoggingMiddleware
from app.core.rate_limit import limiter, rate_limit_exceeded_handler
from app.core.metrics import metrics_endpoint


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

    A production-ready, scalable backend system for managing invoices across
    multiple tenants with complete isolation.

    ### Features

    * **🔐 Authentication**: JWT-based auth with refresh tokens
    * **👥 Multi-Tenancy**: Complete tenant isolation at database level
    * **📄 Invoice Management**: Full CRUD with status lifecycle
    * **📊 Analytics**: Real-time invoice and revenue analytics
    * **⚡ Performance**: Redis caching for optimal response times
    * **🔒 Security**: Role-based access control (RBAC)
    * **📈 Scalability**: Background tasks with Celery

    ### API Versions

    Current: **v1.0.0**
    """,
    version="1.0.0",
    contact={
        "name": "Rotimi Owolabi",
        "url": "https://github.com/rohteemie/multi-tenant-saas-backend",
        "email": "rotimijournal@outlook.com"
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT"
    },
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    redoc_url="/redoc",
    docs_url="/docs",
    lifespan=lifespan
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

# Add rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

# Routers
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/")
def root():
    return {
        "message": "Welcome to Multi-Tenant SaaS Backend",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
def health_check():
    """Health check endpoint for monitoring and load balancers."""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT
    }


@app.get("/metrics")
def metrics():
    """Prometheus metrics endpoint."""
    return metrics_endpoint()
