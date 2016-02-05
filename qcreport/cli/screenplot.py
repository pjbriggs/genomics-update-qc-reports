#!/usr/bin/env python
#
# Plot fastqscreen data

from .. import get_version
import sys
import os
import optparse
from ..screens import screenplot
from ..screens import uscreenplot

def main():
    # Process command line
    p = optparse.OptionParser(usage="%prog SCREEN [SCREEN...]",
                              version="%prog "+get_version(),)
    p.add_option('-t','--threshold',action='store',
                 dest='threshold',default=None,type='float',
                 help="only include organisms with a minimum "
                 "percentage of mapped reads above this "
                 "threshold (default no threshold)")
    p.add_option('-u',action='store_true',dest='micro',
                 help="make a 'micro' screen plot")
    opts,args = p.parse_args()
    if len(args) < 1:
        p.error("Need to supply one or more FastqScreen .txt files")
    screen_files = args[:]
    # Make the boxplot
    ##outfile = os.path.splitext(os.path.basename(fq))[0] + '.png'
    outfile = 'ex.png'
    if opts.micro:
        uscreenplot(screen_files,outfile)
    else:
        if opts.threshold is not None:
            threshold = opts.threshold/100.0
        else:
            threshold = None
        screenplot(screen_files,outfile,threshold=threshold)

if __name__ == '__main__':
    main()
