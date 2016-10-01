#!/usr/bin/env python

import os, uuid, sys
import tornado
import tornado.httpserver
import tornado.ioloop
import tornado.web
from tornado import gen
from tornado.web import asynchronous
import signal

import json
from blessings import Terminal
from check_credentials import CheckCredentials
from upload_scripts.amazon_s3 import AmazonS3
from upload_scripts.main import run_upload
video_dir = '/home/shivam/gat/Gat/files_to_upload/'

terminal = Terminal()


class BaseHandler(tornado.web.RequestHandler):

    @asynchronous
    def get_login_url(self):
        return "/login"

    def get_current_user(self):
        user_json = self.get_secure_cookie("user")
        if user_json:
          return tornado.escape.json_decode(user_json)
        else:
          return None


class RegisterUser(BaseHandler):

    def get(self):
        self.render('register_1.html')

    @asynchronous
    def post(self):
        login_response = {}

        email_address = self.get_argument('email', '')
        password = self.get_argument('password', '')
        name = self.get_argument('name', '')
        age = self.get_argument('age', '')
        user_type = self.get_argument('types')

        if not email_address:
            login_response.update({
                'success': False, 
                'msg': 'Please enter your email address.'
            })
        elif not password:
            login_response.update({
                'success': False, 
                'msg': 'Please enter your password.'
            })
        else:
            print name
            register = CheckCredentials.save(email_address, password,\
                                         name, age, user_type)
            self.redirect('/login')

        #     response = {'success': True, 'msg': 'You have been registered successfully'}\
        #                 if not register else {'success': True, 'msg': \
        #                 'This email_id has already been registered'}
                
        #     login_response.update(response)

        # self.write(login_response)


class GetUser(BaseHandler):

    def get(self):
        self.render("new_login.html")

    @asynchronous
    def post(self):
        login_response = {}

        email_address = self.get_argument('uname', '')
        password = self.get_argument('psw', '')
        
        if not email_address:
            login_response.update({
                'success': False, 
                'msg': 'Please enter your email address.'
            })
        elif not password:
            login_response.update({
                'success': False, 
                'msg': 'Please enter your password.'
            })
        else:
            self.user = CheckCredentials.check(email_address, password)
            if self.user:
                self.set_current_user(self.user)
                self.redirect("/dashboard")
            else:
                self.redirect('/login')
            # response = {'success': True, 'msg': 'Hi '+ user['user'].split('@')[0]} \
            # if user else {'success': True, 'msg': 'No user found'}
            
            # login_response.update(response)
            # print login_response

    def set_current_user(self, username):
        # print "setting "+username['name']
        if username:
          self.set_secure_cookie("user", tornado.escape.json_encode(username))
        else:
          self.clear_cookie("user")


class UserDashboard(BaseHandler):

    @tornado.gen.coroutine
    def get(self):
        print self.get_current_user()
        entry = self.get_current_user()
        users_or_tasks = yield self.get_users_or_tasks(entry)
        view = yield self.get_if_hod(entry)
        print view
        self.render(view, user=entry, users=users_or_tasks)

    @tornado.gen.coroutine
    def get_if_hod(self, entry):
        if 'hod' in entry.keys():
            # raise tornado.gen.Return('dashboard_hod.html')
            raise tornado.gen.Return('dashboard_hod_new.html')
        else:
            # raise tornado.gen.Return('dashboard_user.html')
            raise tornado.gen.Return('dashboard_user_new.html')

    @tornado.gen.coroutine
    def get_users_or_tasks(self, entry):
        if 'hod' in entry.keys():
            users = CheckCredentials.get_users(entry['user_id'])
            raise tornado.gen.Return(users)
        else:
            tasks = CheckCredentials.get_user_tasks(entry['user_id'])
            raise tornado.gen.Return(tasks)

class AddUser(BaseHandler):

    def get(self):
        self.render('create_user.html')

    @tornado.gen.coroutine
    def post(self):

        email_address = self.get_argument('email', '')
        password = self.get_argument('password', '')
        name = self.get_argument('name', '')
        age = self.get_argument('age', '')
        chapter = self.get_argument('chapter')
        hod_user_hash = self.get_current_user().get('user_id')

        CheckCredentials.save_user(hod_user_hash, name, age,\
        email_address, password, chapter)
        print 'let\'s check'

        self.redirect('/dashboard')


class ShowEditor(BaseHandler):

    def get(self):
        user = self.get_current_user()
        print user
        content = user.get('content') if 'content' in user.keys() else None
        self.render('test_editor.html', content=content)


    def post(self):
        user_hash = self.get_current_user().get('user_id')
        content = self.get_body_argument("editor1", default=None, strip=False)
        # content = self.get_argument('editor1')
        # print content
        CheckCredentials.save_user_task(user_hash, content)


class UploadImage(tornado.web.RequestHandler):

    def get(self):
        # user = self.get_current_user()
        # print user
        self.render('media_upload.html')

    @asynchronous
    @tornado.gen.coroutine
    def post(self):
        fileinfo = self.request.files['filearg']
        # ['filearg']
        for f in fileinfo:
            fname = f['filename']
            fbody = f['body']
            print fname
            upload = yield self.upload(fbody, fname)
        # print 'uploaded' if upload else 'uploading'
        print 'bhag!'

    @tornado.gen.coroutine
    def upload(self, file_body, file_name):
        s3_obj = AmazonS3(image_link=file_body, news_id=file_name)  
        raise tornado.gen.Return(s3_obj.run())

class UploadVideo(tornado.web.RequestHandler):

    def get(self):
        # user = self.get_current_user()
        # print user
        self.render('media_upload.html')

    @asynchronous
    @tornado.gen.coroutine
    def post(self):
        fileinfo = self.request.files['filearg']
        # ['filearg']
        for f in fileinfo:
            fname = f['filename']
            fpath = video_dir+fname
            fbody = f['body']
            print fname
            new_file = open(video_dir+fname, 'a')
            new_file.write(fbody)
            new_file.close()
            upload = yield self.upload_video(fpath, 'Fist Upload')
        # print 'uploaded' if upload else 'uploading'
        print 'bhag!'

    @tornado.gen.coroutine
    def upload_video(self, file_path, title):
        raise tornado.gen.coroutine(run_upload(file_path, title))

class UserVideos(BaseHandler):

    def get(self):
        # user = self.get_current_user()
        # print user
        user_hash = self.get_current_user().get('user_id')
        video_id = CheckCredentials.get_videos(user_hash)
        print video_id
        self.render('watch_video.html', video_id=video_id)



handlers = [
    (r"/register", RegisterUser),
    (r"/login", GetUser),
    (r"/dashboard", UserDashboard),
    (r"/add_user", AddUser),
    (r"/editor", ShowEditor),
    (r'/upload_image', UploadImage),
    (r'/upload_video', UploadVideo),
    (r'/your_videos', UserVideos),
]

settings = dict(
        template_path=os.path.join(os.path.dirname(__file__), "templates"),
        static_path=os.path.join(os.path.dirname(__file__), "static"),
        cookie_secret="cookie_secret",
)

app = tornado.web.Application(handlers, **settings)


def on_shutdown():
    print terminal.red(terminal.bold('Shutting down'))
    tornado.ioloop.IOLoop.instance().stop()
    ##gracefully closing mongo connection
    #MONGO_CONNECTION.close()
    # client.close()


def main():
    http_server = tornado.httpserver.HTTPServer(app)
    http_server.bind("8000")
    http_server.start(20)
    loop = tornado.ioloop.IOLoop.instance()
    signal.signal(signal.SIGINT, lambda sig, frame: loop.add_callback_from_signal(on_shutdown))
    loop.start()

if __name__ == '__main__':
    print 'Server Reloaded'
    main()
