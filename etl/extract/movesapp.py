""" Module for extracting Moves data for a
	Phronesis user
"""

import datetime

from pymongo import MongoClient
from sqlalchemy import *
from sqlalchemy.orm import sessionmaker
import moves as mvs

from models.user import *

client = MongoClient('localhost', 27017)
db = client.phronesis_dev

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



# TODO: Review and remove! This is depracated and won't be used in the future.
class MovesStoryline():
	""" Class for importing Moves storyline data """
	def _on_data(self, data):
		storyline = data[0]
		self.insert_segments(storyline['segments'])

	def insert_segments(self, segments):
		segment_objects = [self.create_moves_segment(s) \
							for s in segments]
		for obj in segment_objects:
			session.add(obj)
		session.commit()

	def create_moves_segment(self, segment):
		return MovesSegment(
				parent_id = 1, # NOTE: this will have to change!
				type = segment['type'],
				start_time = segment['startTime'],
				end_time = segment['endTime'],
				last_update = segment['lastUpdate'],
				place = self.create_moves_place(segment['place']) \
					if segment.has_key('place') else None,
				activities = self.create_moves_activities(segment['activities']) \
					if segment.has_key('activities') else []
			)

	def create_moves_place(self, place):
		return MovesPlace(
				type = place['type'],
				place_id = place['id'],
				lat = place['location']['lat'],
				lon = place['location']['lon']
			)

	def create_moves_activities(self, activities):
		return [self.create_moves_activity(activity) \
					for activity in activities]

	def create_moves_activity(self, activity):
		return MovesActivity(
				distance =  activity['distance'],
				group = activity['group'],
				trackpoints = self.create_moves_trackpoints(activity['trackPoints']) \
					if activity.has_key('trackPoints') else [],
				calories = activity['calories'] \
					if activity.has_key('calories')	else None,
				manual = activity['manual'],
				steps = activity['steps'] \
					if activity.has_key('steps') else None,
				start_time = activity['startTime'],
				activity = activity['activity'],
				duration = activity['duration'],
				end_time = activity['endTime']
			)




