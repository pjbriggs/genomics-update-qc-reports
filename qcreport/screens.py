#!/usr/bin/env python
#
# fastq screens library
from bcftbx.TabFile import TabFile
from matplotlib import pyplot as plt
from PIL import Image

"""
Example screen file:

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

"""

class FastqscreenData(TabFile):
    """
    Class representing data from one or more FastqScreen runs

    """
    def __init__(self,screens=None):
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
        if screens:
            for f in screens:
                self.add_screen(f)

    def add_screen(self,screen_file):
        """
        Add data from a FastqScreen output file

        """
        with open(screen_file,'r') as fp:
            for line in fp:
                line = line.strip()
                if not line or \
                   line.startswith('#') or \
                   line.startswith('Library') or \
                   line.startswith('%'):
                    continue
                self.append(tabdata=line)

def screenplot(screen_files,outfile,threshold=5.0):
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
    screen_data = FastqscreenData(screen_files)
    # Sort the data by most to least mapped
    screen_data.sort(lambda line: line['%Unmapped'],reverse=True)
    # Filter on threshold
    screen_data = filter(lambda x: x['%Unmapped'] < (100.0-threshold),
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
    plt.yticks([x+0.5 for x in xrange(len(screen_data))],
               [r['Library'] for r in screen_data])
    plt.legend(loc=4)
    plt.savefig(outfile)
    #for r in screen_data:
    #    print r['Library']

def uscreenplot(screen_files,outfile,threshold=5.0):
    """
    Generate 'micro-plot' of FastqScreen outputs

    Arguments:
      screen_files (list): list of paths to one or more
        ...screen.txt files from FastqScreen
      outfile (str): path to output file,outfile
      threshold (float): minimum percentage of mapped
        reads (below which library is excluded)

    """
    # Read in the screen data
    screen_data = FastqscreenData(screen_files)
    ### Sort the data by most to least mapped
    ##screen_data.sort(lambda line: line['%Unmapped'])
    # Filter on threshold
    screen_data = filter(lambda x: x['%Unmapped'] < (100.0-threshold),
                         screen_data)
    # Make a small stacked bar chart
    barwidth = 5
    height = len(screen_data)*(barwidth + 1)
    img = Image.new('RGB',(50,height),"white")
    pixels = img.load()
    # Draw a box around the plot
    box_color = (145,145,145)
    for i in xrange(50):
        pixels[i,0] = box_color
        pixels[i,height-1] = box_color
    for j in xrange(height):
        pixels[0,j] = box_color
        pixels[50-1,j] = box_color
    # Draw the stacked bars for each library
    libraries = [r['Library'] for r in screen_data]
    for n,library in enumerate(libraries):
        screen = filter(lambda x: x['Library'] == library,screen_data)[0]
        y = n*(barwidth+1) + 1
        x = 0
        for mapping,rgb in (('%One_hit_one_library',(0,0,153)),
                            ('%Multiple_hits_one_library',(0,0,255)),
                            ('%One_hit_multiple_libraries',(255,0,0)),
                            ('%Multiple_hits_multiple_libraries',(128,0,0))):
            npx = int(screen[mapping]/2.0)
            for i in xrange(x,x+npx):
                for j in xrange(barwidth):
                    pixels[i,y+j] = rgb
            x += npx
    # Output the plot to file
    print "Saving to %s" % outfile
    img.save(outfile)
    return outfile
