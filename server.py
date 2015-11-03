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
from scipy.stats import binned_statistic

logging.basicConfig(
    level='DEBUG', format='[%(asctime)s] %(levelname)8s %(message)s')
logger = logging.getLogger(__name__)

executor = concurrent.futures.ThreadPoolExecutor()
memory = joblib.Memory(cachedir='.tmp')

filename = 'data/20150911-ng2000-802-custom-flat-high-quality.fits'
npts_per_bin = 100

def fetch_from_fits(infile, hdu, index):
    index = int(index)
    return infile[hdu][index:index + 1, :].ravel()

def bin_1d(flux, x=None):
    x = x if x is not None else np.arange(flux.size)
    bin_length = int(np.floor(flux.size / npts_per_bin))
    by, be, _ = binned_statistic(x, flux, statistic='mean',
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
    return int(aperture_indexes[ind][int(i)])

def get_lightcurve(hdu, lc_id):
    with fitsio.FITS(filename) as infile:
        mjd = fetch_from_fits(infile, 'hjd', lc_id)
        flux = fetch_from_fits(infile, hdu, lc_id)

    if npts_per_bin is not None:
        flux, mjd = bin_1d(flux, x=mjd)

    mjd0 = int(mjd.min())

    sc = sigma_clip(flux)

    return (mjd - mjd0)[~sc.mask], flux[~sc.mask]


class IndexHandler(tornado.web.RequestHandler):
    def get(self):
        self.render('templates/index.html', npts_per_bin=npts_per_bin,
                   render_frms=True)

class DetailHandler(tornado.web.RequestHandler):
    def get(self, lc_id):
        self.render('templates/view.html', file_index=lc_id,
                   render_frms=False)

class ObjectIndexHandler(tornado.web.RequestHandler):
    def get(self, lc_id):
        self.write({'index': real_index(lc_id)})

class FRMSHandler(tornado.web.RequestHandler):
    def format_frms(self):
        return {'data': list(zip(
            list(np.log10(med_flux[ind].astype(float))),
            list(np.log10(frms[ind].astype(float)))))}

    @gen.coroutine
    def get(self):
        results = yield executor.submit(self.format_frms)
        self.write(results)

class LightcurveHandler(tornado.web.RequestHandler):
    def fetch_data(self, hdu, lc_id):
        mjd, flux = get_lightcurve(hdu, lc_id)
        ind = np.isfinite(flux)
        return list(mjd[ind].astype(float)), list(flux[ind].astype(float))

    @gen.coroutine
    def get(self, hdu, lc_id):
        mjd, flux = yield executor.submit(self.fetch_data, hdu, lc_id)
        self.write({'data': list(zip(mjd, flux))})

class MeanCoordinateHandler(tornado.web.RequestHandler):
    def fetch_coordinate(self, coord_type, lc_id):
        with fitsio.FITS(filename) as infile:
            value = fetch_from_fits(
                infile, 'ccd{coord_type}'.format(coord_type=coord_type), lc_id)
        return {'data': float(np.median(value))}

    @gen.coroutine
    def get(self, coord_type, lc_id):
        results = yield executor.submit(
            self.fetch_coordinate, coord_type, lc_id)
        self.write(results)

class CoordinateHandler(tornado.web.RequestHandler):
    def fetch_coordinate(self, coord_type, lc_id):
        if coord_type == 'xs':
            hdu = 'ccdx'
        elif coord_type == 'ys':
            hdu = 'ccdy'
        else:
            raise RuntimeError("Invalid coordinate type")

        with fitsio.FITS(filename) as infile:
            mjd = fetch_from_fits(infile, 'hjd', lc_id)
            value = fetch_from_fits(infile, hdu, lc_id)

        sc = sigma_clip(value)
        ind = ~sc.mask
        return {'data': list(zip(mjd[ind].astype(float),
                                 value[ind].astype(float)))}

    @gen.coroutine
    def get(self, coord_type, lc_id):
        results = yield executor.submit(
            self.fetch_coordinate, coord_type, lc_id)
        self.write(results)

class ObjectNameHandler(tornado.web.RequestHandler):
    def fetch_obj_id(self, lc_id):
        with fitsio.FITS(filename) as infile:
            cat = infile['catalogue'].read()

        return {'data': cat['OBJ_ID'][lc_id].decode('utf-8')}

    @gen.coroutine
    def get(self,  lc_id):
        results = yield executor.submit(
            self.fetch_obj_id, lc_id)
        self.write(results)

class SysremBasisHandler(tornado.web.RequestHandler):
    def fetch_basis_function(self, basis_id):
        basis_id = int(basis_id)

        with fitsio.FITS(filename) as infile:
            imagelist = infile['imagelist'].read()

        mjd = imagelist['TMID']
        aj = imagelist['AJ'].T[basis_id]

        return {'data': list(zip(mjd.astype(float), aj.astype(float)))}

    @gen.coroutine
    def get(self,  basis_id):
        results = yield executor.submit(
            self.fetch_basis_function, basis_id)
        self.write(results)



application = tornado.web.Application([
    (r'/', IndexHandler),
    (r'/view/([0-9]+)', DetailHandler),
    # API
    (r'/api/object_index/([0-9]+)', ObjectIndexHandler),
    (r'/api/data', FRMSHandler),
    (r'/api/lc/([a-z]+)/([0-9]+)', LightcurveHandler),
    (r'/api/([xy])/([0-9]+)', MeanCoordinateHandler),
    (r'/api/([xy]s)/([0-9]+)', CoordinateHandler),
    (r'/api/obj_id/([0-9]+)', ObjectNameHandler),
    (r'/api/sysrem_basis/([0-9]+)', SysremBasisHandler),
], static_path='static', debug=True)

if __name__ == '__main__':
    port = 5000
    application.listen(port)
    logger.info('Application listening on port %s', port)
    tornado.ioloop.IOLoop().current().start()
