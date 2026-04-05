# Documentation Index

Welcome to the Multi-Tenant SaaS Backend documentation. This directory contains comprehensive guides, feature documentation, system specifications, and visual diagrams.

## 📚 Quick Navigation

### [🚀 Guides](./guides/) — Operational & Setup Documentation
Detailed how-to guides for getting started, deploying, and operating the system.

- **[DEPLOYMENT.md](./guides/DEPLOYMENT.md)** — Step-by-step deployment instructions with environment setup, database initialization, and troubleshooting
- **[CI_CD_PIPELINE.md](./guides/CI_CD_PIPELINE.md)** — Continuous integration and deployment pipeline configuration
- **[MONITORING.md](./guides/MONITORING.md)** — Logging, monitoring, and observability setup
- **[DATABASE_MIGRATION.md](./guides/DATABASE_MIGRATION.md)** — Database migration tools (Alembic) setup and usage

### [⚙️ Features](./features/) — Feature Documentation
Comprehensive documentation for each system feature, covering architecture, API, implementation, and security.

- **[AUTHENTICATION.md](./features/AUTHENTICATION.md)** — User authentication, authorization, and session management
- **[EMAIL_VERIFICATION.md](./features/EMAIL_VERIFICATION.md)** — Email verification system with token lifecycle, security, and frontend integration
- **[PASSWORD_RESET.md](./features/PASSWORD_RESET.md)** — Secure password reset workflow
- **[INVOICING.md](./features/INVOICING.md)** — Invoice data model, API endpoints, PDF generation, multi-currency support, and tax calculations
- **[AUDIT_LOGGING.md](./features/AUDIT_LOGGING.md)** — Comprehensive audit logging system for compliance and tracking
- **[RATE_LIMITING.md](./features/RATE_LIMITING.md)** — Rate limiting and API throttling configuration
- **[SUPER_ADMIN.md](./features/SUPER_ADMIN.md)** — Super Admin platform management and tenant administration
- **[USER_ACCOUNT_MANAGEMENT.md](./features/USER_ACCOUNT_MANAGEMENT.md)** — User account lifecycle (registration, profile, deactivation)
- **[BRANDING.md](./features/BRANDING.md)** — Tenant-specific branding and logo upload system

### [📋 Specifications](./specifications/) — Requirements & System Design
Technical specifications and system design documents.

- **[PRODUCT_REQUIREMENT.md](./specifications/PRODUCT_REQUIREMENT.md)** — Product requirements document (PRD) with use cases and feature overview
- **[SYSTEM_REQUIREMENTS.md](./specifications/SYSTEM_REQUIREMENTS.md)** — System requirements and technical design specifications
- **[ERROR_RESPONSE_FORMAT.md](./specifications/ERROR_RESPONSE_FORMAT.md)** — Standard API error response format and codes

### 📄 Root-Level Documentation

- **[SECURITY.md](./SECURITY.md)** — Comprehensive security and compliance documentation (ISO 27001, GDPR, authentication security, data protection, incident response)
- **[API_STRUCTURE.md](./API_STRUCTURE.md)** — API endpoint structure and organization (48 total endpoints: 5 root/monitoring + 43 business API)

### 🎨 Visual Diagrams

Located in the root of `/docs/`:

- **erd_diagram.png** — Database schema and relationships
- **system_architecture.png** — High-level system architecture
- **api_sequence_diagram.png** — Typical API request/response flow
- **use_case_diagram.png** — System use cases
- **activity_diagram.png** — Invoice workflow activity diagram
- **roadmap_timeline.png** — Project roadmap and timeline

### 📊 Version History

- **[CHANGELOG.md](../CHANGELOG.md)** — Release history with features, metrics, breaking changes, and migration guides for versions 1.0–1.4

## 🔍 How to Use This Documentation

### **For New Developers**
1. Start with [specifications/SYSTEM_REQUIREMENTS.md](./specifications/SYSTEM_REQUIREMENTS.md) for system overview
2. Read [guides/DEPLOYMENT.md](./guides/DEPLOYMENT.md) to set up your development environment
3. Refer to [API_STRUCTURE.md](./API_STRUCTURE.md) for endpoint organization
4. Check specific [features/](./features/) for implementation details

### **For Operations/DevOps**
1. [guides/DEPLOYMENT.md](./guides/DEPLOYMENT.md) — Deployment procedures
2. [guides/CI_CD_PIPELINE.md](./guides/CI_CD_PIPELINE.md) — Pipeline configuration
3. [guides/MONITORING.md](./guides/MONITORING.md) — Observability setup
4. [SECURITY.md](./SECURITY.md) — Security policies and compliance

### **For Feature Implementation**
Each feature in [features/](./features/) includes:
- System architecture overview
- Data model and relationships
- Complete API endpoint documentation
- Configuration options
- Testing strategies
- Security considerations

### **For Compliance & Security**
- [SECURITY.md](./SECURITY.md) — ISO 27001, GDPR, authentication, data protection, audit logging
- [features/AUDIT_LOGGING.md](./features/AUDIT_LOGGING.md) — Event tracking and compliance audit trails
- [specifications/ERROR_RESPONSE_FORMAT.md](./specifications/ERROR_RESPONSE_FORMAT.md) — Standardized error handling

## 📁 Folder Structure Overview

```
docs/
├── guides/                              # How-to guides and operational docs
│   ├── DEPLOYMENT.md
│   ├── CI_CD_PIPELINE.md
│   ├── MONITORING.md
│   └── DATABASE_MIGRATION.md
├── features/                            # Feature-specific documentation
│   ├── AUTHENTICATION.md
│   ├── EMAIL_VERIFICATION.md
│   ├── PASSWORD_RESET.md
│   ├── INVOICING.md
│   ├── AUDIT_LOGGING.md
│   ├── RATE_LIMITING.md
│   ├── SUPER_ADMIN.md
│   ├── USER_ACCOUNT_MANAGEMENT.md
│   └── BRANDING.md
├── specifications/                      # Technical specifications
│   ├── PRODUCT_REQUIREMENT.md
│   ├── SYSTEM_REQUIREMENTS.md
│   └── ERROR_RESPONSE_FORMAT.md
├── SECURITY.md                          # Comprehensive security & compliance
├── API_STRUCTURE.md                     # API endpoint reference
├── README.md                            # This file (navigation hub)
└── [diagrams]                           # Visual documentation (ERD, architecture, etc.)

Related to root:
└── ../CHANGELOG.md                      # Version history (v1.0–1.4)
```

## 🎯 Documentation Standards

All documentation follows these standards:

- **Markdown format** with proper heading hierarchy
- **Table of contents** for documents >1000 lines
- **Code examples** for implementation details
- **Security considerations** highlighted for sensitive features
- **Links** to related documentation and API endpoints
- **Updated** with each release (see CHANGELOG.md)

## 📝 Finding Information

| I'm looking for... | Start here |
|---|---|
| How to deploy the app | [guides/DEPLOYMENT.md](./guides/DEPLOYMENT.md) |
| API endpoint details | [API_STRUCTURE.md](./API_STRUCTURE.md) |
| Email verification flow | [features/EMAIL_VERIFICATION.md](./features/EMAIL_VERIFICATION.md) |
| Invoice system details | [features/INVOICING.md](./features/INVOICING.md) |
| Security policies | [SECURITY.md](./SECURITY.md) |
| System architecture | [specifications/SYSTEM_REQUIREMENTS.md](./specifications/SYSTEM_REQUIREMENTS.md) |
| Database schema | See erd_diagram.png |
| Recent changes | [../CHANGELOG.md](../CHANGELOG.md) |
| Audit logging | [features/AUDIT_LOGGING.md](./features/AUDIT_LOGGING.md) |
| User authentication | [features/AUTHENTICATION.md](./features/AUTHENTICATION.md) |
| Rate limiting | [features/RATE_LIMITING.md](./features/RATE_LIMITING.md) |
| Admin features | [features/SUPER_ADMIN.md](./features/SUPER_ADMIN.md) |

## 🔄 Documentation Maintenance

This documentation is actively maintained and updated with each release. See [../CHANGELOG.md](../CHANGELOG.md) for recent updates and improvements.

---

**Last Updated**: Documentation reorganized into guides/, features/, and specifications/ for improved navigation  
**Status**: ✅ Actively Maintained
