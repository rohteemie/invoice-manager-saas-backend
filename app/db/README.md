# Database Directory (`/app/db`)

## Overview

This directory contains database configuration, session management, and initialization logic for the Multi-Tenant SaaS Backend. It provides a clean abstraction layer for database operations using SQLAlchemy.

## Directory Structure

```bash
db/
├── __init__.py      # Package initialization
├── database.py      # Database engine and session configuration
└── session.py       # Database session dependency
```

## Modules

### Database Configuration (`database.py`)

Configures the SQLAlchemy engine and session factory.

**Key Components:**

#### Database Engine

```python
from sqlalchemy import create_engine
from app.core.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
)
```

**Configuration:**

- `settings.DATABASE_URL`: Connection string from environment variables
- `pool_pre_ping=True`: Validates connections before use (prevents stale connections)

**Supported Databases:**

- SQLite (development): `sqlite:///./app.db`
- PostgreSQL (production): `postgresql://user:pass@host/db`
- MySQL (alternative): `mysql+pymysql://user:pass@host/db`

#### Session Factory

```python
from sqlalchemy.orm import sessionmaker, scoped_session

SessionLocal = scoped_session(
    sessionmaker(
        bind=engine,
        autocommit=False,
        autoflush=False,
        expire_on_commit=False
    )
)
```

**Configuration Options:**

- `bind=engine`: Associates sessions with the database engine
- `autocommit=False`: Requires explicit commits (safer for transactions)
- `autoflush=False`: Manual control over when changes are flushed to DB
- `expire_on_commit=False`: Keeps objects accessible after commit
- `scoped_session`: Thread-local session management

#### Database Initialization

```python
def init_db():
    """Initialize database (create tables)"""
    from app.models.general_model import Base
    Base.metadata.create_all(bind=engine)
```

**Purpose:**

- Creates all tables defined in SQLAlchemy models
- Idempotent: Safe to run multiple times
- Called during application startup via lifespan event

**Table Creation Flow:**

1. Import all models (via `app.models.__init__.py`)
2. SQLAlchemy introspects model definitions
3. Generates CREATE TABLE statements
4. Executes DDL against the database

### Session Dependency (`session.py`)

Provides the database session dependency for FastAPI endpoints.

**get_db Function:**

```python
from app.db.database import SessionLocal

def get_db():
    """
    Database session dependency for FastAPI.
    Yields a database session and ensures it's closed after use.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

**Usage in Endpoints:**

```python
from fastapi import Depends
from sqlalchemy.orm import Session
from app.db.session import get_db

@router.get("/users")
def list_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    return users
```

**Features:**

- Automatic session creation per request
- Guaranteed session cleanup via try/finally
- Thread-safe session management
- Connection pooling

## Database Architecture

### Connection Pooling

SQLAlchemy's connection pool manages database connections efficiently:

**Pool Features:**

- Reuses connections across requests
- Configurable pool size (default: 5)
- Overflow handling for burst traffic
- Automatic connection recycling

**Configuration (Optional):**

```python
engine = create_engine(
    settings.DATABASE_URL,
    pool_size=10,           # Regular pool size
    max_overflow=20,        # Extra connections when needed
    pool_pre_ping=True,     # Validate before use
    pool_recycle=3600,      # Recycle connections after 1 hour
)
```

### Session Lifecycle

```bash
Request Received
      │
      ▼
┌─────────────────┐
│  get_db() called│
│  (Dependency)   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  SessionLocal() │
│  (New Session)  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Yield session  │
│  to endpoint    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Endpoint logic │
│  executes       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  db.close()     │
│  (Cleanup)      │
└────────┬────────┘
         │
         ▼
  Response Returned
```

### Transaction Management

**Explicit Commits:**

```python
@router.post("/users")
def create_user(user_in: UserCreate, db: Session = Depends(get_db)):
    db_user = User(**user_in.dict())
    db.add(db_user)
    db.commit()        # Explicit commit
    db.refresh(db_user)  # Refresh to get generated fields
    return db_user
```

**Rollback on Error:**

```python
try:
    db_user = User(**user_in.dict())
    db.add(db_user)
    db.commit()
except IntegrityError:
    db.rollback()  # Undo changes
    raise HTTPException(status_code=400, detail="User already exists")
```

**Context Manager (Alternative):**

```python
with db.begin():
    # Auto-commit on success, rollback on exception
    db.add(db_user)
```

## Database Configuration

### Environment Variables

**Development (.env):**

```env
DATABASE_URL=sqlite:///./app.db
```

**Production (.env.prod):**

```env
DATABASE_URL=postgresql://user:password@db-host:5432/saas_db
```

**Docker Compose:**

```env
DATABASE_URL=postgresql://saas_user:saas_pass@postgres:5432/saas_db
```

### SQLite (Development)

**Advantages:**

- No installation required
- File-based database
- Fast for development
- Simple to reset (delete file)

**Usage:**

```python
DATABASE_URL=sqlite:///./app.db  # Relative path
DATABASE_URL=sqlite:////absolute/path/to/app.db  # Absolute path
```

**Limitations:**

- Not suitable for production
- Limited concurrency
- No network access
- Missing some SQL features

### PostgreSQL (Production)

**Advantages:**

- Production-ready RDBMS
- Excellent concurrency
- Advanced features (JSON, full-text search)
- Battle-tested reliability

**Connection String:**

```bash
postgresql://username:password@hostname:port/database
```

**Installation:**

```bash
# Docker
docker run --name postgres -e POSTGRES_PASSWORD=password -p 5432:5432 -d postgres

# Install psycopg2 driver
pip install psycopg2-binary
```

## Database Operations

### CRUD Operations

**Create:**

```python
def create_user(db: Session, user_in: UserCreate):
    db_user = User(**user_in.dict())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user
```

**Read:**

```python
def get_user(db: Session, user_id: str):
    return db.query(User).filter(User.id == user_id).first()
```

**Update:**

```python
def update_user(db: Session, user_id: str, user_in: UserUpdate):
    db_user = db.query(User).filter(User.id == user_id).first()
    for key, value in user_in.dict(exclude_unset=True).items():
        setattr(db_user, key, value)
    db.commit()
    db.refresh(db_user)
    return db_user
```

**Delete (Soft):**

```python
def delete_user(db: Session, user_id: str):
    db_user = db.query(User).filter(User.id == user_id).first()
    db_user.is_active = False
    db.commit()
    return db_user
```

### Query Patterns

**Filter by Tenant:**

```python
users = db.query(User).filter(
    User.tenant_id == current_user.tenant_id,
    User.is_active == True
).all()
```

**Pagination:**

```python
users = db.query(User).limit(10).offset(0).all()
```

**Ordering:**

```python
users = db.query(User).order_by(User.created_at.desc()).all()
```

**Joins:**

```python
users_with_tenants = db.query(User).join(Tenant).filter(
    Tenant.plan_type == "enterprise"
).all()
```

## Testing

### Test Database Setup

**conftest.py:**

```python
from app.db.database import Base, engine
from app.db.session import get_db

@pytest.fixture(scope="function")
def db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
    Base.metadata.drop_all(bind=engine)
```

**Override Dependency:**

```python
def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
```

### Test Isolation

Each test gets a fresh database:

```python
@pytest.fixture(autouse=True)
def reset_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
```

## Migration Strategy

### Current Approach (Development)

**Auto-creation on startup:**

- `init_db()` creates tables automatically
- Simple for development
- No version control for schema changes

### Future Approach (Production)

**Alembic Migrations:**

```bash
# Initialize Alembic
alembic init alembic

# Create migration
alembic revision --autogenerate -m "Add invoices table"

# Apply migration
alembic upgrade head

# Rollback
alembic downgrade -1
```

**Benefits:**

- Version-controlled schema changes
- Safe production deployments
- Rollback capability
- Team collaboration

## Performance Optimization

### Query Optimization

**Use Eager Loading:**

```python
# Avoid N+1 queries
users = db.query(User).options(
    joinedload(User.tenant)
).all()
```

**Index Usage:**

```python
# Ensure indexes on foreign keys
class User(Base):
    tenant_id = Column(String, ForeignKey("tenants.id"), index=True)
```

**Query Only Needed Fields:**

```python
# Instead of: db.query(User).all()
user_emails = db.query(User.email).all()
```

### Connection Management

**Connection Pool Tuning:**

```python
engine = create_engine(
    DATABASE_URL,
    pool_size=20,        # Increase for high traffic
    max_overflow=10,     # Burst capacity
    pool_pre_ping=True,  # Validate connections
)
```

**Session Lifespan:**

- Keep sessions short-lived
- Commit or rollback explicitly
- Close sessions in finally blocks

## Monitoring

### Database Health Checks

```python
@app.get("/health/db")
def db_health_check(db: Session = Depends(get_db)):
    try:
        db.execute("SELECT 1")
        return {"status": "healthy"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}
```

### Connection Pool Stats

```python
from sqlalchemy import event

@event.listens_for(engine, "connect")
def receive_connect(dbapi_conn, connection_record):
    print("New connection established")
```

## Troubleshooting

### Common Issues

**Stale Connections:**

```python
# Solution: Enable pool_pre_ping
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
```

**Session Leaks:**

```python
# Always use try/finally
try:
    yield db
finally:
    db.close()
```

**Deadlocks:**

```python
# Use consistent ordering in queries
# Lock tables in same order across transactions
```

### Debug Mode

```python
# Enable SQL logging
engine = create_engine(DATABASE_URL, echo=True)
```

## Security Considerations

### SQL Injection Prevention

**Use ORM (Safe):**

```python
db.query(User).filter(User.email == email).first()  # Parameterized
```

**Avoid Raw SQL:**

```python
# ❌ Dangerous
db.execute(f"SELECT * FROM users WHERE email = '{email}'")

# ✅ Safe
db.execute("SELECT * FROM users WHERE email = :email", {"email": email})
```

### Connection Security

**Use SSL in Production:**

```python
DATABASE_URL=postgresql://user:pass@host/db?sslmode=require
```

**Encrypt Credentials:**

- Store credentials in environment variables
- Use secrets management (AWS Secrets Manager, HashiCorp Vault)
- Never commit credentials to version control

## Related Documentation

- [Models](../models/README.md) - Database table definitions
- [Configuration](../core/README.md) - Database URL configuration
- [API Endpoints](../api/README.md) - Using database sessions
- [Testing](../../tests/README.md) - Test database setup

## Future Enhancements

- **Read Replicas**: Route read queries to replicas
- **Sharding**: Partition data across databases
- **Caching**: Redis for frequently accessed data
- **Connection Pooling**: PgBouncer for PostgreSQL
- **Monitoring**: Database performance metrics
- **Backup Strategy**: Automated backups and restore

## License

MIT License - See [LICENSE](../../LICENSE) for details.
