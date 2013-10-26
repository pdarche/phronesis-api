import tornado.web
import requests
import json
from settings import settings
from pymongo import MongoClient
import pymongo
import time
import datetime

from bson import objectid
from passlib.apps import custom_app_context as pwd_context

client = MongoClient('localhost', 27017)

class BaseHandler(tornado.web.RequestHandler):
	def get_current_user(self):
		return self.get_secure_cookie("username")

class MainHandler(BaseHandler): 
	def get(self):
		username = self.get_secure_cookie('username')
		if username != None:
			self.render('index.html', username=username)
		else:
			self.render("index.html", username="")


class SignUpHandler(tornado.web.RequestHandler):
	def post(self):
		username = self.get_argument('username')
		password = self.get_argument('password')
		hashed_pwd = pwd_context.encrypt(password)
		user = models.userinfo.User.objects(username=username)

		if len(user) == 0:		
			newuser = models.userinfo.User(
				username = username,
				password = hashed_pwd,
				adjectives = models.userinfo.UserAdjectives()
			)
			if newuser.save():
				response = {'response':200, 'data':'signed up!'}
			else:
				response = {
					'response':500, 
					'data':'something went wrong on our end!'
				}
		else:
			response = {'response':400, 'data':'username unavailable!'}
		self.write(json.dumps(response))


class LoginHandler(tornado.web.RequestHandler):
	def post(self):
		username = self.get_argument('username')
		password = self.get_argument('password')
		user = models.userinfo.User.objects(username=username)[0]
		verify = pwd_context.verify(password, user.password)

		if len(user) == 0 or username == None:
			response = {'response':404, 'response': 'Sorry, no user with that username'}
		elif not verify:
			response = {'response':413, 'data': 'unauthorized'}
		else:
			self.set_secure_cookie("username", username)
			response = {'response':200, 'data':'logged in'}

		self.write(response)

	def get(self):
		self.write( "redirect to login")