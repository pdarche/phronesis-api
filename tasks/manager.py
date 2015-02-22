""" ```manager``` module contains functions for managing ETL tasks """

from sqlalchemy import *
from sqlalchemy.orm import sessionmaker

import pymongo

from models.user import *
from etl import movesapp as moves

client = pymongo.MongoClient('localhost', 27017)
db = client.phronesis_dev

engine = create_engine('postgresql+psycopg2://postgres:Morgortbort1!@localhost/pete')
Session = sessionmaker(bind=engine)
session = Session()

user = session.query(User).filter_by(email_address='pdarche@gmail.com').first()
current_services = [
	'moves', 'fitbit', 'withings',
	'open_paths', 'runkeeper'
]

services = {
	'moves': {'update_info': moves.next_import_date_range, 'import': moves.update_resource}
}

