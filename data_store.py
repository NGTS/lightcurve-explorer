import fitsio
import numpy as np


class DataStore(object):
    def __init__(self, hdulist):
        self.hdulist = hdulist

    @classmethod
    def from_filename(cls, filename):
        hdulist = fitsio.FITS(filename)
        return cls(hdulist)


    def get(self, hdu):
        return np.array([[]])
