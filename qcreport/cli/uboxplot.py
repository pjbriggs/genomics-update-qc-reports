#!/usr/bin/env python
#
# Micro boxplot generation from Fastq quality data

from .. import get_version
import sys
import os
import optparse
from ..boxplots import uboxplot_from_fastq
from ..boxplots import uboxplot_from_fastqc_data

def main():
    # Process command line
    p = optparse.OptionParser(usage="%prog FASTQ|FASTQC_DATA",
                              version="%prog "+get_version(),)
    opts,args = p.parse_args()
    if len(args) != 1:
        p.error("Need to supply FASTQ file or fastqc_data.txt file")
    # Try to detect if file is fastq_data.txt or FASTQ
    # and call the appropriate function
    with open(args[0],'r') as fp:
        line = fp.readline()
        if line.startswith('##FastQC'):
            uboxplotter = uboxplot_from_fastqc_data
        else:
            uboxplotter = uboxplot_from_fastq
    # Make the boxplot
    outfile = os.path.splitext(os.path.basename(args[0]))[0] + '.png'
    uboxplotter(args[0],outfile)

if __name__ == '__main__':
    main()
