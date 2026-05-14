# Rechive - A FastAPI Multi-Tenant Invoicing SaaS Backend

[![CI/CD Pipeline](https://github.com/rohteemie/multi-tenant-saas-backend/workflows/Backend%20CI%2FCD%20Pipeline/badge.svg)](https://github.com/rohteemie/multi-tenant-saas-backend/actions)
[![Tests](https://img.shields.io/badge/tests-144%20passed-brightgreen)](tests/)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-009688.svg)](https://fastapi.tiangolo.com)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

A portfolio project showcasing the design and implementation of a **multi-tenant SaaS backend** for **invoice management**.
Built with **FastAPI + SQLAlchemy** and **PostgreSQL**, containerized with **Docker**.

---

## Project Goals

- Demonstrate backend engineering skills in designing and implementing a SaaS application
- Provide multi-tenancy support so organizations can securely manage their own invoices
- Support role-based access control (RBAC) with roles: Owner, Admin, Manager, Attendant
- Enable organizations to create and manage invoices with customer details and creator tracking
- Showcase professional documentation, diagrams, testing, and CI/CD practices

---

## Tech Stack

- **Backend:** FastAPI, SQLAlchemy
- **Database:** PostgreSQL (SQLite for local development)
- **Cache / Queue:** Redis, Celery
- **Containerization:** Docker, Docker Compose
- **Testing:** Pytest
- **CI/CD:** GitHub Actions
- **Authentication:** JWT, OAuth2PasswordBearer
- **Monitoring:** Sentry, Prometheus
- **Rate Limiting:** SlowAPI with Redis
- **Database Migrations:** Alembic

---

## Features

**Core Functionality**
- Tenant registration and management
- User registration with JWT authentication
- Role-based access control (Owner, Admin, Manager, Attendant)
- Owner-controlled user creation with no public registration
- Multi-owner (co-owner) support
- Forced password change on first login
- Super Admin role for platform management

**Invoice Management**
- Invoice CRUD operations (tenant-aware)
- Invoice lifecycle management (Draft, Sent, Paid, Overdue)
- Invoice metadata: creator and customer information
- On-demand PDF generation
- Invoice delivery via email
- Multi-currency support (USD, EUR, GBP, NGN)
- Configurable tax rates per tenant
- CSV and JSON export functionality

**User & Security**
- Email verification required before protected account access
- Password reset functionality
- Tenant branding with logo upload
- Comprehensive audit logging
- Multi-tenant data isolation

**Infrastructure**
- Integration test suite
- Analytics and reporting endpoints
- Redis caching for performance optimization
- Background workers for automated tasks
- CI/CD pipeline with GitHub Actions
- Structured logging and monitoring
- Rate limiting and request throttling
- Health checks and metrics endpoints

---

## Project Roadmap

This project follows a phased, sprint-based development approach:

**Phase 0** — Planning & Documentation (Complete)
- System architecture and ERD design
- Use case and sequence diagrams
- Product and system requirements documentation

**Phase 1** — Authentication & Tenant Isolation (Complete)
- Tenant model implementation
- JWT authentication system
- Role-based access control (RBAC)

**Phase 2** — Invoice Management Module (Complete)
- Invoice data model and schema
- CRUD operations and lifecycle management
- CSV and JSON export endpoints
- Comprehensive test coverage

**Phase 3** — Analytics, Caching & Background Tasks (Complete)
- Invoice analytics and reporting APIs
- Redis-based performance caching
- Celery background worker integration
- Performance benchmarking

**Phase 4** — Reliability & Scalability (Complete)
- CI/CD pipeline automation with GitHub Actions
- Structured logging and monitoring (Sentry, Prometheus)
- Rate limiting and request throttling
- Health checks and Prometheus metrics

**Phase 5** — Production Showcase (In Progress)
- Deployment guides and documentation
- Demo video and case studies
- Production-ready configuration

**Current Status:** Phase 4 Complete (v0.4.0)
**Next:** Phase 5 - Production Showcase & Deployment

---

## Architecture Overview

### System Architecture

```bash
┌─────────────────────────────────────────────────────────────┐
│                        Client Layer                         │
│                  (Web/Mobile Applications)                  │
└───────────────────────────┬─────────────────────────────────┘
                            │ HTTPS
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                      API Gateway (FastAPI)                  │
│  - Authentication (JWT)                                     │
│  - Request Validation (Pydantic)                            │
│  - Rate Limiting ✅ **Sprint 4**                            │
│  - Logging & Monitoring ✅ **Sprint 4**                     │
└───────────────────────────┬─────────────────────────────────┘
                            │
            ┌───────────────┼───────────────┐
            │               │               │
            ▼               ▼               ▼
    ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
    │   Tenant     │ │     User     │ │   Invoice    │
    │  Management  │ │  Management  │ │  Management  │
    │              │ │   (+ RBAC)   │ │      ✅      │
    └──────┬───────┘ └──────┬───────┘ └──────┬───────┘
           │                │                │
           └────────────────┼────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    Database Layer                           │
│  - PostgreSQL (Production) / SQLite (Development)           │
│  - Row-level tenant isolation (tenant_id)                   │
│  - SQLAlchemy ORM                                           │
└─────────────────────────────────────────────────────────────┘
```

### Multi-Tenant Data Isolation

```bash
┌──────────────────────────────────────────────────────────┐
│                     Tenant A                             │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐          │
│  │   Users    │  │  Invoices  │  │  Branches  │          │
│  │ (filtered) │  │ (filtered) │  │ (filtered) │          │
│  └────────────┘  └────────────┘  └────────────┘          │
└──────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│                     Tenant B                             │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐          │
│  │   Users    │  │  Invoices  │  │  Analytics │          │
│  │ (filtered) │  │ (filtered) │  │ (filtered) │          │
│  └────────────┘  └────────────┘  └────────────┘          │
└──────────────────────────────────────────────────────────┘

All queries automatically filtered by tenant_id
```

### Role-Based Access Control

```bash
┌─────────────────────────────────────┐
│            OWNER                    │
│  - Full tenant management           │
│  - Create users (any role incl.     │
│    other owners = co-owners)        │
│  - Delete users (except owners)     │
│  - All admin privileges             │
└─────────────┬───────────────────────┘
              │
┌─────────────▼───────────────────────┐
│            ADMIN                    │
│  - Manage users                     │
│  - Full business operations         │
│  - All manager privileges           │
└─────────────┬───────────────────────┘
              │
┌─────────────▼───────────────────────┐
│           MANAGER                   │
│  - Manage invoices & inventory      │
│  - View reports                     │
│  - All attendant privileges         │
└─────────────┬───────────────────────┘
              │
┌─────────────▼───────────────────────┐
│          ATTENDANT                  │
│  - Create invoices                  │
│  - View inventory                   │
│  - Basic operations only            │
└─────────────────────────────────────┘
```

---

## Project Structure

```bash
multi-tenant-saas-backend/
├── app/
│   ├── api/v1/          # API endpoints (auth, users, tenants)
│   ├── core/            # Config, security, dependencies
│   ├── db/              # Database configuration
│   ├── models/          # SQLAlchemy ORM models
│   ├── schemas/         # Pydantic validation schemas
│   └── main.py          # FastAPI application entry point
├── docs/                # Documentation and diagrams
│   ├── API_STRUCTURE.md
│   ├── authentication.md
│   ├── erd_diagram.png
│   └── ...
├── tests/               # Pytest test suite
│   ├── test_auth.py
│   ├── test_users.py
│   └── ...
├── .env.example         # Environment variables template
├── requirements.txt     # Python dependencies
└── README.md           # This file
```

**Detailed Documentation:**

- [Application Structure](app/README.md) - Application architecture and components
- [API Documentation](app/api/README.md) - API layer overview
- [Models Documentation](app/models/README.md) - Database models
- [Core Utilities](app/core/README.md) - Security and configuration
- [Testing Guide](tests/README.md) - Test suite documentation
- [Full Documentation Index](docs/README.md) - Complete documentation index

---

## Installation & Setup

### Live Demo

Experience the application without local setup:

**[Live Demo](https://multi-tenant-saas-backend.onrender.com)**

- **Interactive API Documentation (Swagger):** [/docs](https://multi-tenant-saas-backend.onrender.com/docs)
- **Alternative Documentation (ReDoc):** [/redoc](https://multi-tenant-saas-backend.onrender.com/redoc)
- **API Base URL:** [/api/v1](https://multi-tenant-saas-backend.onrender.com/api/v1)

### Prerequisites

- Python 3.8+
- PostgreSQL (for production) or SQLite (for development)
- pip or poetry for dependency management

### Quick Start

- **Clone the repository:**

```bash
git clone https://github.com/rohteemie/multi-tenant-saas-backend.git
cd multi-tenant-saas-backend
```

- **Create and activate a virtual environment:**

```bash
# Create virtual environment
python -m venv venv

# Activate (Linux/Mac)
source venv/bin/activate

# Activate (Windows)
venv\Scripts\activate
```

- **Install dependencies:**

```bash
pip install -r requirements.txt
```

- **Set up environment variables:**

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your configuration
# Minimum required:
# - SECRET_KEY (generate with: python -c "import secrets; print(secrets.token_urlsafe(32))")
# - DATABASE_URL (default: sqlite:///./app.db)
```

-**Run the application:**

```bash
uvicorn app.main:app --reload
```

- **Access the API:**

- Swagger UI: <http://localhost:8000/docs>
- ReDoc: <http://localhost:8000/redoc>
- API Base: <http://localhost:8000/api/v1>

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html

# Run specific test file
pytest tests/test_auth.py -v
```

---

## API Reference

The application provides 50 total endpoints: 3 root/monitoring endpoints plus 47 business API endpoints under `/api/v1`.

**Authentication:**

- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login and get JWT tokens
- `POST /api/v1/auth/refresh` - Refresh access token
- `POST /api/v1/auth/verify-email` - Verify email address
- `POST /api/v1/auth/resend-verification-email` - Resend verification email
- `POST /api/v1/auth/forgot-password` - Request password reset
- `POST /api/v1/auth/reset-password` - Reset password with token

**Tenant Management:**

- `POST /api/v1/tenants` - Create new tenant
- `POST /api/v1/tenants/register` - Register tenant with owner
- `GET /api/v1/tenants` - List all tenants
- `GET /api/v1/tenants/{id}` - Get tenant by ID
- `PUT /api/v1/tenants/{id}` - Update tenant
- `DELETE /api/v1/tenants/{id}` - Soft delete tenant
- `POST /api/v1/tenants/{id}/logo` - Upload tenant logo
- `GET /api/v1/tenants/{id}/logo` - Get tenant logo
- `DELETE /api/v1/tenants/{id}/logo` - Delete tenant logo

**User Management:**

- `GET /api/v1/users/me` - Get current user
- `GET /api/v1/users` - List users (Admin+)
- `GET /api/v1/users/{id}` - Get user by ID (Admin+)
- `PUT /api/v1/users/{id}` - Update user (Admin+)
- `DELETE /api/v1/users/{id}` - Delete user (Owner only)

**Invoice Management**

- `POST /api/v1/invoices/` - Create new invoice
- `GET /api/v1/invoices/` - List invoices with filters
- `GET /api/v1/invoices/{id}` - Get invoice by ID
- `PUT /api/v1/invoices/{id}` - Update draft invoice (Manager+)
- `PATCH /api/v1/invoices/{id}/status` - Update invoice status (Manager+)
- `DELETE /api/v1/invoices/{id}` - Delete draft invoice (Admin+)
- `GET /api/v1/invoices/{id}/pdf` - Download invoice as PDF
- `POST /api/v1/invoices/{id}/send` - Send invoice via email
- `GET /api/v1/invoices/export/invoices` - Export invoices (CSV/JSON)

**Analytics & Reporting**

- `GET /api/v1/analytics/invoice-summary` - Invoice summary statistics
- `GET /api/v1/analytics/revenue-by-status` - Revenue breakdown by status

**Audit Logs**

- `GET /api/v1/audit-logs/` - List audit logs (Admin+)
- `GET /api/v1/audit-logs/{id}` - Get specific audit log
- `GET /api/v1/audit-logs/user/{id}` - Get user's audit logs
- `GET /api/v1/audit-logs/resource/{type}/{id}` - Get resource audit logs

**Super Admin (Platform Management)**

- `GET /api/v1/admin/tenants` - List all tenants (Super Admin only)
- `GET /api/v1/admin/tenants/{id}` - Get tenant details (Super Admin only)
- `PUT /api/v1/admin/tenants/{id}/suspend` - Suspend tenant (Super Admin only)
- `PUT /api/v1/admin/tenants/{id}/reactivate` - Reactivate tenant (Super Admin only)
- `GET /api/v1/admin/users` - List all users across tenants (Super Admin only)
- `GET /api/v1/admin/audit-logs` - Platform-wide audit logs (Super Admin only)
- `GET /api/v1/admin/stats` - Platform statistics (Super Admin only)

**Monitoring & Health:**

- `GET /` - API root and welcome endpoint
- `GET /health` - Health check endpoint
- `GET /metrics` - Prometheus metrics endpoint

**Documentation:**

- `GET /docs` - Swagger UI (interactive API documentation)
- `GET /redoc` - ReDoc (alternative API documentation)

**Complete Documentation**

- [API Structure](docs/API_STRUCTURE.md) - Complete API endpoint reference
- [Authentication](docs/features/AUTHENTICATION.md) - Authentication and authorization implementation
- [Email Verification](docs/features/EMAIL_VERIFICATION.md) - Email verification system
- [Password Reset](docs/features/PASSWORD_RESET.md) - Password reset workflow
- [Audit Logging](docs/features/AUDIT_LOGGING.md) - Comprehensive audit logging system
- [Super Admin](docs/features/SUPER_ADMIN.md) - Platform administration features
- [Tenant Branding](docs/features/BRANDING.md) - Tenant logo and branding management
- [User Management](docs/features/USER_ACCOUNT_MANAGEMENT.md) - User account lifecycle
- [Invoicing](docs/features/INVOICING.md) - Invoice management with PDF generation and multi-currency
- [Security & Compliance](docs/SECURITY.md) - Security practices and GDPR compliance
- [CI/CD Pipeline](docs/guides/CI_CD_PIPELINE.md) - Automated deployment workflow
- [Monitoring](docs/guides/MONITORING.md) - Logging and observability setup
- [Rate Limiting](docs/features/RATE_LIMITING.md) - API rate limiting configuration
- [Documentation Index](docs/README.md) - Complete documentation guide

### Example Usage

**Register a new user:**

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@acme.com",
    "full_name": "Admin User",
    "password": "SecurePass123",
    "role": "admin",
    "tenant_id": "tenant-uuid"
  }'
```

**Login:**

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@acme.com&password=SecurePass123"
```

**Access protected endpoint:**

```bash
curl -X GET http://localhost:8000/api/v1/users/me \
  -H "Authorization: Bearer {access_token}"
```

---

## Documentation

### Technical Documentation

- [System Requirements Document (SRD)](docs/specifications/SYSTEM_REQUIREMENTS.md) - Technical specifications
- [Product Requirements Document (PRD)](docs/specifications/PRODUCT_REQUIREMENT.md) - Business requirements
- [Release History](CHANGELOG.md) - Version history with features and changes (v1.0–v1.4)
- [GitHub Releases](https://github.com/rohteemie/multi-tenant-saas-backend/releases) - Published release notes and milestones

### Diagrams

- [Architecture Diagram](docs/system_architecture.png) - System architecture overview
- [ERD Diagram](docs/erd_diagram.png) - Database entity relationships
- [Use Case Diagram](docs/use_case_diagram.png) - User role interactions
- [API Sequence Diagram](docs/api_sequence_diagram.png) - Request flow
- [Roadmap Timeline](docs/roadmap_timeline.png) - Project timeline

### Code Documentation

- [Full Documentation Index](docs/README.md) - Complete documentation guide
- Interactive API Docs - <http://localhost:8000/docs>

---

## Testing

The project includes comprehensive test coverage:

- **28 test files** covering all core functionality

**Test Suites**

- `test_auth.py` - Authentication endpoints
- `test_auth_throttle.py` - Authentication throttling
- `test_login_throttle.py` - Login delay and brute-force protection
- `test_users.py` - User management
- `test_tenants.py` - Tenant CRUD operations
- `test_tenant_isolation.py` - Multi-tenant data isolation
- `test_tenant_logo.py` - Tenant branding and logo upload
- `test_invoices.py` - Invoice management
- `test_invoice_pdf.py` - PDF generation
- `test_invoice_number_config.py` - Invoice number configuration
- `test_multi_currency_tax.py` - Multi-currency and tax functionality
- `test_currency_consistency.py` - Currency consistency
- `test_payment_method_and_currency.py` - Payment methods
- `test_integration.py` - End-to-end integration workflows
- `test_analytics.py` - Analytics endpoints
- `test_performance.py` - Performance benchmarks
- `test_background_tasks.py` - Celery background tasks
- `test_monitoring.py` - Health checks and metrics
- `test_rate_limiting.py` - API rate limiting
- `test_audit_logs.py` - Audit logging
- `test_superadmin.py` - Super Admin features
- `test_email_verification.py` - Email verification flow
- `test_email_verification_enforcement.py` - Email verification enforcement
- `test_password_reset.py` - Password reset functionality
- `test_permission_checks.py` - Permission validation
- `test_pdf_generator.py` - PDF generation service
- `test_cors.py` - CORS configuration
- `test_error_standardization.py` - Error response format

**Test Coverage**

- User registration and authentication
- Email verification flow
- Password reset functionality
- JWT token generation and validation
- Role-based access control (RBAC)
- Tenant isolation and security
- Tenant branding and logo management
- CRUD operations for all entities
- Soft deletion for GDPR compliance
- Invoice lifecycle management
- Multi-currency support and conversions
- Tax calculations per tenant
- PDF generation and rendering
- CSV and JSON export functionality
- End-to-end integration workflows
- Analytics and reporting
- Background task execution
- Monitoring and health checks
- Rate limiting and throttling
- Audit logging for all operations
- Super Admin platform operations

See [Testing Documentation](tests/README.md) for details.

---

## Next Steps

**Phase 4 Completed**

- Invoice CRUD and lifecycle management
- Invoice metadata (customer, creator)
- Multi-currency support (USD, EUR, GBP, NGN)
- Configurable tax rates per tenant
- Invoice PDF generation and email delivery
- Email verification system
- Password reset functionality
- Tenant branding with logo upload
- Analytics and reporting endpoints
- CSV and JSON export functionality
- Redis caching for performance optimization
- Celery background workers for scheduled tasks
- GitHub Actions CI/CD pipeline
- Monitoring with Sentry and Prometheus
- Rate limiting and API throttling
- Comprehensive audit logging
- Super Admin role and platform management

**Phase 5 (In Progress)**

- Finalize production deployment documentation
- Create demo video and case study
- Complete documentation review
- Implement database migrations for production environments

---

## Contributing

Contributions are welcome. To contribute:

1. Fork the repository
2. Create a feature branch
3. Make your changes and add tests
4. Update documentation as needed
5. Submit a pull request

---

## License

MIT License - See [LICENSE](LICENSE) for details

---

## About

**Author:** Rotimi Owolabi

- GitHub: [rohteemie](https://github.com/rohteemie)
- LinkedIn: [Rotimi Owolabi](https://www.linkedin.com/in/rotimijournal/)
- Twitter: [@rohteemie](https://twitter.com/rohteemie)
