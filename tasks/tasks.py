import tornado.web
import tornado.gen
import mixins.mixins as mixins
from pymongo import MongoClient
from celery import Celery

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

		# db.fitbit_test.insert({"test":"testing this shit"})

		# for feature in fitbit_features:
		response = yield tornado.gen.Task(
			self.fitbit_request,
			'/user/-/activities/steps/date/2011-01-01/today',
			access_token = access_token,
			user_id = user_id
		)
		# activities.append(respones)
		

@celery.task
def add(x, y):
    return x + y


@celery.task
def import_fitbit(fitbit):
	fb = FitbitRequest()
	fb.import_data(fitbit)
	return "done"


