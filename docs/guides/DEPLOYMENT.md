# 📘 Deployment Guide

This document provides comprehensive instructions for deploying the **Multi-Tenant SaaS Backend** with automated database migrations.

---

## 📑 Table of Contents

1. [Overview](#overview)
2. [Migration Automation in CI/CD](#migration-automation-in-cicd)
3. [Docker Deployment](#docker-deployment)
4. [Manual Server Deployment](#manual-server-deployment)
5. [Environment Configuration](#environment-configuration)
6. [Troubleshooting](#troubleshooting)
7. [Best Practices](#best-practices)

---

## 🎯 Overview

The deployment process has been enhanced with **automatic database migration** support using Alembic. This ensures that your database schema is always synchronized with your application code across all environments.

### Key Features

✅ **Automated Migrations**: Database migrations run automatically before application startup  
✅ **CI/CD Integration**: Migrations are tested and applied during deployment  
✅ **Fail-Safe**: Deployment fails if migrations encounter errors  
✅ **Traceability**: Clear logs show migration status and any issues  

---

## 🔄 Migration Automation in CI/CD

### GitHub Actions Workflow

The CI/CD pipeline (`.github/workflows/backend.yml`) now includes automatic migration steps:

#### Test Stage

```yaml
- name: Run Alembic migrations
  run: |
    echo "Running Alembic migrations..."
    alembic upgrade head
    echo "Migrations completed successfully"
  env:
    DATABASE_URL: sqlite:///./test.db
```

This ensures migrations are tested against the test database before deployment.

> **Note**: The test stage uses SQLite for fast testing. For production-grade CI testing, consider using PostgreSQL service containers to catch database-specific migration issues. See the PostgreSQL service already configured in the test job for reference.

#### Deploy Stage (Example)

```yaml
- name: Run database migrations
  run: |
    echo "Running Alembic migrations on production database..."
    alembic upgrade head
    echo "✅ Migrations completed successfully"
  env:
    DATABASE_URL: ${{ secrets.DATABASE_URL }}
```

### Required GitHub Secrets

Configure these secrets in your repository settings (`Settings > Secrets and variables > Actions`):

| Secret Name | Description | Example |
|------------|-------------|---------|
| `DATABASE_URL` | Production database connection string | `postgresql://user:pass@host:5432/dbname` |
| `REDIS_URL` | Redis connection string (Celery broker/cache) | `redis://host:6379/0` |
| `SECRET_KEY` | JWT secret key for production | (generate with `openssl rand -hex 32`) |

### Required GitHub Variables

To enable the deployment job, configure this variable (`Settings > Secrets and variables > Actions > Variables`):

| Variable Name | Description | Value |
|--------------|-------------|-------|
| `DEPLOYMENT_ENABLED` | Enable automated deployment job | `true` |

> **Note**: The deploy job in the workflow is configured as an example. Set `DEPLOYMENT_ENABLED` to `true` only when you're ready to enable automated production deployments.

### Viewing Migration Logs

1. Go to repository **Actions** tab
2. Click on the workflow run
3. Expand the "Run Alembic migrations" step
4. Review migration output for success/failure

Example successful output:
```
Running Alembic migrations...
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.runtime.migration] Running upgrade -> abc123, initial schema
INFO  [alembic.runtime.migration] Running upgrade abc123 -> def456, add invoices
✅ Migrations completed successfully
```

---

## 🐳 Docker Deployment

### Using Docker Entrypoint

The Dockerfile now includes an **entrypoint script** that runs migrations when
starting the API. Custom commands (like Celery worker/beat) skip migrations.

**`docker-entrypoint.sh`**:
```bash
#!/bin/bash
set -e

echo "🚀 Starting Multi-Tenant SaaS Backend..."

if [ "$#" -gt 0 ]; then
  echo "⚙️ Running custom command: $*"
  exec "$@"
fi

# Run Alembic migrations
echo "📋 Running Alembic migrations..."
alembic upgrade head
echo "✅ Migrations completed successfully"

# Start the FastAPI application
echo "🌐 Starting FastAPI application..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Building and Running

#### Build the Docker image:

```bash
docker build -t multi-tenant-saas:latest .
```

#### Run with environment variables:

```bash
docker run -d \
  --name multi-tenant-saas \
  -p 8000:8000 \
  -e DATABASE_URL="postgresql://user:password@db:5432/saas_db" \
  -e SECRET_KEY="your-secret-key-here" \
  -e REDIS_URL="redis://redis:6379/0" \
  multi-tenant-saas:latest
```

#### Run Celery worker and beat:

Make sure the containers share a network with your database and Redis, or
replace the `db`/`redis` hostnames with reachable addresses.
Passing a Celery command skips API startup migrations automatically.

```bash
docker run -d \
  --name multi-tenant-saas-worker \
  -e DATABASE_URL="postgresql://user:password@db:5432/saas_db" \
  -e SECRET_KEY="your-secret-key-here" \
  -e REDIS_URL="redis://redis:6379/0" \
  multi-tenant-saas:latest \
  celery -A app.core.celery_app:celery_app worker --loglevel=info

docker run -d \
  --name multi-tenant-saas-beat \
  -e DATABASE_URL="postgresql://user:password@db:5432/saas_db" \
  -e SECRET_KEY="your-secret-key-here" \
  -e REDIS_URL="redis://redis:6379/0" \
  multi-tenant-saas:latest \
  celery -A app.core.celery_app:celery_app beat --loglevel=info --pidfile=/tmp/celerybeat.pid
```

#### Using Docker Compose:

```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:password@db:5432/saas_db
      - SECRET_KEY=your-secret-key-here
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy

  celery_worker:
    build: .
    command: celery -A app.core.celery_app:celery_app worker --loglevel=info
    environment:
      - DATABASE_URL=postgresql://user:password@db:5432/saas_db
      - SECRET_KEY=your-secret-key-here
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy

  celery_beat:
    build: .
    command: celery -A app.core.celery_app:celery_app beat --loglevel=info --pidfile=/tmp/celerybeat.pid
    environment:
      - DATABASE_URL=postgresql://user:password@db:5432/saas_db
      - SECRET_KEY=your-secret-key-here
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy

  db:
    image: postgres:14
    environment:
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
      POSTGRES_DB: saas_db
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U user"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:
```

Start with:
```bash
docker-compose up -d
```

### Viewing Logs

Check migration logs:
```bash
docker logs multi-tenant-saas 2>&1 | grep -A 10 "Running Alembic migrations"
```

Follow application logs:
```bash
docker logs -f multi-tenant-saas
```

---

## 🖥️ Manual Server Deployment

### Using the Deploy Script

The `deploy/deploy.sh` script has been updated to work with migration automation.

#### Prerequisites

1. Configure deployment settings:
```bash
cp deploy/deploy.env.template deploy/deploy.env
# Edit deploy/deploy.env with your server details
```

2. Ensure `.env` file exists with production settings:
```bash
cp .env.example .env
# Edit .env with production values
```

#### Deploy

```bash
./deploy/deploy.sh
```

The deployment script will:
1. Copy application files to server
2. Install dependencies (including Alembic)
3. **Run migrations automatically** (via `server_setup.sh`)
4. Start the application service
5. Start Celery worker and beat services for overdue updates and email jobs

Make sure Redis is running and the `REDIS_URL` points to it before starting
the Celery services.

### Server Setup Script

The `deploy/server_setup.sh` script includes:

```bash
# Run database migrations
echo "Running database migrations..."
alembic upgrade head
```

This runs automatically during deployment.

### Background Workers (Celery)

To manage workers manually on the server:

```bash
sudo systemctl status multi-tenant-saas-celery-worker
sudo systemctl status multi-tenant-saas-celery-beat

sudo systemctl restart multi-tenant-saas-celery-worker
sudo systemctl restart multi-tenant-saas-celery-beat
```

### Manual Migration on Server

If you need to run migrations manually on the server:

```bash
ssh user@your-server.com
cd /home/ubuntu/multi-tenant-saas
source venv/bin/activate
alembic upgrade head
```

---

## ⚙️ Environment Configuration

### Required Environment Variables

Create a `.env` file with the following variables:

```bash
# Application Settings
PROJECT_NAME=Multi-Tenant SaaS Backend
SECRET_KEY=your-secret-key-here  # Generate with: openssl rand -hex 32
ACCESS_TOKEN_EXPIRATION=30       # Minutes
REFRESH_TOKEN_EXPIRATION=10080   # Minutes (7 days)

# Database Configuration
DATABASE_URL=postgresql+psycopg2://user:password@localhost:5432/saas_db

# Redis Configuration (Celery broker + caching)
REDIS_URL=redis://localhost:6379/0

# Optional: Monitoring and Logging
SENTRY_DSN=https://your-sentry-dsn-here
ENVIRONMENT=production
```

### Database URL Format

Different database formats:

**PostgreSQL**:
```
postgresql+psycopg2://user:password@host:port/database
```

**MySQL**:
```
mysql+pymysql://user:password@host:port/database
```

**SQLite** (testing only):
```
sqlite:///./database.db
```

---

## 🔧 Troubleshooting

### Common Migration Issues

#### 1. Migration fails during deployment

**Symptom**: Deployment fails with Alembic error

**Solution**:
- Check DATABASE_URL is correct
- Verify database is accessible
- Review migration scripts in `migrations/versions/`
- Check migration logs for specific errors

**Debug**:
```bash
# Test connection
alembic current

# View migration history
alembic history

# Try upgrade manually
alembic upgrade head --sql  # Generate SQL without executing
```

#### 2. "Target database is not up to date" error

**Symptom**: Migration version mismatch

**Solution**:
```bash
# Check current version
alembic current

# Stamp database to specific version (if needed)
alembic stamp head

# Then upgrade
alembic upgrade head
```

#### 3. Docker container exits immediately

**Symptom**: Container stops after starting

**Solution**:
- Check logs: `docker logs <container-id>`
- Verify DATABASE_URL environment variable
- Ensure database is running and accessible
- Check entrypoint script has execute permissions

#### 4. Database connection errors

**Symptom**: Can't connect to database

**Solution**:
- Verify database host is reachable
- Check firewall rules
- Confirm credentials are correct
- For Docker: ensure network configuration allows communication

### Rolling Back Migrations

If a migration causes issues:

```bash
# Downgrade one version
alembic downgrade -1

# Downgrade to specific version
alembic downgrade <revision_id>

# View available versions
alembic history
```

### CI/CD Debugging

Enable debug mode in workflow:

```yaml
- name: Debug migration
  run: |
    alembic current
    alembic history
    alembic upgrade head --verbose
  env:
    DATABASE_URL: ${{ secrets.DATABASE_URL }}
```

---

## ✨ Best Practices

### 1. **Always Review Migration Scripts**

Before deploying:
```bash
# Generate migration
alembic revision --autogenerate -m "description"

# Review the generated file in migrations/versions/
# Manually verify it does what you expect
```

### 2. **Test Migrations Locally**

```bash
# Test upgrade
alembic upgrade head

# Test downgrade
alembic downgrade -1

# Re-upgrade
alembic upgrade head
```

### 3. **Backup Before Production Migrations**

```bash
# PostgreSQL backup
pg_dump -U user -h host database > backup_$(date +%Y%m%d_%H%M%S).sql

# MySQL backup
mysqldump -u user -p database > backup_$(date +%Y%m%d_%H%M%S).sql
```

### 4. **Use Maintenance Windows**

- Schedule migrations during low-traffic periods
- Enable maintenance mode if needed
- Monitor application after deployment

### 5. **Keep Migrations Atomic**

- One logical change per migration
- Make migrations reversible when possible
- Test both upgrade and downgrade paths

### 6. **Monitor Migration Performance**

- Track migration execution time
- Optimize slow migrations for large datasets
- Consider data migrations separately from schema changes

### 7. **Version Control**

- ✅ Commit migration files to Git
- ✅ Never modify applied migrations
- ✅ Use descriptive migration messages
- ❌ Don't delete migration history

### 8. **Environment Consistency**

- Keep development, staging, and production aligned
- Apply migrations in order across all environments
- Use same database versions across environments

---

## 📊 Deployment Checklist

Before deploying to production:

- [ ] All tests pass locally
- [ ] Migrations tested on staging environment
- [ ] Database backup created
- [ ] Environment variables configured
- [ ] GitHub secrets set (if using CI/CD)
- [ ] Monitoring and logging configured
- [ ] Rollback plan documented
- [ ] Team notified of deployment window

---

## 🚀 Quick Reference

### Local Development
```bash
# Create new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

### Docker
```bash
# Build
docker build -t multi-tenant-saas:latest .

# Run
docker run -p 8000:8000 --env-file .env multi-tenant-saas:latest

# Logs
docker logs -f <container-id>
```

### Server Deployment
```bash
# Deploy
./deploy/deploy.sh

# Check status
ssh user@server 'sudo systemctl status multi-tenant-saas'

# View logs
ssh user@server 'sudo journalctl -u multi-tenant-saas -f'
```

---

## 📚 Related Documentation

- [Alembic Setup Guide](./alembic_setup.md)
- [CI/CD Pipeline](./ci_cd_pipeline.md)
- [System Architecture](./srs_technical_design.md)

---

**Last Updated**: Phase 4 - Sprint 4.9  
**Version**: 2.0.0  
**Status**: ✅ Active with Migration Automation
