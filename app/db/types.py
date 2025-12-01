"""Database-specific custom types.

Place DB TypeDecorator utilities here to avoid importing model modules
from other parts of the application (prevents circular imports and keeps
DB helpers centralised).
"""
from sqlalchemy.types import TypeDecorator, DateTime as SADateTime
from datetime import datetime, timezone


class UTCDateTime(TypeDecorator):
    """Platform-independent DateTime type which stores naive UTC datetimes
    in the database and returns timezone-aware datetimes (tzinfo=UTC) in
    Python.

    This works around backends (like MySQL) that don't store timezone
    information in `DATETIME` columns.
    """
    impl = SADateTime
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if value.tzinfo is not None:
            # convert to UTC then drop tzinfo for storage
            value = value.astimezone(timezone.utc).replace(tzinfo=None)
        return value

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        if value.tzinfo is None:
            # assume stored naive datetimes are UTC
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)
