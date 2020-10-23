# -*- coding: utf-8 -*-
# @Time : 2020/10/9 17:35
# @Author : Jiangzhesheng
# @File : read_getter.py
# @Software: PyCharm
import argparse
import logging
import os
import subprocess
import sys
import re
import time
import myclass
import read_split
import multiprocessing
import traceback
from typing import List

SAMTOOLS_PATH = '/share/app/samtools-1.2/bin/samtools'
SOAP_DENOVO_PATH = '/ldfssz1/ST_OCEAN/USER/jiangzhesheng/software/SOAPdenovo2/SOAPdenovo-63mer'
GAP_PREFIX = 'gap'


def bam2fq(input_bam_filepath: str, output_fq_dir: str, prefix: str,logger):
    """
    将bam文件转化为fastq文件
    samtools bam2fq gap1.bam > gap1.bam.fq
    :param input_bam_filepath:输入bam文件路径
    :param output_fq_dir: 输出fastq文件夹路径
    :return: 返回fastq文件路径
    """
    filename = os.path.basename(input_bam_filepath)
    output_fq_path = os.path.join(output_fq_dir, prefix + '.fq')
    with open(output_fq_path, mode='w') as outputfile:
        cmd = [SAMTOOLS_PATH, 'bam2fq', input_bam_filepath]
        a = subprocess.Popen(cmd, stdout=outputfile)
        a.wait()
        if a.returncode!=0:
            logger.error('error in %s bam2fq with returncode %s' % (prefix,a.returncode))
        logger.info(filename + ' bam2fq finished')
    return output_fq_path


def strategy_PE_only(input_bam_filepath: str, location: str, prefix: str, outputdir: str,logger):
    """
    对于一个单一的gap而言，想要获取其gap附近的read，用samtools可以如下操作
    samtools view -b mem.sort.bam 0:34846-35645 > gap1.bam
    在含有所有read的bam文件中，自身未比对上但PE比对上的read(f4F8)的位置与其PE相同，所以可以直接从整个bam中提取
    :param input_bam_filepath:bam文件路径
    :param location:提取区域
    :param prefix:输出文件前缀
    :param outputdir:输出文件夹路径
    :param logger
    :return:输出bam文件的路径
    """
    cmd = [SAMTOOLS_PATH, 'view', '-b', input_bam_filepath, location]
    out_filename = prefix + '.bam'
    out_bam_path = os.path.join(outputdir, out_filename)
    with open(out_bam_path, mode='w') as outbamfile:
        a = subprocess.Popen(cmd, stdout=outbamfile)
        a.wait()
        if a.returncode!=0:
            logger.error('error in %s read set with returncode %s' % (prefix,a.returncode))
        logger.info(prefix + ' read set finished')
    return out_bam_path


def strategy_PE_and_barcode(input_bam_filepath: str,input_f4f8_readlist:[],location: str, prefix: str, outputdir: str,logger):
    """
    对于那些自身和PE都没有比对上的read(f4f8)，如果其barcode和gap区域内任意一个read相同，则可以纳入read set
    :param input_f4f8_readlist:
    :param input_bam_filepath:
    :param location:
    :param prefix:
    :param outputdir:
    :param logger:
    :return:
    """
    out_bam_path=strategy_PE_only(input_bam_filepath=input_bam_filepath,
                     location=location,
                     prefix=prefix,
                     logger=logger,
                     outputdir=outputdir)

    out_fq_path=bam2fq(input_bam_filepath=out_bam_path,
                       output_fq_dir=out_bam_path,
                       prefix=prefix,
                       logger=logger)

    #对于gap区的read遍历每个barcode,存入barcode_list
    barcode_list=[fastq.barcode for fastq in myclass.Fastqfile(path=out_fq_path)]
    barcode_list=set(barcode_list)

    choosed_read=[fastq for fastq in input_f4f8_readlist if fastq.barcode in barcode_list]
    fqpath=myclass.Fastqlist2file(choosed_read,outfilepath=os.path.join(outputdir,'samebarcode.fastq'))

    return fqpath

def config_generator(read1_path: str, read2_path: str, example_config_path: str, outputdir: str):
    out_config_path = os.path.join(outputdir, 'config.cfg')
    with open(example_config_path, mode='r') as example_config_file, \
            open(out_config_path, mode='w') as out_config:
        example_config = example_config_file.read()
        example_config = re.sub(pattern='q1=.+', string=example_config, repl='q1=' + read1_path)
        example_config = re.sub(pattern='q2=.+', string=example_config, repl='q2=' + read2_path)
        out_config.write(example_config)
    return out_config_path


def soap_denovo(config_path: str, outputdir: str, prefix: str,logger):
    """
    使用SOAPdenovo进行补洞需要如下命令
    SOAPdenovo-63mer all -s config.cfg -K 63 -o gap 1>ass.log 2>ass.err
    :param config_path:
    :param outputdir:
    :return:
    """
    os.chdir(outputdir)
    cmd = [SOAP_DENOVO_PATH, 'all', '-s', config_path, '-K', '63', '-o', prefix]
    with open(os.path.join(outputdir, 'ass.log'), mode='w') as stdout, \
            open(os.path.join(outputdir, 'ass.err'), mode='w') as stderr:
        a = subprocess.Popen(cmd, stdout=stdout, stderr=stderr)
        a.wait()
        if a.returncode!=0:
            logger.error('error in %s SOAPdenovo with returncode %s' % (prefix,a.returncode))
            return
        logger.info(prefix + ' SOAPdenovo finished')


def read_getter_PE_strategy(input_bam_filepath: str,
                            input_example_config_filepath: str,
                            outputdir: str,
                            gap_id: int,
                            bed: myclass.Bed,
                            logger:logging.Logger):
    dirname = GAP_PREFIX + str(gap_id)
    dirpath = os.path.join(outputdir, dirname)
    try:
        os.mkdir(dirpath)
    except FileExistsError:
        logger.warning(dirpath + ' is exist, files in it may be overwritten')

    try:
        # 1.将bam文件中对应区域的read提取到bam文件
        # samtools view -b mem.sort.bam 0:34846-35645 > gap1.bam
        location = bed.chrom_id + ':' + str(bed.chrom_start) + '-' + str(bed.chrom_end)
        bampath = strategy_PE_only(input_bam_filepath=input_bam_filepath,
                                   location=location,
                                   prefix=dirname,
                                   outputdir=dirpath,
                                   logger=logger)
        # 2.将bam文件转化为fastq文件
        # samtools bam2fq gap1.bam > gap1.bam.fq
        fqpath = bam2fq(input_bam_filepath=bampath,
                        prefix=dirname,
                        output_fq_dir=dirpath,
                        logger=logger)

        # 3.将fastq文件切割成read1、read2
        # python read_split.py
        read1_path, read2_path = read_split.read_split(input_fastq_path=fqpath,
                                                       outputdir=dirpath,
                                                       prefix=dirname)
        # os.remove(outfqpath)

        # 4.生成config文件
        config_path = config_generator(read1_path=read1_path,
                                       read2_path=read2_path,
                                       example_config_path=input_example_config_filepath,
                                       outputdir=dirpath)

        # 5.调用SOAPdenovo
        soapdir = os.path.join(dirpath, 'SOAPdenovo')
        try:
            os.mkdir(soapdir)
        except FileExistsError:
            logger.warning(dirpath + ' is exist, files in it may be overwritten')

        soap_denovo(config_path=config_path,
                    prefix=dirname,
                    outputdir=soapdir,
                    logger=logger)
    except Exception:
        logger.error(traceback.print_exc())


f4f8list = [fastq for fastq in
                myclass.Fastqfile(path='/ldfssz1/ST_OCEAN/USER/jiangzhesheng/data/bwa_to_assemble/mem.f4f8.fq')]

def read_getter_barcode_strategy(input_bam_filepath: str,
                                 input_example_config_filepath: str,
                                 outputdir: str,
                                 gap_id: int,
                                 bed: myclass.Bed,
                                 logger:logging.Logger
                                 ):
    dirname = GAP_PREFIX + str(gap_id)
    dirpath = os.path.join(outputdir, dirname)
    try:
        os.mkdir(dirpath)
    except FileExistsError:
        logger.warning(dirpath + ' is exist, files in it may be overwritten')


    # 1.将bam文件中对应区域的read提取到bam文件
    # samtools view -b mem.sort.bam 0:34846-35645 > gap1.bam
    location = bed.chrom_id + ':' + str(bed.chrom_start) + '-' + str(bed.chrom_end)

    fqpath = strategy_PE_and_barcode(input_bam_filepath=input_bam_filepath,
                                     input_f4f8_readlist=f4f8list,
                                     location=location,
                                     prefix=dirname,
                                     logger=logger,
                                     outputdir=dirpath
                                     )


def read_getter_multi(input_bam_filepath: str,
                      input_bed_filepath: str,
                      input_example_config_filepath: str,
                      outputdir: str,
                      thread: int,
                      logger,
                      flanking_region: int = 200):
    """
    通过samtools软件读取bam文件，根据bed文件中的位置信息提取相关read(ailgnment)
    """
    i = 0

    pool = multiprocessing.Pool(processes=thread)
    for bed in myclass.Bedfile(path=input_bed_filepath):
        i += 1
        bed = bed.add_distance(distance=flanking_region)
        # result = pool.apply_async(func=read_getter_PE_strategy,
        #                           args=(input_bam_filepath, input_example_config_filepath, outputdir, i, bed,logger))
        result = pool.apply_async(func=read_getter_barcode_strategy,
                                  args=(input_bam_filepath, input_example_config_filepath, outputdir, i, bed, logger))
    pool.close()
    pool.join()
    logger.info('finished at %s' % time.asctime())


def main(argv):
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('-bam', '--input_bam_filepath')
    parser.add_argument('-bed', '--input_bed_filepath')
    parser.add_argument('-cfg', '--input_example_config_filepath')
    parser.add_argument('-o', '--outputdir', default='read_getter_result')
    parser.add_argument('-t', '--thread', default=8, type=int)
    args = parser.parse_args(argv[1:])
    input_bam_filepath = args.input_bam_filepath
    input_bed_filepath = args.input_bed_filepath
    input_example_config_filepath = args.input_example_config_filepath
    outputdir = args.outputdir
    thread = args.thread

    try:
        os.mkdir(outputdir)
    except FileExistsError:
        logging.warning(outputdir + ' is exist, files in it may be overwritten')

    logger=logging.getLogger()
    logger.setLevel(logging.INFO)
    logfile=os.path.join(outputdir,'totallog')
    fh = logging.FileHandler(logfile, mode='w')
    fh.setLevel(logging.WARNING)
    fh.setFormatter(fmt=logging.Formatter("%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s"))
    logger.addHandler(fh)
    ch=logging.StreamHandler()
    ch.setLevel(logging.INFO)
    logger.addHandler(ch)


    read_getter_multi(input_bam_filepath=os.path.abspath(input_bam_filepath),
                      input_bed_filepath=os.path.abspath(input_bed_filepath),
                      input_example_config_filepath=os.path.abspath(input_example_config_filepath),
                      thread=thread,
                      outputdir=os.path.abspath(outputdir),
                      logger=logger)


if __name__ == '__main__':
    main(sys.argv)
