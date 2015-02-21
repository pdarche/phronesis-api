""" ```manager``` module contains functions for managing ETL tasks """

from sqlalchemy import *
from sqlalchemy.orm import sessionmaker

import pymongo

from models.user import *

client = pymongo.MongoClient('localhost', 27017)
db = client.phronesis_dev

engine = create_engine('postgresql+psycopg2://postgres:Morgortbort1!@localhost/pete')
Session = sessionmaker(bind=engine)
session = Session()

user = session.query(User).filter_by(email_address='pdarche@gmail.com').first()


def backfill_status(service, profile):
	""" Determines whether data should continue to be
	backfilled for a given service
	"""
	db.profiles.find_one()


def backfill_serivice(service, profile):
	""" Backfills """