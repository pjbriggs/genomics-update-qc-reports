#!/usr/bin/env python
#
# boxplotting library
from bcftbx.FASTQFile import FastqIterator
from PIL import Image

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
    #print quality_per_base

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
        #print "Position: %d" % pos
        # Expand to a list
        scores = ''
        for q in counts:
            scores += q*counts[q]
        # Sort into order
        scores = ''.join(sorted(scores))
        #print scores
        # Get the mean (scores are Phred+33 encoded)
        mean = float(sum([(ord(q)-33) for q in scores]))/nreads
        #print "Mean: %.2f" % mean
        # Get the median etc
        median = ord(scores[median_pos])-33
        q25 = ord(scores[q25_pos])-33
        q75 = ord(scores[q75_pos])-33
        p10 = ord(scores[p10_pos])-33
        p90 = ord(scores[p90_pos])-33
        #print "Median: %d" % median
        #print "Q25   : %d" % q25
        #print "Q75   : %d" % q75
        #print "P10   : %d" % p10
        #print "P90   : %d" % p90
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
