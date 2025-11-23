from sqlalchemy import QueuePool, create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from app.models.general_model import Base
from app.core.config import settings

# Create the engine
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=settings.POOL_SIZE,
    max_overflow=settings.MAX_OVERFLOW,
    pool_timeout=settings.POOL_TIMEOUT,
    pool_recycle=settings.POOL_RECYCLE,
    # Optional: for psycopg2 set a connect timeout
    connect_args={"connect_timeout": int(getattr(settings, "DB_CONNECT_TIMEOUT", 10))},
    poolclass=QueuePool,
)

# Session factory
SessionLocal = scoped_session(
    sessionmaker(
        bind=engine,
        autocommit=False,
        autoflush=False,
        expire_on_commit=False
    )
)


def init_db():
    """Initialize database (create tables)"""
    Base.metadata.create_all(bind=engine)
