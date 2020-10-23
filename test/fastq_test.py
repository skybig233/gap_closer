import unittest
import os
from myclass.fastq_tools import *

class MyTestCase(unittest.TestCase):
    def test_path(self):
        testfile=Fastqfile('data/test.fastq')
        self.assertEqual(testfile.path,os.path.abspath('data/test.fastq'))
    def test_unit(self):
        testfile = Fastqfile('data/test.fastq')
        for fastq in testfile:
            self.assertEqual(fastq.orient,'+')
    def test_barcode(self):
        testfile = Fastqfile('data/test.fastq')
        for fastq in testfile:
            self.assertEqual(fastq.barcode, '+')
    def test_equal(self):
        testfile = Fastqfile('data/test.fastq')
        for fastq in testfile:
            tmp=str(fastq)
            testcase=Fastq_unit(info=tmp)
            self.assertEqual(fastq,testcase)

    def test_Fastqlist2file(self):
        testfile = Fastqfile('data/test.fastq')
        act_list=[fastq for fastq in testfile]
        Fastqlist2file(act_list,outfilepath='func_test')
        test_list=[fastq for fastq in Fastqfile('func_test')]
        for i in range(10):
            act_fastq,test_fastq=act_list[i],test_list[i]
            self.assertEqual(act_fastq,test_fastq)
if __name__ == '__main__':
    unittest.main()