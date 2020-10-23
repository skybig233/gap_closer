# -*- coding: utf-8 -*-
# @Time : 2020/9/27 9:28
# @Author : Jiangzhesheng
# @File : read_split.py
# @Software: PyCharm

import sys
import argparse
import os
import logging
from myclass.fastq_tools import *

def read_split(input_fastq_path:str,outputdir:str,prefix:str):
    """
    读取一个既含有read1也含有read2的fastq文件，将read1和read2分开放在两个fastq文件中
    :param input_fastq_path:fastq源文件路径
    :param outputdir:输出fastq文件的文件夹路径
    :return:read1,read2文件路径
    """
    prefix=os.path.basename(input_fastq_path) if prefix=='' else prefix
    out_read1_path=os.path.join(outputdir,prefix+'.1.fastq')
    out_read2_path=os.path.join(outputdir,prefix+'.2.fastq')
    with open(out_read1_path,mode='w') as out_read1_file,\
            open(out_read2_path,mode='w') as out_read2_file:
        for reads in Fastqfile(input_fastq_path):
            reads.setPE()
            if reads.PEinfo=='1':
                out_read1_file.write(str(reads))
            elif reads.PEinfo=='2':
                out_read2_file.write(str(reads))
            else:
                logging.warning(reads.id+' has no PE info')
    return out_read1_path,out_read2_path
def main(argv):
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('-i', '--inputfastq')
    parser.add_argument('-p', '--prefix',default='')
    parser.add_argument('-o', '--outputdir',default='read_split_result')
    args = parser.parse_args(argv[1:])
    input = args.inputfastq
    outputdir=args.outputdir
    prefix=args.prefix

    try:
        os.mkdir(outputdir)
    except FileExistsError as e:
        logging.warning(outputdir + ' is exist, files in it may be overwritten')

    read_split(input_fastq_path=os.path.abspath(input),
               outputdir=os.path.abspath(outputdir),
               prefix=prefix)

if __name__ == '__main__':
    main(sys.argv)