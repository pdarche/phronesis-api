import tornado.web
import tornado.gen
import mixins.mixins as mixins
from settings import settings
from models.object import FitbitActivity
from models.object import FitbitSleep
from models.object import FitbitActivity
from models.object import FitbitBody

from pymongo import MongoClient
from celery import Celery

import json
import fitbit
import time
import copy

celery = Celery('tasks', broker='amqp://guest@localhost//')

client = MongoClient('localhost', 27017)
db = client.phronesis_dev

class FitbitRequest(tornado.web.RequestHandler, mixins.FitbitMixin):
	@tornado.gen.engine
	def import_data(self, fitbit):
		user_id = fitbit["username"]
		access_token = fitbit["access_token"]
		member_since = fitbit["user"]["memberSince"]
		activities = []
		fitbit_features = [
			'activities/steps', 'activities/calories', 
			'activities/distance', 'activities/floors',
			'activities/elevation', 'activities/minutesSedentary', 
			'activities/minutesLightlyActive', 'activities/minutesFairlyActive',
			'activities/minutesVeryActive', 'sleep/startTime',
			'sleep/timeInBed', 'sleep/minutesAsleep',
			'sleep/awakeningsCount', 'sleep/minutesAwake',
			'sleep/minutesToFallAsleep', 'sleep/minutesAfterWakeup',
			'sleep/efficiency', 'body/weight', 'body/bmi',
			'body/fat', 'body/fat', 
		]

		# for feature in fitbit_features:
		# response = yield tornado.gen.Task(
		# 	self.fitbit_request,
		# 	'/user/-/activities/steps/date/2011-01-01/today',
		# 	access_token = access_token,
		# 	user_id = user_id
		# )
		# activities.append(respones)
		

def fetch_resource(f, user_id, resource):
	res = f.time_series(
		resource,
		user_id=user_id, 
		base_date="2010-12-01",
		end_date="today"
	)
	key = resource.replace("/", "-")
	time.sleep(.1)
	return res[key]


def daily_activity(tup):
	doc = copy.deepcopy(FitbitActivity)
	doc['date'] = tup[0]['dateTime']
	doc['steps'] = tup[0]['value']
	doc['calories'] = tup[1]['value']
	doc['distance'] = tup[2]['value']
	doc['floors'] = tup[3]['value']
	doc['elevation'] = tup[4]['value']
	doc['minutesSedentary'] = tup[5]['value']
	doc['minutesLightlyActive'] = tup[6]['value']
	doc['minutesFairlyActive'] = tup[7]['value']
	doc['minutesVeryActive'] = tup[8]['value'] 
	return doc


def daily_sleep(tup):
	doc = copy.deepcopy(FitbitSleep)
	doc['date'] = tup[0]['dateTime']
	doc['startTime'] = tup[0]['value']
	doc['timeInBed'] = tup[1]['value']
	doc['minutesAsleep'] = tup[2]['value']
	doc['awakeningsCount'] = tup[3]['value']
	doc['minutesAwake'] = tup[4]['value']
	doc['minutesToFallAsleep'] = tup[5]['value']
	doc['minutesAfterWakeup'] = tup[6]['value']
	doc['efficiency'] = tup[7]['value']
	return doc


def daily_body(tup):
	doc = copy.deepcopy(FitbitBody)
	doc['date'] = tup[0]['dateTime']
	doc['weight'] = tup[0]['value']
	doc['bmi'] = tup[1]['value']
	doc['fat'] = tup[2]['value']
	return doc


@celery.task
def add(x, y):
    return x + y


@celery.task
def import_fitbit(access_token):
	activities = [
		'activities/steps', 'activities/calories', 
		'activities/distance', 'activities/floors',
		'activities/elevation', 'activities/minutesSedentary', 
		'activities/minutesLightlyActive', 'activities/minutesFairlyActive',
		'activities/minutesVeryActive'
	]

	sleep = [
		'sleep/startTime', 'sleep/timeInBed', 'sleep/minutesAsleep',
		'sleep/awakeningsCount', 'sleep/minutesAwake',
		'sleep/minutesToFallAsleep', 'sleep/minutesAfterWakeup',
		'sleep/efficiency'
	]

	body = [
		'body/weight', 'body/bmi',
		'body/fat'
	]

	f = fitbit.Fitbit(
			settings['fitbit_consumer_key'], 
			settings['fitbit_consumer_secret'],
			user_key=access_token['key'],
			user_secret=access_token['secret']
		)

	activity_records = zip(*[fetch_resource(f, access_token['encoded_user_id'], resource) for resource in activities])
	activity_records = [daily_activity(tup) for tup in activity_records]
	sleep_records = zip(*[fetch_resource(f, access_token['encoded_user_id'], resource) for resource in sleep])
	sleep_records = [daily_sleep(tup) for tup in sleep_records]
	body_records = zip(*[fetch_resource(f, access_token['encoded_user_id'], resource) for resource in body])
	body_records = [daily_body(tup) for tup in body_records]

	db.activities.insert(activity_records)
	db.sleep.insert(sleep_records)
	db.body.insert(body_records)
	return "success"


