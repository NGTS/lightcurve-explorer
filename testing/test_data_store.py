import sys
sys.path.append('.')
from data_store import DataStore
import fitsio


class TestDataStoreConstruction(object):
    def setup(self):
        self.fits_filename = '/ngts/pipedev/ParanalOutput/nightly_data/20150909-ng2000-802-custom-flat-high-quality.fits'


    def test_read_from_hdulist(self):
        hdulist = fitsio.FITS(self.fits_filename)
        store = DataStore(hdulist)
        assert store.hdulist == hdulist


    def test_get_timeseries(self):
        store = DataStore.from_filename(self.fits_filename)
        assert len(store.get('flux').shape) == 2
