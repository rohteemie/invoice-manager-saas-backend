import os
from app.db.database import SessionLocal, init_db
import time
from sqlalchemy.exc import OperationalError

# Initialize tables (skip in test environment)
if not os.getenv("TESTING"):
    init_db()


def get_db():
    attempts = 0
    max_attempts = 3
    backoff = 0.5
    while True:
        try:
            db = SessionLocal()
            break
        except OperationalError:
            attempts += 1
            if attempts >= max_attempts:
                raise
            time.sleep(backoff)
            backoff *= 2
    try:
        yield db
    finally:
        db.close()
