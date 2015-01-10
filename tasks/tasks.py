import json
import datetime
import time
import itertools

import tornado.web
import tornado.gen
import mixins.mixins as mixins
import psycopg2
import celery as clry
import pandas as pd
import requests
import fitbit
import moves
# TODO: refactor import *
from sqlalchemy import *
from sqlalchemy.orm import sessionmaker
# TODO: refactor import *
from models.user import *
from settings import settings

engine = create_engine('postgresql+psycopg2://postgres:Morgortbort1!@localhost/pete')
Session = sessionmaker(bind=engine)
session = Session()
celery = clry.Celery('tasks', broker='amqp://guest@localhost//')


@celery.task
def celtest(collectionType, date):
	dates = [date]

	if collectionType == 'foods':
		foods = FitbitFetchFood()
		foods.foods_processor(dates)

	elif collectionType == 'activities':
		activities = FitbitFetchActivities()
		activities.activities_processor(dates)

	elif collectionType == 'sleep':
		sleep = FitbitFetchSleep()
		sleep.sleep_processor(dates)

	time.sleep(.25)
	return "%s, %s" % (collectionType, date)


@celery.task
def import_fitbit(offset):
	# Find the signup date of the user
	fb = fitbit.FitBit()
	token = 'oauth_token_secret=%s&oauth_token=%s' % \
		(settings['fitbit_access_secret'], settings['fitbit_access_key'])

	user = json.loads(fb.ApiCall(token, apiCall='/1/user/-/profile.json'))
	signup_date = pd.to_datetime(user['user']['memberSince'])

	# Create the date ranges of resources that will be fetched
	f = FitbitFetchResource()
	base_date_food = f.find_first_record_date('fitbit_food')
	base_date_activity = f.find_first_record_date('fitbit_activity')
	base_date_sleep = f.find_first_record_date('fitbit_sleep')

	food_dates = f.date_range(base_date_food, offset)
	activity_dates = f.date_range(base_date_activity, offset)
	sleep_dates = f.date_range(base_date_sleep, offset)

	# if the signupdate is creater than the
	# last fetch the resources in the date range
	if pd.to_datetime(base_date_food) > signup_date:
		print "fetching foods!"
		foods = FitbitFetchFood()
		foods.foods_processor(food_dates)
	else:
		notify_pete('Fitbit food import complete')

	if pd.to_datetime(base_date_activity) > signup_date:
		print "fetching activities!"
		activities = FitbitFetchActivities()
		activities.activities_processor(activity_dates)
	else:
		notify_pete('Fitbit activities import complete')

	if pd.to_datetime(base_date_sleep) > signup_date:
		print "fetching sleeps!"
		sleep = FitbitFetchSleep()
		sleep.sleep_processor(sleep_dates)
	else:
		notify_pete('Fitbit sleep import complete')

	time.sleep(.25)
	return "success!"


@celery.task
def import_moves():
	m = MovesStoryline()
	moves_service = session.query(Service).filter_by(name='moves', parent_id=1).first()
	access_token = moves_service.access_secret

	Moves = moves.MovesClient(settings['moves_client_id'], settings['moves_client_secret'])
	Moves.access_token = access_token

	# if the date is none, find the earliest date with data
	# if that date is greater than the signup date, fetch the moves data for the day
	start_date = session.query(MovesSegment) \
		    .filter_by(parent_id=1) \
		    .order_by(MovesSegment.start_time) \
		    .first().start_time

	dates = [(start_date - datetime.timedelta(days=offset)) \
				.strftime('%Y%m%d') for offset in range(1,50)]

	print start_date

	for date in dates:
		request_url = 'user/storyline/daily/%s' % date
		data = Moves.api(request_url, 'GET', params={'access_token': access_token}).json()

		m._on_data(data)
		time.sleep(.25)

	return "suceess"


def notify_pete(notification):
	return requests.post(
		settings['mailgun_post_url'],
		auth=("api", settings['mailgun_api_key']),
		data={"from": "Pete <pdarche@gmail.com>",
			"to": ["pdarche@gmail.com"],
			"subject": "%s" % notification,
			"text": "%s"  % notification})


class MovesStoryline():
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


