import json
import datetime
import time

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
		pass

	if pd.to_datetime(base_date_activity) > signup_date:
		print "fetching activities!"
		activities = FitbitFetchActivities()
		activities.activities_processor(activity_dates)
	else:
		pass

	if pd.to_datetime(base_date_sleep) > signup_date:
		print "fetching sleeps!"
		sleep = FitbitFetchSleep()
		sleep.sleep_processor(sleep_dates)
	else:
		pass

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

	for date in dates:
		request_url = 'user/storyline/daily/%s' % date
		data = Moves.api(request_url, 'GET', params={'access_token': access_token}).json()

		m._on_data(data)
		time.sleep(.25)

	return "suceess"
