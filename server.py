#!/usr/bin/env python
# -*- coding: utf-8 -*-

import tornado.ioloop
import tornado.web
from tornado import gen
import logging
import concurrent.futures
import fitsio
from binmodule import fast_bin
from astropy.stats import sigma_clip
import numpy as np
import joblib

logging.basicConfig(
    level='DEBUG', format='[%(asctime)s] %(levelname)8s %(message)s')
logger = logging.getLogger(__name__)

executor = concurrent.futures.ThreadPoolExecutor()
memory = joblib.Memory(cachedir='.tmp')

filename = 'data/20150909-ng2000-802-custom-flat-high-quality.fits'
npts_per_bin = 5

def bin_1d(flux, x=None):
    x = x if x is not None else np.arange(flux.size)
    bin_length = int(np.floor(flux.size / npts_per_bin))
    by, be, _ = stats.binned_statistic(x, flux,
                                        statistic='mean',
                                        bins=bin_length)
    return by, (be[:-1] + be[1:]) / 2.

@memory.cache
def extract_data(filename):
    logger.info('Loading data')
    with fitsio.FITS(filename) as infile:
        flux = infile['tamflux'].read()

    sc_flux = sigma_clip(flux, axis=1)

    if npts_per_bin is not None:
        sc_flux = fast_bin(sc_flux, npts_per_bin)

    med_flux = np.median(sc_flux, axis=1)
    mad_flux = np.median(np.abs(sc_flux - med_flux[:, np.newaxis]), axis=1)
    std_flux = 1.48 * mad_flux
    frms = std_flux / med_flux
    ind = np.where((med_flux > 0) & (frms > 0))[0]
    return ind, med_flux, frms

ind, med_flux, frms = extract_data(filename)
aperture_indexes = np.arange(med_flux.size)

def real_index(i):
    return aperture_indexes[ind][i]

class IndexHandler(tornado.web.RequestHandler):
    def get(self):
        self.render('templates/index.html')

class LightcurveHandler(tornado.web.RequestHandler):
    def get(self, hdu, lc_id):
        self.write({'hdu': hdu, 'lc_id': lc_id})

application = tornado.web.Application([
    (r'/', IndexHandler),
    (r'/api/lc/([a-z]+)/([0-9]+)', LightcurveHandler),
], static_path='static', debug=True)

if __name__ == '__main__':
    port = 5000
    application.listen(port)
    logger.info('Application listening on port %s', port)
    tornado.ioloop.IOLoop().current().start()
