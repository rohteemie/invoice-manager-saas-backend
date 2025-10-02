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
- **Cache / Queue:** Redis, Celery (planned)
- **Containerization:** Docker, Docker Compose
- **Testing:** Pytest
- **CI/CD:** GitHub Actions (planned)
- **Auth:** JWT Authentication, OAuth2PasswordBearer
- **Migrations:** Alembic (planned)

---

## 🏗️ Features (Planned & Implemented)

- [x] Tenant registration & management
- [x] User registration & JWT authentication
- [x] Role-based access (Owner, Admin, Manager, Attendant)
- [ ] Invoice CRUD (tenant-aware)
- [ ] Invoice lifecycle (Draft → Sent → Paid → Overdue)
- [ ] Invoice metadata: branch, creator, customer info
- [ ] Audit logging
- [ ] CSV/JSON exports
- [ ] Analytics & reporting endpoints (e.g., revenue by branch, overdue invoices)
- [ ] Caching & background workers for heavy tasks

---

## 📅 Roadmap

This project follows a **phased + sprint-based roadmap**:

1. **Phase 0**: Planning & Documentation
   - ERD, Use Case, Architecture diagrams
   - System & Product Requirements Docs

2. **Phase 1**: Authentication & Tenant Isolation
   - Tenant model, JWT auth, RBAC

3. **Phase 2**: Core Business Module (Invoices)
   - Invoice schema (branch, customer, creator)
   - Invoice CRUD & lifecycle
   - Export endpoints

4. **Phase 3**: Analytics & Reporting
   - Invoice metrics APIs, caching, scheduled tasks

5. **Phase 4**: Reliability & Scalability
   - CI/CD pipelines, monitoring, rate limiting

6. **Phase 5**: Final Showcase (Polish & Deployment)
   - Demo video, blog post, deployment guides

---

## 🔧 Setup Instructions

Clone the repo:

```bash
git clone https://github.com/YOUR-USERNAME/fastapi-multitenant-saas.git
cd fastapi-multitenant-saas

Clone the repo:

git clone https://github.com/YOUR-USERNAME/fastapi-multitenant-saas.git
cd fastapi-multitenant-saas
```

Navigate into the project directory:

```bash
cd fastapi-multitenant-saas
```

Create and activate a virtual environment:

```bash
python -m venv venv
source venv/bin/activate    # Linux/Mac
venv\Scripts\activate       # Windows

python -m venv venv
source venv/bin/activate    # Linux/Mac
venv\Scripts\activate       # Windows

REM venv\Scripts\activate       # Windows

pip install -r requirements.txt

Run the app locally:

uvicorn app.main:app --reload
```

API Docs available at:

Swagger UI → <http://localhost:8000/docs>
ReDoc → <http://localhost:8000/redoc>

📖 Documentation:

System Requirements Document (SRD)
Product Requirements Document (PRD)
API Specs
Architecture Diagram
ERD Diagram
Use Case Diagram

📌 Next Steps:

Implement invoice CRUD and lifecycle.
Add Alembic migrations for production-ready DB setup.
Implement caching and analytics modules.
Configure CI/CD pipeline with GitHub Actions.

📜 License:

MIT License. See LICENSE for details.
