from joblib import Memory
import numpy as np

memory = Memory(cachedir='.tmp', verbose=0)


# @memory.cache
def fast_bin(flux, bin_size, bin_fn=np.average):
    nbins = np.floor(flux.shape[1] / bin_size).astype(int)
    out = np.zeros((flux.shape[0], nbins))
    bins = range(nbins)
    for i in bins:
        values = flux[:, i * bin_size:(i + 1) * bin_size]
        averaged = bin_fn(values, axis=1)
        out[:, i] = averaged
    return out
