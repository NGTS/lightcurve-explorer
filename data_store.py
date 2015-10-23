import fitsio
import numpy as np


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
