# FastAPI Multi-Tenant SaaS Backend

A portfolio project showcasing the design and implementation of a **multi-tenant SaaS backend**.
Built with **FastAPI + SQLAlchemy** and **PostgreSQL**, containerized with **Docker**.

---

## 🚀 Project Goals

- Demonstrate backend engineering skills in designing and implementing a SaaS application.
- Show **multi-tenancy support** (isolated tenant data per organization).
- Include **authentication, role-based access control (RBAC), audit logging, and exports**.
- Provide a roadmap for **scaling from MVP to enterprise-ready**.
- Showcase **documentation, diagrams, and CI/CD practices** for professional presentation.

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
- [ ] User registration & JWT authentication
- [ ] Role-based access (Owner, Admin, Manager, Attendant)
- [ ] CRUD for Invoices (tenant-aware)
- [ ] Invoice lifecycle (Draft → Sent → Paid → Overdue)
- [ ] Audit logging
- [ ] CSV/JSON exports
- [ ] Analytics & reporting endpoints
- [ ] Caching & background workers for heavy tasks

---

## 📅 Roadmap

This project follows a **phased + sprint-based roadmap**:

1. **Phase 0**: Planning & Documentation
   - ERD, Use Case, Architecture diagrams
   - System & Product Requirements Docs

2. **Phase 1**: Authentication & Tenant Isolation
   - Tenant model, JWT auth, RBAC

3. **Phase 2**: Core Business Module (Clients, Invoices)
   - CRUD endpoints, lifecycle stages, exports

4. **Phase 3**: Analytics & Reporting
   - Metrics APIs, caching, scheduled tasks

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
