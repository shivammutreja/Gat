#!/usr/bin/env python

import pymongo
import hashlib
import settings
# from bs4 import BeautifulSoup

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
    def save_user(hod_user_hash, user_name, user_email, password, birthdate):

        user_hash = hashlib.md5(user_email).hexdigest()
        pass_hash = hashlib.md5(password).hexdigest()

        coll.update({'user_id': hod_user_hash}, {'$addToSet': {'users':\
            {'user_name': user_name, 'user_email': user_email, 'birthdate':\
            birthdate, 'user_id': user_hash}}})
        print 'some chudap'


        user_coll.update({'user_id': user_hash, 'password': pass_hash}, {'$set':\
        {'user_name': user_name, 'user_birthdate': birthdate, 'user_email':\
        user_email,}}, upsert=True)

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
            False})
            return tasks
        except Exception,e:
            print e

    @staticmethod
    def save_user_content(user_hash, content):
        user_coll.update({'user_id': user_hash}, {'$set': {'content': content}})
        return

    """
    This method sets the status to 'under review' after the user clicks on 'final submission' button
    """
    @staticmethod
    def final_user_submission(user_hash, content, user_email):
        user_coll.update({'user_id': user_hash}, {'$set': {'content': content, 'status': \
            'Under Review'}})

        coll.update({'users.user_email': user_email}, {'$set': {'users.$.status': 'for review'}})
        return


    @staticmethod
    def get_user_task(user_hash):
        try:
            content = user_coll.find_one({'user_id': user_hash}, {'_id': False})['content']
            return content
        except Exception,e:
            print e

    @staticmethod
    def save_user_video(user_hash, video_id):
        user_coll.update({'user_id': user_hash}, {'$set': {'video_id': video_id}})

    @staticmethod
    def save_user_doc(user_hash, doc_id):
        if doc_id.endswith('.pdf'):
            user_coll.update({'user_id': user_hash}, {'$addToSet': {'file_id': doc_id}})
        else:
            user_coll.update({'user_id': user_hash}, {'$addToSet': {'image_id': doc_id}})


    @staticmethod
    def get_videos(user_hash):
        try:
            video_id = user_coll.find_one({'user_id': user_hash}, {'_id': False})['video_id']
            return video_id
        except Exception,e:
            print e

    @staticmethod
    def get_images(user_hash):
        try:
            image_id = user_coll.find_one({'user_id': user_hash}, {'_id': False})['image_id']
            return image_id
        except Exception,e:
            print e

    @staticmethod
    def get_files(user_hash):
        try:
            file_id = user_coll.find_one({'user_id': user_hash}, {'_id': False})['file_id']
            return file_id
        except Exception,e:
            print e

    @staticmethod
    def get_available_users(hod_user_hash):
        available_users = list()
        try:
            users = list(coll.find({'user_id': '52db15126120e575ab471b046d46fbab'}, \
            {'users': True, '_id': False}))[0]['users']

            for user in users:
                if not 'status' in user.keys() or user['status']=='complete':
                    available_users.append(user)

            return available_users
        except Exception,e:
            print e
        return

    @staticmethod
    def assign_task(hod_user_hash, chapter, user_id):
        user_coll.update({'user_id': user_id}, {'$set': {'chapter': chapter, \
        'status': 'Pending'}})

        print user_id, '@!@@!'

        coll.update({'user_id': hod_user_hash, 'users.user_id': user_id}, {'$set': {'users.$.chapter': \
        chapter, 'users.$.status': 'pending'}})
        return
