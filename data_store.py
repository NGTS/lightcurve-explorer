import fitsio
import numpy as np
from scipy import stats

from binmodule import fast_bin


class DataStore(object):
    def __init__(self, hdulist):
        self.hdulist = hdulist
        self._cache = {}

    @classmethod
    def from_filename(cls, filename):
        hdulist = fitsio.FITS(filename)
        return cls(hdulist)

    def _cache_fn(self, key, fn):
        try:
            value = self._cache[key]
        except KeyError:
            value = fn()
            self._cache[key] = value
        return value

    def get(self, hdu_name, aperture=None):
        hdu = self.hdulist[hdu_name]
        if aperture is not None:
            key = (hdu_name, aperture)
            return self._cache_fn(key,
                lambda: hdu[aperture:aperture+1, :].ravel())
        else:
            key = (hdu_name, None)
            return self._cache_fn(key,
                lambda: hdu.read())

    @staticmethod
    def bin_1d(timeseries, npts, x=None):
        x = x if x is not None else np.arange(timeseries.size)
        bin_length = int(np.floor(timeseries.size / npts))
        by, be, _ = stats.binned_statistic(x, timeseries,
                                           statistic='mean',
                                           bins=bin_length)
        return by, (be[:-1] + be[1:]) / 2.

    @staticmethod
    def bin_2d(arr, npts):
        return fast_bin(arr, npts)

    def get_and_bin(self, hdu_name, npts, x=None, aperture=None):
        data = self.get(hdu_name, aperture=aperture)
        if aperture is not None:
            return self.bin_1d(data, npts, x=x)
        else:
            return self.bin_2d(data, npts)
