""" Module for extracting Moves data for a Phronesis user """

import datetime
import dateutil.parser

from sqlalchemy import *
from sqlalchemy.orm import sessionmaker
import pymongo
import moves as mvs

from models.user import *

client = pymongo.MongoClient('localhost', 27017)
db = client.phronesis_dev

engine = create_engine('postgresql+psycopg2://postgres:Morgortbort1!@localhost/pete')
Session = sessionmaker(bind=engine)
session = Session()

user = session.query(User).filter_by(email_address='pdarche@gmail.com').first()
moves_profile = db.profiles.find_one({"phro_user_email": user.email_address})
moves = mvs.MovesClient(access_token=moves_profile['access_token']['access_token'])

# TODO: NEED to understand Moves' subscription to know how to handle updating
# NOTE: Moves API documentation: https://dev.moves-app.com/docs/api_summaries
# NOTE: MOVES API stores datetimes as UTC
# NOTE: the Moves API ratelimits at 60 requirest/hour and 2000 requests/day


def nonstaged_dates(profile, record_type):
    """ Finds dates that aren't in the staging db for a given
    Moves record type
    """
    curr_dates = existing_dates(profile, record_type)
    all_dates = service_daterange(profile['profile']['firstDate'])
    date_diff = [date for date in all_dates if date not in curr_dates]

    return date_diff


def existing_dates(profile, record_type):
    """ Finds the earliest update for a moves record. """

    docs = db.moves.find({
        'record_type': record_type,
        'phro_user_id': profile['phro_user_id']
        }, {'date': 1})
    dates = [doc['date'].date() for doc in docs]

    return dates


def service_daterange(start_date):
    """ Creates a list of datatime date objects from starting with
    the date the person joined Moves to today.
    """
    base_date = dateutil.parser.parse(start_date)
    today = datetime.datetime.today()
    numdays = (today - base_date).days
    dates = [(today - datetime.timedelta(days=x)).date() for x in range(0, numdays)]

    return dates


def last_staged_record_update_(profile, record_type):
    """ Finds the update time of the last staged Moves
    of a given type.
    """
    record = db.moves.find_one({
        '$query': {'record_type': record_type, 'phro_user_id': profile['phro_user_id']},
        '$orderby': {'last_update': 1}
    })

    return record


def next_import_date_range(date_list):
    """ Creates a range information for the records to fetch based
    on the earliest date in the db.

    Args:
        profile: Dict of the Phronesis user's Moves profile.
        record_type: String of the type of record to pull

    Returns:
        range_info: Dict of the start, end, update time, and timezone
        of the resources to be fetched
    """

    sorted_dates = sorted(date_list, reverse=True)
    offset = 30
    dates_len = len(sorted_dates)

    if dates_len < 30:
        offset = dates_len

    end = date_list[0].strftime('%Y%m%d')
    start = datetime.timedelta(offset).strftime('%Y%m%d')

    range_info = {
        'start_date': start_date.strftime('%Y%m%d'),
        'end_date': end_date.strftime('%Y%m%d'),
        'last_update': None,
        'timezone': 'UTC'
    }

    return range_info


def update_access_token():
    """ Updates the Phronesis users Moves access token. """
    pass


def fetch_resource(resource, start_date, end_date, update_since=None):
    """ Fetches a user's Moves summary for a given date range

    Args:
        resource: String of the moves resource to fetch.
        start_date: String of the start date.
        end_date: String of the end date.

    Returns:
        resources: List of resouce dicts from the Moves API

    Raises:
        ValueError: resource requested is not a moves resource.
    """

    if resource not in ['summary', 'activities', 'places', 'storyline']:
        raise ValueError('Invalid Moves resource.')

    resource_path = 'user/%s/daily?from=%s&to=%s' % (resource, start_date, end_date)

    if update_since:
        resource_path = "%s&updateSince=T%sZ" % (resource_path, update_since)

    resources = moves.api(resource_path, 'GET').json()

    return resources


def transform_resource(resource, record_type, profile):
    """ Adds metadata to a move source record. """
    update_datetime = dateutil.parser.parse(resource['lastUpdate'])
    date_datetime = dateutil.parser.parse(resource['date'])
    transformed = {
        'phro_user_id': profile['phro_user_id'],
        'record_type': record_type,
        'last_update': update_datetime,
        'date': date_datetime,
        'data': resource
    }

    return transformed


def transform_resources(resources, record_type, profile):
    """ Adds some phro metadata to raw Moves resources. """
    for resource in resources:
        yield transform_resource(resource, record_type, profile)


def insert_resources(transformed_resources):
    """ Inserts a collection of transformed resources into
    the moves staging database.
    """
    try:
        res = db.moves.insert(transformed_resources)
    except pymongo.errors.BulkWriteError, results:
        res = db.moves.remove(results)
    except:
        res = None

    return res


def update_resource(profile, record_type, update_info):
    """ Updates records for a given moves record type. """
    resources = fetch_resource(
                    record_type,
                    update_info['start_date'],
                    update_info['end_date'],
                    update_since=update_info['last_update']
                )
    transformed = transform_resources(resources, record_type, profile)
    inserted = insert_resources(transformed)

    return inserted


def backfill_resource_type(profile, record_type):
    """ Finds the dates to backfill and """
    update_info = next_import_date_range(profile, record_type)
    if update_info:
        updated_ids = update_resource(profile, record_type, update_info)
    else:
        return None

    return updated_ids


