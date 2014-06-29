from sqlalchemy import *
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

metadata = MetaData()
Base = declarative_base(metadata=metadata)

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(String)
    email_address = Column(String)
    password = Column(String)
    services = relationship("Service")


class Service(Base):
    __tablename__ = 'user_services'

    id = Column(Integer, primary_key=True)
    parent_id = Column(Integer, ForeignKey('users.id'))
    service_name = Column(String)
    service_identifier = Column(String)
    access_key = Column(String)
    access_secret = Column(String)







