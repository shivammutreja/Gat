#!/usr/bin/env python

import pymongo
import hashlib

conn = pymongo.MongoClient()
db = conn.test_db
coll = db.test_coll

class CheckCredentials:
	@staticmethod
	def check(username, password):
		user = coll.find_one({'user': username, 'pwd': password}, {'_id': False})
		return user

	@staticmethod
	def save(username, password, name, age):
		user_hash = hashlib.md5(username).hexdigest()
		if coll.find_one({'user_id': user_hash}):
			return True
		else:
			user = coll.insert({'user': username, 'pwd': password, 'name':\
		 	name, 'age': age, 'user_id': user_hash})


