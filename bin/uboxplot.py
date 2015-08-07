#!/usr/bin/env python
#
# Micro boxplot generation from Fastq quality data
#
# NB this version uses "pillow" for the PIL package

import sys
import os
import optparse
from qcreport.illumina import uboxplot

if __name__ == '__main__':
    
    # Process command line
    p = optparse.OptionParser()
    opts,args = p.parse_args()
    if len(args) != 1:
        p.error("Need to supply fastq file")
    fq = args[0]    
    # Make the boxplot
    outfile = os.path.splitext(os.path.basename(fq))[0] + '.png'
    uboxplot(fq,outfile)
