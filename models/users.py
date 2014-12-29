""" Models for Phronesis User-related classes """

from mongoengine import *
from datetime import datetime

class User(Document):
    username = Column(String)
    email_address = Column(String)
    password = Column(String)
    member_since = Column(DateTime)
    # timezone = Column(String)
    # utc_offset = Column(Integer)
    services = relationship("Service")