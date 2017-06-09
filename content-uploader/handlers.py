#!/usr/bin/env python


import os, uuid, sys
import tornado
import tornado.httpserver
import tornado.ioloop
import tornado.web
from tornado import gen
from tornado.web import asynchronous
import json
import base64

from amazon_s3 import AmazonS3

class BaseHandler(tornado.web.RequestHandler):
    def set_default_headers(self):
        print "setting headers!!!"
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Headers", "x-requested-with")
        self.set_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
        self.links = list()

class Try(BaseHandler):
    def get(self):
        image = self.get_argument("image", "")
        print image
        self.render("test_view.html", image=image)

    @asynchronous
    @tornado.gen.coroutine
    def post(self):
        content = self.get_body_argument('editor1', default=None, strip=False)
        # print content
        print self.request.files

class HandleFile(BaseHandler):
    def get(self):
        img = self.get_argument("img_data")
        print img

    @asynchronous
    @tornado.gen.coroutine
    def post(self):
        name = self.request.files['get_image'][0]['filename']
        body = self.request.files['get_image'][0]['body']

        image = yield self.upload(body, name)
        print image
        self.redirect("/test?image={}".format(image.get("hdpi")))
        # self.write(json.dumps({"image_id": image}))

    @tornado.gen.coroutine
    def upload(self, file_body, file_name):
        s3_obj = AmazonS3(image_link=file_body, news_id=file_name)
        raise tornado.gen.Return(s3_obj.run())

        # f = open(name, "ar+")
        # f.write(body)
        # f.close()

class GetLinks(BaseHandler):
    def get(self):
        print self.links
        self.render("find.html", links=self.links)

handlers = [
    (r'/test', Try),
    (r'/file', HandleFile),
    (r'/find', GetLinks)
]

settings = dict(
        template_path=os.path.join(os.path.dirname(__file__), "templates"),
        static_path=os.path.join(os.path.dirname(__file__), "static"),
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
    loop.start()

if __name__ == '__main__':
    print 'Server Reloaded'
    main()
