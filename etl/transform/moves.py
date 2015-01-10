""" Transforms raw moves records in preparation for staging """

import datetime
import dateutil.parser

def transform(record, record_type):
    transformed = {}
    update_datetime = dateutil.parser.parse(record['lastUpdate'])
    date = dateutil.parser.parse(record['date'])
    transformed['record_type'] = record_type
    transformed['last_update'] = update_datetime
    transformed['date'] = date
    transformed['source'] = record
    return transformed

