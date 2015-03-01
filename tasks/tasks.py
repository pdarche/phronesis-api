import json
import datetime
import time

import celery as clry
import pandas as pd
import requests
import fitbit
from sqlalchemy import *
from sqlalchemy.orm import sessionmaker

from settings import settings
from models.user import *
import etl.movesapp as moves

engine = create_engine('postgresql+psycopg2://postgres:Morgortbort1!@localhost/pete')
Session = sessionmaker(bind=engine)
session = Session()
celery = clry.Celery('tasks', broker='amqp://guest@localhost//')
current_services = [
	'moves', 'fitbit', 'withings',
	'open_paths', 'runkeeper'
]
service_backfillers = {
	'moves': backfill_moves_resources
}


def backfill_service(service, user):
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

	if profile:
		# execute the celery task to backfill the data
		service_backfillers[service](profile)
	else:
		return None


def backfill_moves_resources(profile):
	""" Backfills moves resources. """
    resource_types = ['summary', 'activities', 'places', 'storyline']

    for resource_type in resource_types:
    	# this should also be a celery subtask
    	moves.backfill_resource_type(profile, resource_type)


@celery.task
def etl_manager():
	""" Executes service etl management functions for services
	that need to be backfilled and for services who don't
	offer subscribe functionality
	"""
	for service in current_services:
		# This should be a subtask!
		backfill_service(service, user)


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
