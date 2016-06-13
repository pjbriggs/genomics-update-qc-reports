#!/usr/bin/env python
#
# Micro boxplot generation from Fastq quality data

from .. import get_version
import sys
import os
import optparse
from ..plots import uboxplot

def main():
    # Process command line
    p = optparse.OptionParser(usage="%prog FASTQ|FASTQC_DATA",
                              version="%prog "+get_version(),)
    opts,args = p.parse_args()
    if len(args) != 1:
        p.error("Need to supply FASTQ file or fastqc_data.txt file")
    # Make output file name
    outfile = os.path.splitext(os.path.basename(args[0]))[0] + '.png'
    # Try to detect if file is fastq_data.txt or FASTQ
    # and call the plotter with the appropriate args
    with open(args[0],'r') as fp:
        line = fp.readline()
        if line.startswith('##FastQC'):
            uboxplot(fastq_data=args[0],outfile=outfile)
        else:
            uboxplot(fastq=args[0],outfile=outfile)

if __name__ == '__main__':
    main()
