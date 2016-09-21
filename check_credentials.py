#!/usr/bin/env python

import pymongo
import hashlib
import settings

conn = settings.get_mongodb_connection()
db = conn.test_db
coll = db.test_coll
types = {'hod': True, 'user': False}

class CheckCredentials:
	@staticmethod
	def check(username, password):
		pass_hash = hashlib.md5(password).hexdigest()
		print pass_hash
		user = coll.find_one({'user': username, 'pwd': pass_hash}, {'_id': False})
		return user

	@staticmethod
	def save(username, password, name, age, user_type):
		user_hash = hashlib.md5(username).hexdigest()
		if coll.find_one({'user_id': user_hash}):
			return True
		else:
			pass_hash = hashlib.md5(password).hexdigest()
			coll.insert({'user': username, 'pwd': pass_hash, 'name':\
		 	name, 'age': age, 'user_id': user_hash, 'hod':\
		 	types.get(user_type, '')})

	@staticmethod
	def save_user(hod_user_hash, user_name, user_age, user_email ,chapter):
		# if coll.find_one({'user_id': hod_user_hash})['users']['chapter']:
		# 	return True
		# else:
			# hod_user_hash = hashlib.md5(hod_user_name).hexdigest()
			print 'bund!'
			coll.update({'user_id': hod_user_hash}, {'$addToSet': {'users':\
				{'user_name': user_name, 'user_email': user_email, 'chapter':\
				chapter}}})

	@staticmethod
	def get_users(hod_user_hash):
		users = coll.find_one({'user_id': hod_user_hash}, {'_id': False})['users']
		return users


