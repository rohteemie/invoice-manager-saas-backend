#!/usr/bin/env python3
""" Base class config for CityWide."""
from sqlalchemy import Column, String, DateTime
from sqlalchemy.orm import declarative_base
from datetime import datetime
from uuid import uuid4
# import config


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
    updated_at = Column(DateTime, nullable=False, default=datetime.now)

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

    # def save(self):
    #     """ update 'update time' and saves instance to database """
    #     self.updated_at = datetime.now()
    #     config.storage.new(self)
    #     config.storage.save()

    # def to_dict(self):
    #     """
    #     returns dictionary of user object
    #     """
    #     my_dict = dict(self.__dict__)
    #     my_dict["created_at"] = self.created_at.isoformat()
    #     my_dict["updated_at"] = self.updated_at.isoformat()
    #     if '_sa_instance_state' in my_dict.keys():
    #         del my_dict['_sa_instance_state']
    #     if 'password' in my_dict.keys():
    #         del my_dict['password']
    #     if 'NIN' in my_dict.keys():
    #         del my_dict['NIN']
    #     return my_dict

    # def delete(self):
    #     """ deletes instance """
    #     config.storage.delete(self)

    # def filter_data(self, entity: str, filter_condition: dict = None):
    #     if entity is None:
    #         return None
    #     if not Database._validate_entity(entity):
    #         return None
    #     entity = self._entity_mapping.get(entity.lower())
    #     try:
    #         query = self.__session.query(entity)
    #         query = query.filter_by(**filter_condition)
    #         data = query.first()
    #         if data is None:
    #             return False
    #         else:
    #             return True
    #     except Exception as e:
    #         return False

    # def data_lock(self, entity: str=None, filter_condition: dict=None):
    #     if entity is None:
    #         return None
    #     if not Database._validate_entity(entity):
    #         return None
    #     entity = self._entity_mapping.get(entity.lower())
    #     try:
    #         data = self.__session.query(entity).filter_by(**filter_condition)
    # .with_lockmode("update").first()#.to_dict()
    #         if data is not None:
    #             return data
    #     except Exception as e:
    #         self.__session.rollback()
    #         return None

    # def rollback(self):
    #     self.__session.rollback()

    # def get_by_field(self, field, value, entity: str=None):
    #     if not Database._validate_entity(entity):
    #         return False
    #     entity = self._entity_mapping[entity.lower()]
    #     data = self.__session.query(
    #         entity).filter_by(**{field: value}).first()
    #     if data is None and type(data) != 'list':
    #         return None
    #     elif data:
    #         return data




if __name__ == "__main__":
    new_object = Gen_Model()
    print(new_object)
