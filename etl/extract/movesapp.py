"""
	Module for extracting Moves data for a
	Phronesis user
"""
# Standard Lib
import datetime
# MongoDB
from pymongo import MongoClient
# SQL Alchemy
from sqlalchemy import *
from sqlalchemy.orm import sessionmaker
# Moves python wrapper
import moves as mvs
# Phronesis User model
from models.user import *

# Mongo
client = MongoClient('localhost', 27017)
db = client.phronesis_dev

# SQL Alchemy
engine = create_engine('postgresql+psycopg2://postgres:Morgortbort1!@localhost/pete')
Session = sessionmaker(bind=engine)
session = Session()

user = session.query(User).filter_by(email_address='pdarche@gmail.com').first()
moves_profile = db.profiles.find_one({"phro_user_email": user.email_address})
moves = mvs.MovesClient(access_token=moves_profile['access_token']['access_token'])

# NOTE: the Moves API ratelimits at 60 requirest/hour and 2000 requests/day
def update_access_token():
	""" Updates the Phronesis users Moves access token """
	pass


def fetch_summary(date=None):
	""" Fetches a user's Moves summary for a given date """
	if not date:
		date = datetime.datetime.today().strftime('%Y%m%d')

	resource_path = 'user/summary/daily/%s' % date
	return moves.api(resource_path, 'GET').json()


def fetch_activities(date=None):
	""" Fetches a user's Moves activities for a given date """
	if not date:
		date = datetime.datetime.today().strftime('%Y%m%d')

	resource_path = 'user/activities/daily/%s' % date
	return moves.api(resource_path, 'GET').json()


def fetch_places(date=None):
	""" Fetches a user's Moves places for a given date """
	if not date:
		date = datetime.datetime.today().strftime('%Y%m%d')

	resource_path = 'user/places/daily/%s' % date
	return moves.api(resource_path, 'GET').json()


