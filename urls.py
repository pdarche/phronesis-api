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
    (r"/test/moves", handlers.MovesTestHandler),
    (r"/connect/withings", handlers.WithingsConnectHandler),
    (r"/push/fitbit", handlers.FitbitSubscribeHandler),
    (r"/research", handlers.ResearchPaperHandler),
    (r"/api/research", handlers.ResearchPaperAPIHandler),
    (r"/brain", handlers.BrainTrainingHandler),
    (r"/api/brain", handlers.BrainTrainingGameAPIHandler),
    (r"/api/brain-games", handlers.BrainTrainingGameAPIHandler),
    (r"/api/brain-exercises", handlers.BrainTrainingExerciseAPIHandler),
    (r"/stimulants", handlers.StimulantHandler),
    (r"/api/stimulants", handlers.StimulantAPIHandler),
    (r"/foods", handlers.FoodsHandler),
    (r"/api/foods", handlers.FoodsAPIHandler)
]
