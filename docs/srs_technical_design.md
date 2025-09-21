# System Requirements Document (SRD) - Technical Design

## Introduction
This System Requirements Document (SRD) provides a detailed technical specification for the FastAPI Multi-Tenant SaaS Platform designed to manage tenants, their users, invoices, subscriptions, and business operations under a unified backend system.

It defines:
- System architecture
- Functional & non-functional requirements
- Data model (ERD)
- Security & compliance standards
- API flow diagrams
- CI/CD & deployment strategy

This document aligns with enterprise-grade software standards and GDPR compliance to meet the expectations and qualities.

## Scope & Objectives

### In Scope (MVP)
- Multi-tenant onboarding with data isolation
- Role-based access control (RBAC)
- JWT authentication with refresh tokens
- Invoice management APIs
- Subscription tiers (Free, Pro, Enterprise)
- Audit logging for compliance
- CI/CD automation for deployments

### Out of Scope (Future Releases)
- AI-powered analytics dashboards
- WebSocket-based real-time notifications
- Self-service billing portals
- Advanced reporting and BI integrations

## System Architecture
The architecture is divided into the following layers:

- **Client Layer**: Web & Mobile apps consuming REST APIs
- **API Gateway (FastAPI)**: Request routing, rate-limiting, authentication
- **Business Services**: Tenant management, user & role management, invoice management, analytics
- **Data Layer**: PostgreSQL with row-level security, Redis for caching & rate-limiting
- **External Services**: Stripe (payments), SendGrid (emails), S3 storage
- **CI/CD Pipeline**: GitHub Actions for build → test → deploy automation

## Data Model (ERD)
The data model supports multi-tenancy with strict data isolation using tenant_id.

**Key Entities:**
- **Tenants**: Organization details and subscription plans
- **Users**: Linked to tenants with roles
- **Roles & Permissions**: Owner, Admin, Manager, Attendant
- **Invoices**: CRUD operations with multi-tenant scope
- **Reports**: For extended business functionality
- **Audit Logs**: Tracks user activities for compliance

## Functional Requirements

| ID  | Requirement Description |
|-----|-------------------------|
| FR1 | Tenant Management: Manage tenants, CRUD operations with data isolation. |
| FR2 | User Management: Role-based access control, with predefined roles (Owner, Admin). |
| FR3 | Authentication: Secure login with JWT, refresh tokens for secure session handling. |
| FR4 | Business Operations(Invoice Management): CRUD APIs for tenant-specific invoices, including status transitions (Draft → Sent → Paid/Overdue). |
| FR5 | Subscription Plans: Free, Pro, and Enterprise tiers with feature gating. |
| FR6 | Audit Logs: Record user actions for traceability & debugging. |

## Non-Functional Requirements

| ID  | Requirement Description |
|-----|-------------------------|
| NFR1 | Performance: API response <200ms under normal load (≤100 requests/sec, 95th percentile latency). |
| NFR2 | Scalability: Horizontal scaling using containers & load balancers. |
| NFR3 | Security: TLS encryption at rest and in transit, GDPR compliance, and audit logs. |
| NFR4 | Reliability: 99.9% uptime SLA with monitoring & alerts. |
| NFR5 | Maintainability: Modular code & architecture with CI/CD pipelines. |
| NFR6 | Usability: Swagger & Postman documentation for API endpoints. |

## API Request/Response Flow
A typical client request flow:
1. Client sends HTTPS request to API Gateway
2. API Gateway validates JWT & RBAC roles
3. Auth Service confirms identity & permissions
4. Business Service processes request (e.g., invoice CRUD)
5. Database fetches/stores data
6. Response is returned through the API Gateway to the Client

### Activity Diagram (Invoice Workflow)
Visualizes the workflow for creating and sending an invoice:
Login → Select Tenant → Create Invoice → Add Items → Save Invoice → Send to Customer

## Security Considerations
- **Authentication & Authorization**: JWT with RBAC enforcement
- **Data Isolation**: Tenant-based row-level security in PostgreSQL
- **Encryption**: TLS for data in transit, AES for sensitive data at rest
- **Audit Logs**: Immutable logs for all critical actions
- **Compliance**: GDPR-compliant data handling, right-to-be-forgotten support

## CI/CD Pipeline
Stages include:
1. Developer Push Code → GitHub repository
2. CI Pipeline → Automated unit & integration tests
3. Docker Image Build → Containerization of services
4. Staging Deployment → QA & testing environment
5. Production Deployment → Zero-downtime release

## Technology Stack
- **Backend Framework**: FastAPI
- **Database**: PostgreSQL
- **Caching**: Redis
- **Containerization**: Docker
- **CI/CD**: GitHub Actions
- **Authentication**: JWT
- **External Services**: Stripe (payments), SendGrid (emails)

## Deployment Strategy
- **Containers**: Docker-based microservices
- **Orchestration**: Kubernetes or Docker Swarm
- **Environments**: Dev → Staging → Production with separate configs
- **Monitoring**: Prometheus, Grafana, Sentry for metrics & alerts

## Future Enhancements
- AI-driven analytics dashboards
- Real-time notifications using WebSockets
- Self-service billing & subscription upgrades
- Multi-language & localization support

## Scaling Plan Section

### Scaling Strategy:
- **Short-term (MVP)**: Single DB with row-level security + indexes
- **Medium-term (100–500 tenants)**: Use read replicas for PostgreSQL, cache frequent queries with Redis
- **Long-term (500+ tenants)**: Shard tenants across multiple databases, move invoices to partitioned tables, and introduce message queues for async processing

## Glossary & References

### Glossary
- **RBAC**: Role-Based Access Control
- **JWT**: JSON Web Token
- **GDPR**: General Data Protection Regulation
- **CI/CD**: Continuous Integration / Continuous Deployment
- **ERD**: Entity Relationship Diagram
- **RLS**: Row-Level Security (PostgreSQL)
- **SaaS**: Software as a Service

### References:
- FastAPI Documentation
- PostgreSQL Row-Level Security
- Stripe & SendGrid API Docs
- GDPR Compliance Guidelines
