#!/usr/bin/env python3
""" Base class config For all models """
from sqlalchemy import Column, String, DateTime
from sqlalchemy.orm import declarative_base
from datetime import datetime
from uuid import uuid4


Base = declarative_base()


class Gen_Model:
    """
    Defines all common attributes and methods
    for all other models
    """
    id = Column(String(60), unique=True, nullable=False, primary_key=True,
                index=True
                )
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now,
                        onupdate=datetime.now)

    def __init__(self, *args, **kwargs):
        """ Initializes the general class """
        if kwargs:
            for key, value in kwargs.items():
                if key == "created_at" or key == "updated_at":
                    value = datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%f")
                if key != "__class__":
                    setattr(self, key, value)
            if "id" not in kwargs:
                self.id = str(uuid4())
            if "created_at" not in kwargs:
                self.created_at = datetime.now()
            if "updated_at" not in kwargs:
                self.updated_at = datetime.now()
        else:
            self.id = str(uuid4())
            self.created_at = self.updated_at = datetime.now()

    def __str__(self):
        """
        string representation of object
        """
        return "[{:s}] with identity number: ({:s})\n{}\n{}\n{}".format(
               self.__class__.__name__, self.id, '*' * 75, self.__dict__,
               '*' * 75)
