# Invoice Manager SaaS Backend

A FastAPI-based multi-tenant backend for invoice management.

## What You Get

- Tenant-aware authentication and authorization (RBAC)
- Invoice lifecycle management
- PDF invoice generation and email delivery
- Analytics, audit logs, rate limiting, and monitoring endpoints

## Quick Start

### Prerequisites

- Python 3.11+
- pip

### Setup

```bash
cp .env.example .env
python -m venv venv
source venv/bin/activate  # Windows: venv\\Scripts\\activate
pip install -r requirements.txt
```

### Run the API

```bash
uvicorn app.main:app --reload
```

- Swagger: <http://localhost:8000/docs>
- ReDoc: <http://localhost:8000/redoc>
- API base: <http://localhost:8000/api/v1>

## Test

```bash
pytest -v
```

For full testing guidance, see [tests/README.md](tests/README.md).

## Documentation

Detailed system and feature documentation lives in [docs/README.md](docs/README.md).

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add or update tests for your changes
4. Open a pull request

## License

MIT — see [LICENSE](LICENSE).
