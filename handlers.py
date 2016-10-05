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
import functools
from blessings import Terminal
from check_credentials import CheckCredentials
from upload_scripts.amazon_s3 import AmazonS3
from upload_scripts.main import run_upload
video_dir = '/home/shivam/gat/Gat/files_to_upload/'

terminal = Terminal()


class BaseHandler(tornado.web.RequestHandler):

    def set_default_headers(self):
        self.set_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        self.set_header('Pragma', 'no-cache')
        self.set_header('Expires', '0')
        
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

    @asynchronous
    @tornado.gen.coroutine
    def get(self):
        user = self.get_current_user()
        content = yield self.get_user_content(user.get('user_id'))
        self.render('test_editor.html', content=content)

    @tornado.gen.coroutine
    def get_user_content(self, user_hash):
        raise tornado.gen.Return(CheckCredentials.get_user_task(user_hash))

    @asynchronous
    @tornado.gen.coroutine
    def post(self):
        user_hash = self.get_current_user().get('user_id')
        content = self.get_argument("editor1", default=None, strip=False)
        # content = self.get_argument('editor1')
        # print content
        yield self.save_user_content(user_hash, content)
        self.redirect('/dashboard')

    @tornado.gen.coroutine
    def save_user_content(self, user_hash, content):
        raise tornado.gen.Return(CheckCredentials.save_user_task(user_hash, content))


class UploadImage(BaseHandler):

    def get(self):
        # user = self.get_current_user()
        # print user
        self.render('media_upload.html')

    @asynchronous
    @tornado.gen.coroutine
    def post(self):
        fileinfo = self.request.files['filearg']
        user_hash = self.get_current_user().get('user_id')
        for f in fileinfo:
            fname = f['filename']
            fbody = f['body']
            # print fbody, '@!@!@!@!'
            image = yield self.upload(fbody, fname)
            doc_id = image.get('hdpi', '')
            CheckCredentials.save_user_doc(user_hash, doc_id)
        self.redirect('/dashboard')
        # print 'uploaded' if upload else 'uploading'
        print 'bhag!'

    @tornado.gen.coroutine
    def upload(self, file_body, file_name):
        s3_obj = AmazonS3(image_link=file_body, news_id=file_name)  
        raise tornado.gen.Return(s3_obj.run())


class UserImages(BaseHandler):

    def get(self):
        # user = self.get_current_user()
        # print user
        user_hash = self.get_current_user().get('user_id')
        image_id = CheckCredentials.get_images(user_hash)
        self.render('user_images.html', image_id=image_id)

class UserFiles(BaseHandler):

    def get(self):
        # user = self.get_current_user()
        # print user
        user_hash = self.get_current_user().get('user_id')
        doc_id = CheckCredentials.get_files(user_hash)
        self.render('user_files.html', doc_id=doc_id)

class UploadVideo(BaseHandler):

    def get(self):
        # user = self.get_current_user()
        # print user
        self.render('media_upload.html')

    @asynchronous
    @tornado.gen.coroutine
    def post(self):
        fileinfo = self.request.files['filearg']
        user_hash = self.get_current_user().get('user_id')
        # ['filearg']
        for f in fileinfo:
            fname = f['filename']
            fpath = video_dir+fname
            fbody = f['body']
            print fname
            new_file = open(video_dir+fname, 'ar+')
            print new_file
            if not new_file.read():
                new_file.write(fbody)
                new_file.close()
                video_id = yield self.upload_video(fpath, 'Check chunk size')
                self.redirect('/your_videos')
                CheckCredentials.save_user_video(user_hash, video_id)
            else:
                self.write('the file already exists')


    @tornado.gen.coroutine
    def upload_video(self, file_path, title):
        get_video_id = run_upload(file_path, title)
        print get_video_id
        raise tornado.gen.Return(get_video_id)


class UserVideos(BaseHandler):

    def get(self):
        # user = self.get_current_user()
        # print user
        user_hash = self.get_current_user().get('user_id')
        video_id = CheckCredentials.get_videos(user_hash)
        print video_id
        self.render('watch_video.html', video_id=video_id)


class SignOut(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        self.clear_cookie("user")
        self.redirect(self.get_argument("next", "/login"))


handlers = [
    (r"/register", RegisterUser),
    (r"/login", GetUser),
    (r"/dashboard", UserDashboard),
    (r"/add_user", AddUser),
    (r"/editor", ShowEditor),
    (r'/upload_image', UploadImage),
    (r'/your_images', UserImages),
    (r'/your_files', UserFiles),
    (r'/upload_video', UploadVideo),
    (r'/your_videos', UserVideos),
    (r'/logout', SignOut),

]

settings = dict(
        template_path=os.path.join(os.path.dirname(__file__), "templates"),
        static_path=os.path.join(os.path.dirname(__file__), "static"),
        cookie_secret="cookie_secret",
        login_url="/login"
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
    http_server.start(10)
    loop = tornado.ioloop.IOLoop.instance()
    signal.signal(signal.SIGINT, lambda sig, frame: loop.add_callback_from_signal(on_shutdown))
    loop.start()

if __name__ == '__main__':
    print 'Server Reloaded'
    main()
