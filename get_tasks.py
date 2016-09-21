#!/usr/bin/env python


import pymongo
import hashlib
import settings

conn = settings.get_mongodb_connection()
db = conn.test_db
coll = db.test_coll
types = {'hod': True, 'user': False}

class FetchTasks:
	@staticmethod
	def fetch_tasks(username, password):
		print password
		pass_hash = hashlib.md5(password).hexdigest()
		user = coll.find_one({'user': username, 'pwd': pass_hash}, {'_id': False})
		return user

	@staticmethod
	def add_task(username, password, name, age, user_type):
		user_hash = hashlib.md5(username).hexdigest()
		if coll.find_one({'user_id': user_hash}):
			return True
		else:
			pass_hash = hashlib.md5(password).hexdigest()
			user = coll.insert({'user': username, 'pwd': pass_hash, 'name':\
		 	name, 'age': age, 'user_id': user_hash, 'hod': types.get(user_type, '')})
