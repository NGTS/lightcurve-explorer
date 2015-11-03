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
from astropy.coordinates import SkyCoord
from astropy import units as u
import numpy as np
import joblib
from scipy.stats import binned_statistic
import argparse

logging.basicConfig(
    level='DEBUG', format='[%(asctime)s] %(levelname)8s %(message)s')
logger = logging.getLogger(__name__)

executor = concurrent.futures.ThreadPoolExecutor()
memory = joblib.Memory(cachedir='.tmp')

filename = 'data/20150911-ng2000-802-custom-flat-high-quality.fits'
npts_per_bin = 100

def compute_extent(ts, percentile=5):
    '''
    Given a time series, compute the extent.

    Return the difference between the 100 - `percentile`th and `percentile`th
    percentiles
    '''
    percentiles = np.percentile(ts, [percentile, 100 - percentile])
    return percentiles[-1] - percentiles[0]

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
def extract_data(filename, npts_per_bin):
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


def get_lightcurve(hdu, lc_id):
    with fitsio.FITS(filename) as infile:
        mjd = fetch_from_fits(infile, 'hjd', lc_id)
        flux = fetch_from_fits(infile, hdu, lc_id)

    if npts_per_bin is not None:
        flux, mjd = bin_1d(flux, x=mjd)

    mjd0 = int(mjd.min())

    sc = sigma_clip(flux)

    return (mjd - mjd0)[~sc.mask], flux[~sc.mask]

class BaseHandler(tornado.web.RequestHandler):
    def initialize(self, args, aperture_indexes, ind,
                  frms, med_flux):
        self.args = args
        self.aperture_indexes = aperture_indexes
        self.ind = ind
        self.frms = frms
        self.med_flux = med_flux


class IndexHandler(BaseHandler):
    def get(self):
        self.render('templates/index.html', npts_per_bin=npts_per_bin,
                   render_frms=True)

class DetailHandler(BaseHandler):
    def get(self, lc_id):
        self.render('templates/view.html', file_index=lc_id,
                   render_frms=False)

class ObjectIndexHandler(BaseHandler):
    def real_index(self, i):
        return int(self.aperture_indexes[self.ind][int(i)])

    def get(self, lc_id):
        self.write({'index': self.real_index(lc_id)})

class FRMSHandler(BaseHandler):
    def format_frms(self):
        return {'data': list(zip(
            list(np.log10(self.med_flux[self.ind].astype(float))),
            list(np.log10(self.frms[self.ind].astype(float)))))}

    @gen.coroutine
    def get(self):
        results = yield executor.submit(self.format_frms)
        self.write(results)

class LightcurveHandler(BaseHandler):
    def fetch_data(self, hdu, lc_id):
        mjd, flux = get_lightcurve(hdu, lc_id)
        ind = np.isfinite(flux)
        return mjd[ind].astype(float), flux[ind].astype(float)

    @gen.coroutine
    def get(self, hdu, lc_id):
        mjd, flux = yield executor.submit(self.fetch_data, hdu, lc_id)
        ind = np.isfinite(flux)
        extent = float(flux[ind].ptp())
        frms = float(flux[ind].std() / np.median(flux)) * 1000.
        self.write({
            'data': list(zip(mjd, flux)),
            'extent': extent,
            'frms': frms,
        })

class MeanCoordinateHandler(BaseHandler):
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

class CoordinateHandler(BaseHandler):
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
        extent = float(compute_extent(sc[ind]))
        return {
            'data': list(zip(mjd[ind].astype(float),
                             value[ind].astype(float))),
            'extent': extent,
        }

    @gen.coroutine
    def get(self, coord_type, lc_id):
        results = yield executor.submit(
            self.fetch_coordinate, coord_type, lc_id)
        self.write(results)

class ObjectNameHandler(BaseHandler):
    def fetch_obj_id(self, lc_id):
        with fitsio.FITS(filename) as infile:
            cat = infile['catalogue'].read()

        return {'data': cat['OBJ_ID'][int(lc_id)].decode('utf-8')}

    @gen.coroutine
    def get(self,  lc_id):
        results = yield executor.submit(
            self.fetch_obj_id, lc_id)
        self.write(results)

class SysremBasisHandler(BaseHandler):
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

class EquatorialCoordinateHandler(BaseHandler):
    def fetch_coordinates(self, lc_id):
        with fitsio.FITS(filename) as infile:
            cat_entry = infile['catalogue'][lc_id:lc_id + 1][0]

        ra, dec = float(cat_entry['RA']), float(cat_entry['DEC'])
        coord = SkyCoord(ra * u.degree, dec * u.degree)

        ra_hms = coord.ra.to_string()
        dec_dms = coord.dec.to_string()

        return {'data': {
            'ra': '{ra:.5f}'.format(ra=ra),
            'dec': '{dec:.5f}'.format(dec=dec),
            'ra_full': float(ra),
            'dec_full': float(dec),
            'ra_hms': ra_hms,
            'dec_dms': dec_dms}}

    @gen.coroutine
    def get(self, lc_id):
        lc_id = int(lc_id)
        results = yield executor.submit(self.fetch_coordinates, lc_id)
        self.write(results)


def construct_application(args, ind, med_flux, frms, aperture_indexes):
    url_mapping = [
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
        (r'/api/coordinates/([0-9]+)', EquatorialCoordinateHandler),
    ]

    constructor_params = {
        'args': args,
        'aperture_indexes': aperture_indexes,
        'ind': ind,
        'frms': frms,
        'med_flux': med_flux,
    }

    application = tornado.web.Application([
        (route, handler, constructor_params)
        for (route, handler) in url_mapping
    ], static_path='static', debug=args.debug)
    return application

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('filename', help='File to analyse')
    parser.add_argument('-b', '--bin', required=False, type=int,
                        help='Number of data points to bin togther')
    parser.add_argument('-H', '--hdu', required=False, default='tamflux',
                        help='HDU to extract flux from')
    parser.add_argument('-p', '--port', required=False, default=5000, type=int,
                        help='Port to listen to')
    parser.add_argument('--host', required=False, default='0.0.0.0',
                        help='Host to listen to')
    parser.add_argument('-v', '--verbose', action='store_true')
    parser.add_argument('--debug', action='store_true',
                        help='Run the debug server')
    args = parser.parse_args()
    if args.verbose:
        logger.setLevel('DEBUG')
    logger.debug(args)

    ind, med_flux, frms = extract_data(args.filename, npts_per_bin=args.bin)
    aperture_indexes = np.arange(med_flux.size)

    logger.info('Application listening on port %s', args.port)
    application = construct_application(args, ind, med_flux, frms,
                                        aperture_indexes)
    application.listen(args.port)
    tornado.ioloop.IOLoop().current().start()
