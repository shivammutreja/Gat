#!/usr/bin/env python

import os
import pymongo
import hashlib
import pwd

def get_mongodb_connection():
	conn = pymongo.MongoClient(project_settings.MONGO_SERVERIP) if pwd.getpwuid(os.getuid()).pw_name in ['ubuntu','root'] else pymongo.MongoClient()
	return conn