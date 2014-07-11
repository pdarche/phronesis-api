# -*- coding: utf-8 -*-

from handlers import handlers


url_patterns = [
    (r"/", handlers.MainHandler),
    (r"/login", handlers.LoginHandler),
    (r"/signup", handlers.SignupHandler),
    (r"/connect/fitbit", handlers.FitbitConnectHandler),
    (r"/import/fitbit", handlers.FitbitImportHandler),
    (r"/connect/moves", handlers.MovesConnectHandler),
    (r"/import/moves", handlers.MovesStorylineHandler),
    (r"/connect/withings", handlers.WithingsConnectHandler),
    (r"/push/fitbit", handlers.FitbitSubscribeHandler),
]
