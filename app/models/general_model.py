#!/usr/bin/env python3
""" Base class config For all models """
from sqlalchemy import Column, String
from sqlalchemy.orm import declarative_base
from datetime import datetime, timezone
from uuid import uuid4
from app.db.types import UTCDateTime


Base = declarative_base()


class Gen_Model:
    """
    Defines all common attributes and methods
    for all other models
    """
    id = Column(String(60), unique=True, nullable=False, primary_key=True,
                index=True
                )
    created_at = Column(
        UTCDateTime(), nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )
    updated_at = Column(
        UTCDateTime(), nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    def __init__(self, *args, **kwargs):
        """ Initializes the general class """
        if kwargs:
            for key, value in kwargs.items():
                if key == "created_at" or key == "updated_at":
                    # accept naive or ISO-formatted datetimes; assume UTC for
                    # naive inputs
                    try:
                        value = datetime.strptime(
                            value,
                            "%Y-%m-%dT%H:%M:%S.%f"
                        )
                    except (ValueError, TypeError):
                        pass
                    if not isinstance(value, datetime):
                        raise ValueError(f"Invalid datetime value for {key}: {value!r}")
                if key != "__class__":
                    setattr(self, key, value)
            if "id" not in kwargs:
                self.id = str(uuid4())
            if "created_at" not in kwargs:
                self.created_at = datetime.now(timezone.utc)
            if "updated_at" not in kwargs:
                self.updated_at = datetime.now(timezone.utc)
        else:
            self.id = str(uuid4())
            self.created_at = self.updated_at = datetime.now(timezone.utc)

    def __str__(self):
        """
        string representation of object
        """
        return "[{:s}] with identity number: ({:s})\n{}\n{}\n{}".format(
               self.__class__.__name__, self.id, '*' * 75, self.__dict__,
               '*' * 75)
