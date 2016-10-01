#!/usr/bin/env python

import sys
import os
import glob
import urllib2 as urllib
import shutil
from cStringIO import StringIO
from PIL import Image
import PIL
import base64
import requests
file_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(file_path)
from global_credentials import S3_BUCKET_NAME, AMAZON_SECRET_KEY, AMAZON_ACCESS_KEY

from boto.s3.connection import S3Connection
from boto.exception import S3ResponseError, S3CreateError


class AmazonS3(object):
        def __init__(self, image_link, news_id):
                self.image_link = image_link
                self.image_format = "png"
                self.news_id = news_id

                self.ldpi_size = (240, 320)
                self.mdpi_size = (320, 480)
                self.hdpi_size = (480, 800)
                self.xhdpi_size = (640, 960)


        def amazon_bucket(self):
                """
                return amazon bucket which will be used to store the images sizes
                """
                try:
                        s3_connection = S3Connection(AMAZON_ACCESS_KEY, AMAZON_SECRET_KEY)
                except Exception as e:
                        raise StandardError("The attempt to connect amazon s3 cloud has been failed")

                try:
                        bucket = s3_connection.get_bucket(S3_BUCKET_NAME)
                        
                except S3ResponseError as e:
                        print "The bucket you are trying to connect doesnt exists yet, \
                                Trying to create the bucket required to store the relevant images"
                        bucket = s3_connection.create_bucket(S3_BUCKET_NAME)

                return bucket

        def run(self):
                self.bucket = self.amazon_bucket()
                print self.bucket
                self.download_image()
                self.make_resolutions()
                self.encode_images()
                return {"mdpi": self.mdpi_image_url, 
                        "hdpi": self.hdpi_image_url,
                        }

        def download_image(self):
                """
                Download an image from the link
                """
                try:
                    #response = urllib.urlopen(self.image_link)
                    #source = response.read()
                    self.img = Image.open(StringIO(self.image_link))
                except Exception as e:
                    print "opening file"
                    f = open(self.image_link)
                    source = f.read()
                    self.img = Image.open(StringIO(source))
		    
                    #goose_instance = goose.Goose()
                    #g = goose_instance.extract(self.image_link)
                    #self.img  = Image.open(StringIO(g.raw_html))

                return

        def make_resolutions(self):
                """
                converts the image link to byte 64 encoding
                """             
                
                wpercent = (self.mdpi_size[0]/float(self.img.size[0]))
                hsize = int((float(self.img.size[1])*float(wpercent)))
                self.img_mdpi = self.img.resize((self.mdpi_size[0], hsize), Image.ANTIALIAS) 
                
                
                wpercent = (self.hdpi_size[0]/float(self.img.size[0]))
                hsize = int((float(self.img.size[1])*float(wpercent)))
                self.img_hdpi = self.img.resize((self.hdpi_size[0], hsize), Image.ANTIALIAS)

                return 


        def encode_images(self):
                """
                converts the image to different resolutions
                hdpi, mdpi, xdpi
                """

                output = StringIO()
                self.img_mdpi.save(output, self.image_format,optimize=True,quality=65)
                key = self.news_id + "_mdpi.png"
                mdpi_key = self.bucket.new_key(key)
                mdpi_key.set_metadata('Content-Type', 'image/png')
                mdpi_key.set_contents_from_string(output.getvalue())
                mdpi_key.set_canned_acl('public-read')
                self.mdpi_image_url = mdpi_key.generate_url(0, query_auth=False, force_http=True)
                
                output = StringIO()
                self.img_hdpi.save(output, self.image_format,optimize=True,quality=65)
                key = self.news_id + "_hdpi.png"
                hdpi_key = self.bucket.new_key(key)
                hdpi_key.set_metadata('Content-Type', 'image/png')
                hdpi_key.set_contents_from_string(output.getvalue())
                hdpi_key.set_canned_acl('public-read')
                self.hdpi_image_url = hdpi_key.generate_url(0, query_auth=False, force_http=True)


                return




if __name__ == "__main__":
        i = AmazonS3(image_link='/home/shivam/images/hannah_reid_2.jpg', news_id= 'd574f3211fb0bab45048ce4778613cc2')
        print i.run()

