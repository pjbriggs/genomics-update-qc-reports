#######################################################################
# Unit tests
#######################################################################

import unittest

from auto_process_ngs.utils import AnalysisSample
from qcreport.illumina import get_fastq_pairs
class TestFqPairsFunction(unittest.TestCase):
    def test_paired_end(self):
        s = AnalysisSample('PB1')
        s.add_fastq('/data/PB/PB1_ATTAGG_L001_R1_001.fastq')
        s.add_fastq('/data/PB/PB1_ATTAGG_L001_R2_001.fastq')
        s.add_fastq('/data/PB/PB1_GCCAAG_L002_R1_001.fastq')
        s.add_fastq('/data/PB/PB1_GCCAAG_L002_R2_001.fastq')
        self.assertEqual(get_fastq_pairs(s),[('/data/PB/PB1_ATTAGG_L001_R1_001.fastq',
                                              '/data/PB/PB1_ATTAGG_L001_R2_001.fastq'),
                                             ('/data/PB/PB1_GCCAAG_L002_R1_001.fastq',
                                              '/data/PB/PB1_GCCAAG_L002_R2_001.fastq')])
    def test_single_end(self):
        s = AnalysisSample('PB1')
        s.add_fastq('/data/PB/PB1_ATTAGG_L001_R1_001.fastq')
        s.add_fastq('/data/PB/PB1_GCCAAG_L002_R1_001.fastq')
        self.assertEqual(get_fastq_pairs(s),[('/data/PB/PB1_ATTAGG_L001_R1_001.fastq',None),
                                             ('/data/PB/PB1_GCCAAG_L002_R1_001.fastq',None)])


from qcreport.illumina import fastq_screen_output
class TestFastqScreenOutputFunction(unittest.TestCase):
    def test_fastq_screen_output(self):
        self.assertEqual(fastq_screen_output('/data/PB/PB1_ATTAGG_L001_R1_001.fastq',
                                             'model_organisms'),
                         ('PB1_ATTAGG_L001_R1_001_model_organisms_screen.png',
                          'PB1_ATTAGG_L001_R1_001_model_organisms_screen.txt'))
    def test_fastq_screen_output_fastqgz(self):
        self.assertEqual(fastq_screen_output('/data/PB/PB1_ATTAGG_L001_R1_001.fastq.gz',
                                             'model_organisms'),
                         ('PB1_ATTAGG_L001_R1_001_model_organisms_screen.png',
                          'PB1_ATTAGG_L001_R1_001_model_organisms_screen.txt'))

from qcreport.illumina import fastqc_output
class TestFastqcOutputFunction(unittest.TestCase):
    def test_fastqc_output(self):
        self.assertEqual(fastqc_output('/data/PB/PB1_ATTAGG_L001_R1_001.fastq'),
                         ('PB1_ATTAGG_L001_R1_001_fastqc',
                          'PB1_ATTAGG_L001_R1_001_fastqc.html',
                          'PB1_ATTAGG_L001_R1_001_fastqc.zip'))
    def test_fastqc_output_fastqgz(self):
        self.assertEqual(fastqc_output('/data/PB/PB1_ATTAGG_L001_R1_001.fastq.gz'),
                         ('PB1_ATTAGG_L001_R1_001_fastqc',
                          'PB1_ATTAGG_L001_R1_001_fastqc.html',
                          'PB1_ATTAGG_L001_R1_001_fastqc.zip'))
    
        
                         
