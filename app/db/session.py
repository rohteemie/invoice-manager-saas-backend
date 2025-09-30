from app.db.database import SessionLocal, init_db

# Initialize tables
init_db()


def get_db():
    """Dependency that provides a DB session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
