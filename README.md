# Rechive - FastAPI Multi-Tenant Invoicing Backend

Rechive is a FastAPI backend for multi-tenant invoice management. It uses SQLAlchemy, PostgreSQL, Redis, Celery, and Docker to support tenant-aware authentication, invoicing, and background processing.

## What It Covers

- Tenant registration and isolation
- JWT authentication and RBAC
- Invoice CRUD, PDF generation, and email delivery
- Email verification, password reset, and audit logging
- Analytics, caching, monitoring, and rate limiting

## Tech Stack

- FastAPI
- SQLAlchemy
- PostgreSQL
- Redis and Celery
- Docker and Docker Compose
- Pytest and GitHub Actions

## Quick Start

```bash
git clone https://github.com/rohteemie/multi-tenant-saas-backend.git
cd multi-tenant-saas-backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

Open the app at:

- API: http://localhost:8000/api/v1
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Testing

```bash
pytest tests/ -v
```

## Documentation

- [API Structure](docs/API_STRUCTURE.md)
- [Security](docs/SECURITY.md)
- [Documentation Index](docs/README.md)
- [Application README](app/README.md)

## License

MIT License. See [LICENSE](LICENSE).