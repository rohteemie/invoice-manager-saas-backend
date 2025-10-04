# 📅 Project Roadmap – Multi-Tenant Invoicing SaaS Backend

This document outlines the **phases, sprints, and milestones** for building the multi-tenant SaaS backend.
The roadmap blends **traditional planning** with **iterative sprints**, showcasing backend engineering best practices.

---

## 🔖 Phase 0 – Planning & Foundation

**Goal:** Establish technical design, repo structure, and project management setup.
**Deliverables:**

- [x] [Initial README](../README.md)
- [x] [Technical design document outline](../docs/srs_technical_design.md)
- [x] [Architecture diagram](../docs/system_architecture.png)
- [x] [ERD diagram](../docs/erd_diagram.png)
- [x] [Use Case diagram](../docs/use_case_diagram.png)
- [x] [Activity diagram](../docs/activity_diagram.png)
- [x] [API Sequence diagram](../docs/api_sequence_diagram.png)
- [x] GitHub Project board created

**Effort:** S
**Dependencies:** None

---

## 🚀 Phase 1 – Authentication & Tenant Isolation

**Goal:** Build tenant-aware authentication and basic user roles.
**Sprints:**

- [x] Sprint 1.1: Tenant model + registration endpoint
  **Effort:** S | **Core** | **Depends on:** Phase 0
- [x] Sprint 1.2: User model + JWT authentication
  **Effort:** M | **Core** | **Depends on:** 1.1
- [x] Sprint 1.3: Tenant resolution middleware
  **Effort:** M | **Core** | **Depends on:** 1.2
- [x] Sprint 1.4: Basic role-based access (Owner, Admin, Manager, Attendant)
  **Effort:** M | **Core** | **Depends on:** 1.2, 1.3
- [ ] Tests for auth + tenant isolation
  **Effort:** S | **Core** | **Depends on:** All above

**Tech Stack:** FastAPI, SQLAlchemy, JWT (python-jose)

---

## 📦 Phase 2 – Core Business Module (Invoices)

**Goal:** Deliver the tenant-aware invoice management system.
**Sprints:**

- [x] Sprint 2.1: Invoice schema (branch, customer info, creator details)
  **Effort:** M | **Core** | **Depends on:** Phase 1
- [x] Sprint 2.2: Invoice CRUD + lifecycle (Draft → Sent → Paid → Overdue)
  **Effort:** M | **Core** | **Depends on:** 2.1
- [x] Sprint 2.3: Tenant-aware query enforcement
  **Effort:** S | **Core** | **Depends on:** 2.2
- [x] Sprint 2.4: CSV/JSON export endpoints
  **Effort:** S | **Nice-to-have** | **Depends on:** 2.2
- [x] Integration tests ✅ **COMPLETED**
  **Effort:** S | **Core** | **Depends on:** All above

**Tech Stack:** FastAPI, SQLAlchemy, Pandas (for export)
**Status:** ✅ **PHASE 2 COMPLETE** - Tag: `v0.2.0-sprint-2`

---

## 📊 Phase 3 – Analytics & Reporting

**Goal:** Add value-added insights on invoices.
**Sprints:**

- [ ] Sprint 3.1: Tenant-level invoice summary (total revenue, overdue count)
  **Effort:** M | **Core** | **Depends on:** Phase 2
- [ ] Sprint 3.2: Caching with Redis for reports
  **Effort:** M | **Nice-to-have** | **Depends on:** 3.1
- [ ] Sprint 3.3: Background worker (Celery/RQ) for overdue invoice checks
  **Effort:** M | **Nice-to-have** | **Depends on:** 2.2
- [ ] Performance benchmarks
  **Effort:** S | **Core** | **Depends on:** 3.1

**Tech Stack:** FastAPI, Redis, Celery/RQ

---

## ⚙️ Phase 4 – Reliability & Scalability

**Goal:** Make system production-grade.
**Sprints:**

- [ ] Sprint 4.1: CI/CD pipeline (GitHub Actions)
  **Effort:** M | **Core** | **Depends on:** All previous phases
- [ ] Sprint 4.2: API docs (Swagger/OpenAPI)
  **Effort:** S | **Core** | **Depends on:** Phase 1
- [ ] Sprint 4.3: Structured logging & monitoring hooks (Sentry/Prometheus)
  **Effort:** M | **Nice-to-have** | **Depends on:** Phase 2
- [ ] Sprint 4.4: Rate limiting & request throttling
  **Effort:** M | **Nice-to-have** | **Depends on:** Phase 2

---

## 🎨 Phase 5 – Final Showcase

**Goal:** Polish the project for portfolio presentation.
**Deliverables:**

- [ ] Detailed README (setup + usage examples)
- [ ] Short demo video (screen-recorded API walkthrough)
- [ ] Blog post: *“How I Designed a Multi-Tenant Invoicing SaaS Backend”*
- [ ] Optional live demo deployment (Render/Heroku)

**Effort:** M
**Depends on:** All previous phases

---

## 🗂️ Timeline (Suggested)

- **Weeks 1–2:** Phase 0–1
- **Weeks 3–4:** Phase 2
- **Week 5:** Phase 3
- **Weeks 6–7:** Phase 4
- **Week 8:** Phase 5 (showcase + polish)

---

## ✅ Status Tracking

Progress will be tracked via:

- [ ] This roadmap file
- [ ] GitHub Issues (one per sprint)
- [ ] GitHub Project board (Kanban view)

---## 📬 Feedback & Iteration

We welcome feedback on this roadmap and the project as a whole. Please feel free to reach out via:

- GitHub Issues
- Direct messages
- Comments on this document

Your input is invaluable in helping us improve and adapt the project to better meet user needs.
