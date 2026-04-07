# 🧱 Alembic Setup & Database Migration Guide

This document explains how Alembic is configured and used for managing database migrations in the **FastAPI Multi-Tenant Invoicing SaaS Backend** project.

---

## 📖 Overview

Alembic is a lightweight database migration tool for **SQLAlchemy**.
It allows us to evolve our database schema over time while keeping track of changes through version-controlled migration scripts.

Each change to a SQLAlchemy model (adding tables, columns, or constraints) can be reflected in the database by generating a new Alembic migration.

---

## ⚙️ Initial Setup

Alembic has already been initialized in this project under the `/migrations` directory.

**Directory structure:**

```bash
/migrations
    /versions
    env.py
    script.py.mako
    alembic.ini
```

**Key files:**

- `versions/`: Contains individual migration scripts.
- `env.py`: Configures the Alembic environment.
- `script.py.mako`: Template for generating new migration scripts.
- `alembic.ini`: Main configuration file for Alembic.

**Key configuration details:**

- Alembic uses the same database URL as the FastAPI app.
- The `Base.metadata` from our SQLAlchemy models is imported into `migrations/env.py`.
- Autogeneration of migrations is enabled via `target_metadata = Base.metadata`.

---

## 🔧 Running Migrations

### 1️⃣ Generate a New Migration

Whenever models change (new fields, new tables, etc.), create a new migration file using:

```bash
alembic revision --autogenerate -m "describe your change"
```

This command compares the current database schema with the models and generates a migration script in `migrations/versions/`.

💡 Example:

```bash
alembic revision --autogenerate -m "Add branch_id to invoices table"
```

### 2️⃣ Apply Migrations to the Database

To apply all pending migrations:

```bash
alembic upgrade head
```

This brings the database schema up to date with the latest version.

💡 You can also upgrade to a specific version:

```bash
alembic upgrade <revision_id>

### 3️⃣ Roll Back Migrations

If you need to undo the last migration:

```bash
alembic downgrade -1
```

Or roll back to a specific version:

```bash
alembic downgrade <revision_id>
```

---

### 🧪 Checking Migration Status

To see which migration the database is currently on:

```bash
alembic current
```

To view the full history of migrations:

```bash
alembic history
```

---

### 🧩 Environment Configuration

The database connection URL is managed through the app’s settings, not hardcoded in alembic.ini.

In migrations/env.py, we dynamically inject the URL from your environment:

```python
from app.core.config import settings
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)
```

So make sure your .env file contains:

```bash
DATABASE_URL=postgresql+psycopg2://user:password@localhost:5432/your_db_name
```

---

### 🧰 Makefile Shortcuts (Optional)

You can also manage migrations using a Makefile for convenience:

```makefile
migrate:
    alembic revision --autogenerate -m "$(m)"

upgrade:
    alembic upgrade head

downgrade:
    alembic downgrade -1
```

Usage examples:

```bash
make migrate m="Add subscription table"
make upgrade
```

### 🧱 Best Practices

- ✅ Always run alembic revision --autogenerate after modifying models.
- ✅ Inspect migration scripts manually before applying them.
- ✅ Commit migration files (migrations/versions/*.py) to Git for version tracking.
- ✅ Never edit existing migration scripts that have already been applied in production.
- ✅ Keep migrations in sync across environments to avoid schema drift.

### 🧾 Example Workflow

- Modify or add SQLAlchemy models.

- Generate a new migration:

```bash
alembic revision --autogenerate -m "Add new table or field"
```

- Apply the migration:

```bash
alembic upgrade head
```

- Verify the schema in your database.

- Commit and push the new migration file.

---

### 📜 References

- [Alembic Documentation](https://alembic.sqlalchemy.org/en/latest/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/en/20/)
- [FastAPI SQLAlchemy Documentation](https://fastapi.tiangolo.com/tutorial/sql-databases/)

---

### ✅ Summary

Alembic provides a clean, consistent way to manage schema changes across environments.
This ensures that as our SaaS backend grows — adding invoices, subscriptions, branches, or reports — our database stays synchronized, maintainable, and production-ready.

---

### 🧩 Next Step

Integrate Alembic into the CI/CD pipeline so migrations run automatically before deployments.
Happy coding! 🚀
