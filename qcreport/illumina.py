#!/usr/bin/env python
#
# illuminaqc library

import sys
import os
from auto_process_ngs.utils import AnalysisFastq
from bcftbx.TabFile import TabFile
from bcftbx.qc.report import strip_ngs_extensions
from bcftbx.htmlpagewriter import PNGBase64Encoder
from .docwriter import Document
from .docwriter import Table
from .docwriter import Img
from .docwriter import Link
from .docwriter import Target
from .fastqc import Fastqc
from .screens import uscreenplot

FASTQ_SCREENS = ('model_organisms',
                 'other_organisms',
                 'rRNA',)

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
        print "Found %d samples" % len(self._samples)

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
        report.add_css_rule("h1 { background-color: #42AEC2;\n"
                            "     color: white;\n"
                            "     padding: 5px 10px; }")
        report.add_css_rule("h2 { background-color: #8CC63F;\n"
                            "     color: white;\n"
                            "     display: inline-block;\n"
                            "     padding: 5px 15px;\n"
                            "     margin: 0;\n"
                            "     border-top-left-radius: 20;\n"
                            "     border-bottom-right-radius: 20; }")
        report.add_css_rule("h3 { background-color: grey;\n"
                            "     color: white;\n"
                            "     display: block;\n"
                            "     padding: 5px 15px;\n"
                            "     margin: 0;\n"
                            "     border-top-left-radius: 20;\n"
                            "     border-bottom-right-radius: 20; }")
        report.add_css_rule(".sample { margin: 10 10;\n"
                            "          border: solid 2px #8CC63F;\n"
                            "          padding: 0;\n"
                            "          background-color: #ffe;\n"
                            "          border-top-left-radius: 25;\n"
                            "          border-bottom-right-radius: 25; }")
        report.add_css_rule("table.summary { border: solid 1px grey;\n"
                            "                background-color: white;\n"
                            "                font-size: 80% }")
        report.add_css_rule("table.summary th { background-color: grey;\n"
                            "                   color: white;\n"
                            "                   padding: 2px 5px; }")
        report.add_css_rule("table.summary td { text-align: right; \n"
                            "                   padding: 2px 5px;\n"
                            "                   border-bottom: solid 1px lightgray; }")
        report.add_css_rule("table.fastqc_summary span.PASS { font-weight: bold;\n"
                            "                                 color: green; }")
        report.add_css_rule("table.fastqc_summary span.WARN { font-weight: bold;\n"
                            "                                 color: orange; }")
        report.add_css_rule("table.fastqc_summary span.FAIL { font-weight: bold;\n"
                            "                                 color: red; }")
        # Rules for printing
        report.add_css_rule("@media print\n"
                            "{\n"
                            "a { color: black; text-decoration: none; }\n"
                            ".sample { page-break-before: always; }\n"
                            "table th { border-bottom: solid 1px lightgray; }\n"
                            ".no_print { display: none; }\n"
                            "}")
        # Set up summary section & table
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
        for i,sample in enumerate(self._samples):
            print "Sample #%3d: %s " % (i+1,sample.name)
            sample_name = sample.name
            sample_report = report.add_section("%s" % sample_name,
                                               name="sample_%s" % sample_name)
            sample_report.add_css_classes('sample')
            for fq_pair in sample.fastq_pairs:
                # Sample name for first pair only
                idx = summary_tbl.add_row(sample="<a href='#%s'>%s</a>"
                                          % (sample_report.name,
                                             sample_name))
                # Fastq name(s)
                fq_r1 = os.path.basename(fq_pair.r1)
                fq_r2 = os.path.basename(fq_pair.r2)
                if self.paired_end:
                    # Create subsections for R1 and R2
                    fqr1_report = sample_report.add_subsection(fq_r1)
                    fqr2_report = sample_report.add_subsection(fq_r2)
                    # Add entries to summary table
                    summary_tbl.set_value(idx,'fastqs',
                                          "%s<br />%s" %
                                          (Link(fq_r1,fqr1_report),
                                           Link(fq_r2,fqr2_report)))
                else:
                    # Create subsection for R1 only
                    fqr1_report = sample_report.add_subsection(fq_r1)
                    # Add entry to summary table
                    summary_tbl.set_value(idx,'fastq',Link(fq_r1,
                                                           fqr1_report))
                # Locate FastQC outputs for R1
                fastqc = Fastqc(os.path.join(self._qc_dir,
                                             fastqc_output(fq_pair.r1)[0]))
                # Number of reads
                nreads = fastqc.data.basic_statistics('Total Sequences')
                summary_tbl.set_value(idx,'reads',nreads)
                # FastQC quality boxplot
                boxplot = Img(fastqc.quality_boxplot(inline=True),
                              height=250,
                              width=480,
                              href=fastqc.summary.link_to_module(
                                  'Per base sequence quality'),
                              name="boxplot_%s" % fq_r1)
                fqr1_report.add(boxplot)
                summary_tbl.set_value(idx,'boxplot_r1',
                                      Img(fastqc.data.uboxplot(),
                                          href=boxplot))
                # FastQC summary plot
                fastqc_tbl = Target("fastqc_%s" % fq_r1)
                fqr1_report.add(fastqc_tbl,fastqc.summary.html_table())
                summary_tbl.set_value(idx,'fastqc_r1',
                                      Img(fastqc.summary.ufastqcplot(),
                                          href=fastqc_tbl))
                # Fastq_screens
                fqr1_report.add(Target("fastq_screens_%s" % fq_r1))
                screen_files = []
                for name in FASTQ_SCREENS:
                    png,txt = fastq_screen_output(fq_pair.r1,name)
                    png = os.path.join(self._qc_dir,png)
                    screen_files.append(os.path.join(self._qc_dir,txt))
                    fqr1_report.add(Img(self._screenpng(png),
                                        height=250,
                                        href=png))
                summary_tbl.set_value(idx,'screens_r1',
                                      Img(self._uscreenplot(screen_files),
                                          href="#fastq_screens_%s" % fq_r1))
                # R2
                if self.paired_end:
                    # Locate FastQC outputs for R2
                    fastqc = Fastqc(os.path.join(self._qc_dir,
                                                 fastqc_output(fq_pair.r2)[0]))
                    # FastQC quality boxplot
                    boxplot = Img(fastqc.quality_boxplot(inline=True),
                                  height=250,
                                  width=480,
                                  href=fastqc.summary.link_to_module(
                                      'Per base sequence quality'),
                                  name="boxplot_%s" % fq_r2)
                    fqr2_report.add(boxplot)
                    summary_tbl.set_value(idx,'boxplot_r2',
                                          Img(fastqc.data.uboxplot(),
                                          href=boxplot))
                    # FastQC summary plot
                    fqr2_report.add(Target("fastqc_%s" % fq_r2),
                                    fastqc.summary.html_table())
                    summary_tbl.set_value(idx,'fastqc_r2',
                                          Img(fastqc.summary.ufastqcplot(),
                                              href="#fastqc_%s" % fq_r2))
                    # Fastq_screens
                    fqr2_report.add(Target("fastq_screens_%s" % fq_r2))
                    screen_files = []
                    for name in FASTQ_SCREENS:
                        png,txt = fastq_screen_output(fq_pair.r2,name)
                        png = os.path.join(self._qc_dir,png)
                        screen_files.append(os.path.join(self._qc_dir,txt))
                        fqr2_report.add(Img(self._screenpng(png),
                                            height=250,
                                            href=png))
                    summary_tbl.set_value(idx,'screens_r2',
                                          Img(self._uscreenplot(screen_files),
                                              href="#fastq_screens_%s" % fq_r2))
                # Reset sample name for remaining pairs
                sample_name = '&nbsp;'
        # Write the report
        report.write("%s.qcreport.html" % self.name)

    def _uscreenplot(self,fastq_screens):
        """
        """
        tmp_plot = "tmp.%s.ufastqscreenplot.png" % \
                   os.path.basename(fastq_screens[0])
        uscreenplot(fastq_screens,tmp_plot)
        uscreenplot64encoded = "data:image/png;base64," + \
                               PNGBase64Encoder().encodePNG(tmp_plot)
        os.remove(tmp_plot)
        return uscreenplot64encoded

    def _screenpng(self,fastq_screen_png):
        return "data:image/png;base64," + \
            PNGBase64Encoder().encodePNG(fastq_screen_png)

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

class FastqSet:
    """
    Class describing a set of Fastq files

    A set can be a single or a pair of fastq files.

    """
    def __init__(self,fqr1,fqr2=None):
        """
        Initialise a new QCFastqSet instance

        Arguments:
           fqr1 (str): path to R1 Fastq file
           fqr2 (str): path to R2 Fastq file, or
             None if the 'set' is a single Fastq

        """
        self._fastqs = list((fqr1,fqr2))

    def __getitem__(self,key):
        return self._fastqs[key]

    @property
    def r1(self):
        """
        Return R1 Fastq file from pair

        """
        return self._fastqs[0]

    @property
    def r2(self):
        """
        Return R2 Fastq file from pair

        """
        return self._fastqs[1]

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
       list: list of FastqSet instances

    """
    pairs = []
    fastqs_r1 = sample.fastq_subset(read_number=1)
    fastqs_r2 = sample.fastq_subset(read_number=2)
    for fqr1 in fastqs_r1:
        # Split up R1 name
        print "fqr1 %s" % os.path.basename(fqr1)
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
        print "fqr2 %s" % os.path.basename(fqr2)
        if fqr2 in fastqs_r2:
            pairs.append(FastqSet(fqr1,fqr2))
        else:
            pairs.append(FastqSet(fqr1))
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

