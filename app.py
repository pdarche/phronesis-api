#!/usr/bin/env python
# -*- coding: utf-8 -*-

#import os.path
#import wsgiref.handlers

#import tornado.auth
import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
import tornado.autoreload
#from tornado.options import define, options
from tornado.options import options
import tornado.web
#import tornado.wsgi

from tasks.tasks import celtest
from tasks.tasks import import_fitbit
from tasks.tasks import import_moves

from settings import settings
from urls import url_patterns
import ui_methods


def update_fitbit():
	print "trying to fetch"
	import_fitbit.delay(5)


def update_moves():
    print "trying to fetch"
    import_moves.delay()
	

class TornadoApplication(tornado.web.Application):
    def __init__(self):
        tornado.web.Application.__init__(self, url_patterns, ui_methods=ui_methods, **settings)


def main():
    app = TornadoApplication()
    http_server = tornado.httpserver.HTTPServer(app)
    http_server.listen(options.port)
    # tornado.ioloop.PeriodicCallback(update_moves, 60000).start()
    tornado.ioloop.IOLoop.instance().start()


if __name__ == "__main__":
    main()