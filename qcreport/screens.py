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
    for r in screen_data:
        print r['Library']

def uscreenplot(screen_files,outfile,threshold=5.0):
    """
    Generate 'micro-plot' of FastqScreen outputs

    Arguments:
      screen_files (list): list of paths to one or more
       ...screen.txt files from FastqScreen
      outfile (str): path to output file,outfile

    """
    # Read in the screen data
    screen_data = FastqscreenData(screen_files)
    # Sort the data by most to least mapped
    screen_data.sort(lambda line: line['%Unmapped'])
    raise NotImplementedError("uscreenplot not implemented yet")

    # Initialise output image instance
    #img = Image.new('RGB',(len(quality_per_base),40),"white")
    #pixels = img.load()
    # Draw onto the image
    ##for j in xrange(p10,p90):
    ##    # 10th-90th percentile coloured cyan
    ##    pixels[pos,40-j] = (0,255,255)
    ##    for j in xrange(q25,q75):
    ##        # Interquartile range coloured yellow
    ##        pixels[pos,40-j] = (255,255,0)
    ##    # Mean coloured black
    ##pixels[pos,40-int(mean)] = (0,0,0)

    # Output the screen to file
    ##print "Saving to %s" % outfile
    ##img.save(outfile)
    ##return outfile
