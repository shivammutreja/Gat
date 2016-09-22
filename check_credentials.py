#!/usr/bin/env python

import pymongo
import hashlib
import settings

conn = settings.get_mongodb_connection()
coll = conn.test_db.test_coll
user_coll = conn.test_db.user_coll
types = {'hod': True, 'user': False}

class CheckCredentials:
    @staticmethod
    def check(username, password):
        pass_hash = hashlib.md5(password).hexdigest()
        print pass_hash
        user = coll.find_one({'user': username, 'pwd': pass_hash}, {'_id': False})
        if not user:
            user = user_coll.find_one({'user_email': username, 'password':\
            pass_hash}, {'_id': False})
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
    def save_user(hod_user_hash, user_name, user_age, user_email, password, chapter):

        # if coll.find_one({'user_id': hod_user_hash})['users']['chapter']:
        # 	return True
        # else:
        	# hod_user_hash = hashlib.md5(hod_user_name).hexdigest()

        coll.update({'user_id': hod_user_hash}, {'$addToSet': {'users':\
            {'user_name': user_name, 'user_email': user_email, 'chapter':\
            chapter}}})
        print 'some chudap'

        user_hash = hashlib.md5(user_name).hexdigest()
        pass_hash = hashlib.md5(password).hexdigest()

        user_coll.update({'user_id': user_hash, 'password': pass_hash}, {'$set':\
        {'user_name': user_name, 'user_age': user_age, 'user_email':\
        user_email, 'chapter': chapter}}, upsert=True)

    @staticmethod
    def get_users(hod_user_hash):
        try:
            users = coll.find_one({'user_id': hod_user_hash}, {'_id': False})['users']
            return users
        except Exception,e:
            print e

    @staticmethod
    def get_user_tasks(user_hash):
        try:
            tasks = user_coll.find_one({'user_id': user_hash}, {'_id':\
            False})['chapter']
            return tasks
        except Exception,e:
            print e


