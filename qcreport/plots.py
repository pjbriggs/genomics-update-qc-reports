#!/usr/bin/env python
#
# QC plot generation
import os
import tempfile
from math import ceil
from matplotlib import pyplot as plt
from PIL import Image
from bcftbx.htmlpagewriter import PNGBase64Encoder
from .fastqc import FastqcData
from .fastqc import FastqcSummary
from .screens import Fastqscreen
from .fastq_stats import FastqQualityStats

# Colours taken from http://www.rapidtables.com/web/color/RGB_Color.htm
RGB_COLORS = {
    'black': (0,0,0),
    'blue': (0,0,255),
    'cyan': (0,255,255),
    'darkyellow1': (204,204,0),
    'grey': (145,145,145),
    'lightgrey': (211,211,211),
    'orange': (255,165,0),
    'red': (255,0,0),
    'yellow': (255,255,0),
}

def encode_png(png_file):
    """
    Return Base64 encoded string for a PNG
    """
    return "data:image/png;base64," + \
        PNGBase64Encoder().encodePNG(png_file)

def screenplot(screen_files,outfile,threshold=None):
    """
    Generate plot of FastqScreen outputs

    Arguments:
      screen_files (list): list of paths to one or more
        ...screen.txt files from FastqScreen
      outfile (str): path to output file,outfile
      threshold (float): minimum percentage of mapped
        reads (below which library is excluded)

    """
    # Read in the screen data
    screens = []
    for screen_file in screen_files:
        screens.append(Fastqscreen(screen_file))
    nscreens = len(screens)
    # Plot the data
    plt.figure(1)
    for i,screen_data in enumerate(screens):
        # Create a sub-plot
        plt.subplot(nscreens,1,i+1)
        # Filter on threshold
        if threshold:
            screen_data = filter(lambda x: float(x['%Unmapped'])
                                 <= (100.0-threshold),
                                 screen_data)
        # Make a stacked bar chart
        plt.grid(True)
        x = xrange(len(screen_data))
        for mapping,color in (('%Multiple_hits_multiple_libraries','#800000'),
                              ('%One_hit_multiple_libraries','#000099'),
                              ('%Multiple_hits_one_library','r'),
                              ('%One_hit_one_library','b'),):
            data = [r[mapping] for r in screen_data]
            plt.barh(x,data,color=color,label=mapping)
        # Add the library names
        plt.yticks([x+0.5 for x in xrange(len(screen_data))],
                   [r['Library'] for r in screen_data])
        # Set axis limits on current plot
        plt.gca().set_xlim([0,100])
        plt.gca().set_ylim([0,len(screen_data)])
        # Only set legend for last plot
        if i == 0:
            plt.legend(loc=4)
    # Write out plot
    plt.savefig(outfile)
    
def uscreenplot(screen_files,outfile=None,inline=None):
    """
    Generate 'micro-plot' of FastqScreen outputs

    Arguments:
      screen_files (list): list of paths to one or more
        ...screen.txt files from FastqScreen
      outfile (str): path to output file

    """
    # Read in the screen data
    screens = []
    for screen_file in screen_files:
        screens.append(Fastqscreen(screen_file))
    nscreens = len(screens)
    # Make a small stacked bar chart
    bbox_color = (145,145,145)
    barwidth = 4
    width = nscreens*50
    n_libraries_max = max([len(s) for s in screens])
    height = (n_libraries_max + 1)*(barwidth + 1)
    img = Image.new('RGB',(width,height),"white")
    pixels = img.load()
    # Process each screen in turn
    for nscreen,screen in enumerate(screens):
        xorigin = nscreen*50
        xend = xorigin+50-1
        yend = height-1
        # Draw a box around the plot
        for i in xrange(xorigin,xorigin+50):
            pixels[i,0] = bbox_color
            pixels[i,yend] = bbox_color
        for j in xrange(height):
            pixels[xorigin,j] = bbox_color
            pixels[xend,j] = bbox_color
        # Draw the stacked bars for each library
        for n,library in enumerate(screen.libraries):
            data = filter(lambda x: x['Library'] == library,screen)[0]
            x = xorigin
            y = n*(barwidth+1) + 1
            for mapping,rgb in (('%One_hit_one_library',(0,0,153)),
                                ('%Multiple_hits_one_library',(0,0,255)),
                                ('%One_hit_multiple_libraries',(255,0,0)),
                                ('%Multiple_hits_multiple_libraries',(128,0,0))):
                # Round up to nearest pixel (so that non-zero
                # percentages are always represented)
                npx = int(ceil(data[mapping]/2.0))
                for i in xrange(x,x+npx):
                    for j in xrange(y,y+barwidth):
                        pixels[i,j] = rgb
                x += npx
        # Add 'no hits'
        x = xorigin
        y = n_libraries_max*(barwidth+1) + 1
        npx = int(screen.no_hits/2.0)
        for i in xrange(x,x+npx):
            for j in xrange(y,y+barwidth):
                pixels[i,j] = bbox_color
    # Output the plot to file
    fp,tmp_plot = tempfile.mkstemp(".ufastqscreen.png")
    img.save(tmp_plot)
    os.fdopen(fp).close()
    if inline:
        encoded_plot = encode_png(tmp_plot)
    if outfile is not None:
        os.rename(tmp_plot,outfile)
    os.remove(tmp_plot)
    if inline:
        return encoded_plot
    else:
        return outfile

def uboxplot(fastqc_data=None,fastq=None,
             outfile=None,inline=None):
    """
    Generate FASTQ per-base quality 'micro-boxplot'

    'Micro-boxplot' is a thumbnail version of the per-base
    quality boxplots for a FASTQ file.

    Arguments:
       fastqc_data (str): path to a ``fastqc_data.txt``
        file
       outfile (str): path to output file

    Returns:
       String: path to output PNG file

    """
    # Boxplots need: mean, median, 25/75th and 10/90th quantiles
    # for each base
    fastq_stats = FastqQualityStats()
    if fastqc_data is not None:
        fastq_stats.from_fastqc_data(fastqc_data)
    elif fastq is not None:
        fastq_stats.from_fastq(fastq)
    else:
        raise Exception("supply path to fastqc_data.txt or fastq file")
    # To generate a bitmap in Python see:
    # http://stackoverflow.com/questions/20304438/how-can-i-use-the-python-imaging-library-to-create-a-bitmap
    #
    # Initialise output image instance
    img = Image.new('RGB',(fastq_stats.nbases,40),"white")
    pixels = img.load()
    # Draw a box around the outside
    box_color = RGB_COLORS['grey']
    for i in xrange(fastq_stats.nbases):
        pixels[i,0] = box_color
        pixels[i,40-1] = box_color
    for j in xrange(40):
        pixels[0,j] = box_color
        pixels[fastq_stats.nbases-1,j] = box_color
    # For each base position determine stats
    for i in xrange(fastq_stats.nbases):
        #print "Position: %d" % i
        for j in xrange(fastq_stats.p10[i],fastq_stats.p90[i]):
            # 10th-90th percentile coloured cyan
            pixels[i,40-j] = RGB_COLORS['lightgrey']
        for j in xrange(fastq_stats.q25[i],fastq_stats.q75[i]):
            # Interquartile range coloured yellow
            pixels[i,40-j] = RGB_COLORS['darkyellow1']
        # Median coloured red
        pixels[i,40-int(fastq_stats.median[i])] = RGB_COLORS['red']
        # Mean coloured black
        pixels[i,40-int(fastq_stats.mean[i])] = RGB_COLORS['blue']
    # Output the plot to file
    fp,tmp_plot = tempfile.mkstemp(".uboxplot.png")
    img.save(tmp_plot)
    os.fdopen(fp).close()
    if inline:
        encoded_plot = encode_png(tmp_plot)
    if outfile is not None:
        os.rename(tmp_plot,outfile)
    os.remove(tmp_plot)
    if inline:
        return encoded_plot
    else:
        return outfile

def ufastqcplot(summary_file,outfile=None,inline=False):
    """
    Make a 'micro' summary plot of FastQC output

    The micro plot is a small PNG which represents the
    summary results from each FastQC module in a
    matrix, with rows representing the modules and
    three columns representing the status ('PASS', 'WARN'
    and 'FAIL', from left to right).

    For example (in text form):

          ==
    ==
    ==
       ==
    ==

    indictaes that the status of the first module is
    'FAIL', the 2nd, 3rd and 5th are 'PASS', and the
    4th is 'WARN'.

    Arguments:
      summary_file (str): path to a FastQC
        'summary.txt' output file
      outfile (str): path for the output PNG

    """
    status_codes = {
        'PASS' : { 'index': 0,
                   'color': 'green',
                   'rgb': (0,128,0),
                   'hex': '#008000' },
        'WARN' : { 'index': 1,
                   'color': 'orange',
                   'rgb': (255,165,0),
                   'hex': '#FFA500' },
        'FAIL' : { 'index': 2,
                   'color': 'red',
                   'rgb': (255,0,0),
                   'hex': '#FF0000' },
        }
    fastqc_summary = FastqcSummary(summary_file)
    # Initialise output image instance
    nmodules = len(fastqc_summary.modules)
    img = Image.new('RGB',(30,4*nmodules),"white")
    pixels = img.load()
    # For each test: put a mark depending on the status
    for im,m in enumerate(fastqc_summary.modules):
        code = status_codes[fastqc_summary.status(m)]
        # Make the mark
        x = code['index']*10 + 1
        #y = 4*nmodules - im*4 - 3
        y = im*4 + 1
        for i in xrange(x,x+8):
            for j in xrange(y,y+3):
                #print "%d %d" % (i,j)
                pixels[i,j] = code['rgb']
    # Output the plot to file
    fp,tmp_plot = tempfile.mkstemp(".ufastqc.png")
    img.save(tmp_plot)
    os.fdopen(fp).close()
    if inline:
        encoded_plot = encode_png(tmp_plot)
    if outfile is not None:
        os.rename(tmp_plot,outfile)
    os.remove(tmp_plot)
    if inline:
        return encoded_plot
    else:
        return outfile

