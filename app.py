from flask import Flask, jsonify, render_template
import joblib
import fitsio
import numpy as np
import argparse
from scipy import stats
from astropy.stats import sigma_clip
import sys
sys.path.append('.')

from binmodule import fast_bin

def fetch_from_fits(infile, hdu, index):
    return infile[hdu][index:index + 1, :].ravel()


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

        self.preload_aperture_indexes()

    def run(self, *args, **kwargs):
        self.app.run(*args, **kwargs)

    def extract_data(self):
        with fitsio.FITS(self.filename) as infile:
            flux = infile[args.hdu].read()

        sc_flux = sigma_clip(flux, axis=1)

        if self.npts_per_bin is not None:
            sc_flux = self.bin_by(sc_flux)

        med_flux = np.median(sc_flux, axis=1)
        mad_flux = np.median(np.abs(sc_flux - med_flux[:, np.newaxis]), axis=1)
        std_flux = 1.48 * mad_flux
        frms = std_flux / med_flux
        return med_flux, frms

    def bin_1d(self, flux, x=None):
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
        return jsonify({'data': self.google_xyseries(*args, **kwargs)})

    def get_lightcurve(self, hdu, index):
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

    def fetch_lightcurve(self, hdu, lc_id):
        real_lc_id = self.aperture_indexes[self.ind][lc_id]
        mjd, flux = self.get_lightcurve(hdu, real_lc_id)
        ind = np.isfinite(flux)
        return self.json_xyseries(
            mjd[ind].astype(float), flux[ind].astype(float))

    def index(self):
        return render_template('index.html')

    def fetch_x(self, lc_id):
        real_lc_id = self.aperture_indexes[self.ind][lc_id]
        with fitsio.FITS(self.filename) as infile:
            x = fetch_from_fits(infile, 'ccdx', real_lc_id)
        return jsonify({'data': float(np.median(x))})

    def fetch_y(self, lc_id):
        real_lc_id = self.aperture_indexes[self.ind][lc_id]
        with fitsio.FITS(self.filename) as infile:
            y = fetch_from_fits(infile, 'ccdy', real_lc_id)
        return jsonify({'data': float(np.median(y))})


    def fetch_binning(self):
        return jsonify({'binning': self.npts_per_bin})

    def fetch_obj_id(self, lc_id):
        real_lc_id = self.aperture_indexes[self.ind][lc_id]
        with fitsio.FITS(self.filename) as infile:
            cat = infile['catalogue'].read()

        return jsonify({'data': cat['OBJ_ID'][real_lc_id].decode('utf-8')})

    def fetch_sysrem_basis_functions(self, basis_id):
        with fitsio.FITS(self.filename) as infile:
            imagelist = infile['imagelist'].read()

        mjd = imagelist['TMID']
        aj = imagelist['AJ'].T[basis_id]

        return self.json_xyseries(mjd.astype(float), aj.astype(float))

    def show_object(self, lc_id):
        real_lc_id = self.aperture_indexes[self.ind][lc_id]
        return render_template('view.html', lc_id=real_lc_id)



if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('filename')
    parser.add_argument('-b', '--bin', required=False, type=int)
    parser.add_argument('-H', '--hdu', required=False, default='tamflux')
    args = parser.parse_args()
    VisualiseLightcurve(args).run(host='0.0.0.0', debug=True)
