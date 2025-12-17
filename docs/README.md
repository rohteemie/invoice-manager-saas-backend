# Documentation Directory (`/docs`)

## Overview

This directory contains comprehensive documentation for the Multi-Tenant SaaS Backend project, including technical specifications, system designs, diagrams, and sprint summaries.

## Directory Structure

```bash
docs/
├── API_STRUCTURE.md                        # Visual API structure (47 total endpoints: 4 root + 43 API)
├── authentication.md                       # User authentication & authorization guide
├── SECURITY.md                             # Security & compliance documentation (ISO 27001, GDPR)
├── SECURITY_GDPR_COMPLIANCE.md            # Security and GDPR compliance details
├── alembic_setup.md                        # Database migration setup guide
├── ci_cd_pipeline.md                       # CI/CD pipeline documentation
├── deployment.md                           # Deployment guide with migration automation
├── logging_monitoring.md                   # Logging and monitoring implementation
├── rate_limiting.md                        # Rate limiting and throttling
├── product_requirement.md                  # Product Requirements Document (PRD)
├── srs_technical_design.md                 # System Requirements Document (SRD)
├── INVOICE_IMPLEMENTATION.md               # Invoice feature with multi-currency & tax support
├── PDF_GENERATION.md                       # Invoice PDF generation feature ✨ NEW
├── EMAIL_VERIFICATION.md                   # Email verification feature documentation ✨ NEW
├── EMAIL_VERIFICATION_IMPLEMENTATION_SUMMARY.md  # Email verification implementation details ✨ NEW
├── FRONTEND_EMAIL_VERIFICATION.md          # Frontend integration guide for email verification ✨ NEW
├── PASSWORD_RESET.md                       # Password reset feature documentation ✨ NEW
├── AUDIT_LOGGING.md                        # Comprehensive audit logging system ✨ NEW
├── SUPER_ADMIN.md                          # Super Admin platform management ✨ NEW
├── branding.md                             # Tenant branding and logo upload ✨ NEW
├── USER_ACCOUNT_MANAGEMENT.md              # User account management guide ✨ NEW
├── IMPLEMENTATION_SUMMARY.md               # Overall implementation summary
├── IMPLEMENTATION_SUMMARY_PDF.md           # PDF implementation summary
├── sprint_1.2_summary.md                   # Sprint 1.2 implementation summary
├── sprint_2_summary.md                     # Sprint 2 implementation summary
├── sprint_3_summary.md                     # Sprint 3 implementation summary
├── sprint_4_summary.md                     # Sprint 4 implementation summary
├── activity_diagram.png                    # Invoice workflow activity diagram
├── api_sequence_diagram.png                # API request/response sequence
├── erd_diagram.png                         # Entity Relationship Diagram
├── roadmap_timeline.png                    # Project roadmap timeline
├── system_architecture.png                 # High-level system architecture
└── use_case_diagram.png                    # Use case diagram
```

## Documentation Files

### Product & System Documentation

#### Product Requirements Document (`product_requirement.md`)

**Purpose:** Defines business goals, features, and user stories.

**Key Sections:**

- Project objectives and business goals
- Key features and priorities
- User roles and permissions (Owner, Admin, Manager, Attendant)
- User stories for each role
- Success metrics
- Future enhancements

**Audience:** Product managers, stakeholders, developers

**Contents:**

- Multi-tenancy strategy
- Role-based access control requirements
- Subscription tiers (Free, Pro, Enterprise)
- Feature prioritization matrix
- Assumptions and constraints

---

#### System Requirements Document (`srs_technical_design.md`)

**Purpose:** Technical specifications and architecture design.

**Key Sections:**

- System architecture layers
- Data model (ERD)
- Functional requirements (FR1-FR6)
- Non-functional requirements (NFR1-NFR6)
- API request/response flow
- Security considerations
- CI/CD strategy

**Audience:** Developers, architects, DevOps engineers

**Contents:**

- Multi-tenant architecture
- Authentication & authorization mechanisms
- Database design and isolation strategy
- Performance requirements
- Security standards (OWASP, GDPR)
- Scalability approach

---

### API Documentation

#### API Structure Overview (`API_STRUCTURE.md`)

**Purpose:** Visual representation of the entire API structure with security compliance.

**Key Sections:**

- Complete API endpoint tree (47 total endpoints: 4 root/monitoring + 43 business API)
- Email verification endpoints
- Role hierarchy visualization
- Authentication flow diagram
- Data model relationships with security annotations
- Security layers (5 layers)
- Token lifecycle
- File structure mapping
- Security & Compliance section (ISO 27001, GDPR)
- Multi-currency support details

**Highlights:**

- 47 total endpoints (4 root + 43 API endpoints across 7 categories)
- Visual ASCII diagrams for flows
- Security layer architecture
- ISO 27001 and GDPR compliance annotations
- Multi-currency (ISO 4217) documentation

**Audience:** Developers, API consumers, testers, security reviewers

---

#### Security & Compliance Documentation (`SECURITY.md`)

**Purpose:** Comprehensive security and compliance guide covering ISO 27001 and GDPR standards.

**Key Sections:**

- ISO 27001 Compliance (A.9, A.10, A.12)
- GDPR Compliance (Articles 5, 6, 17, 25, 32)
- Authentication & Access Control
- Data Protection measures
- Financial Data Security
- Email Verification Security
- Multi-Currency & Tax Compliance
- Security Best Practices
- Incident Response Plan
- Audit & Monitoring guidance

**Highlights:**

- 500+ lines of comprehensive security documentation
- Compliance checklist with status
- Security measures for developers, deployers, and users
- Incident response procedures
- Financial data handling (ISO 4217, tax data)
- Token security details
- Privacy protection measures

**Audience:** Security reviewers, compliance officers, developers, DevOps engineers

---

#### Invoice Implementation (`INVOICE_IMPLEMENTATION.md`)

**Purpose:** Complete documentation of invoice features including multi-currency and tax support.

**Key Sections:**

- Invoice data model
- Invoice lifecycle and status transitions
- API endpoints and permissions
- Multi-Currency support (ISO 4217 compliant)
- Tax configuration per tenant
- Security and compliance measures
- Database schema details
- Testing coverage

**Highlights:**

- Multi-currency support (USD, EUR, GBP, NGN)
- Configurable tax rates per tenant
- GDPR compliance for financial data
- Migration details and backward compatibility
- Security annotations for sensitive fields

**Audience:** Developers, API consumers, compliance officers

---

#### Email Verification (`EMAIL_VERIFICATION.md`)

**Purpose:** Documentation of email verification feature with security best practices.

**Key Sections:**

- Token generation and security
- Email verification workflow
- Resend functionality
- Rate limiting
- Security considerations
- Frontend integration guide

**Highlights:**

- Cryptographically secure tokens
- 24-hour token expiration
- Single-use tokens
- Rate limiting protection
- GDPR data minimization compliance

**Audience:** Frontend developers, security reviewers

---

#### Database Migration Guide (`alembic_setup.md`)

**Purpose:** Setup and usage guide for Alembic database migrations.

**Key Sections:**

- Initial setup
- Creating new migrations
- Applying migrations
- Rolling back migrations
- Best practices
- Environment configuration

**Audience:** Developers, DevOps engineers

---

#### CI/CD Pipeline Documentation (`ci_cd_pipeline.md`)

**Purpose:** Continuous Integration and Deployment pipeline documentation.

**Key Sections:**

- Pipeline architecture
- Workflow stages (lint, test, build, deploy)
- GitHub Actions configuration
- Migration automation
- Docker build process
- Environment variables and secrets

**Audience:** DevOps engineers, developers

---

#### Deployment Guide (`deployment.md`)

**Purpose:** Comprehensive deployment guide with automated migrations.

**Key Sections:**

- Migration automation in CI/CD
- Docker deployment with entrypoint
- Manual server deployment
- Environment configuration
- Troubleshooting guide
- Best practices and checklists

**Contents:**

- GitHub Actions workflow examples
- Docker entrypoint script usage
- Server setup procedures
- Database URL configuration
- Migration rollback procedures
- Production deployment checklist

**Audience:** DevOps engineers, system administrators, developers

---

#### Authentication Guide (`authentication.md`)

**Purpose:** Comprehensive authentication and authorization documentation with security compliance.

**Key Sections:**

- User model attributes (including verification tokens)
- Email verification fields with security annotations
- Password reset fields with security annotations ✨ NEW
- User role definitions and hierarchy (including Super Admin) ✨ NEW
- Authentication endpoints (register, login, refresh, verify-email, forgot-password, reset-password)
- JWT token structure
- Security features (ISO 27001, GDPR)
- Testing examples

**Contents:**

- Password hashing with bcrypt (ISO 27001 A.10)
- JWT token generation and validation
- Email verification token security ✨ NEW
- Password reset token security ✨ NEW
- Role-based access control implementation
- Super Admin role documentation ✨ NEW
- Soft deletion for GDPR compliance (Art. 17)
- Token expiration for data minimization (GDPR Art. 5.1.c)
- Code examples for each endpoint

**Audience:** Frontend developers, API integrators, security reviewers

---

#### Password Reset (`PASSWORD_RESET.md`) ✨ **NEW**

**Purpose:** Documentation of secure password reset functionality.

**Key Sections:**

- Password reset architecture
- Forgot password endpoint
- Reset password endpoint
- Email templates
- Security features and best practices
- Rate limiting
- Token management

**Highlights:**

- Secure token generation (30-minute expiration)
- Email enumeration prevention
- Rate limiting (3 requests/hour for forgot, 5/hour for reset)
- OWASP security compliance
- Audit logging for all reset requests
- Single-use tokens

**Audience:** Frontend developers, security reviewers, API integrators

---

#### Audit Logging (`AUDIT_LOGGING.md`) ✨ **NEW**

**Purpose:** Comprehensive audit logging system documentation.

**Key Sections:**

- Automatic logging of critical operations
- Audit log data structure
- API endpoints for accessing logs
- Filtering and querying capabilities
- Security and compliance
- Implementation details

**Highlights:**

- 40+ audited event types
- Authentication events (login, logout, token refresh)
- User management events (create, update, delete, role changes)
- Tenant management events
- Invoice operations
- Password reset tracking
- Data export logging
- IP address and user agent tracking
- Before/after state tracking for changes

**Audience:** Security reviewers, compliance officers, administrators

---

#### Super Admin (`SUPER_ADMIN.md`) ✨ **NEW**

**Purpose:** Platform-level administration and management documentation.

**Key Sections:**

- Super Admin role characteristics
- Database schema changes
- Platform management API endpoints
- Tenant management operations
- User management across tenants
- Audit log access
- Platform statistics

**Highlights:**

- Platform-level access (not tied to any tenant)
- 7 dedicated admin endpoints
- Tenant suspension/reactivation
- Cross-tenant user visibility
- Platform-wide audit logs
- Aggregated statistics
- Bypass tenant-level role checks

**Audience:** Platform administrators, DevOps engineers, developers

---

#### Tenant Branding (`branding.md`) ✨ **NEW**

**Purpose:** Tenant branding and logo management feature documentation.

**Key Sections:**

- Logo upload functionality
- Supported file formats and sizes
- Branded invoice generation
- Tenant contact information
- API endpoints
- Security and validation

**Highlights:**

- Logo upload (PNG, JPG, JPEG, SVG up to 2MB)
- Logo appears in invoice PDFs
- Tenant contact details on invoices
- Custom tax labels
- File validation and storage
- Owner/Admin access only

**Audience:** Frontend developers, API integrators, business users

---

#### PDF Generation (`PDF_GENERATION.md`) ✨ **NEW**

**Purpose:** Invoice PDF generation feature documentation.

**Key Sections:**

- PDF generation architecture
- Invoice PDF endpoint
- Template structure
- Branding integration
- Multi-currency formatting
- Tax calculations

**Highlights:**

- On-demand PDF generation
- Includes tenant logo and branding
- Multi-currency support
- Professional invoice layout
- Automatic tax calculations
- WeasyPrint-based rendering

**Audience:** Developers, API consumers

---

#### User Account Management (`USER_ACCOUNT_MANAGEMENT.md`) ✨ **NEW**

**Purpose:** User account management rules and permissions guide.

**Key Sections:**

- Role hierarchy
- Account management rules
- User deletion rules
- User update rules
- API endpoints
- Error handling
- Security considerations

**Highlights:**

- Only owners can delete users
- Owners cannot delete themselves or other owners
- Soft delete mechanism (GDPR compliant)
- Role-based permissions
- Comprehensive permission matrix

**Audience:** Developers, API consumers, administrators

---

- Password hashing with bcrypt (ISO 27001 A.10)
- JWT token generation and validation
- Email verification token security
- Role-based access control implementation
- Soft deletion for GDPR compliance (Art. 17)
- Token expiration for data minimization (GDPR Art. 5.1.c)
- Code examples for each endpoint

**Audience:** Frontend developers, API integrators, security reviewers

---

### Sprint Documentation

#### Sprint 1.2 Summary (`sprint_1.2_summary.md`)

**Purpose:** Implementation summary for User Model + JWT Authentication sprint.

**Key Sections:**

- What was implemented (8 major components)
- Security features
- Testing results
- Code quality metrics
- API endpoints created
- Database schema
- Dependencies added
- Files created/modified
- Next steps

**Highlights:**

- User model with RBAC
- JWT authentication with refresh tokens
- Comprehensive test coverage (76 tests passing)
- Bcrypt password hashing
- Tenant isolation
- GDPR compliance (soft deletes)

**Audience:** Project managers, developers, stakeholders

---

## Diagrams

### Entity Relationship Diagram (`erd_diagram.png`)

**Shows:**

- Database tables (Tenants, Users)
- Relationships (1:N from Tenants to Users)
- Field definitions
- Primary and foreign keys
- Constraints

**Purpose:** Understand data model and relationships

---

### System Architecture Diagram (`system_architecture.png`)

**Shows:**

- High-level system layers
- Client → API → Database flow
- External services integration
- Caching and queue services
- Deployment infrastructure

**Purpose:** Understand overall system design

---

### Use Case Diagram (`use_case_diagram.png`)

**Shows:**

- Actors (Owner, Admin, Manager, Attendant)
- Use cases for each role
- System boundaries
- Relationships between actors and use cases

**Purpose:** Understand user interactions and permissions

---

### API Sequence Diagram (`api_sequence_diagram.png`)

**Shows:**

- Client-to-server communication flow
- Authentication sequence
- Token generation process
- API request lifecycle

**Purpose:** Understand API interaction patterns

---

### Activity Diagram (`activity_diagram.png`)

**Shows:**

- Invoice workflow (create → send → track)
- Decision points
- Process flow
- User actions

**Purpose:** Understand business process flows

---

### Roadmap Timeline (`roadmap_timeline.png`)

**Shows:**

- Project phases (0-5)
- Sprint breakdown
- Feature timeline
- Milestones

**Purpose:** Understand project planning and progress

---

## Documentation Usage

### For Developers

**Getting Started:**

1. Read [README.md](../README.md) for project overview
2. Review [srs_technical_design.md](srs_technical_design.md) for architecture
3. Check [deployment.md](deployment.md) for deployment setup
4. Study [alembic_setup.md](alembic_setup.md) for database migrations
5. Review [API_STRUCTURE.md](API_STRUCTURE.md) for endpoint details
6. Check [authentication.md](authentication.md) for auth implementation

**Development Workflow:**

1. Refer to diagrams for system understanding
2. Follow coding patterns from sprint summaries
3. Use API documentation for endpoint specs
4. Test against documented requirements

### For Frontend/API Consumers

**Integration Guide:**

1. Start with [authentication.md](authentication.md) for auth flow
2. Review [API_STRUCTURE.md](API_STRUCTURE.md) for endpoints
3. Use interactive docs at <http://localhost:8000/docs>
4. Reference [product_requirement.md](product_requirement.md) for features

### For Stakeholders

**Project Understanding:**

1. Review [product_requirement.md](product_requirement.md) for business goals
2. Check [roadmap_timeline.png](roadmap_timeline.png) for timeline
3. Read sprint summaries for progress updates
4. View [use_case_diagram.png](use_case_diagram.png) for user roles

### For Security Reviewers

**Security Assessment:**

1. Review [SECURITY.md](SECURITY.md) for comprehensive security documentation
2. Check [authentication.md](authentication.md) for auth mechanisms and token security
3. Examine [srs_technical_design.md](srs_technical_design.md) for security requirements
4. Review security layers in [API_STRUCTURE.md](API_STRUCTURE.md)
5. Validate GDPR compliance across all documentation
6. Check [INVOICE_IMPLEMENTATION.md](INVOICE_IMPLEMENTATION.md) for financial data security

### For Compliance Officers

**Compliance Review:**

1. Review [SECURITY.md](SECURITY.md) for ISO 27001 and GDPR compliance
2. Check compliance status table and measures
3. Review data retention policies
4. Validate legal basis for processing (GDPR Art. 6)
5. Verify data protection by design measures
6. Review incident response procedures

## Document Relationships

```bash
product_requirement.md
        │
        ├─> Defines business requirements
        │
        ▼
srs_technical_design.md
        │
        ├─> Specifies technical implementation
        │
        ▼
API_STRUCTURE.md + authentication.md
        │
        ├─> Document implementation details
        │
        ▼
sprint_1.2_summary.md
        │
        └─> Summarizes completed work
```

## Diagrams Overview

### How Diagrams Support Documentation

**ERD Diagram:**

- Supports: srs_technical_design.md, API_STRUCTURE.md
- Shows: Data model structure

**System Architecture:**

- Supports: srs_technical_design.md, product_requirement.md
- Shows: High-level design

**Use Case Diagram:**

- Supports: product_requirement.md
- Shows: User interactions

**Sequence Diagram:**

- Supports: API_STRUCTURE.md, authentication.md
- Shows: Request flow

**Activity Diagram:**

- Supports: product_requirement.md
- Shows: Business workflows

**Roadmap Timeline:**

- Supports: All documents
- Shows: Project planning

## Documentation Standards

### Markdown Format

All text documentation uses Markdown for:

- Version control friendly
- Easy to read in plain text
- Renders beautifully on GitHub
- Supports code blocks and tables

### Code Examples

All code examples include:

- Language specification
- Complete, runnable code
- Comments for clarity
- Request/response examples

### Diagram

All diagrams follow:

- PNG format for images
- Clear, readable resolution
- Consistent styling
- Descriptive filenames

### Versioning

Documentation is versioned with:

- Git commits for history
- Sprint summaries for milestones
- Last updated dates
- Version numbers where applicable

## Keeping Documentation Updated

### When to Update

**After Feature Implementation:**

- Update API_STRUCTURE.md with new endpoints
- Add to sprint summary
- Update diagrams if structure changes

**After Architecture Changes:**

- Update srs_technical_design.md
- Regenerate relevant diagrams
- Update README.md if needed

**During Development:**

- Keep authentication.md current with security changes
- Update code examples
- Add new use cases

### Documentation Checklist

- [ ] Update endpoint documentation for new APIs
- [ ] Add code examples for new features
- [ ] Update diagrams if data model changes
- [ ] Create sprint summary after each sprint
- [ ] Review and update PRD/SRD quarterly
- [ ] Keep README.md feature checklist current

## Accessing Documentation

### Local Access

All documentation is in the `/docs` directory:

```bash
cd docs
ls -la
```

View Markdown files:

```bash
# Using any text editor
code API_STRUCTURE.md

# Using Markdown previewer
grip authentication.md

# In browser (if served)
http://localhost:8000/docs/
```

### GitHub Access

Documentation is also available on GitHub:

```bash
https://github.com/rohteemie/multi-tenant-saas-backend/tree/main/docs
```

### Interactive API Docs

Live API documentation:

- Swagger UI: <http://localhost:8000/docs>
- ReDoc: <http://localhost:8000/redoc>

## Future Documentation

### Planned Documents

**Technical:**

- ~~Database migration guide (when Alembic is added)~~ ✅ Completed: `alembic_setup.md`
- ~~Deployment guide (Docker, Kubernetes)~~ ✅ Completed: `deployment.md`
- ~~CI/CD documentation~~ ✅ Completed: `ci_cd_pipeline.md`
- Performance tuning guide
- Monitoring and logging guide

**Feature Specific:**

- Invoice management documentation
- Branch management guide
- Analytics API documentation
- Export functionality guide

**Operations:**

- Backup and recovery procedures
- Disaster recovery plan
- Incident response playbook
- Runbook for common tasks

## Related Documentation

### Application Documentation

- [Application README](../app/README.md) - Application structure
- [Models Documentation](../app/models/README.md) - Data models
- [API Documentation](../app/api/README.md) - API layer
- [Testing Guide](../tests/README.md) - Test suite

### Root Documentation

- [Project README](../README.md) - Main project overview
- [License](../LICENSE) - MIT License
- [Contributing Guidelines](../CONTRIBUTING.md) - If added

## Contributing to Documentation

### Documentation Guidelines

1. **Clarity**: Write for the target audience
2. **Completeness**: Cover all aspects of the topic
3. **Accuracy**: Keep information up-to-date
4. **Examples**: Include code examples where helpful
5. **Formatting**: Follow Markdown best practices

### Review Process

1. Update documentation alongside code changes
2. Request review from team members
3. Validate examples and code snippets
4. Check for broken links
5. Ensure diagrams are current

## License

All documentation is covered under the project's MIT License. See [LICENSE](../LICENSE) for details.
