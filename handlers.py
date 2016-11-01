#!/usr/bin/env python


"""
Author: Shivam Mutreja
Date: 18/10/2016
Purpose: Writing all the serving urls.

Revision:
	Author: Shivam Mutreja
	Date: 20/10/2016
    Purpose: To add POST handle for deleting user images.

	Author: Shivam Mutreja
	Date: 24/10/2016
	Purpose: Added a new handler to get user task(content) from the HOD dashboard.
"""

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
        if not self.get_current_user():
            self.redirect('/login')
        entry = self.get_current_user()
        users_or_tasks = yield self.get_users_or_tasks(entry)
        view = yield self.get_if_hod(entry)
        print view
        self.render(view, users=users_or_tasks)

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
        if not self.get_current_user():
            self.redirect('/login')
        else:
            self.hod_user_hash = self.get_current_user().get('user_id')
            self.render('create_user_new.html')

    @tornado.gen.coroutine
    def post(self):

        self.hod_user_hash = self.get_current_user().get('user_id')
        email_address = self.get_argument('email', '')
        password = self.get_argument('password', '')
        name = self.get_argument('name', '')
        # age = self.get_argument('age', '')
        birthdate = self.get_argument('birthDate', '')
        # chapter = self.get_argument('chapter')
        print self.hod_user_hash
        CheckCredentials.save_user(self.hod_user_hash, name,\
        email_address, password, birthdate)
        print 'let\'s check'

        self.redirect('/dashboard')


class ShowEditor(BaseHandler):

    @asynchronous
    @tornado.gen.coroutine
    def get(self):
        user = self.get_current_user()
        # task = yield self.check_task_status(user.get('user_id'))
        # task_status = task.get('status', '')
        if not user:
            self.redirect('/login')

        # if task_status=="Under Review":
        #     self.render("user_task_status.html")
        # else:
        content = yield self.get_user_content(user.get('user_id'))
        self.render('test_editor.html', content=content)

    @tornado.gen.coroutine
    def get_user_content(self, user_hash):
        raise tornado.gen.Return(CheckCredentials.get_user_task(user_hash))

    @asynchronous
    @tornado.gen.coroutine
    def post(self):
        user_hash = self.get_current_user().get('user_id')
        user_email = self.get_current_user().get('user_email')
        chapter_id = self.get_body_argument("get_chapter")
        print chapter_id, '##'*10
        content = self.get_argument("editor1", default=None, strip=False)
        if self.get_body_argument('draft', default=None):
            print 'draft hai!'
            yield self.save_user_written_content(user_hash, content, chapter_id)
        else:
            print 'final hai!'
            yield self.send_user_content_for_review(user_hash, content, user_email, \
                chapter_id)
        self.redirect('/dashboard')

    @tornado.gen.coroutine
    def check_task_status(self, user_hash):
        raise tornado.gen.Return(CheckCredentials.get_user_tasks(user_hash))

    @tornado.gen.coroutine
    def save_user_written_content(self, user_hash, content, chapter_id):
        raise tornado.gen.Return(CheckCredentials.save_user_content(user_hash, content, \
            chapter_id))

    @tornado.gen.coroutine
    def send_user_content_for_review(self, user_hash, content, user_email, chapter_id):
        raise tornado.gen.Return(CheckCredentials.final_user_submission(user_hash, 
            content, user_email, chapter_id))


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
        if not self.get_current_user():
            self.redirect('/login')
        else:
            user_hash = self.get_current_user().get('user_id')
            image_id = CheckCredentials.get_images(user_hash)
            self.render('user_images.html', image_id=image_id)

    def post(self):
        user_hash = self.get_current_user().get('user_id')
        image_id = self.get_body_argument('image')
        print image_id
        # print image
        CheckCredentials.delete_image(user_hash, image_id)

class UserFiles(BaseHandler):

    def get(self):
        # user = self.get_current_user()
        # print user
        if not self.get_current_user():
            self.redirect('/login')
        else:
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
        if not self.get_current_user():
            self.redirect('/login')
        else:
            user_hash = self.get_current_user().get('user_id')
            video_id = CheckCredentials.get_videos(user_hash)
            print video_id
            self.render('watch_video.html', video_id=video_id)

class AssignTask(BaseHandler):

    def get(self):
        if not self.get_current_user():
            self.redirect('/login')
        else:
            user_hash = self.get_current_user().get('user_id')
            available_users = CheckCredentials.get_available_users(user_hash)
            self.render('assign_task.html', users=available_users)

    def post(self):
        user_hash = self.get_current_user().get('user_id')
        assigned_to = self.get_argument('select-user')
        task = self.get_argument('select-chapter')
        print assigned_to, task
        CheckCredentials.assign_task(user_hash, task, assigned_to)
        self.redirect('/dashboard')

	# TODO: Make the assign task method such that the collection can hold multiple \
    #chapters assigned to user. Do it using addToSet!

class UserTaskFromHod(BaseHandler):

    @asynchronous
    @tornado.gen.coroutine
    def get(self):
        user_id, task_content = yield self.get_user_task_content()
        print task_content
        self.render("hod_editor.html", content=task_content, user_id=user_id)

    @tornado.gen.coroutine
    def get_user_task_content(self):
        user_id = self.get_argument('user_hash', '')
        # print user_id
        raise tornado.gen.Return((user_id, CheckCredentials.get_user_task(user_id)))

    def post(self):
        user_id = self.get_argument("re-assign", '')
        hod_id = self.get_current_user().get("user_id",'')
        chapter_id = self.get_argument("get_chapter")
        if user_id:
            self.redirect('/reassign_form?user_hash={}&chapter_id={}'.\
                format(user_id, chapter_id))
        else:
            user_id = self.get_argument("complete")
            CheckCredentials.mark_task_complete(hod_id, user_id, chapter_id)
            self.redirect('/dashboard')

        # TODO: Need a unique id for chapter.

class ReassignmentForm(BaseHandler):

    def get(self):
        user_id = self.get_argument('user_hash')
        chapter_id = self.get_argument('chapter_id')
        self.render("reassignment_form.html", user_id=user_id, chapter_id=chapter_id,)

    def post(self):
        user_id = self.get_body_argument("get_user_id")
        chapter_id = self.get_body_argument("get_chapter_id")
        hod_id = self.get_current_user().get("user_id",'')
        remarks = self.get_body_argument("message")
        print user_id
        print remarks
        CheckCredentials.reassign_task(hod_id, user_id, remarks, chapter_id)
        self.redirect("/dashboard")


class SignOut(BaseHandler):
    # @tornado.web.authenticated
    def get(self):
        self.clear_cookie("user")
        self.redirect('/login')

class Try(BaseHandler):
    def get(self):
        self.render("try_jq.html")


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
    (r'/assign_task', AssignTask),
    (r'/user_from_hod', UserTaskFromHod),
    (r'/reassign_form', ReassignmentForm),
    (r'/logout', SignOut),
    (r'/test', Try),
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
    sockets = tornado.netutil.bind_sockets(8000)
    tornado.process.fork_processes(10)
    http_server = tornado.httpserver.HTTPServer(app, max_body_size=200 * 1024 * 1024)
    http_server.add_sockets(sockets)
    # http_server = tornado.httpserver.HTTPServer(app)
    # http_server.bind("8000")
    # http_server.start(10)
    # app.listen('8000')
    loop = tornado.ioloop.IOLoop.instance()
    signal.signal(signal.SIGINT, lambda sig, frame: loop.add_callback_from_signal(on_shutdown))
    loop.start()

if __name__ == '__main__':
    print 'Server Reloaded'
    main()
