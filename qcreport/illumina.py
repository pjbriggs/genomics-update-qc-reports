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
from .boxplots import uboxplot_from_fastq
from .boxplots import uboxplot_from_fastqc_data
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
        # Initialise HTML
        html = HTMLPageWriter("%s" % self.name)
        html.add("<h1>%s: QC report</h1>" % self.name)
        # Styles
        html.addCSSRule("table.summary { border: solid 1px grey;\n"
                        "                background-color: white;\n"
                        "                font-size: 80% }")
        html.addCSSRule("table.summary th { background-color: grey;\n"
                        "                   color: white;\n"
                        "                   padding: 2px 5px; }")
        html.addCSSRule("table.summary td { text-align: right; \n"
                        "                   padding: 2px 5px;\n"
                        "                   border-bottom: solid 1px lightgray; }")
        # Write summary table
        summary = ReportTable(('Sample',))
        if self.paired_end:
            summary.append_columns('Fastqs')
        else:
            summary.append_columns('Fastq')
        summary.append_columns('Reads','FastQC(R1)','Boxplot(R1)','Screen(R1)')
        if self.paired_end:
            summary.append_columns('FastQC(R2)','Boxplot(R2)','Screen(R2)')
        # Write entries for samples, fastqs etc
        current_sample = None
        for sample in self._samples:
            sample_name = sample.name
            for fq_pair in sample.fastq_pairs:
                # Sample name for first pair only
                idx = summary.add_row(Sample=sample_name)
                # Fastq name(s)
                if self.paired_end:
                    summary.set_value(idx,'Fastqs',
                                      "%s<br />%s" %
                                      (os.path.basename(fq_pair[0]),
                                       os.path.basename(fq_pair[1])))
                else:
                    summary.set_value(idx,'Fastq',
                                      os.path.basename(fq_pair[0]))
                # Number of reads
                summary.set_value(idx,'Reads','?')
                # Locate FastQC outputs for R1
                fastqc_dir = fastqc_output(fq_pair[0])[0]
                fastqc_data = os.path.join(self._qc_dir,fastqc_dir,
                                           'fastqc_data.txt')
                fastqc_summary =  os.path.join(self._qc_dir,fastqc_dir,
                                               'summary.txt')
                # Boxplot
                ##summary.set_value(idx,'Boxplot(R1)',"<img src='%s' />" %
                ##                  self._uboxplot(fq_pair[0]))
                summary.set_value(idx,'Boxplot(R1)',"<img src='%s' />" %
                                  self._uboxplot(fastqc_data))
                # FastQC summary plot
                summary.set_value(idx,
                                  'FastQC(R1)',"<img src='%s' />" %
                                  self._ufastqcplot(fastqc_summary))
                # Screens
                screen_files = []
                for name in ('model_organisms','other_organisms','rRNA',):
                    png,txt = fastq_screen_output(fq_pair[0],name)
                    screen_files.append(os.path.join(self._qc_dir,txt))
                    summary.set_value(idx,'Screen(R1)',"<img src='%s' />" %
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
                    summary.set_value(idx,'Boxplot(R2)',"<img src='%s' />" %
                                      self._uboxplot(fastqc_data))
                    # FastQC summary plot
                    summary.set_value(idx,
                                      'FastQC(R2)',"<img src='%s' />" %
                                      self._ufastqcplot(fastqc_summary))
                    # Screens
                    screen_files = []
                    for name in ('model_organisms','other_organisms','rRNA',):
                        png,txt = fastq_screen_output(fq_pair[1],name)
                        screen_files.append(os.path.join(self._qc_dir,txt))
                        summary.set_value(idx,'Screen(R2)',"<img src='%s' />" %
                                          self._uscreenplot(screen_files))
                # Reset sample name for remaining pairs
                sample_name = '&nbsp;'
        # Write the table
        html.add(summary.html(css_class="summary"))
        html.write("%s.qcreport.html" % self.name)

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

class ReportTable:
    """
    Utility class to help with assembling table for output

    """
    def __init__(self,columns):
        """
        Create a new ReportTable instance

        """
        self._columns = [x for x in columns]
        self._rows = []

    def append_columns(self,*names):
        """
        Add a new columns to the table

        """
        for name in names:
            if name in self._columns:
                raise KeyError("Column called '%s' already defined"
                               % name)
            self._columns.append(name)

    def add_row(self,**kws):
        """
        Add a row to the table

        """
        self._rows.append({})
        n = len(self._rows)-1
        for key in kws:
            self.set_value(n,key,kws[key])
        return n

    def set_value(self,row,key,value):
        """
        Set the value of a field in a row

        """
        if key not in self._columns:
            raise KeyError("Key '%s' not found" % key)
        self._rows[row][key] = value

    def html(self,css_class=None,css_id=None):
        """
        Generate HTML version of the table contents

        """
        html = []
        # Opening tag
        table_tag = []
        table_tag.append("<table")
        if css_id is not None:
            table_tag.append(" id='%s'" % css_id)
        if css_class is not None:
            table_tag.append(" class='%s'" % css_class)
        table_tag.append(">\n")
        html.append(''.join(table_tag))
        # Header
        header = []
        header.append("<tr>")
        for col in self._columns:
            header.append("<th>%s</th>" % col)
        header.append("</tr>")
        html.append(''.join(header))
        # Body
        for row in self._rows:
            line = []
            line.append("<tr>")
            for col in self._columns:
                try:
                    value = row[col]
                except KeyError:
                    value = '&nbsp;'
                line.append("<td>%s</td>" % value)
            line.append("</tr>")
            html.append(''.join(line))
        # Finish
        html.append("</table>")
        return '\n'.join(html)

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

