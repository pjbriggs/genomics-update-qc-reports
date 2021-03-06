#!/usr/bin/env python
#
# fastqc library
import os
from bcftbx.TabFile import TabFile
from bcftbx.htmlpagewriter import PNGBase64Encoder
from .docwriter import Table
from .docwriter import Link

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

class Fastqc:
    """
    Wrapper class for handling outputs from FastQC

    The ``Fastqc`` object gives access to various
    aspects of the outputs of the FastQC program.

    """
    # Base names for plots in the 'Images' subdir
    plot_names = ('adapter_content',
                  'duplication_levels',
                  'kmer_profiles',
                  'per_base_n_content',
                  'per_base_quality',
                  'per_base_sequence_content',
                  'per_sequence_gc_content',
                  'per_sequence_quality',
                  'per_tile_quality',
                  'sequence_length_distribution',
                  )
    def __init__(self,fastqc_dir):
        """
        Create a new Fastqc instance

        Arguments:
          fastqc_dir (str): path to the top-level
            output directory from a FastQC run.

        """
        self._fastqc_dir = os.path.abspath(fastqc_dir)
        self._fastqc_summary = FastqcSummary(
            summary_file=os.path.join(self._fastqc_dir,
                                      'summary.txt'))
        self._fastqc_data = FastqcData(
            os.path.join(self._fastqc_dir,
                         'fastqc_data.txt'))
        self._html_report = self._fastqc_dir + '.html'
        self._zip = self._fastqc_dir + '.zip'

    @property
    def version(self):
        return self.data.version

    @property
    def dir(self):
        return self._fastqc_dir

    @property
    def html_report(self):
        return self._html_report

    @property
    def zip(self):
        return self._zip

    @property
    def summary(self):
        """
        Return a FastqcSummary instance

        """
        return self._fastqc_summary

    @property
    def data(self):
        """
        Return a FastqcData instance

        """
        return self._fastqc_data

    def plot(self,module,inline=False):
        """
        """
        # Normalise name
        name = module.lower().replace(' ','_')
        plot_png = os.path.join(self._fastqc_dir,
                                'Images',
                                '%s.png' % name)
        # Check png exists
        if not os.path.exists(plot_png):
            return None
        # Return requested format
        if inline:
            return "data:image/png;base64," + \
                PNGBase64Encoder().encodePNG(plot_png)
        else:
            return plot_png

    def quality_boxplot(self,inline=False):
        """
        """
        return self.plot('per_base_quality',
                         inline=inline)

    def adapter_content_plot(self,inline=False):
        """
        """
        return self.plot('Adapter Content',
                         inline=inline)

class FastqcSummary(TabFile):
    """
    Class representing data from a Fastqc summary file

    """
    def __init__(self,summary_file=None):
        """
        Create a new FastqcSummary instance

        """
        TabFile.__init__(self,
                         column_names=('Status',
                                       'Module',
                                       'File',))
        if summary_file:
            summary_file = os.path.abspath(summary_file)
            with open(summary_file,'r') as fp:
                for line in fp:
                    line = line.strip()
                    self.append(tabdata=line)
        self._summary_file = summary_file

    @property
    def path(self):
        # Path to the summary file
        return self._summary_file

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

    def link_to_module(self,name,full_path=True):
        """
        """
        i = self.modules.index(name)
        link = "#M%d" % i
        if full_path:
            return self.html_report() + link
        else:
            return link

    def html_report(self):
        """
        """
        return os.path.dirname(self.path)+'.html'

    def html_table(self):
        """
        Generate HTML table for FastQC summary

        """
        tbl = Table(('module','status'),
                    module='FastQC test',status='Outcome')
        tbl.add_css_classes('fastqc_summary','summary')
        for name in self.modules:
            tbl.add_row(module=Link(name,self.link_to_module(name)),
                        status="<span class='%s'>%s</span>" % (
                            self.status(name),
                            self.status(name)))
        return tbl.html()

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
        self._data_file = os.path.abspath(data_file)
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

    @property
    def version(self):
        """
        FastQC version number
        """
        return self._fastqc_version

    @property
    def path(self):
        """
        Path to the fastqc_data.txt file

        """
        return self._data_file

    def data(self,module):
        """
        """
        if module in self._modules:
            return self._modules[module]
        return None

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
        for line in self.data('Basic Statistics'):
            key,value = line.split('\t')
            if key == measure:
                return value
        raise KeyError("No key '%s'" % key)
