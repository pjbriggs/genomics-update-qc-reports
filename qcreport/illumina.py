#!/usr/bin/env python
#
# illuminaqc library

import os
from auto_process_ngs.utils import AnalysisFastq
from bcftbx.TabFile import TabFile
from bcftbx.qc.report import strip_ngs_extensions
from bcftbx.htmlpagewriter import HTMLPageWriter
from bcftbx.htmlpagewriter import PNGBase64Encoder
from .boxplots import uboxplot_from_fastq as uboxplot

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
        self._stats_file = os.path.join(os.path.dirname(self._project.dirn),
                                        'statistics.info')
        try:
            self._stats = FastqStats(self._stats_file)
        except IOError:
            print "Failed to load stats"
            self._stats = None
        for sample in self._project.samples:
            self._samples.append(QCSample(sample))

    @property
    def name(self):
        return self._project.name

    @property
    def paired_end(self):
        return self._project.info.paired_end

    def report(self):
        """
        Report the QC for the project

        """
        # Initialise HTML
        html = HTMLPageWriter("%s" % self.name)
        html.add("<h1>%s: QC report</h1>" % self.name)
        # Styles
        html.addCSSRule("table.summary { border: solid 1px grey;\n"
                        "                background-color: white;\n"
                        "                font-size: 90% }")
        html.addCSSRule("table.summary th { background-color: grey;\n"
                        "                   color: white;\n"
                        "                   padding: 2px 5px; }")
        html.addCSSRule("table.summary td { text-align: right; \n"
                        "                   padding: 2px 5px;\n"
                        "                   border-bottom: solid 1px lightgray; }")
        # Write summary table
        html.add("<table class='summary'>")
        html.add("<tr><th>Sample</th>")
        if self.paired_end:
            html.add("<th>Fastq (R1)</th><th>Fastq (R2)</th>")
        else:
            html.add("<th>Fastq</th>")
        html.add("<th>Reads</th><th>R1</th>")
        if self.paired_end:
            html.add("<th>R2</th>")
        html.add("</tr>")
        # Write entries for samples, fastqs etc
        current_sample = None
        for sample in self._samples:
            sample_name = sample.name
            for fq_pair in sample.fastq_pairs:
                # Sample name for first pair only
                html.add("<tr><td>%s</td>" % sample_name)
                # Fastq name(s)
                html.add("<td>%s</td>" % os.path.basename(fq_pair[0]))
                if self.paired_end:
                    html.add("<td>%s</td>" % os.path.basename(fq_pair[1]))
                # Number of reads
                html.add("<td>?</td>")
                # Little boxplot(s)
                # R1 boxplot
                tmp_boxplot = "tmp.%s.uboxplot.png" % os.path.basename(fq_pair[0])
                uboxplot(fq_pair[0],tmp_boxplot)
                uboxplot64encoded = "data:image/png;base64," + \
                                    PNGBase64Encoder().encodePNG(tmp_boxplot)
                html.add("<td><img src='%s' /></td>" % uboxplot64encoded)
                os.remove(tmp_boxplot)
                # R2 boxplot
                if self.paired_end:
                    tmp_boxplot = "tmp.%s.uboxplot.png" % os.path.basename(fq_pair[1])
                    uboxplot(fq_pair[1],tmp_boxplot)
                    uboxplot64encoded = "data:image/png;base64," + \
                                        PNGBase64Encoder().encodePNG(tmp_boxplot)
                    html.add("<td><img src='%s' /></td>" % uboxplot64encoded)
                    os.remove(tmp_boxplot)
                # End of line
                html.add("</tr>")
                # Reset sample name for remaining pairs
                sample_name = '&nbsp;'
        # Close off table
        html.add("</table>")
        html.write("%s.qcreport.html" % self.name)

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

    @property
    def fastq_pairs(self):
        return self._fastq_pairs

class QCFastqSet:
    """
    Class describing QC results for a set of Fastq files

    A set can be a single or a pair of fastq files.

    """
    def __init__(self,*fastqs):
        """
        Initialise a new QCFastqSet instance

        Arguments:
           fastqs (str):

        """
        self._fastqs = list(fastqs)

class FastqStats(TabFile):
    """
    Class for looking up statistics on Fastq files

    """
    def __init__(self,stats_file):
        """
        Initialise a FastqStats instance

        Arguments:
           stats_file (str): path to a stats file

        """
        self._stats_file = stats_file
        TabFile.__init__(self,self._stats_file)

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

