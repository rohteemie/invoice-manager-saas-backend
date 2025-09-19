# Product Requirements Document (PRD)

## Project: Henex SaaS – Multi-Tenant Business Management Platform

### Version

v1.0

### Objective

Build a multi-tenant SaaS platform that allows organizations (tenants) to manage their business operations under one backend system while maintaining data isolation and role-based access control.

### Business Goals

1. Support multiple organizations with isolated data under one backend instance.
2. Provide role-based access control (RBAC) for different user roles: Owner, Admin, Manager, Attendant.
3. Offer subscription tiers (Free, Pro, Enterprise) with feature limitations.
4. Deliver RESTful APIs with easy integration for future frontend or mobile apps.
5. Ensure scalability, security, and cloud-readiness for production.

### Key Features

| Feature    | Description    | Priority    |
|---|---|---|
| Multi-Tenancy    | Each organization (tenant) has isolated data.    | High    |
| Role-Based Access Control (RBAC)  | Different roles with granular permissions.    | High    |
| Authentication & Authorization   | JWT-based auth with refresh tokens.    | High    |
| Subscription Plans    | Feature limits by plan (Free, Pro, Enterprise).    | Medium    |
| Tenant Onboarding    | Tenant creation, invite users via email.    | Medium    |
| Metrics Dashboard    | API usage, active users, and subscription usage stats.    | Medium    |
| Admin Panel API    | For system admin to manage tenants and subscriptions.    | Medium    |
| Caching & Rate Limiting    | Redis for performance and rate limits per tenant.    | Low    |
| CI/CD Pipeline    | Automated tests, lining, and deployments.    | Medium    |

### User Roles & Permissions

- **Owner**: Manage subscription, users, and all organization data.
- **Admin**: Manage users, inventory, and sales for the tenant.
- **Manager**: Manage inventory and sales only.
- **Attendant**: Record sales, view inventory but no administrative rights.

### User Stories

- As an Owner, I want to create an organization account so that I can onboard my employees.
- As an Admin, I want to manage users within my organization so that I control access.
- As a Manager, I want to track sales and inventory so I can manage daily operations.
- As an Attendant, I want to record sales quickly so that I can process transactions.
- As a System Admin, I want to manage all tenants from a centralized API.

### Assumptions & Constraints

- We will use FastAPI with PostgreSQL and Redis for caching.
- JWT tokens for authentication, with optional refresh tokens.
- RESTful APIs, documented via Swagger/OpenAPI.
- Deployed via Docker with CI/CD pipelines.

### Success Metrics

- System can onboard 100 tenants with isolated data without performance degradation.
- Role-based access fully enforced for all endpoints.
- APIs documented, tested, and deployed successfully.

### Future Enhancements

- WebSockets for real-time dashboard updates.
- AI-driven analytics for business insights.
- Self-service billing and invoicing integration.
