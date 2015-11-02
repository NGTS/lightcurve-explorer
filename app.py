from flask import Flask, jsonify, render_template
import fitsio
import numpy as np
import argparse
from scipy import stats
from astropy.stats import sigma_clip
import sys
import logging
from astropy.coordinates import SkyCoord
from astropy import units as u
sys.path.append('.')

from binmodule import fast_bin

logging.basicConfig(
    level='INFO', format='[%(asctime)s] %(levelname)8s %(message)s')
logger = logging.getLogger(__name__)

SKIP = 30

def fetch_from_fits(infile, hdu, index, skip=SKIP):
    return infile[hdu][index:index + 1, skip:].ravel()


def compute_extent(ts, percentile=5):
    '''
    Given a time series, compute the extent.

    Return the difference between the 100 - `percentile`th and `percentile`th
    percentiles
    '''
    percentiles = np.percentile(ts, [percentile, 100 - percentile])
    return percentiles[-1] - percentiles[0]


class VisualiseLightcurve(object):

    def __init__(self, args):
        self.filename = args.filename
        self.hdu = args.hdu
        self.npts_per_bin = args.bin
        self.app = Flask(__name__)

        self.app.add_url_rule('/', 'index', self.index)
        self.app.add_url_rule('/view/<int:lc_id>', 'show',
                              self.show_object)

        self.app.add_url_rule('/api/data', 'frms', self.frms)
        self.app.add_url_rule('/api/object_index/<int:lc_id>', 'object_index',
                              self.fetch_object_index)
        self.app.add_url_rule('/api/lc/<hdu>/<int:lc_id>', 'lc',
                              self.fetch_lightcurve)
        self.app.add_url_rule('/api/x/<int:lc_id>', 'x', self.fetch_x)
        self.app.add_url_rule('/api/y/<int:lc_id>', 'y', self.fetch_y)
        self.app.add_url_rule('/api/binning', 'binning', self.fetch_binning)
        self.app.add_url_rule('/api/obj_id/<int:lc_id>', 'obj_id',
                             self.fetch_obj_id)
        self.app.add_url_rule('/api/sysrem_basis/<int:basis_id>',
                              'sysrem_basis',
                              self.fetch_sysrem_basis_functions)
        self.app.add_url_rule('/api/xs/<int:lc_id>', 'xs', self.fetch_xs)
        self.app.add_url_rule('/api/ys/<int:lc_id>', 'ys', self.fetch_ys)
        self.app.add_url_rule('/api/coordinates/<int:lc_id>',
                              'coordinates', self.fetch_coordinates)

        self.preload_aperture_indexes()

    def run(self, *args, **kwargs):
        logger.info('Listening for connections')
        self.app.run(*args, **kwargs)

    def extract_data(self):
        logger.info('Extracting data')
        with fitsio.FITS(self.filename) as infile:
            flux = infile[args.hdu][:, SKIP:]

        logger.debug('Sigma clipping')
        sc_flux = sigma_clip(flux, axis=1)

        if self.npts_per_bin is not None:
            sc_flux = self.bin_by(sc_flux)

        logger.debug('Computing statistics')
        med_flux = np.median(sc_flux, axis=1)
        mad_flux = np.median(np.abs(sc_flux - med_flux[:, np.newaxis]), axis=1)
        std_flux = 1.48 * mad_flux
        frms = std_flux / med_flux
        return med_flux, frms

    def bin_1d(self, flux, x=None):
        logger.debug('Binning 1d')
        x = x if x is not None else np.arange(flux.size)
        bin_length = int(np.floor(flux.size / self.npts_per_bin))
        by, be, _ = stats.binned_statistic(x, flux,
                                           statistic='mean',
                                           bins=bin_length)
        return by, (be[:-1] + be[1:]) / 2.

    def bin_by(self, flux, x=None):
        return fast_bin(flux, self.npts_per_bin)

    def google_xyseries(self, x, y):
        return list(zip(list(x), list(y)))

    def json_xyseries(self, *args, **kwargs):
        extra_keys = kwargs.pop('extra_keys', {})
        out = {'data': self.google_xyseries(*args, **kwargs)}
        if extra_keys is not None:
            out.update(extra_keys)

        return jsonify(out)

    def get_lightcurve(self, hdu, index):
        logger.info('Fetching lightcurve {hdu}:{index}'.format(
            hdu=hdu, index=index))
        with fitsio.FITS(self.filename) as infile:
            mjd = fetch_from_fits(infile, 'hjd', index)
            flux = fetch_from_fits(infile, hdu, index)

        if self.npts_per_bin is not None:
            flux, mjd = self.bin_1d(flux, x=mjd)

        mjd0 = int(mjd.min())

        sc = sigma_clip(flux)

        return (mjd - mjd0)[~sc.mask], flux[~sc.mask]

    def preload_aperture_indexes(self):
        med_flux, frms = self.extract_data()
        self.ind = np.where((med_flux > 0) & (frms > 0))[0]
        self.aperture_indexes = np.arange(med_flux.size)
        return med_flux, frms

    def frms(self):
        med_flux, frms = self.preload_aperture_indexes()
        return self.json_xyseries(
            np.log10(med_flux[self.ind].astype(float)),
            np.log10(frms[self.ind].astype(float)))

    def get_real_lc_id(self, lc_id):
        real_lc_id = self.aperture_indexes[self.ind][lc_id]
        logger.debug('Lightcurve %s => %s', lc_id, real_lc_id)
        return int(real_lc_id)

    def fetch_object_index(self, lc_id):
        return jsonify({'index': self.get_real_lc_id(lc_id)})

    def fetch_lightcurve(self, hdu, lc_id):
        logger.info('Fetching lightcurve %s', lc_id)
        mjd, flux = self.get_lightcurve(hdu, lc_id)
        ind = np.isfinite(flux)
        extent = float(flux[ind].ptp())
        frms = float(flux[ind].std() / np.median(flux)) * 1000.
        return self.json_xyseries(
            mjd[ind].astype(float), flux[ind].astype(float),
            extra_keys={
                'extent': extent,
                'frms': frms,
            })

    def fetch_x(self, lc_id):
        logger.info('Fetching x %s', lc_id)
        with fitsio.FITS(self.filename) as infile:
            x = fetch_from_fits(infile, 'ccdx', lc_id)
        return jsonify({'data': float(np.median(x))})

    def fetch_y(self, lc_id):
        logger.info('Fetching y %s', lc_id)
        with fitsio.FITS(self.filename) as infile:
            y = fetch_from_fits(infile, 'ccdy', lc_id)
        return jsonify({'data': float(np.median(y))})

    def fetch_xs(self, lc_id):
        logger.info('Fetching xs %s', lc_id)
        with fitsio.FITS(self.filename) as infile:
            mjd = fetch_from_fits(infile, 'hjd', lc_id)
            x = fetch_from_fits(infile, 'ccdx', lc_id)

        sc = sigma_clip(x)
        ind = ~sc.mask
        extent = float(compute_extent(x[ind]))
        return self.json_xyseries(
            mjd[ind].astype(float), x[ind].astype(float),
            extra_keys={'extent': extent})

    def fetch_ys(self, lc_id):
        logger.info('Fetching ys %s', lc_id)
        with fitsio.FITS(self.filename) as infile:
            mjd = fetch_from_fits(infile, 'hjd', lc_id)
            y = fetch_from_fits(infile, 'ccdy', lc_id)

        sc = sigma_clip(y)
        ind = ~sc.mask
        extent = float(compute_extent(y[ind]))
        return self.json_xyseries(
            mjd[ind].astype(float), y[ind].astype(float),
            extra_keys={'extent': extent})

    def fetch_binning(self):
        logger.info('Fetching binning value')
        return jsonify({'binning': self.npts_per_bin})

    def fetch_obj_id(self, lc_id):
        logger.info('Fetching obj_id %s', lc_id)
        with fitsio.FITS(self.filename) as infile:
            cat = infile['catalogue'].read()

        return jsonify({'data': cat['OBJ_ID'][lc_id].decode('utf-8')})

    def fetch_sysrem_basis_functions(self, basis_id):
        logger.info('Fetching sysrem basis function %s', basis_id)
        with fitsio.FITS(self.filename) as infile:
            imagelist = infile['imagelist'].read()

        mjd = imagelist['TMID'][SKIP:]
        aj = imagelist['AJ'].T[basis_id][SKIP:]

        return self.json_xyseries(mjd.astype(float), aj.astype(float))

    def fetch_coordinates(self, lc_id):
        logger.info('Fetching coordinates %s', lc_id)
        with fitsio.FITS(self.filename) as infile:
            cat_entry = infile['catalogue'][lc_id:lc_id + 1][0]

        ra, dec = float(cat_entry['RA']), float(cat_entry['DEC'])
        coord = SkyCoord(ra * u.degree, dec * u.degree)

        ra_hms = coord.ra.to_string()
        dec_dms = coord.dec.to_string()

        return jsonify({'data': {
            'ra': '{ra:.5f}'.format(ra=ra),
            'dec': '{dec:.5f}'.format(dec=dec),
            'ra_full': float(ra),
            'dec_full': float(dec),
            'ra_hms': ra_hms,
            'dec_dms': dec_dms}})

    def index(self):
        return render_template('index.html', render_frms=True)

    def show_object(self, lc_id):
        return render_template('view.html', file_index=lc_id,
                              render_frms=False)



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
    logger.info('Skipping the first %s points', SKIP)
    VisualiseLightcurve(args).run(host=args.host, port=args.port,
                                  debug=args.debug)
