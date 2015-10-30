#!/usr/bin/env python
#
# fastqc library
from bcftbx.TabFile import TabFile
from PIL import Image

"""
Example Fastqc summary text file (FASTQ_fastqc/summary.txt):

PASS	Basic Statistics	ES1_GTCCGC_L008_R1_001.fastq.gz
PASS	Per base sequence quality	ES1_GTCCGC_L008_R1_001.fastq.gz
PASS	Per tile sequence quality	ES1_GTCCGC_L008_R1_001.fastq.gz
PASS	Per sequence quality scores	ES1_GTCCGC_L008_R1_001.fastq.gz
FAIL	Per base sequence content	ES1_GTCCGC_L008_R1_001.fastq.gz
WARN	Per sequence GC content	ES1_GTCCGC_L008_R1_001.fastq.gz
PASS	Per base N content	ES1_GTCCGC_L008_R1_001.fastq.gz
PASS	Sequence Length Distribution	ES1_GTCCGC_L008_R1_001.fastq.gz
FAIL	Sequence Duplication Levels	ES1_GTCCGC_L008_R1_001.fastq.gz
PASS	Overrepresented sequences	ES1_GTCCGC_L008_R1_001.fastq.gz
PASS	Adapter Content	ES1_GTCCGC_L008_R1_001.fastq.gz
FAIL	Kmer Content	ES1_GTCCGC_L008_R1_001.fastq.gz

Head of the FastQC data file (FASTQ_fastqc/fastqc_data.txt), which
contains raw numbers for the plots etc):

##FastQC	0.11.3
>>Basic Statistics	pass
#Measure	Value
Filename	ES1_GTCCGC_L008_R1_001.fastq.gz
File type	Conventional base calls
Encoding	Sanger / Illumina 1.9
Total Sequences	12317096
Sequences flagged as poor quality	0
Sequence length	101
%GC	50
>>END_MODULE
>>Per base sequence quality	pass
#Base	Mean	Median	Lower Quartile	Upper Quartile	10th Percentile	90th Pe
rcentile
1	32.80553403172306	33.0	33.0	33.0	33.0	33.0
...

"""

class FastqcSummary(TabFile):
    """
    Class representing data from a Fastqc summary file

    """
    def __init__(self,summary_file=None):
        """
        Create a new FastqscSummary instance

        """
        TabFile.__init__(self,
                         column_names=('Status',
                                       'Module',
                                       'File',))
        if summary_file:
            with open(summary_file,'r') as fp:
                for line in fp:
                    line = line.strip()
                    self.append(tabdata=line)

    @property
    def modules(self):
        # Return list of modules
        return [r['Module'] for r in self]

    def status(self,name):
        # Return status for module 'name'
        return self.lookup('Module',name)[0]['Status']

    @property
    def passes(self):
        # Return modules with passes
        return [r['Module'] for r in filter(lambda x: x['Status'] == 'PASS',
                                            self)]

    @property
    def warnings(self):
        # Return modules with warnings
        return [r['Module'] for r in filter(lambda x: x['Status'] == 'WARN',
                                            self)]

    @property
    def failures(self):
        # Return modules with failures
        return [r['Module'] for r in filter(lambda x: x['Status'] == 'FAIL',
                                            self)]

class FastqcData:
    """
    Class representing data from a Fastqc data file

    Reads in the data from a ``fastqc_data.txt`` file
    and makes it available programmatically.

    To create a new FastqcData instance:

    >>> fqc = FastqcData('fastqc_data.txt')

    To access a field in the 'Basic Statistics' module:

    >>> nreads = fqc.basic_statistics('Total Sequences')

    """
    def __init__(self,data_file):
        """
        Create a new FastqcData instance

        Arguments:
          data_file (str): path to a ``fastqc_data.txt``
            file which will be read in and processed

        """
        self._fastqc_version = None
        self._modules = {}
        if data_file:
            fastqc_module = None
            with open(data_file,'r') as fp:
                for line in fp:
                    line = line.strip()
                    if fastqc_module is None:
                        if line.startswith('##FastQC'):
                            self._fastqc_version = line.split()[-1]
                        elif line.startswith('>>'):
                            fastqc_module = line.split('\t')[0][2:]
                            self._modules[fastqc_module] = []
                    elif line.startswith('>>END_MODULE'):
                        fastqc_module = None
                    else:
                        self._modules[fastqc_module].append(line)

    def basic_statistics(self,measure):
        """
        Access a data item in the ``Basic Statistics`` section

        Possible values include:

        - Filename
        - File type
        - Encoding
        - Total Sequences
        - Sequences flagged as poor quality
        - Sequence length
        - %GC

        Arguments:
          measure (str): key corresponding to a 'measure'
            in the ``Basic Statistics`` section.

        Returns:
          String: value of the requested 'measure'

        Raises:
          KeyError: if measure is not found.

        """
        for line in self._modules['Basic Statistics']:
            key,value = line.split('\t')
            if key == measure:
                return value
        raise KeyError("No key '%s'" % key)

def ufastqcplot(summary_file,outfile):
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
    print "Saving to %s" % outfile
    img.save(outfile)
    return outfile
