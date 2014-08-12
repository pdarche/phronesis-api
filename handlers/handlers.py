import tornado.web
import tornado.gen
import requests
import json
from settings import settings
from pymongo import MongoClient
import pymongo
import time
import datetime
import copy
import re

from bson import objectid
from bson import json_util
from passlib.apps import custom_app_context as pwd_context

from models.user import *
import mixins.mixins as mixins

from tasks.tasks import celtest
from tasks.tasks import import_moves

from sqlalchemy import *
from sqlalchemy.orm import sessionmaker

# Mongo
client = MongoClient('localhost', 27017)
db = client.phronesis_research_papers

# SQL Alchemy
engine = create_engine('postgresql+psycopg2://postgres:Morgortbort1!@localhost/pete')
Session = sessionmaker(bind=engine)
session = Session()


class BaseHandler(tornado.web.RequestHandler):
	def get_current_user(self):
		return self.get_secure_cookie("username")


class MainHandler(BaseHandler):
	@tornado.web.authenticated
	def get(self):
		username = self.get_secure_cookie('username')
		if username != None:
			self.render('index.html')


class SignupHandler(tornado.web.RequestHandler):
	def get(self):
		self.render('signup.html')

	def post(self):
		email = self.get_argument('email')
		password = self.get_argument('password')
		hashed_pwd = pwd_context.encrypt(password)
		curr_users = session.query(User).filter_by(email_address=email).count()
		print curr_users

		if curr_users != 1:
			newuser = User(email_address=email, password=hashed_pwd)
			session.add(newuser)
			session.commit()
			response = {'response':200, 'data':'signed up!'}
		else:
			response = {'response':400, 'data':'That email is already registered'}
		
		self.write(json.dumps(response))


class LoginHandler(tornado.web.RequestHandler):
	def post(self):
		email = self.get_argument('email')
		password = self.get_argument('password')
		user = session.query(User).filter_by(email_address=email).first()
		verify = pwd_context.verify(password, user.password)

		if user is None or email == None:
			response = {'response':404, 'response': 'Sorry, no user with that username'}
		elif not verify:
			response = {'response':413, 'data': 'unauthorized'}
		else:
			self.set_secure_cookie("username", email)
			response = {'response':200, 'data':'logged in'}

		self.write(response)

	def get(self):
		self.render('login.html')
		# self.write({"response":300, "data":"redirect"})


class ResearchPaperHandler(BaseHandler):
	def get(self):
		self.render('research-papers.html')


class ResearchPaperAPIHandler(BaseHandler):
	def get(self):
		key = self.get_argument('param_name')
		value = self.get_argument('value')
		favorite = self.get_argument('favorite')

		print value
		search_val = re.compile(".*%s.*" % value, re.IGNORECASE)
		# query = {"favorite": favorite}
		query = {}
		query[str(key)] = search_val

		papers = db.papers.find(query)
		papers = [self.conver_obj_id(doc) for doc in list(papers)]
		self.write(json.dumps({"data": papers}))

		# sqlAlchem version
		# documents = session.query(ResearchPaper, ResearchKeyword) \
		# 	.filter(or_(ResearchPaper.title.contains(title),
		# 			ResearchKeyword.keyword.contains(keyword))).all()

		# docs = map(lambda d: {"title": d.title}, documents)
		
		# self.write(json.dumps(docs))

	def post(self):
		title = self.get_argument('title')
		abstract = self.get_argument('abstract')
		url = self.get_argument('url')
		keywords = self.get_argument('keywords')
		adjectives = self.get_argument('adjectives')
		note = self.get_argument('note')
		favorite = self.get_argument('favorite')

		# Mongo Version
		data = {
			"title": title,
			"abstract": abstract,
			"url": url,
			"keywords": [kw.strip() for kw in keywords.split(',')],
			"adjectives": [adj.strip() for adj in adjectives.split(',')],
			"note": note,
			"favorite": favorite
		}

		db.papers.insert(data)
		self.write({'status':200})
		# SQL Alchemy Version
		# keywords = [kw.strip() for kw in keywords.split(',')]
		
		# paper = ResearchPaper(
		# 	title=title,
		# 	abstract=abstract,
		# 	url=url,
		# 	favorite=favorite,
		# 	keywords=[ResearchKeyword(keyword=kw) for kw in keywords],
		# 	note=note
		# )
		# session.add(paper)
		# session.commit()

	def conver_obj_id(self, doc):
		doc['_id'] = str(doc['_id'])

		return doc

class FitbitSubscribeHandler(BaseHandler):
	def post(self):
		files = self.request.files
		for update in files['updates']:
			for body in json.loads(update['body']):
				# db.fitbit_test.insert(body)
				celtest.delay(body['collectionType'], body['date'])
		
		self.set_status(204)


class FitbitConnectHandler(BaseHandler, mixins.FitbitMixin): 
	@tornado.web.authenticated
	@tornado.web.asynchronous
	def get(self):
		user_email = self.get_secure_cookie("username")
		user = session.query(User).filter_by(email_address=user_email).first()

		if self.get_argument('oauth_token', None):
			print "doin dis thang"
			self.get_authenticated_user(self.async_callback(self._fitbit_on_auth))
			return

		# if the user has fitbit info, respond accordingly
		self.authorize_redirect()

	def _fitbit_on_auth(self, user):
		if not user:
			self.clear_all_cookies()
			raise tornado.web.HTTPError(500, 'Fitbit authentication failed')

		curr_user = self.get_secure_cookie("username")

		print "the incoming fitbit user is %r" % user
		
		self.fitbit_request(
			'/user/-/apiSubscriptions/1',
			access_token= user['access_token'],
			post_args={},
			callback=self.async_callback(self._fitbit_on_subscribe)
		)

	def _fitbit_on_user(self, user):
		if not user:
			self.clear_all_cookies()
			raise tornado.web.HTTPError(500, "Couldn't retrieve user information")

		self.write(json.dumps(user))
		self.finish()

	def _fitbit_on_subscribe(self, response):
		if not response:
			self.clear_all_cookies()
			raise tornado.web.HTTPError(500, "Couldn't retrieve user information")
		
		self.write(response)
		self.finish()


class FitbitImportHandler(tornado.web.RequestHandler, mixins.FitbitMixin):
	@tornado.web.asynchronous
	@tornado.gen.engine
	def get(self):
		curr_user = self.get_secure_cookie("username")
		curr_user = db.users.find_one({"username":curr_user})

		# import_fitbit.delay(curr_user["fitbit"]["access_token"])
		
		response = yield tornado.gen.Task(
			self.fitbit_request,
			'/user/-/foods/log/date/2013-11-10',
			access_token = curr_user['fitbit']['access_token'],
			user_id = curr_user['fitbit']['username']
		)

		# self.write(json.dumps({"response":200,"data":"Success"}))
		self.write(json.dumps(response))
		self.finish()


class FitbitPushHandler(tornado.web.RequestHandler, mixins.FitbitMixin):
	def post(self):
		print 'got some stuff %r' % self.request



class MovesConnectHandler(tornado.web.RequestHandler, mixins.MovesMixin):
    @tornado.web.asynchronous
    def get(self):
    	# if the user already has a moves 
    	# account connected, don't create a record
		if self.get_argument("code", False):
			self.get_authenticated_user(
			    redirect_uri='http://localhost:8080/connect/moves',
			    client_id=settings["moves_client_id"],
			    client_secret=self.settings["moves_client_secret"],
			    code=self.get_argument("code"),
			    callback=self.async_callback(self._on_login)
			)
			return

		self.authorize_redirect(
			redirect_uri='http://localhost:8080/connect/moves',
			client_id=settings["moves_client_id"],
			scope="activity location",
			response_type="code"
		)

    def _on_login(self, moves_user):
		user_email = self.get_secure_cookie("username")
		user = session.query(User).filter_by(email_address=user_email).first()

		moves_service = Service(
			parent_id=user.id,
			name='moves',
			identifier=moves_user['userId'],
			start_date=moves_user['profile']['firstDate'],
			access_secret=moves_user['access_token']['access_token'],
			token_type=moves_user['access_token']['token_type'],
			token_expiration=moves_user['access_token']['expires_in'],
			refresh_token=moves_user['access_token']['refresh_token'],
			timezone=moves_user['profile']['currentTimeZone']['id'],
			utc_offset=moves_user['profile']['currentTimeZone']['offset']
		)
		session.add(moves_service)
		session.commit()

		# Celery task to import the users data from Moves

		self.write(json.dumps({"response":200, "data": "success"}))
		self.finish()


class MovesTestHandler(tornado.web.RequestHandler):
	def get(self):
		date = self.get_argument('date')
		import_moves.delay(date, '1')
		self.write("success")


class MovesStorylineHandler(tornado.web.RequestHandler, mixins.MovesMixin):
	@tornado.web.asynchronous
	def get(self):
		user_email = self.get_secure_cookie("username")
		user = session.query(User) \
					.filter_by(email_address=user_email).first()
		date = self.get_argument('date')
		
		# if the user doesn't have a Moves account
		# redirect them to the moves connect
		user_moves = session.query(Service) \
							.filter_by(
								parent_id = user.id,
								name = 'moves').first()
		access_token = user_moves.access_secret

		if date is None:
			date = datetime.datetime.now().strftime('%Y%m%d')

		self.moves_request(
		    path="/user/storyline/daily/%s" % date,
		    callback=self._on_data,
		    access_token=access_token,
		    args={"trackPoints": "true"}
		)

	def _on_data(self, data):
		print "GOT SOME DATA NOW SAVING!"
		storyline = data[0]
		self.insert_segments(storyline['segments'])
		self.write(json.dumps(data))
		self.finish()

	def insert_segments(self, segments):
		segment_objects = [self.create_moves_segment(s) \
							for s in segments]
		for obj in segment_objects:
			session.add(obj)
		session.commit()

	def create_moves_segment(self, segment):
		return MovesSegment(
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
					if activity.has_key('trackPoints') else None,
				calories = activity['calories'] \
					if activity.has_key('calories')	else None,
				manual = activity['manual'],
				steps = activity['steps'] \
					if activity.has_key('steps')	else None,
				start_time = activity['startTime'],
				activity = activity['activity'],
				duration = activity['duration'],
				end_time = activity['endTime']
			)

	def create_moves_trackpoints(self, trackpoints):
		return [self.create_trackpoint(tp) \
					for tp in trackpoints]

	def create_trackpoint(self, trackpoint):
		return MovesTrackPoint(
				lat = trackpoint['lat'],
				lon = trackpoint['lon'],
				time = trackpoint['time']
			)



# class MovesImportHandler(tornado.web.RequestHandler, mixins.MovesMixin):
# 	@tornado.web.asynchronous
# 	def get(self):
# 		curr_user = self.get_secure_cookie("username")
# 		curr_user = db.users.find_one({"username":curr_user})
# 		access_token = curr_user["moves"]["access_token"]["access_token"]

# 		self.moves_request(
# 		    path="/user/storyline/daily/201310",
# 		    callback=self._on_data,
# 		    access_token=access_token,
# 		    args={"trackPoints": "true"}
# 		)

# 	def _on_data(self, data):

# 		self.write(json.dumps(data))
# 		self.finish()


class WithingsConnectHandler(BaseHandler, mixins.WithingsMixin):
	# @tornado.web.authenticated
	@tornado.web.asynchronous
	def get(self):
		curr_user = self.get_secure_cookie("username")
		curr_user = db.user.find_one({"username":curr_user})

		if self.get_argument('oauth_token', None):
			print "doin dis thang"
			self.get_authenticated_user(self.async_callback(self._fitbit_on_auth))
			return

		callback_uri = { "oauth_callback" : "http://localhost:8080/connect/withings" }
		self.authorize_withings_redirect(extra_params=callback_uri)

	def _withings_on_auth(self, user):
		if not user:
			self.clear_all_cookies()
			raise tornado.web.HTTPError(500, 'Withings authentication failed')

		curr_user = self.get_secure_cookie("username")
		db.users.update({"username":curr_user}, {'$set': {"fitbit": user}})


	def _withings_on_user(self, user):
		if not user:
			self.clear_all_cookies()
			raise tornado.web.HTTPError(500, "Couldn't retrieve user information")

		self.write(json.dumps(user))
		self.finish()


class BrainTrainingExerciseAPIHandler(BaseHandler):
	@tornado.web.authenticated
	def get(self):
		# REFACTOR: I need to figure out how to do this for real
		# I think there's an issue with the 
		query = """SELECT * FROM brain_training_exercises 
		    JOIN brain_training_games ON
		    (brain_training_exercises.game_id = brain_training_games.id)
		"""
		exercises = engine.execute(query).fetchall()
		exercises = [{
			'id': row[0], 
			'timestamp': row[2].strftime('%m/%d/%Y %H:%M'),
			'name': row[5],
			'type': row[7],
			'platform': row[9],
			'score': row[3]
		} for row in exercises]
		exercises = json.dumps({"data":exercises})
		
		self.write(exercises)

	def post(self):
		game_id = self.get_argument('game_id')
		score = self.get_argument('score')

		training_record = BrainTrainingExercise(
				game_id 	= game_id,
				timestamp 	= datetime.datetime.now(),
				score 		= score
			)

		try: 
			session.add(training_record)
			session.commit()
			self.write({"data": "Success"})
		except:
			session.rollback()
			self.write({"data": "Internal Server Error"})


class BrainTrainingGameAPIHandler(BaseHandler):
	@tornado.web.authenticated
	def get(self):
		games = session.query(BrainTrainingGame).all()
		games = [{"id":r.id, "name":r.name, "platform":r.platform,
					"type":r.type, "subtype":r.subtype, 
					"subtype_description":r.subtype_description} 
						for r in games]		
		games = json.dumps({"data":games})						
		self.write(games)

	@tornado.web.authenticated
	def post(self):
		game_id = self.get_argument('game_id')
		score = self.get_argument('score')

		training_record = BrainTrainingExercise(
				game_id 	= game_id,
				timestamp 	= datetime.datetime.now(),
				score 		= score
			)
		try: 
			session.add(training_record)
			session.commit()
			self.write({"data": "Success"})
		except:
			session.rollback()
			self.write({"data": "Internal Server Error"})
		

	@tornado.web.authenticated
	def delete(self):
		game_id = self.get_argument('game_id')
		
		try:
			session.query(BrainTrainingGame)\
					.filter_by(id=game_id).delete()
			session.commit()
			print "sucessfully deleted"
		except Exception, e:
			session.rollback()
			print "not sucessfully deleted %s" % e

		self.write({"data": "success"})

	@tornado.web.authenticated
	def put(self):
		update_dict = {}
		game_id = self.get_argument('game_id')
		update_key = self.get_argument('key')
		update_value = self.get_argument('value')
		update_dict[update_key] = update_value
		
		try:
			session.query(BrainTrainingGame)\
					.filter(BrainTrainingGame.id==game_id)\
					.update(update_dict)
			session.commit()
		except:
			session.rollback()
		
		self.write("success")


class BrainTrainingHandler(BaseHandler):
	@tornado.web.authenticated
	def get(self):
		games = session.query(BrainTrainingGame).all()
		games = [{"id":r.id, "name":r.name, "platform":r.platform,
					"type":r.type, "subtype":r.subtype, 
					"subtype_description":r.subtype_description} 
						for r in games]

		self.render('brain-training.html', games=games)

