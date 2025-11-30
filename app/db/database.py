
from sqlalchemy import QueuePool, create_engine
from sqlalchemy.orm import sessionmaker
from app.models.general_model import Base
from app.core.config import settings


# Create the engine with sensible defaults and pool pre-ping
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=settings.POOL_SIZE,
    max_overflow=settings.MAX_OVERFLOW,
    pool_timeout=settings.POOL_TIMEOUT,
    pool_recycle=settings.POOL_RECYCLE,
    poolclass=QueuePool,
)

# Use a plain sessionmaker (one Session per request) rather than scoped_session.
# scoped_session can cause unexpected session reuse across async contexts.
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


def init_db():
    """Initialize database (create tables)"""
    Base.metadata.create_all(bind=engine)
