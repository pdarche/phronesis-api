""" ```manager``` module contains functions for managing ETL tasks """

from sqlalchemy import *
from sqlalchemy.orm import sessionmaker

import pymongo

from models.user import *
from etl import movesapp as moves

client = pymongo.MongoClient('localhost', 27017)
db = client.phronesis_dev

engine = create_engine('postgresql+psycopg2://postgres:Morgortbort1!@localhost/pete')
Session = sessionmaker(bind=engine)
session = Session()

user = session.query(User).filter_by(email_address='pdarche@gmail.com').first()
current_services = [
	'moves', 'fitbit', 'withings',
	'open_paths', 'runkeeper'
]

def backfill_status(service, user):
	""" Determines whether data should continue to be
	backfilled for a given service

	Args:
		service: String of the service to be checked
		user: Dict of the Phronesis user

	"""
	if service not in current_services:
		raise ValueError('Invalid Moves resource.')

	profile = db.profiles.find_one(
		{'service': service, 'phro_user_id': user['id']})


def backfill_serivice(service, profile):
	""" Backfills """
	pass

