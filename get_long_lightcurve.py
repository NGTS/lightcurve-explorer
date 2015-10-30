#!/usr/bin/env python
# -*- coding: utf-8 -*-

import fitsio
import argparse
import IPython
import logging
from scipy.stats import binned_statistic
from astropy.stats import sigma_clip
from gatspy.periodic import FastLombScargle
from pylab import *

plt.ion()

logging.basicConfig(
    level='INFO', format='[%(asctime)s] %(levelname)8s %(message)s')
logger = logging.getLogger(__name__)

def fetch_from_fits(infile, hdu, index, skip=0):
    return infile[hdu][index:index + 1, skip:].ravel()

def bin(y, bins, x=None, statistic='median'):
    x = x if x is not None else np.arange(y.size)
    by, bx, _ = binned_statistic(x, y, statistic=statistic, bins=bins)
    return (bx[:-1] + bx[1:]) / 2., by

def nightly_bin(x, y, nights, bins, statistic='median'):
    unique_nights = np.unique(nights)
    out_x, out_y = [], []
    for night in unique_nights:
        ind = nights == night
        bx, by = bin(y[ind], x=x[ind], bins=bins, statistic=statistic)
        out_x.append(bx)
        out_y.append(by)

    return np.array(out_x).ravel(), np.array(out_y).ravel()

def period_fit(x, y, period_range):
    model = FastLombScargle(fit_period=True)
    model.optimizer.set(quiet=False, period_range=period_range)
    model.fit(x, y)
    return model

def periodogram(model, nperiods=1000):
    period_range = model.optimizer.period_range
    periods = np.logspace(np.log10(period_range[0]),
                          np.log10(period_range[1]), nperiods)
    power = model.periodogram(periods)
    return periods, power

def main(args):
    if args.verbose:
        logger.setLevel('DEBUG')
    logger.debug(args)

    ap = args.ap
    with fitsio.FITS(args.filename) as infile:
        hjd = fetch_from_fits(infile, 'hjd', ap)
        if 'TAMFLUX' in infile:
            # NGTS pipeline output
            rawflux = fetch_from_fits(infile, 'flux', ap)
            tamflux = fetch_from_fits(infile, 'tamflux', ap)
            casuflux = fetch_from_fits(infile, 'casudet', ap)
        else:
            # Post-sysrem file
            rawflux = None
            tamflux = fetch_from_fits(infile, 'flux', ap)
            casuflux = None
        skybkg = fetch_from_fits(infile, 'skybkg', ap)
        imagelist = infile['imagelist'].read()
        cat = infile['catalogue'].read()[ap]

    header = '''
variables available:
    * hjd
    * rawflux (may be None)
    * tamflux
    * casuflux (may be None)
    * skybkg
    * imagelist
    * cat
'''

    IPython.embed(header=header)



if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('filename')
    parser.add_argument('-a', '--ap', required=True, type=int)
    parser.add_argument('-v', '--verbose', action='store_true')
    main(parser.parse_args())
