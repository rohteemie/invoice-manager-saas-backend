# FastAPI Multi-Tenant Invoicing SaaS Backend

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
- **CI/CD:** GitHub Actions (planned)
- **Auth:** JWT Authentication, OAuth2PasswordBearer
- **Migrations:** Alembic (planned)

---

## 🏗️ Features (Planned & Implemented)

- [x] Tenant registration & management ✅
- [x] User registration & JWT authentication ✅
- [x] Role-based access (Owner, Admin, Manager, Attendant) ✅
- [x] Invoice CRUD (tenant-aware) ✅ **Sprint 2**
- [x] Invoice lifecycle (Draft → Sent → Paid → Overdue) ✅ **Sprint 2**
- [x] Invoice metadata: branch, creator, customer info ✅ **Sprint 2**
- [x] CSV/JSON exports ✅ **Sprint 2**
- [x] Integration tests ✅ **Sprint 2**
- [x] Analytics & reporting endpoints ✅ **Sprint 3**
- [x] Caching with Redis for performance ✅ **Sprint 3**
- [x] Background workers for automated tasks ✅ **Sprint 3**
- [ ] Audit logging

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

5. **Phase 4**: Reliability & Scalability
   - CI/CD pipelines, monitoring, rate limiting

6. **Phase 5**: Final Showcase (Polish & Deployment)
   - Demo video, blog post, deployment guides

**Current Status:** ✅ Phase 3 Complete (Tag: `v0.3.0-sprint-3`)
**Next:** Phase 4 - Reliability & Scalability

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
│  - Rate Limiting (planned)                                  │
└───────────────────────────┬─────────────────────────────────┘
                            │
            ┌───────────────┼───────────────┐
            │               │               │
            ▼               ▼               ▼
    ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
    │   Tenant     │ │     User     │ │   Invoice    │
    │  Management  │ │  Management  │ │  Management  │
    │              │ │   (+ RBAC)   │ │   (planned)  │
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

**Authentication:**

- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login and get JWT tokens
- `POST /api/v1/auth/refresh` - Refresh access token

**Tenant Management:**

- `POST /api/v1/tenants` - Create new tenant
- `GET /api/v1/tenants` - List all tenants
- `GET /api/v1/tenants/{id}` - Get tenant by ID
- `PUT /api/v1/tenants/{id}` - Update tenant
- `DELETE /api/v1/tenants/{id}` - Soft delete tenant

**User Management:**

- `GET /api/v1/users/me` - Get current user
- `GET /api/v1/users` - List users (Admin+)
- `GET /api/v1/users/{id}` - Get user by ID (Admin+)
- `PUT /api/v1/users/{id}` - Update user (Admin+)
- `DELETE /api/v1/users/{id}` - Delete user (Owner only)

**Invoice Management:** ✨ **NEW in Sprint 2**

- `POST /api/v1/invoices/` - Create new invoice
- `GET /api/v1/invoices/` - List invoices with filters
- `GET /api/v1/invoices/{id}` - Get invoice by ID
- `PUT /api/v1/invoices/{id}` - Update draft invoice (Manager+)
- `PATCH /api/v1/invoices/{id}/status` - Update invoice status (Manager+)
- `DELETE /api/v1/invoices/{id}` - Delete draft invoice (Admin+)
- `GET /api/v1/invoices/export/invoices` - Export invoices (CSV/JSON)

**Comprehensive Documentation:**

- [API Structure Overview](docs/API_STRUCTURE.md) - Complete API documentation
- [Authentication Guide](docs/authentication.md) - Auth implementation details
- [Endpoint Documentation](app/api/v1/endpoints/README.md) - Detailed endpoint specs

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
- [Sprint 1.2 Summary](docs/sprint_1.2_summary.md) - Latest implementation summary

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

- **109 tests** covering all core functionality ✨ **Updated**
- **Test files:**
  - `test_auth.py` - Authentication endpoints (14 tests)
  - `test_users.py` - User management (18 tests)
  - `test_tenants.py` - Tenant CRUD operations (11 tests)
  - `test_tenant_isolation.py` - Multi-tenant isolation (11 tests)
  - `test_invoices.py` - Invoice management (45 tests) ✨ **NEW**
  - `test_integration.py` - End-to-end workflows (10 tests) ✨ **NEW**

**Coverage includes:**

- ✅ User registration and authentication
- ✅ JWT token generation and validation
- ✅ Role-based access control (RBAC)
- ✅ Tenant isolation
- ✅ CRUD operations
- ✅ Soft deletion (GDPR compliance)
- ✅ Invoice lifecycle management ✨ **NEW**
- ✅ Export functionality (CSV/JSON) ✨ **NEW**
- ✅ End-to-end integration workflows ✨ **NEW**

See [Testing Documentation](tests/README.md) for details.

---

## 🚦 Next Steps

**Immediate (Phase 2):**

- [x] Implement invoice CRUD and lifecycle
- [x] Add invoice metadata (branch, customer, creator)
- [ ] Implement Alembic migrations for production

**Short-term (Phase 3):**

- [ ] Analytics & reporting endpoints
- [ ] CSV/JSON export functionality
- [ ] Caching with Redis

**Long-term (Phase 4-5):**

- [ ] CI/CD pipeline with GitHub Actions
- [ ] Monitoring and logging
- [ ] Rate limiting and performance optimization
- [ ] Production deployment guide

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
