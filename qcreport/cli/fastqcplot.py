#!/usr/bin/env python
#
# Plot fastqc data

from .. import get_version
import sys
import os
import optparse
from ..fastqc import ufastqcplot

def main():
    # Process command line
    p = optparse.OptionParser(usage="%prog FASTQC_SUMMARY",
                              version="%prog "+get_version(),)
    opts,args = p.parse_args()
    if len(args) != 1:
        p.error("Need to supply one FastQC summary files")
    summary = args[0]
    # Make the summary plot
    ##outfile = os.path.splitext(os.path.basename(fq))[0] + '.png'
    outfile = 'ufastqc.png'
    ufastqcplot(summary,outfile)

if __name__ == '__main__':
    main()
