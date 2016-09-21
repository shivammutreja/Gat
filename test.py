#!/usr/bin/env python

import os
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
    	self.render("login.html")

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
        print "setting "+username['name']
        if username:
          self.set_secure_cookie("user", tornado.escape.json_encode(username))
        else:
          self.clear_cookie("user")


class UserDashboard(BaseHandler):

    @tornado.gen.coroutine
    def get(self):
        print self.get_current_user()
        entry = self.get_current_user()
        view = yield self.get_if_hod(entry)
        print view
        self.render(view, user=entry)

    @tornado.gen.coroutine
    def get_if_hod(self, entry):
        if entry['hod']:
            raise tornado.gen.Return('dashboard_hod.html')
        else:
            raise tornado.gen.Return('dashboard_user.html')

handlers = [
		(r"/register", RegisterUser),
		(r"/login", GetUser),
        (r"/dashboard", UserDashboard),
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
        client.close()

def main():
        http_server = tornado.httpserver.HTTPServer(app)
        http_server.bind("8000")
        http_server.start(30)
        loop = tornado.ioloop.IOLoop.instance()
        # signal.signal(signal.SIGINT, lambda sig, frame: loop.add_callback_from_signal(on_shutdown))
        loop.start()

if __name__ == '__main__':
    print 'Server Reloaded'
    main()
