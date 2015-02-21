""" Module for extracting Moves data for a Phronesis user """

import datetime
import dateutil.parser

import pymongo
from sqlalchemy import *
from sqlalchemy.orm import sessionmaker
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
def next_import_date_range(profile, record_type):
    """ Finds the date range of the records to backfill

    Args:
        profile: Dict of the Phronesis user's Moves profile.
        record_type: String of the type of record to pull

    Returns:
        range_info: Dict of the start, end, update time, and timezone
        of the resources to be fetched
    """

    join_date = datetime.datetime.strptime(profile['firstDate'], '%Y%m%d')

    # TODO: thinkg about localization strategy
    if db.moves.find({'record_type': record_type}).count():
        last_import_record = db.moves.find({'record_type': record_type})\
                                        .sort('last_update', 1).limit(1)[0]
        start_date = last_import_record['last_update'] - datetime.timedelta(30)
        end_date = last_import_record['last_update']
        last_update = last_import_record['last_update']
    else:
        today = datetime.datetime.today()
        start_date = today - datetime.timedelta(30)
        end_date = today
        last_update = datetime.datetime.now()

    if start_date < join_date:
        start_date = join_date

    range_info = {
        'start_date': start_date.strftime('%Y%m%d'),
        'end_date': end_date.strftime('%Y%m%d'),
        'last_update': last_update.strftime('%H%M%S'),
        'timezone': 'UTC'
    }

    return range_info


def missing_dates():
    """ Finds any dates missing between today and Moves
    join date for a record type (summary, activity, etc.)
    """
    # fetch covered date ranges
    # fetch the dates between today and the signup date
    pass


def update_access_token():
    """ Updates the Phronesis users Moves access token """
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


def transform_resources(resources, record_type, profile):
    """ inserts raw Moves resources into the staging database. """
    for resource in resources:
        yield transform_resource(resource, record_type, profile)


def transform_resource(resource, record_type, profile):
    """ Adds metadata to a move source record. """
    update_datetime = dateutil.parser.parse(resource['lastUpdate'])
    transformed = {
        'phro_user_id': profile['phro_user_id'],
        'record_type': record_type,
        'last_update': update_datetime,
        'data': resource
    }

    return transformed


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


def update_resource(record_type, profile):
    """ Updates records for a given moves record type. """
    update_info = next_import_date_range(profile['profile'], record_type)
    resources = fetch_resource(
                    record_type,
                    update_info['start_date'],
                    update_info['end_date'],
                    update_since=update_info['last_update']
                )
    transformed_resources = transform_resources(resources, record_type, profile)
    inserted_resources = insert_resources(transformed_resources)

    return inserted_resources


# TODO: Review and remove! This is depracated and won't be used in the future.
class MovesStoryline():
    """ Class for importing Moves storyline data """
    def _on_data(self, data):
        storyline = data[0]
        self.insert_segments(storyline['segments'])

    def insert_segments(self, segments):
        segment_objects = [self.create_moves_segment(s) \
                            for s in segments]
        for obj in segment_objects:
            session.add(obj)
        session.commit()

    def create_moves_segment(self, segment):
        return MovesSegment(
                parent_id = 1, # NOTE: this will have to change!
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
                    if activity.has_key('trackPoints') else [],
                calories = activity['calories'] \
                    if activity.has_key('calories') else None,
                manual = activity['manual'],
                steps = activity['steps'] \
                    if activity.has_key('steps') else None,
                start_time = activity['startTime'],
                activity = activity['activity'],
                duration = activity['duration'],
                end_time = activity['endTime']
            )

