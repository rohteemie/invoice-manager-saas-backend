# FastAPI Multi-Tenant Invoicing SaaS Backend

[![CI/CD Pipeline](https://github.com/rohteemie/multi-tenant-saas-backend/workflows/Backend%20CI%2FCD%20Pipeline/badge.svg)](https://github.com/rohteemie/multi-tenant-saas-backend/actions)
[![Tests](https://img.shields.io/badge/tests-144%20passed-brightgreen)](tests/)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-009688.svg)](https://fastapi.tiangolo.com)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

A portfolio project showcasing the design and implementation of a **multi-tenant SaaS backend** for **invoice management**.
Built with **FastAPI + SQLAlchemy** and **PostgreSQL**, containerized with **Docker**.

---

## 🚀 Project Goals

- Demonstrate backend engineering skills in designing and implementing a SaaS application.
- Provide **multi-tenancy support** so organizations (e.g., Coca-Cola, Facebook, McDonalds) can securely manage their own invoices.
- Support **role-based access control (RBAC)** with roles (Owner, Admin, Manager, Attendant).
- Allow organizations to create and manage invoices across **branches/locations**, with embedded **customer details**.
- Showcase **documentation, diagrams, testing, and CI/CD practices** for professional presentation.

---

## 📂 Tech Stack

- **Backend:** FastAPI, SQLAlchemy
- **Database:** PostgreSQL (SQLite for local dev)
- **Cache / Queue:** Redis ✅, Celery ✅
- **Containerization:** Docker, Docker Compose
- **Testing:** Pytest
- **CI/CD:** GitHub Actions ✅ **Sprint 4**
- **Auth:** JWT Authentication, OAuth2PasswordBearer
- **Monitoring:** Sentry ✅, Prometheus ✅ **Sprint 4**
- **Rate Limiting:** SlowAPI + Redis ✅ **Sprint 4**
- **Migrations:** Alembic

---

## 🏗️ Features (Planned & Implemented)

- [x] Tenant registration & management ✅
- [x] User registration & JWT authentication ✅
- [x] Role-based access (Owner, Admin, Manager, Attendant) ✅
- [x] **Super Admin role for platform management** ✅ **NEW**
- [x] Invoice CRUD (tenant-aware) ✅ **Sprint 2**
- [x] Invoice lifecycle (Draft → Sent → Paid → Overdue) ✅ **Sprint 2**
- [x] Invoice metadata: branch, creator, customer info ✅ **Sprint 2**
- [x] Invoice PDF generation (on-demand) ✅ **NEW**
- [x] Invoice email sending ✅ **NEW**
- [x] Multi-currency support (USD, EUR, GBP, NGN) ✅ **NEW**
- [x] Configurable tax rates per tenant ✅ **NEW**
- [x] CSV/JSON exports ✅ **Sprint 2**
- [x] Email verification for new users ✅ **NEW**
- [x] Password reset functionality ✅ **NEW**
- [x] Tenant branding with logo upload ✅ **NEW**
- [x] Integration tests ✅ **Sprint 2**
- [x] Analytics & reporting endpoints ✅ **Sprint 3**
- [x] Caching with Redis for performance ✅ **Sprint 3**
- [x] Background workers for automated tasks ✅ **Sprint 3**
- [x] CI/CD pipeline with GitHub Actions ✅ **Sprint 4**
- [x] Structured logging & monitoring ✅ **Sprint 4**
- [x] Rate limiting & request throttling ✅ **Sprint 4**
- [x] Health checks & metrics endpoints ✅ **Sprint 4**
- [x] Comprehensive audit logging ✅ **Sprint 4**

---

## 📅 Roadmap

This project follows a **phased + sprint-based roadmap**:

1. **Phase 0**: Planning & Documentation ✅
   - ERD, Use Case, Architecture diagrams
   - System & Product Requirements Docs

2. **Phase 1**: Authentication & Tenant Isolation ✅
   - Tenant model, JWT auth, RBAC

3. **Phase 2**: Core Business Module (Invoices) ✅ **COMPLETED**
   - Invoice schema (branch, customer, creator)
   - Invoice CRUD & lifecycle
   - Export endpoints (CSV/JSON)
   - **Integration tests** ✅

4. **Phase 3**: Analytics & Reporting ✅ **COMPLETED**
   - Invoice analytics APIs
   - Redis caching for performance
   - Background workers (Celery) for scheduled tasks
   - Performance benchmarks

5. **Phase 4**: Reliability & Scalability ✅ **COMPLETED**
   - CI/CD pipelines with GitHub Actions
   - Structured logging & monitoring (Sentry, Prometheus)
   - Rate limiting & request throttling
   - Health checks & metrics

6. **Phase 5**: Final Showcase (Polish & Deployment)
   - Demo video, blog post, deployment guides

**Current Status:** ✅ Phase 4 Complete (Tag: `v0.4.0-sprint-4`)
**Next:** Phase 5 - Final Showcase & Deployment

---

## 📐 Architecture Overview

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
│  │   Users    │  │  Invoices  │  │  Branches  │          │
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
│  - Delete users                     │
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

## 📁 Project Structure

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

## 🔧 Setup Instructions

### 🌐 Live Testing

**Don't want to set up locally?** Try the live application:

🔗 **[Live Demo: http://3.86.89.25:8000/](http://3.86.89.25:8000/)**

- **ReDoc (Documentation):** [http://3.86.89.25:8000/redoc](http://3.86.89.25:8000/redoc)
- **Swagger UI (Interactive):** [http://3.86.89.25:8000/docs](http://3.86.89.25:8000/docs)
- **API Base URL:** [http://3.86.89.25:8000/api/v1](http://3.86.89.25:8000/api/v1)

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

- **Swagger UI (Interactive):** <http://localhost:8000/docs>
- **ReDoc (Documentation):** <http://localhost:8000/redoc>
- **API Base URL:** <http://localhost:8000/api/v1>

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

## 📖 API Documentation

### Quick API Reference

**Note:** The application has 47 total endpoints: 4 root/monitoring endpoints + 43 business API endpoints under `/api/v1`.

**Authentication:**

- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login and get JWT tokens
- `POST /api/v1/auth/refresh` - Refresh access token
- `POST /api/v1/auth/verify-email` - Verify email address ✨ **NEW**
- `POST /api/v1/auth/resend-verification-email` - Resend verification email ✨ **NEW**
- `POST /api/v1/auth/forgot-password` - Request password reset ✨ **NEW**
- `POST /api/v1/auth/reset-password` - Reset password with token ✨ **NEW**

**Tenant Management:**

- `POST /api/v1/tenants` - Create new tenant
- `POST /api/v1/tenants/register` - Register tenant with owner
- `GET /api/v1/tenants` - List all tenants
- `GET /api/v1/tenants/{id}` - Get tenant by ID
- `PUT /api/v1/tenants/{id}` - Update tenant
- `DELETE /api/v1/tenants/{id}` - Soft delete tenant
- `POST /api/v1/tenants/{id}/logo` - Upload tenant logo ✨ **NEW**
- `GET /api/v1/tenants/{id}/logo` - Get tenant logo ✨ **NEW**
- `DELETE /api/v1/tenants/{id}/logo` - Delete tenant logo ✨ **NEW**

**User Management:**

- `GET /api/v1/users/me` - Get current user
- `GET /api/v1/users` - List users (Admin+)
- `GET /api/v1/users/{id}` - Get user by ID (Admin+)
- `PUT /api/v1/users/{id}` - Update user (Admin+)
- `DELETE /api/v1/users/{id}` - Delete user (Owner only)

**Invoice Management:** ✨ **Sprint 2**

- `POST /api/v1/invoices/` - Create new invoice
- `GET /api/v1/invoices/` - List invoices with filters
- `GET /api/v1/invoices/{id}` - Get invoice by ID
- `PUT /api/v1/invoices/{id}` - Update draft invoice (Manager+)
- `PATCH /api/v1/invoices/{id}/status` - Update invoice status (Manager+)
- `DELETE /api/v1/invoices/{id}` - Delete draft invoice (Admin+)
- `GET /api/v1/invoices/{id}/pdf` - Download invoice as PDF ✨ **NEW**
- `POST /api/v1/invoices/{id}/send` - Send invoice via email ✨ **NEW**
- `GET /api/v1/invoices/export/invoices` - Export invoices (CSV/JSON)

**Analytics & Reporting:** ✨ **Sprint 3**

- `GET /api/v1/analytics/invoice-summary` - Invoice summary statistics
- `GET /api/v1/analytics/revenue-by-status` - Revenue breakdown by status

**Audit Logs:** ✨ **Sprint 4**

- `GET /api/v1/audit-logs/` - List audit logs (Admin+) ✨ **NEW**
- `GET /api/v1/audit-logs/{id}` - Get specific audit log ✨ **NEW**
- `GET /api/v1/audit-logs/user/{id}` - Get user's audit logs ✨ **NEW**
- `GET /api/v1/audit-logs/resource/{type}/{id}` - Get resource audit logs ✨ **NEW**

**Super Admin (Platform Management):** ✨ **NEW**

- `GET /api/v1/admin/tenants` - List all tenants (Super Admin only)
- `GET /api/v1/admin/tenants/{id}` - Get tenant details (Super Admin only)
- `PUT /api/v1/admin/tenants/{id}/suspend` - Suspend tenant (Super Admin only)
- `PUT /api/v1/admin/tenants/{id}/reactivate` - Reactivate tenant (Super Admin only)
- `GET /api/v1/admin/users` - List all users across tenants (Super Admin only)
- `GET /api/v1/admin/audit-logs` - Platform-wide audit logs (Super Admin only)
- `GET /api/v1/admin/stats` - Platform statistics (Super Admin only)

**Monitoring & Health:** ✨ **Sprint 4**

- `GET /health` - Health check endpoint
- `GET /metrics` - Prometheus metrics endpoint
- `GET /docs` - Swagger UI documentation
- `GET /redoc` - ReDoc documentation

**Comprehensive Documentation:**

- [API Structure Overview](docs/API_STRUCTURE.md) - Complete API documentation
- [Authentication Guide](docs/authentication.md) - Auth implementation details
- [Email Verification](docs/EMAIL_VERIFICATION.md) - Email verification feature ✨ **NEW**
- [Password Reset](docs/PASSWORD_RESET.md) - Password reset functionality ✨ **NEW**
- [Audit Logging](docs/AUDIT_LOGGING.md) - Comprehensive audit logging ✨ **NEW**
- [Super Admin Guide](docs/SUPER_ADMIN.md) - Platform management features ✨ **NEW**
- [Tenant Branding](docs/branding.md) - Logo upload and branding ✨ **NEW**
- [User Account Management](docs/USER_ACCOUNT_MANAGEMENT.md) - User management guide
- [PDF Generation Guide](docs/PDF_GENERATION.md) - Invoice PDF generation
- [Invoice Implementation](docs/INVOICE_IMPLEMENTATION.md) - Multi-currency & tax support
- [Security & GDPR Compliance](docs/SECURITY_GDPR_COMPLIANCE.md) - Security documentation
- [CI/CD Pipeline](docs/ci_cd_pipeline.md) - GitHub Actions workflow ✨ **Sprint 4**
- [Logging & Monitoring](docs/logging_monitoring.md) - Observability guide ✨ **Sprint 4**
- [Rate Limiting](docs/rate_limiting.md) - Rate limit configuration ✨ **Sprint 4**
- [Sprint Summaries](docs/) - Sprint implementation details

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

## 📚 Documentation Resources

### Technical Documentation

- [System Requirements Document (SRD)](docs/srs_technical_design.md) - Technical specifications
- [Product Requirements Document (PRD)](docs/product_requirement.md) - Business requirements
- [Sprint Summaries](docs/) - Implementation summaries for all sprints

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

## 🧪 Testing

The project includes comprehensive test coverage:

- **23 test files** covering all core functionality
- **Test files:**
  - `test_auth.py` - Authentication endpoints
  - `test_users.py` - User management
  - `test_tenants.py` - Tenant CRUD operations
  - `test_tenant_isolation.py` - Multi-tenant isolation
  - `test_tenant_logo.py` - Tenant branding and logo upload ✨ **NEW**
  - `test_invoices.py` - Invoice management
  - `test_invoice_pdf.py` - PDF generation ✨ **NEW**
  - `test_integration.py` - End-to-end workflows
  - `test_analytics.py` - Analytics endpoints ✨ **Sprint 3**
  - `test_performance.py` - Performance benchmarks ✨ **Sprint 3**
  - `test_background_tasks.py` - Celery tasks ✨ **Sprint 3**
  - `test_monitoring.py` - Health & metrics ✨ **Sprint 4**
  - `test_rate_limiting.py` - Rate limiting ✨ **Sprint 4**
  - `test_audit_logs.py` - Audit logging ✨ **Sprint 4** **NEW**
  - `test_superadmin.py` - Super Admin features ✨ **NEW**
  - `test_email_verification.py` - Email verification ✨ **NEW**
  - `test_password_reset.py` - Password reset ✨ **NEW**
  - `test_multi_currency_tax.py` - Multi-currency and tax ✨ **NEW**
  - `test_currency_consistency.py` - Currency consistency ✨ **NEW**
  - `test_payment_method_and_currency.py` - Payment methods ✨ **NEW**
  - `test_permission_checks.py` - Permission validation ✨ **NEW**
  - `test_pdf_generator.py` - PDF generation service ✨ **NEW**
  - `test_cors.py` - CORS configuration ✨ **NEW**

**Coverage includes:**

- ✅ User registration and authentication
- ✅ Email verification flow
- ✅ Password reset functionality
- ✅ JWT token generation and validation
- ✅ Role-based access control (RBAC)
- ✅ Tenant isolation
- ✅ Tenant branding and logo management
- ✅ CRUD operations
- ✅ Soft deletion (GDPR compliance)
- ✅ Invoice lifecycle management
- ✅ Multi-currency support
- ✅ Tax calculations
- ✅ PDF generation
- ✅ Export functionality (CSV/JSON)
- ✅ End-to-end integration workflows
- ✅ Analytics & reporting ✨ **Sprint 3**
- ✅ Background tasks & caching ✨ **Sprint 3**
- ✅ Monitoring & health checks ✨ **Sprint 4**
- ✅ Rate limiting ✨ **Sprint 4**
- ✅ Audit logging ✨ **Sprint 4**
- ✅ Super Admin operations ✨ **NEW**

See [Testing Documentation](tests/README.md) for details.

---

## 🚦 Next Steps

**Completed:**

- [x] Implement invoice CRUD and lifecycle ✅
- [x] Add invoice metadata (branch, customer, creator) ✅
- [x] Multi-currency support (USD, EUR, GBP, NGN) ✅
- [x] Configurable tax rates per tenant ✅
- [x] Invoice PDF generation ✅
- [x] Invoice email sending ✅
- [x] Email verification for new users ✅
- [x] Password reset functionality ✅
- [x] Tenant branding with logo upload ✅
- [x] Analytics & reporting endpoints ✅
- [x] CSV/JSON export functionality ✅
- [x] Caching with Redis ✅
- [x] Background workers (Celery) ✅
- [x] CI/CD pipeline with GitHub Actions ✅
- [x] Monitoring and logging ✅
- [x] Rate limiting and performance optimization ✅
- [x] Comprehensive audit logging ✅
- [x] Super Admin role and platform management ✅

**Next (Phase 5):**

- [ ] Production deployment guide
- [ ] Demo video and blog post
- [ ] Final polish and documentation review
- [ ] Implement Alembic migrations for production

---

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add/update tests
5. Update documentation
6. Submit a pull request

---

## 📜 License

MIT License - See [LICENSE](LICENSE) for details.

---

## 👤 Author

Name: Rotimi Owolabi

- X/Twitter: [Rotimi Owolabi](https://twitter.com/rohteemie)
- LinkedIn: [Rotimi Owolabi](https://www.linkedin.com/in/rotimijournal/)
- GitHub: [Rotimi Owolabi](https://github.com/rohteemie)

---

Built with ❤️ using FastAPI, SQLAlchemy, and PostgreSQL**
