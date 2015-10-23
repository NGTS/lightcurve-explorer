import sys
sys.path.append('.')
from data_store import DataStore
import fitsio
import numpy as np


class TestDataStoreConstruction(object):
    def setup(self):
        self.fits_filename = '/ngts/pipedev/ParanalOutput/nightly_data/20150909-ng2000-802-custom-flat-high-quality.fits'


    def test_read_from_hdulist(self):
        hdulist = fitsio.FITS(self.fits_filename)
        store = DataStore(hdulist)
        assert store.hdulist == hdulist


    def test_get_array(self):
        store = DataStore.from_filename(self.fits_filename)
        assert len(store.get('flux').shape) == 2


    def test_get_timeseries(self):
        store = DataStore.from_filename(self.fits_filename)
        assert len(store.get('flux', aperture=0).shape) == 1


    def test_caching_array(self):
        with fitsio.FITS(self.fits_filename) as infile:
            flux = infile['flux'].read()

        store = DataStore.from_filename(self.fits_filename)
        store.get('flux')
        assert np.all(store._cache[('flux', None)] == flux)


    def test_caching_lc(self):
        with fitsio.FITS(self.fits_filename) as infile:
            lc = infile['flux'][0:1, :].ravel()

        store = DataStore.from_filename(self.fits_filename)
        store.get('flux', aperture=0)
        assert np.all(store._cache[('flux', 0)] == lc)

    def test_bin_1d(self):
        arr = np.array([1, 1, 2, 2])
        assert np.all(DataStore.bin_1d(arr, 2)[0] == np.array([1, 2]))
