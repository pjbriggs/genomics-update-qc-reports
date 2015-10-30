#!/usr/bin/env python
#
# illuminaqc library

import sys
import os
from auto_process_ngs.utils import AnalysisFastq
from bcftbx.TabFile import TabFile
from bcftbx.qc.report import strip_ngs_extensions
from bcftbx.htmlpagewriter import HTMLPageWriter
from bcftbx.htmlpagewriter import PNGBase64Encoder
from .docwriter import Document
from .docwriter import Table
from .boxplots import uboxplot_from_fastq
from .boxplots import uboxplot_from_fastqc_data
from .fastqc import FastqcData
from .fastqc import ufastqcplot
from .screens import uscreenplot
from .screens import multiscreenplot

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
        self._qc_dir = self._project.qc_dir
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
        # Initialise report
        report = Document(title="%s: QC report" % self.name)
        # Styles
        report.add_css_rule("table.summary { border: solid 1px grey;\n"
                            "                background-color: white;\n"
                            "                font-size: 80% }")
        report.add_css_rule("table.summary th { background-color: grey;\n"
                            "                   color: white;\n"
                            "                   padding: 2px 5px; }")
        report.add_css_rule("table.summary td { text-align: right; \n"
                            "                   padding: 2px 5px;\n"
                            "                   border-bottom: solid 1px lightgray; }")
        # Build summary section & table
        summary = report.add_section("Summary")
        summary_tbl = Table(('sample',),sample='Sample')
        summary_tbl.add_css_classes('summary')
        summary.add(summary_tbl)
        if self.paired_end:
            summary_tbl.append_columns('fastqs',fastqs='Fastqs (R1/R2)')
        else:
            summary_tbl.append_columns('fastq',fastq='Fastq')
        summary_tbl.append_columns('reads','fastqc_r1','boxplot_r1','screens_r1',
                                   reads='#reads',fastqc_r1='FastQC',boxplot_r1='Boxplot',
                                   screens_r1='Screens')
        if self.paired_end:
            summary_tbl.append_columns('fastqc_r2','boxplot_r2','screens_r2',
                                   fastqc_r2='FastQC',boxplot_r2='Boxplot',
                                   screens_r2='Screens')
        # Write entries for samples, fastqs etc
        current_sample = None
        for sample in self._samples:
            sample_name = sample.name
            for fq_pair in sample.fastq_pairs:
                # Sample name for first pair only
                idx = summary_tbl.add_row(sample=sample_name)
                # Fastq name(s)
                if self.paired_end:
                    summary_tbl.set_value(idx,'fastqs',
                                          "%s<br />%s" %
                                          (os.path.basename(fq_pair[0]),
                                           os.path.basename(fq_pair[1])))
                else:
                    summary_tbl.set_value(idx,'fastq',
                                          os.path.basename(fq_pair[0]))
                # Locate FastQC outputs for R1
                fastqc_dir = fastqc_output(fq_pair[0])[0]
                fastqc_data = os.path.join(self._qc_dir,fastqc_dir,
                                           'fastqc_data.txt')
                fastqc_summary =  os.path.join(self._qc_dir,fastqc_dir,
                                               'summary.txt')
                # Number of reads
                nreads = FastqcData(fastqc_data).\
                         basic_statistics('Total Sequences')
                summary_tbl.set_value(idx,'reads',nreads)
                # Boxplot
                summary_tbl.set_value(idx,'boxplot_r1',"<img src='%s' />" %
                                      self._uboxplot(fastqc_data))
                # FastQC summary plot
                summary_tbl.set_value(idx,
                                      'fastqc_r1',"<img src='%s' />" %
                                      self._ufastqcplot(fastqc_summary))
                # Screens
                screen_files = []
                for name in ('model_organisms','other_organisms','rRNA',):
                    png,txt = fastq_screen_output(fq_pair[0],name)
                    screen_files.append(os.path.join(self._qc_dir,txt))
                    summary_tbl.set_value(idx,'screens_r1',"<img src='%s' />" %
                                          self._uscreenplot(screen_files))
                # R2
                if self.paired_end:
                    # Locate FastQC outputs for R2
                    fastqc_dir = fastqc_output(fq_pair[1])[0]
                    fastqc_data = os.path.join(self._qc_dir,fastqc_dir,
                                               'fastqc_data.txt')
                    fastqc_summary =  os.path.join(self._qc_dir,fastqc_dir,
                                                   'summary.txt')
                    # Boxplot
                    summary_tbl.set_value(idx,'boxplot_r2',"<img src='%s' />" %
                                          self._uboxplot(fastqc_data))
                    # FastQC summary plot
                    summary_tbl.set_value(idx,
                                          'fastqc_r2',"<img src='%s' />" %
                                          self._ufastqcplot(fastqc_summary))
                    # Screens
                    screen_files = []
                    for name in ('model_organisms','other_organisms','rRNA',):
                        png,txt = fastq_screen_output(fq_pair[1],name)
                        screen_files.append(os.path.join(self._qc_dir,txt))
                        summary_tbl.set_value(idx,'screens_r2',"<img src='%s' />" %
                                              self._uscreenplot(screen_files))
                # Reset sample name for remaining pairs
                sample_name = '&nbsp;'
        # Write the report
        report.write("%s.qcreport.html" % self.name)

    #def _uboxplot(self,fastq):
    def _uboxplot(self,fastqc_data):
        """
        Generate Base64 encoded micro boxplot for FASTQ quality

        """
        #tmp_boxplot = "tmp.%s.uboxplot.png" % os.path.basename(fastq)
        #uboxplot_from_fastq(fastq,tmp_boxplot)
        tmp_boxplot = "tmp.%s.uboxplot.png" % os.path.basename(fastqc_data)
        uboxplot_from_fastqc_data(fastqc_data,tmp_boxplot)
        uboxplot64encoded = "data:image/png;base64," + \
                            PNGBase64Encoder().encodePNG(tmp_boxplot)
        os.remove(tmp_boxplot)
        return uboxplot64encoded

    def _ufastqcplot(self,fastqc_summary):
        """
        Generate Base64 encoded micro FastQC summary plot

        """
        tmp_plot = "tmp.%s.ufastqcplot.png" % \
                   os.path.basename(fastqc_summary)
        ufastqcplot(fastqc_summary,tmp_plot)
        ufastqcplot64encoded = "data:image/png;base64," + \
                               PNGBase64Encoder().encodePNG(tmp_plot)
        os.remove(tmp_plot)
        return ufastqcplot64encoded

    def _uscreenplot(self,fastq_screens):
        """
        """
        tmp_plot = "tmp.%s.ufastqscreenplot.png" % \
                   os.path.basename(fastq_screens[0])
        multiscreenplot(fastq_screens,tmp_plot)
        uscreenplot64encoded = "data:image/png;base64," + \
                               PNGBase64Encoder().encodePNG(tmp_plot)
        os.remove(tmp_plot)
        return uscreenplot64encoded

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

    - {FASTQ}_fastqc/
    - {FASTQ}_fastqc.html
    - {FASTQ}_fastqc.zip

    Arguments:
       fastq (str): name of Fastq file

    Returns:
       tuple: FastQC outputs (without leading paths)

    """
    base_name = "%s_fastqc" % strip_ngs_extensions(os.path.basename(fastq))
    return (base_name,base_name+'.html',base_name+'.zip')

