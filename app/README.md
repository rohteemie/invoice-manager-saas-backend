# Application Directory (`/app`)

## Overview

This directory contains the main FastAPI application code for the Multi-Tenant SaaS Backend. The application is structured following best practices for scalable, maintainable backend systems with clear separation of concerns.

## Directory Structure

```
app/
├── api/               # API route handlers and endpoints
├── core/              # Core application utilities (config, security, dependencies)
├── db/                # Database configuration and session management
├── models/            # SQLAlchemy ORM models (database tables)
├── schemas/           # Pydantic schemas for request/response validation
├── main.py            # FastAPI application entry point
└── __init__.py        # Package initialization
```

## Key Components

### `main.py`
The application entry point that:
- Initializes the FastAPI application
- Configures lifespan events (startup/shutdown)
- Includes API routers
- Defines the root endpoint
- Sets up OpenAPI documentation

**Key Features:**
- Application title and description configuration
- Database initialization on startup
- API versioning with `/api/v1` prefix
- Automatic OpenAPI documentation at `/docs` and `/redoc`

### Subdirectories

#### `/api` - API Layer
Contains all API endpoints and routing logic. Organized by API version and feature domain.

**See:** [api/README.md](api/README.md) for detailed API documentation.

#### `/core` - Core Utilities
Houses core application functionality including:
- Configuration management
- Security utilities (JWT, password hashing)
- Dependency injection functions
- Shared application logic

**See:** [core/README.md](core/README.md) for core utilities documentation.

#### `/db` - Database Layer
Manages database connectivity and session handling:
- Database engine configuration
- Session factory and dependency
- Database initialization

**See:** [db/README.md](db/README.md) for database configuration details.

#### `/models` - Data Models
SQLAlchemy ORM models representing database tables:
- Tenant model (multi-tenant support)
- User model (authentication and RBAC)
- Base model with common fields
- Relationships and constraints

**See:** [models/README.md](models/README.md) for data model documentation.

#### `/schemas` - Request/Response Schemas
Pydantic schemas for API validation and serialization:
- Input validation schemas
- Response serialization schemas
- Data transfer objects (DTOs)

**See:** [schemas/README.md](schemas/README.md) for schema documentation.

## Architecture Patterns

### Multi-Tenant Architecture
The application implements tenant isolation at the data layer:
- All user data is scoped to a `tenant_id`
- Foreign key relationships enforce data boundaries
- API endpoints validate tenant access

### Role-Based Access Control (RBAC)
Four-tier role hierarchy:
1. **Owner** - Full tenant management
2. **Admin** - User and business operations management
3. **Manager** - Invoice and inventory management
4. **Attendant** - Basic operations (create invoices, view inventory)

### Security Layers
1. **Input Validation** - Pydantic schemas validate all inputs
2. **Authentication** - JWT token verification
3. **Authorization** - Role-based access control
4. **Tenant Isolation** - Database-level data segregation
5. **Audit Logging** - Tracking of sensitive operations (planned)

## Application Flow

```
Client Request
      │
      ▼
┌─────────────────┐
│  FastAPI App    │ (main.py)
│  (main.py)      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  API Router     │ (api/v1/api.py)
│  (/api/v1)      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Endpoint       │ (api/v1/endpoints/*.py)
│  Handler        │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Dependencies   │ (core/deps.py)
│  (Auth, DB)     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Business Logic │
│  & Validation   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  ORM Models     │ (models/*.py)
│  (Database)     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Response       │ (schemas/*.py)
│  Serialization  │
└────────┬────────┘
         │
         ▼
   Client Response
```

## Running the Application

### Local Development

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables (copy `.env.example` to `.env`):
```bash
cp .env.example .env
```

3. Run the development server:
```bash
uvicorn app.main:app --reload
```

4. Access the application:
- API Documentation: http://localhost:8000/docs
- Alternative Docs: http://localhost:8000/redoc
- API Endpoints: http://localhost:8000/api/v1/

### Database Initialization

The database is automatically initialized on application startup via the `lifespan` context manager in `main.py`. Tables are created based on SQLAlchemy models defined in the `/models` directory.

## API Documentation

The application provides automatic interactive API documentation:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Configuration

Application configuration is managed through environment variables (see `core/config.py`):
- `DATABASE_URL`: Database connection string
- `SECRET_KEY`: JWT signing key
- `ACCESS_TOKEN_EXPIRE_MINUTES`: Token expiration time
- `PROJECT_NAME`: Application name
- `API_V1_STR`: API version prefix

## Development Guidelines

### Adding New Features

1. **Define the model** in `/models` if database changes are needed
2. **Create schemas** in `/schemas` for request/response validation
3. **Implement endpoints** in `/api/v1/endpoints`
4. **Add tests** in `/tests` directory
5. **Update documentation** as needed

### Code Organization

- Keep endpoint handlers thin - move business logic to service layers
- Use dependency injection for database sessions and authentication
- Validate inputs with Pydantic schemas
- Handle errors consistently with HTTPException
- Follow FastAPI best practices

## Testing

Tests are located in the `/tests` directory at the project root.

Run tests with:
```bash
pytest tests/ -v
```

See [/tests/README.md](../tests/README.md) for detailed testing documentation.

## Current Implementation Status

### ✅ Implemented
- Multi-tenant architecture with data isolation
- User authentication and JWT token management
- Role-based access control (RBAC)
- Tenant CRUD operations
- User CRUD operations
- Comprehensive test coverage

### 🚧 Planned
- Invoice management (CRUD and lifecycle)
- Audit logging for compliance
- Caching with Redis
- Background tasks with Celery
- Email notifications
- File exports (CSV/JSON)
- Analytics and reporting endpoints

## Related Documentation

- [System Requirements Document](../docs/srs_technical_design.md)
- [Product Requirements Document](../docs/product_requirement.md)
- [API Structure Overview](../docs/API_STRUCTURE.md)
- [Authentication Documentation](../docs/authentication.md)
- [Test Suite Documentation](../tests/README.md)

## License

MIT License - See [LICENSE](../LICENSE) for details.
