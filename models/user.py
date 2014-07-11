from sqlalchemy import *
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

metadata = MetaData()
Base = declarative_base(metadata=metadata)
# engine = create_engine('postgresql+psycopg2://postgres:Morgortbort1!@localhost/pete')

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(String)
    email_address = Column(String)
    password = Column(String)
    member_since = Column(DateTime)
    # timezone = Column(String)
    # utc_offset = Column(Integer)
    services = relationship("Service")


class Service(Base):
    __tablename__ = 'user_services'

    id = Column(Integer, primary_key=True)
    parent_id = Column(Integer, ForeignKey('users.id'))
    name = Column(String)
    identifier = Column(String)
    # connected_at = Column(DateTime)
    start_date = Column(String)
    access_key = Column(String)
    access_secret = Column(String)
    token_type = Column(String)
    token_expiration = Column(Integer)
    refresh_token = Column(String)
    timezone = Column(String)
    utc_offset = Column(Integer)

# Base.metadata.create_all(engine)


