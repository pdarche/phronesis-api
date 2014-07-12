from sqlalchemy import *
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

metadata = MetaData()
Base = declarative_base(metadata=metadata)
engine = create_engine('postgresql+psycopg2://postgres:Morgortbort1!@localhost/pete')

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


class MovesSegment(Base):
	__tablename__ = 'moves_segments'

	id = Column(Integer, primary_key=True)
	parent_id = Column(Integer, ForeignKey('users.id'))
	type = Column(String)
	start_time = Column(DateTime(timezone=True))
	end_time = Column(DateTime(timezone=True))
	last_update = Column(DateTime(timezone=True))
	place = relationship('MovesPlace', uselist=False, backref="moves_segments")
	activities = relationship('MovesActivity')


class MovesPlace(Base):
	__tablename__ = 'moves_places'

	id = Column(Integer, primary_key=True)
	parent_id = Column(Integer, ForeignKey('moves_segments.id'))
	type = Column(String)
	place_id = Column(Integer)
	lat = Column(Float)
	lon = Column(Float)


class MovesActivity(Base):
	__tablename__ = 'moves_activities'

	id = Column(Integer, primary_key=True)
	parent_id = Column(Integer, ForeignKey('moves_segments.id'))
	distance = Column(Integer)
	group = Column(String)
	trackpoints = relationship('MovesTrackPoint')
	calories = Column(Integer)
	manual = Column(Boolean)
	steps = Column(Integer)
	start_time = Column(DateTime(timezone=True))
	activity = Column(String)
	duration = Column(Integer)
	end_time = Column(DateTime(timezone=True))


class MovesTrackPoint(Base):
	__tablename__ = 'moves_track_points'

	id = Column(Integer, primary_key=True)
	parent_id = Column(Integer, ForeignKey('moves_activities.id'))
	lat = Column(Float)
	lon = Column(Float)
	time = Column(DateTime(timezone=True))


# Base.metadata.create_all(engine)


