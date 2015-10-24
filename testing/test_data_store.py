import sys
sys.path.append('.')
from data_store import DataStore
import fitsio
import numpy as np
try:
    from unittest import mock
except ImportError:
    import mock


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

    def test_bin_2d(self):
        arr = np.array([[1, 1, 1, 1], [2, 2, 2, 2]])
        assert np.all(DataStore.bin_2d(arr, 2) == np.array([[1, 1], [2, 2]]))

    def test_get_and_bin(self):
        store = DataStore.from_filename(self.fits_filename)
        with mock.patch.object(store, 'get') as mock_get:
            mock_get.return_value = np.array([1, 1, 2, 2])
            value = store.get_and_bin('not used', npts=2, aperture=0)
        assert np.all(value[0] == np.array([1, 2]))
