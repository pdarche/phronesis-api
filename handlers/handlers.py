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
import mixins.mixins as mixins


client = MongoClient('localhost', 27017)
db = client.phronesis_dev

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
	def post(self):
		username = self.get_argument('username')
		password = self.get_argument('password')
		hashed_pwd = pwd_context.encrypt(password)
		user = db.users.find_one({'username': username})

		if user == None:
			newuser = copy.deepcopy(User)
			newuser["username"] = username
			newuser["password"] = hashed_pwd
			db.users.insert(newuser)
			response = {'response':200, 'data':'signed up!'}
		else:
			response = {'response':400, 'data':'username unavailable!'}
		
		self.write(json.dumps(response))


class LoginHandler(tornado.web.RequestHandler):
	def post(self):
		username = self.get_argument('username')
		password = self.get_argument('password')
		user = db.users.find_one({'username': username})
		verify = pwd_context.verify(password, user['password'])

		if len(user) == 0 or username == None:
			response = {'response':404, 'response': 'Sorry, no user with that username'}
		elif not verify:
			response = {'response':413, 'data': 'unauthorized'}
		else:
			self.set_secure_cookie("username", username)
			response = {'response':200, 'data':'logged in'}

		self.write(response)

	def get(self):
		self.render('login.html')
		# self.write({"response":300, "data":"redirect"})


class FitbitConnectHandler(BaseHandler, mixins.FitbitMixin): 
	@tornado.web.authenticated
	@tornado.web.asynchronous
	def get(self):
		curr_user = self.get_secure_cookie("username")
		curr_user = db.user.find_one({"username":curr_user})

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
		db.users.update({"username":curr_user}, {'$set': {"fitbit": user}})

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
		user_id = curr_user["fitbit"]["username"]
		access_token = curr_user["fitbit"]["access_token"]
		member_since = curr_user["fitbit"]["user"]["memberSince"]

		response = yield tornado.gen.Task(self.fitbit_request,
			'/user/-/activities/steps/date/2011-01-01/today',
			access_token = access_token,
			user_id = user_id)
		
		self.write(response)
		self.finish()
		

class FitbitPushHandler(tornado.web.RequestHandler, mixins.FitbitMixin):
	def post(self):
		print 'got some stuff %r' % self.request


