#!/usr/bin/env python
#
# fastq screens library
import os
from bcftbx.TabFile import TabFile
from matplotlib import pyplot as plt
from PIL import Image
from math import ceil

"""
Example screen file for v0.4.1:

#Fastq_screen version: 0.4.1
Library	%Unmapped	%One_hit_one_library	%Multiple_hits_one_library	%One_hit_multiple_libraries	%Multiple_hits_multiple_libraries
hg19	98.10	0.02	0.27	0.55	1.06
mm9	35.92	47.46	10.18	3.56	2.88
rn4	93.01	0.18	0.17	3.87	2.77
dm3	99.97	0.00	0.00	0.01	0.02
ws200	99.98	0.00	0.00	0.00	0.02
ecoli	96.52	0.43	3.05	0.00	0.00
saccer	99.97	0.00	0.00	0.00	0.03
PhiX	99.33	0.67	0.00	0.00	0.00
Vectors	99.99	0.00	0.00	0.01	0.00
SpR6	100.00	0.00	0.00	0.00	0.00

%Hit_no_libraries: 30.80

Example screen file for v0.4.2:

#Fastq_screen version: 0.4.2	#Reads in subset: 1000000
Library	#Reads_processed	#Unmapped	%Unmapped	#One_hit_one_library	%One_hit_one_library	#Multiple_hits_one_library	%Multiple_hits_one_library	#One_hit_multiple_libraries	%One_hit_multiple_libraries	Multiple_hits_multiple_libraries	%Multiple_hits_multiple_libraries
hg19	89393	89213	99.80	1	0.00	0	0.00	11	0.01	168	0.19
mm9	89393	89157	99.74	11	0.01	5	0.01	2	0.00	218	0.24
rn4	89393	89170	99.75	2	0.00	1	0.00	8	0.01	212	0.24
dm3	89393	89391	100.00	0	0.00	0	0.00	0	0.00	2	0.00
ws200	89393	89391	100.00	0	0.00	0	0.00	1	0.00	1	0.00
ecoli	89393	89393	100.00	0	0.00	0	0.00	0	0.00	0	0.00
saccer	89393	89392	100.00	0	0.00	0	0.00	1	0.00	0	0.00
PhiX	89393	89393	100.00	0	0.00	0	0.00	0	0.00	0	0.00
Vectors	89393	89393	100.00	0	0.00	0	0.00	0	0.00	0	0.00
SpR6	89393	89393	100.00	0	0.00	0	0.00	0	0.00	0	0.00

%Hit_no_libraries: 99.73

"""

class Fastqscreen(TabFile):
    """
    Class representing data from a FastqScreen run

    """
    def __init__(self,screen_file):
        """
        Create a new FastqscreenData instance

        """
        TabFile.__init__(self,
                         column_names=('Library',
                                       '%Unmapped',
                                       '%One_hit_one_library',
                                       '%Multiple_hits_one_library',
                                       '%One_hit_multiple_libraries',
                                       '%Multiple_hits_multiple_libraries',))
        self._screen_file = os.path.abspath(screen_file)
        self._version = None
        self._no_hits = None
        # Read in data
        with open(self._screen_file,'r') as fp:
            for line in fp:
                line = line.strip()
                if line.startswith('#Fastq_screen version:'):
                    self._version = line.split()[2]
                    continue
                elif line.startswith('Library'):
                    tabfile = TabFile(column_names=line.split())
                    continue
                elif line.startswith('%Hit_no_libraries:'):
                    self._no_hits = float(line.split()[-1])
                    continue
                elif not line or \
                   line.startswith('#') or \
                   line.startswith('%'):
                    continue
                tabfile.append(tabdata=line)
        # Move data to main object
        for line in tabfile:
            data = []
            for col in self.header():
                data.append(line[col])
            self.append(data=data)

    @property
    def txt(self):
        """
        Path of the fastq_screen.txt file
        """
        return self._screen_file

    @property
    def png(self):
        """
        Path of the fastq_screen.png file
        """
        return os.path.splitext(self._screen_file)[0]+'.png'

    @property
    def version(self):
        """
        Version of fastq_screen which produced the screens
        """
        return self._version

    @property
    def libraries(self):
        """
        List of library names used in the screen
        """
        return [lib['Library'] for lib in self]

    @property
    def no_hits(self):
        """
        Percentage of reads with no hits on any library
        """
        return self._no_hits

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

def uscreenplot(screen_files,outfile):
    """
    Generate 'micro-plot' of FastqScreen outputs

    Arguments:
      screen_files (list): list of paths to one or more
        ...screen.txt files from FastqScreen
      outfile (str): path to output file,outfile

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
    img.save(outfile)
    return outfile
