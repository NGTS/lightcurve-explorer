#!/usr/bin/env python
# -*- coding: utf-8 -*-

import tornado.ioloop
import tornado.web
from tornado import gen
import logging
import concurrent.futures

logging.basicConfig(
    level='INFO', format='[%(asctime)s] %(levelname)8s %(message)s')
logger = logging.getLogger(__name__)

executor = concurrent.futures.ThreadPoolExecutor()

filename = 'data/20150909-ng2000-802-custom-flat-high-quality.fits'
npts_per_bin = 5

class IndexHandler(tornado.web.RequestHandler):
    def get(self):
        self.write('Hello world')

application = tornado.web.Application([
    (r'/', IndexHandler),
])

if __name__ == '__main__':
    application.listen(5000)
    print('Application listening on port 5000')
    tornado.ioloop.IOLoop().current().start()
