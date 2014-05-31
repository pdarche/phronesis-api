import tornado.web
import tornado.gen

import mixins.mixins as mixins
from settings import settings

# from models.object import FitbitActivity
# from models.object import FitbitSleep
# from models.object import FitbitActivity
# from models.object import FitbitBody
# from models.object import FitbitFood

from pymongo import MongoClient
from celery import Celery

import json
import fitbit
import time
import pandas as pd
import itertools

import psycopg2
# import copy

celery = Celery('tasks', broker='amqp://guest@localhost//')

client = MongoClient('localhost', 27017)
db = client.phronesis_dev

conn_string = "host='localhost' dbname='postgres' user='pete' password='Morgortbort1!'"
conn = psycopg2.connect(conn_string)
cursor = conn.cursor()

# class FitbitRequest(tornado.web.RequestHandler, mixins.FitbitMixin):
# 	@tornado.gen.engine
# 	def import_data(self, fitbit):
# 		user_id = fitbit["username"]
# 		access_token = fitbit["access_token"]
# 		member_since = fitbit["user"]["memberSince"]
# 		activities = []
# 		fitbit_features = [
# 			'activities/steps', 'activities/calories', 
# 			'activities/distance', 'activities/floors',
# 			'activities/elevation', 'activities/minutesSedentary', 
# 			'activities/minutesLightlyActive', 'activities/minutesFairlyActive',
# 			'activities/minutesVeryActive', 'sleep/startTime',
# 			'sleep/timeInBed', 'sleep/minutesAsleep',
# 			'sleep/awakeningsCount', 'sleep/minutesAwake',
# 			'sleep/minutesToFallAsleep', 'sleep/minutesAfterWakeup',
# 			'sleep/efficiency', 'body/weight', 'body/bmi',
# 			'body/fat', 'body/fat', 
# 		]

		# for feature in fitbit_features:
		# response = yield tornado.gen.Task(
		# 	self.fitbit_request,
		# 	'/user/-/activities/steps/date/2011-01-01/today',
		# 	access_token = access_token,
		# 	user_id = user_id
		# )
		# activities.append(respones)
		

# def fetch_resource(f, user_id, resource):
# 	res = f.time_series(
# 		resource,
# 		user_id=user_id, 
# 		base_date="2010-12-01",
# 		end_date="today"
# 	)
# 	key = resource.replace("/", "-")
# 	time.sleep(.1)
# 	return res[key]


# def daily_activity(tup):
# 	doc = copy.deepcopy(FitbitActivity)
# 	doc['date'] = tup[0]['dateTime']
# 	doc['steps'] = tup[0]['value']
# 	doc['calories'] = tup[1]['value']
# 	doc['distance'] = tup[2]['value']
# 	doc['floors'] = tup[3]['value']
# 	doc['elevation'] = tup[4]['value']
# 	doc['minutesSedentary'] = tup[5]['value']
# 	doc['minutesLightlyActive'] = tup[6]['value']
# 	doc['minutesFairlyActive'] = tup[7]['value']
# 	doc['minutesVeryActive'] = tup[8]['value'] 
# 	return doc


# def daily_sleep(tup):
# 	doc = copy.deepcopy(FitbitSleep)
# 	doc['date'] = tup[0]['dateTime']
# 	doc['startTime'] = tup[0]['value']
# 	doc['timeInBed'] = tup[1]['value']
# 	doc['minutesAsleep'] = tup[2]['value']
# 	doc['awakeningsCount'] = tup[3]['value']
# 	doc['minutesAwake'] = tup[4]['value']
# 	doc['minutesToFallAsleep'] = tup[5]['value']
# 	doc['minutesAfterWakeup'] = tup[6]['value']
# 	doc['efficiency'] = tup[7]['value']
# 	return doc

# def daily_body(tup):
# 	doc = copy.deepcopy(FitbitBody)
# 	doc['date'] = tup[0]['dateTime']
# 	doc['weight'] = tup[0]['value']
# 	doc['bmi'] = tup[1]['value']
# 	doc['fat'] = tup[2]['value']
# 	return doc

# def daily_food(tup):
# 	doc = copy.deepcopy(FitbitFood)
# 	doc['date'] = tup[0]['dateTime']
# 	doc['caloriesIn]'] = tup[0]['value']
# 	doc['water'] = tup[1]['value']
# 	return doc


def delete_fitbit_records(table, dates):
    for date in dates:
        sql = "DELETE FROM %s WHERE timestamp::date = '%s'" % (table, date)
        cursor.execute(sql, values)
        conn.commit()        

###### FLATTEN FITBIT API RESPONSES ######

mealTypeMapping = {
    "1": "breakfast",
    "2": "morning snack",
    "3": "lunch",
    "4": "afternoon snack",
    "5": "dinner",
    "7": "anytime"
}

def flatten_food(food):
    mealTypeId = food['loggedFood']['mealTypeId']
    meal = mealTypeMapping[str(mealTypeId)]
    
    return {
        'favorite': food['isFavorite'],
        'timestamp': food['logDate'],
        'amount': food['loggedFood']['amount'],
        'brand': food['loggedFood']['brand'],
        'calories': food['loggedFood']['calories'],
        'mealTypeId': food['loggedFood']['mealTypeId'],
        'meal': meal,
        'name': food['loggedFood']['name'],
        'unit': food['loggedFood']['unit']['name'],
        'total_calories': food['nutritionalValues']['calories'],
        'carbs': food['nutritionalValues']['carbs'],
        'fat': food['nutritionalValues']['fat'],
        'fiber': food['nutritionalValues']['fiber'],
        'protein': food['nutritionalValues']['protein'],
        'sodium': food['nutritionalValues']['sodium']
    }

def flatten_sleep(sleep):
    del sleep['minuteData']
    sleep['startTime'] = pd.to_datetime(sleep['startTime'])
    sleep['timestamp'] = pd.to_datetime(sleep['startTime'])
    return sleep

def flatten_activity(activity):
    activity['distance'] = activity['distances'][0]['distance']
    del activity['distances']
    return activity

#### FETCH FITBIT RESOURCES ####

def fitbit_activities(dates):
    """ fetches the activity records for a list of dates
    and returns a Pandas DataFrame with 
    a food record for each logged food 
    
    dates -- list of date strings in the format %Y-%m-%d
    """
    
    f = fitbit.FitBit()
    token = 'oauth_token_secret=%s&oauth_token=%s' % \
        (settings['fitbit_access_secret'], settings['fitbit_access_key'])
    
    records = []
    for date in dates:
        activities = f.ApiCall(token, apiCall='/1/user/-/activities/date/%s.json' % date)
        activities = json.loads(activities)
        activities['summary']['timestamp'] = pd.to_datetime(date)
        records.append(activities['summary'])
        
    activities = [flatten_activity(activity) for activity in records]
    return pd.DataFrame(activities)


def fitbit_sleeps(dates):
    """ fetches the sleep records for a list of dates
    and returns a Pandas DataFrame with 
    a food record for each logged food 
    
    dates -- list of date strings in the format %Y-%m-%d
    """
    
    f = fitbit.FitBit()
    token = 'oauth_token_secret=%s&oauth_token=%s' % \
        (settings['fitbit_access_secret'], settings['fitbit_access_key'])
    
    records = []
    for date in dates:
        sleeps = f.ApiCall(token, apiCall='/1/user/-/sleep/date/%s.json' % date)
        # NOTE: the date should be added to the record here!
        records.append(sleeps)
        
    sleeps = [[flatten_sleep(sleep) for sleep in json.loads(record)['sleep']] \
                  for record in records if len(record) > 0]
    sleep_records = list(itertools.chain(*sleeps))
    return pd.DataFrame(sleep_records)


def fitbit_foods(dates):
    """ fetches the food records for a list of dates
    and returns a Pandas DataFrame with 
    a food record for each logged food 
    
    dates -- list of date strings in the format %Y-%m-%d
    """
    
    f = fitbit.FitBit()
    token = 'oauth_token_secret=%s&oauth_token=%s' % \
        (settings['fitbit_access_secret'], settings['fitbit_access_key'])
    
    records = []
    for date in dates:
        foods = f.ApiCall(token, apiCall='/1/user/-/foods/log/date/%s.json' % date)
        records.append(foods)        

    foods = [[flatten_food(food) for food in json.loads(record)['foods']] for record in records]
    food_records = list(itertools.chain(*foods))
    return pd.DataFrame(food_records)


#### INSERTS FLAT FITBIT RECORDS INTO DB ####

def insert_fitbit_activity_records(records):
    """ inserts a collection of FitBit resource
    records into the database

    records -- dictionary of Fitbt activity records
    """
    for row in records:
        values = (
            row['activeScore'], row['activityCalories'], 
            row['caloriesBMR'], row['caloriesOut'], 
            row['distance'], row['elevation'],
            row['floors'], row['marginalCalories'], 
            row['lightlyActiveMinutes'], row['fairlyActiveMinutes'], 
            row['sedentaryMinutes'], row['veryActiveMinutes'],
            row['steps'], row['timestamp']
        ) 
        sql = """INSERT INTO fitbit_activity
                (active_score, activity_calories, 
                calories_bmr, calories_out, distance,
                elevation, floors, marginal_calories,
                minutes_lightly_active, minutes_fairly_active,
                minutes_sedentary, minutes_very_active,
                steps, timestamp)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 
                %s, %s, %s, %s, %s, %s)"""
        cursor.execute(sql, values)
        conn.commit()


def insert_fitbit_food_records(records):
    """ inserts a collection of Fitbit resource
    records into the database

    records -- dictionary of Fitbt food records
    """
    for row in records:
        values = (
            row['amount'], row['brand'], row['calories'], 
            row['carbs'], row['fat'], row['favorite'],
            row['fiber'], row['meal'], row['mealTypeId'], 
            row['name'], row['protein'], row['sodium'], 
            row['timestamp'], row['total_calories'], row['unit']
        ) 
        sql = """INSERT INTO fitbit_food 
                (amount, brand, calories, 
                carbs, fat, favorite, fiber, 
                meal, meal_type_id, name, protein, 
                sodium, timestamp, total_calories, unit) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 
                %s, %s, %s, %s, %s, %s, %s)"""
        cursor.execute(sql, values)
        conn.commit()


def insert_fitbit_sleep_records(records):
    """ inserts a collection of FitBit resource
    records into the database

    records -- dictionary of Fitbt sleep records
    """	
    for row in records:
        values = (
            row['awakeCount'], row['awakeDuration'], 
            row['awakeningsCount'], row['duration'], 
            row['efficiency'], row['isMainSleep'], 
            row['logId'], row['minutesAfterWakeup'], 
            row['minutesAsleep'], row['minutesAwake'], 
            row['minutesToFallAsleep'], row['restlessCount'], 
            row['restlessDuration'], row['startTime'], 
            row['timeInBed'], row['timestamp']
        ) 
        sql = """INSERT INTO fitbit_sleep 
                (awake_count, awake_duration, awakenings_count, 
                duration, efficiency, is_main_sleep, log_id, 
                minutes_after_wakeup, minutes_asleep, minutes_awake,
                minutes_to_fall_asleep, restless_count,
                restless_duration, start_time, time_in_bed, timestamp) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 
                %s, %s, %s, %s, %s, %s, %s, %s)"""
        cursor.execute(sql, values)
        conn.commit()



def sleep_processor(update):
	""" takes an update record from the FitBit
		subscription post, deletes the records
		for the date of update for resources 
		of the given type, fetches the given 
		resource for the given day from the 
		FitBit api and then inserts the resulting
		records into the db

		update -- an update dict from the FitBit Api

	"""
	# delete the sleep records for the given date
	print "deleting record for date %s " % update['date']
	delete_fitbit_records('fitbit_sleep', [update['date']])
	# create the food records for the given date
	print "fetching records for date %s " % update['date']
	sleep_records = fitbit_sleeps([update['date']]).to_dict(outtype='records')
	# insert the new records
	print "inserting new records for date %s " % update['date']
	insert_fitbit_sleep_records(sleep_records)
	# set the update notification records to 'used'
	print "removing update notification record"
	db.fitbit_test.remove({'_id': update['_id']})

    
def activities_processor(update):
	""" takes an update record from the FitBit
		subscription post, deletes the records
		for the date of update for resources 
		of the given type, fetches the given 
		resource for the given day from the 
		FitBit api and then inserts the resulting
		records into the db

		update -- an update dict from the FitBit Api

	"""	
	# delete the activity records for the given date
	print "deleting activity record for date %s " % update['date']
	delete_fitbit_records('fitbit_activity', [update['date']])
	# create the food records for the given date
	print "fetching records for date %s " % update['date']
	activity_records = fitbit_activities([update['date']]).to_dict(outtype='records')
	# insert the new records
	print "inserting new records for date %s " % update['date']
	insert_fitbit_activity_records(activity_records)
	# set the update notification records to 'used'
	print "removing update notification record"
	db.fitbit_test.remove({'_id': update['_id']})


def foods_processor(collectionType, date):
	""" takes an update record from the FitBit
		subscription post, deletes the records
		for the date of update for resources 
		of the given type, fetches the given 
		resource for the given day from the 
		FitBit api and then inserts the resulting
		records into the db

		update -- an update dict from the FitBit Api

	"""	
	# delete the food records for the given date
	print "deleting food record for date %s " % date
	delete_fitbit_records('fitbit_food', [date])
	# create the food records for the given date
	print "fetching records for date %s " % date
	food_records = fitbit_foods([date]).to_dict(outtype='records')
	# insert the new records
	print "inserting new records for date %s " % date
	insert_fitbit_food_records(food_records)
	# set the update notification records to 'used'
	# print "removing update notification record"
	# db.fitbit_test.remove({'_id': update['_id']})


##### CELERY TASKS #####
@celery.task
def add(x, y):
    return x + y

@celery.task
def celtest(collectionType, date):
    foods_processor(collectionType, date)
    return "%s, %s" % (collectionType, date)

@celery.task
def fetch_fitbit(resources):
	for resource in resources:
	    if resource['collectionType'] == 'foods':
	        foods_processor(p)
	    elif resource['collectionType'] == 'activities':
	        activities_processor(p)
	    elif resource['collectionType'] == 'sleep':
	        sleep_processor(p)
	    time.sleep(.25)


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

	food = [
		'foods/log/caloriesIn', 'foods/log/water'
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
	food_records = zip(*[fetch_resource(f, access_token['encoded_user_id'], resource) for resource in food])
	food_records = [daily_food(tup) for tup in food_records]

	db.activities.insert(activity_records)
	db.sleep.insert(sleep_records)
	db.body.insert(body_records)
	db.food.insert(food_records)
	
	return "success"


