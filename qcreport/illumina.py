#!/usr/bin/env python
#
# illuminaqc library

import os
from auto_process_ngs.utils import AnalysisFastq
from bcftbx.qc.report import strip_ngs_extensions
from bcftbx.FASTQFile import FastqIterator
from PIL import Image

#######################################################################
# Classes
#######################################################################

class QCReporter:
    """
    Class describing QC results for an AnalysisProject

    """
    def __init__(self,project):
        """
        Initialise a new QCReporter instance

        Arguments:
           project (AnalysisProject): project to handle the QC for

        """
        self._project = project
        self._samples = []
        for sample in self._project.samples:
            self._samples.append(QCSample(sample))

    def report(self):
        """
        Report the QC for the project

        """
        for sample in self._samples:
            print "%s" % s.name
            for fq_pair in s.get_fastq_pairs(sample):
                if self._project.paired_end:
                    print "%s\t%s" % (os.path.basename(fq_pair[0]),
                                      os.path.basename(fq_pair[1]))
                else:
                    print "%s" % os.path.basename(fq_pair[0])

class QCSample:
    """
    Class describing QC results for an AnalysisSample

    """
    def __init__(self,sample):
        """
        Initialise a new QCSample instance

        Arguments:
           sample (AnalysisSample): sample instance
        
        """
        self._sample = sample
        self._fastq_pairs = get_fastq_pairs(sample)

    @property
    def name(self):
        return self._sample.name

class QCFastqSet:
    """
    Class describing QC results for a set of Fastq files

    A set can be a single or a pair of fastq files.

    """
    def __init__(self,*fastqs):
        """
        Initialise a new QCFastqSet

        Arguments:
           fastqs (str):

        """
        self._fastqs = list(fastqs)

#######################################################################
# Functions
#######################################################################

def get_fastq_pairs(sample):
    """
    Return pairs of Fastqs for an AnalysisSample instance

    Arguments:
       sample (AnalysisSample): sample to get Fastq pairs for

    Returns:
       list: list of Fastq path pairs

    """
    pairs = []
    fastqs_r1 = sample.fastq_subset(read_number=1)
    fastqs_r2 = sample.fastq_subset(read_number=2)
    for fqr1 in fastqs_r1:
        # Split up R1 name
        print "fqr1 %s" % fqr1
        fastq_base = os.path.basename(fqr1)
        dir_path = os.path.dirname(fqr1)
        try:
            i = fastq_base.index('.')
            ext = fastq_base[i:]
        except ValueError:
            ext = ''
        # Generate equivalent R2 file
        fqr2 = AnalysisFastq(fqr1)
        fqr2.read_number = 2
        fqr2 = os.path.join(dir_path,"%s" % fqr2)
        if ext:
            fqr2 += ext
        print "fqr2 %s" % fqr2
        if fqr2 in fastqs_r2:
            pairs.append((fqr1,fqr2))
        else:
            pairs.append((fqr1,None))
    return pairs

def fastq_screen_output(fastq,screen_name):
    """
    Generate name of fastq_screen output files

    Given a Fastq file name and a screen name, the outputs from
    fastq_screen will look like:

    - {FASTQ}_{SCREEN_NAME}_screen.png
    - {FASTQ}_{SCREEN_NAME}_screen.txt

    Arguments:
       fastq (str): name of Fastq file
       screen_name (str): name of screen

    Returns:
       tuple: fastq_screen output names (without leading path)

    """
    base_name = "%s_%s_screen" % (strip_ngs_extensions(os.path.basename(fastq)),
                                  str(screen_name))
    
    return (base_name+'.png',base_name+'.txt')

def fastqc_output(fastq):
    """
    Generate name of FastQC outputs

    Given a Fastq file name, the outputs from FastQC will look
    like:

    - {FASTQ}_fastqc
    - {FASTQ}_fastqc.html
    - {FASTQ}_fastqc.zip

    Arguments:
       fastq (str): name of Fastq file

    Returns:
       tuple: FastQC outputs (without leading paths)

    """
    base_name = "%s_fastqc" % strip_ngs_extensions(os.path.basename(fastq))
    return (base_name,base_name+'.html',base_name+'.zip')

def uboxplot(fastq,outfile):
    """
    Generate 'micro-boxplot' for Fastq quality scores

    'Micro-boxplot' is a thumbnail version of the quality boxplots for a
    Fastq file.

    Arguments:
       fastq (str): path to a Fastq file
       outfile (str): path to output file

    Returns:
       ?

    """
    # Boxplots need: mean, median, 25/75th and 10/90th quantiles for each base
    #
    # To generate a bitmap in Python see:
    # http://stackoverflow.com/questions/20304438/how-can-i-use-the-python-imaging-library-to-create-a-bitmap

    # Initialise using first read for sequence length
    quality_per_base = []
    for read in FastqIterator(fastq):
        for i in xrange(read.seqlen):
            quality_per_base.append({})
            for j in xrange(ord('!'),ord('I')+1):
                quality_per_base[i][chr(j)] = 0
        break

    # Iterate through fastq file and count quality scores
    nreads = 0
    for read in FastqIterator(fastq):
        nreads += 1
        for pos,q in enumerate(read.quality):
            quality_per_base[pos][q] += 1
    print quality_per_base

    # Median etc positions
    # FIXME these are not correct if the list has an odd number of values!
    median_pos = nreads/2
    q25_pos = median_pos/2
    q75_pos = median_pos + q25_pos
    # For percentiles see http://stackoverflow.com/a/2753343/579925
    # FIXME 10th/90th percentiles is a fudge here
    p10_pos = nreads/10
    p90_pos = nreads - p10_pos

    # Initialise output image instance
    img = Image.new('RGB',(len(quality_per_base),40),"white")
    pixels = img.load()

    # For each base position determine stats
    for pos,counts in enumerate(quality_per_base):
        print "Position: %d" % pos
        # Expand to a list
        scores = ''
        for q in counts:
            scores += q*counts[q]
        # Sort into order
        scores = ''.join(sorted(scores))
        print scores
        # Get the mean (scores are Phred+33 encoded)
        mean = float(sum([(ord(q)-33) for q in scores]))/nreads
        print "Mean: %.2f" % mean
        # Get the median etc
        median = ord(scores[median_pos])-33
        q25 = ord(scores[q25_pos])-33
        q75 = ord(scores[q75_pos])-33
        p10 = ord(scores[p10_pos])-33
        p90 = ord(scores[p90_pos])-33
        print "Median: %d" % median
        print "Q25   : %d" % q25
        print "Q75   : %d" % q75
        print "P10   : %d" % p10
        print "P90   : %d" % p90
        # Draw onto the image
        for j in xrange(p10,p90):
            # 10th-90th percentile coloured cyan
            pixels[pos,40-j] = (0,255,255)
        for j in xrange(q25,q75):
            # Interquartile range coloured yellow
            pixels[pos,40-j] = (255,255,0)
        # Mean coloured black
        pixels[pos,40-int(mean)] = (0,0,0)

    # Output the boxplot to file
    print "Saving to %s" % outfile
    img.save(outfile)
    return outfile
