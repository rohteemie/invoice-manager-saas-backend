from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from app.models.general_model import Base
from app.core.config import settings

# Create the engine
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
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
