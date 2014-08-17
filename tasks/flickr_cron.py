from settings import settings
import flickrapi
import json
from pymongo import MongoClient

# Mongo
client = MongoClient('localhost', 27017)
db = client.phronesis_food_photos

api_key = settings['flickr_api_key']
secret = settings['flickr_api_secret']

flickr = flickrapi.FlickrAPI(api_key)

# get the entire 'Foods' photo set
foods_set_id = '72157642752099113'
foods_set = list(flickr.walk_set(foods_set_id))

# get the current photo ids in the staging db
photo_id_dicts = list(db.photos.find({},{"_id":0, 'id':1}))
existing_photo_ids = [p['id'] for p in photo_id_dicts]

# for each photo in the set 
for photo in foods_set[:10]:
	photo_id = photo.get('id')
	# if the photo_id isn't already in flickr photos
    # get the photo
    if photo_id not in existing_photo_ids:
		photo_info_json = flickr.photos_getInfo(photo_id=photo_id, format='json')
		photo_info = json.loads(photo_info_json[14:-1])
		db.photos.insert(photo_info['photo'])
	else:
		pass