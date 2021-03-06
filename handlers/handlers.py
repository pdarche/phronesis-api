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

from bson import objectid
from passlib.apps import custom_app_context as pwd_context

from models.user import User
from models.user import Service
import mixins.mixins as mixins

from tasks.tasks import add
from tasks.tasks import celtest
# from tasks.tasks import import_fitbit

from sqlalchemy import *
from sqlalchemy.orm import sessionmaker


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
        # Do something interesting with user here. See: user["access_token"]
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


class MovesStorylineHandler(tornado.web.RequestHandler, mixins.MovesMixin):
	@tornado.web.asynchronous
	def get(self):
		user_email = self.get_secure_cookie("username")
		user = session.query(User).filter_by(email_address=user_email).first()
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
		self.write(json.dumps(data))
		self.finish()


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

# class CeleryHandler(tornado.web.RequestHandler):
# 	def get(self):
# 		add.delay(4,4)
# 		self.write("testing")
		

