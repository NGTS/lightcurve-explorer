#!/usr/bin/env python
# -*- coding: utf-8 -*-

import fitsio
import argparse
import IPython
import logging
from scipy.stats import binned_statistic
from astropy.stats import sigma_clip
from pylab import *

plt.ion()

logging.basicConfig(
    level='INFO', format='[%(asctime)s] %(levelname)8s %(message)s')
logger = logging.getLogger(__name__)

def fetch_from_fits(infile, hdu, index, skip=0):
    return infile[hdu][index:index + 1, skip:].ravel()

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
