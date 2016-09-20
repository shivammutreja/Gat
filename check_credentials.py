#!/usr/bin/env python

import pymongo
import hashlib

conn = pymongo.MongoClient()
db = conn.test_db
coll = db.test_coll
types = {'hod': True, 'user': False}

class CheckCredentials:
	@staticmethod
	def check(username, password):
		print password
		pass_hash = hashlib.md5(password).hexdigest()
		user = coll.find_one({'user': username, 'pwd': pass_hash}, {'_id': False})
		return user

	@staticmethod
	def save(username, password, name, age, user_type):
		user_hash = hashlib.md5(username).hexdigest()
		if coll.find_one({'user_id': user_hash}):
			return True
		else:
			pass_hash = hashlib.md5(password).hexdigest()
			user = coll.insert({'user': username, 'pwd': pass_hash, 'name':\
		 	name, 'age': age, 'user_id': user_hash, 'hod': types.get(user_type, '')})


