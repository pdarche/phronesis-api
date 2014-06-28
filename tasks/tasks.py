import tornado.web
import tornado.gen
import mixins.mixins as mixins
from settings import settings
import psycopg2
from celery import Celery
import json
import fitbit
import datetime
import time
import numpy as np
import pandas as pd
import itertools
import requests


celery = Celery('tasks', broker='amqp://guest@localhost//')

class FitbitFetchResource(object):
	def __init__(self):
		# self.conn_string = "host='localhost' dbname='postgres' user='pete' password='Morgortbort1!'"
		self.conn_string = "host='localhost' dbname='pete' user='postgres' password='Morgortbort1!'"
		self.conn = psycopg2.connect(self.conn_string)
		self.cursor = self.conn.cursor()

	def delete_fitbit_records(self, table, dates):
	    for date in dates:
			try:
				sql = "DELETE FROM %s WHERE timestamp::date = '%s'" % (table, date)
				self.cursor.execute(sql)
				self.conn.commit()
			except:
				# REFACTOR: this should be logged
				pass

	def find_first_record_date(self, table):
		""" finds the date of the last record for a user.
			for a given table.  If no record is found returns
			the current date

			table -- resource table name string
		"""
		try: 
			sql = """SELECT timestamp::date FROM %s 
						ORDER BY timestamp::date LIMIT 1""" % table
			self.cursor.execute(sql)			
			last_record_date = self.cursor.fetchone()

			if last_record_date is None:
				return datetime.datetime.now()
			else:
				return last_record_date[0]

		except Exception, e:
			print e

	def date_range(self, base_date, num_days):
		return [(base_date - datetime.timedelta(days=x)).strftime('%Y-%m-%d') \
					for x in range(0, num_days)]


class FitbitFetchFood(FitbitFetchResource):
	def __init__(self):
		super(FitbitFetchFood, self).__init__()
		self.mealTypeMapping = {
		    "1": "breakfast",
		    "2": "morning snack",
		    "3": "lunch",
		    "4": "afternoon snack",
		    "5": "dinner",
		    "7": "anytime"
		}

	def flatten_food(self, food):
		if type(food) == dict:
			mealTypeId = food['loggedFood']['mealTypeId']
			meal = self.mealTypeMapping[str(mealTypeId)]
		    
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
				'total_calories': food['nutritionalValues']['calories'] if 'nutritionalValues' in food else 0,
			    'carbs': food['nutritionalValues']['carbs'] if 'nutritionalValues' in food else 0,
			    'fat': food['nutritionalValues']['fat'] if 'nutritionalValues' in food else 0,
			    'fiber': food['nutritionalValues']['fiber'] if 'nutritionalValues' in food else 0,
			    'protein': food['nutritionalValues']['protein'] if 'nutritionalValues' in food else 0,
			    'sodium': food['nutritionalValues']['sodium'] if 'nutritionalValues' in food else 0
			}
		else:
			return {
			    'favorite': None, 'timestamp': food, 'amount': 0,
			    'brand': None, 'calories': 0,'mealTypeId': 0, 
			    'meal': None,'name': None, 'unit': None, 'total_calories': 0,
			    'carbs': 0, 'fat': 0, 'fiber':  0, 'protein': 0,'sodium':  0
			}

	def fitbit_foods(self, dates):
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
	    	print "fetching date %s" % date 
	        foods = f.ApiCall(token, apiCall='/1/user/-/foods/log/date/%s.json' % date)
	        foods_dict = json.loads(foods)['foods']
	        if len(foods_dict) > 0:
	        	records.append(foods_dict)
	        else:
	        	records.append([date])
	        time.sleep(.01)

	    foods = [[self.flatten_food(food) for food in record] for record in records]
	    food_records = list(itertools.chain(*foods))
	    return pd.DataFrame(food_records)

	def insert_fitbit_food_records(self, records):
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
	        self.cursor.execute(sql, values)
	        self.conn.commit()


	def foods_processor(self, dates):
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
		self.delete_fitbit_records('fitbit_food', dates)
		# create the food records for the given date
		food_records = self.fitbit_foods(dates).to_dict(outtype='records')
		# insert the new records
		self.insert_fitbit_food_records(food_records)
		#close the connection
		self.conn.close()


class FitbitFetchSleep(FitbitFetchResource):
	def __init__(self):
		super(FitbitFetchSleep, self).__init__()

	# def delete_fitbit_records(self, table, dates):
	#     for date in dates:
	#         sql = "DELETE FROM %s WHERE timestamp::date = '%s'" % (table, date)
	#         self.cursor.execute(sql)
	#         self.conn.commit()

	def flatten_sleep(self, sleep):		
		if type(sleep) == dict:			
			sleep_rec = sleep
			del sleep_rec['minuteData']
			sleep_rec['startTime'] = pd.to_datetime(sleep_rec['startTime'])
			sleep_rec['timestamp'] = pd.to_datetime(sleep_rec['startTime'])
		else:
			sleep_rec = {
				'logId': None, 'isMainSleep': None, 'minutesToFallAsleep': None, 'awakeningsCount': None, 
				'minutesAwake': None, 'timeInBed': None, 'minutesAsleep': None,
				'awakeDuration': None, 'efficiency': None, 'startTime': pd.to_datetime(sleep),
				'restlessCount': 11, 'duration': None, 'restlessDuration': None,
				'awakeCount': None, 'minutesAfterWakeup': None, 'timestamp': pd.to_datetime(sleep)
			}
		return sleep_rec


	def fitbit_sleeps(self, dates):
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
	        print "fetching date %s" % date 
	        sleeps = f.ApiCall(token, apiCall='/1/user/-/sleep/date/%s.json' % date)
	        json_sleeps = json.loads(sleeps)
	        sleeps_arr = json_sleeps['sleep'] if json_sleeps.has_key('sleep') else []
	        if len(sleeps_arr) > 0:
	        	records.append(sleeps_arr)
	        else:
	        	records.append([date])
	        
	    sleeps = [[self.flatten_sleep(sleep) for sleep in record] for record in records]
	    sleep_records = list(itertools.chain(*sleeps))
	    return pd.DataFrame(sleep_records)

	def insert_fitbit_sleep_records(self, records):
	    """ inserts a collection of Fitbit resource
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
	        self.cursor.execute(sql, values)
	        self.conn.commit()

	def sleep_processor(self, dates):
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
		self.delete_fitbit_records('fitbit_sleep', dates)
		# create the food records for the given date
		sleep_records = self.fitbit_sleeps(dates)
		sleep_records = sleep_records.where((pd.notnull(sleep_records)), None).to_dict(outtype='records')
		# insert the new records
		self.insert_fitbit_sleep_records(sleep_records)

## NOTE: flattend activity will probably be a problem
## cuz it doesn't take into account other 
## logged activities

class FitbitFetchActivities(FitbitFetchResource):
	def __init__(self):
		super(FitbitFetchActivities, self).__init__()

	def delete_fitbit_records(self, table, dates):
	    # maybe put another cursor here?
	    for date in dates:
	        sql = "DELETE FROM %s WHERE timestamp::date = '%s'" % (table, date)
	        self.cursor.execute(sql)
	        self.conn.commit()

	def flatten_activity(self, activity):
	    activity['distance'] = activity['distances'][0]['distance']
	    del activity['distances']
	    return activity

	def fitbit_activities(self, dates):
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
	    	print "fetching date %s" % date
	        activities = f.ApiCall(token, apiCall='/1/user/-/activities/date/%s.json' % date)
	        activities = json.loads(activities)
	        activities['summary']['timestamp'] = pd.to_datetime(date)	        
	        records.append(activities['summary'])
	        
	    activities = [self.flatten_activity(activity) for activity in records]
	    return pd.DataFrame(activities)
	    

	def insert_fitbit_activity_records(self, records):
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
	        self.cursor.execute(sql, values)
	        self.conn.commit()


	def activities_processor(self, dates):
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
		self.delete_fitbit_records('fitbit_activity', dates)
		# create the food records for the given date
		activity_records = self.fitbit_activities(dates).to_dict(outtype='records')
		# insert the new records
		self.insert_fitbit_activity_records(activity_records)


##### CELERY TASKS #####
@celery.task
def add(x, y):
    return x + y

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
		notify_pete('foods')

	if pd.to_datetime(base_date_activity) > signup_date:
		print "fetching activities!"
		activities = FitbitFetchActivities()
		activities.activities_processor(activity_dates)
	else:	
		notify_pete('activities')

	if pd.to_datetime(base_date_sleep) > signup_date:
		print "fetching sleeps!"
		sleep = FitbitFetchSleep()
		sleep.sleep_processor(sleep_dates)
	else:
		notify_pete('sleep')

	time.sleep(.25)
	return "success!"	


def notify_pete(collectionType):
	return requests.post(
		settings['mailgun_post_url'],
		auth=("api", settings['mailgun_api_key']),
		data={"from": "Pete <pdarche@gmail.com>",
			"to": ["pdarche@gmail.com"],
			"subject": "Fitbit %s import complete",
			"text": "Fitbit %s import complete"}) % (collectionType, collectionType)


# import_fitbit(5)

