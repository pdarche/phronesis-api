import json
import datetime
import time

import celery as clry
import fitbit
import pandas as pd
import pymongo
from sqlalchemy import *
from sqlalchemy.orm import sessionmaker

from settings import settings
from models.user import *
import etl.movesapp as moves

engine = create_engine('postgresql+psycopg2://postgres:Morgortbort1!@localhost/pete')
Session = sessionmaker(bind=engine)
session = Session()
celery = clry.Celery('tasks', broker='amqp://guest@localhost//')
client = pymongo.MongoClient('localhost', 27017)

db = client.phronesis_dev
user = session.query(User).filter_by(email_address='pdarche@gmail.com').first()
current_services = [
    'moves'
]


@celery.task
def import_moves_resources(profile):
    """ Backfills moves storyline. """
    moves.import_resource_type(profile, 'storyline')

    return 'executing moves import'


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
        pass

    if pd.to_datetime(base_date_activity) > signup_date:
        print "fetching activities!"
        activities = FitbitFetchActivities()
        activities.activities_processor(activity_dates)
    else:
        pass

    if pd.to_datetime(base_date_sleep) > signup_date:
        print "fetching sleeps!"
        sleep = FitbitFetchSleep()
        sleep.sleep_processor(sleep_dates)
    else:
        pass

    time.sleep(.25)
    return "success!"


def etl_manager():
    """ Determines whether data should continue to be
    backfilled for a given service

    Args:
        service: String of the service to be checked
        user: Dict of the Phronesis user

    """
    service_backfillers = {
        'moves': import_moves_resources
    }

    for service in current_services:
        profile = db.profiles.find_one(
            {'service': service, 'phro_user_id': user.id})

        if profile:
            # execute the celery task to backfill the data
            service_backfillers[service].delay(profile)
        else:
            pass
