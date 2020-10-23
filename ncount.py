import argparse
import os
import logging
from myclass import Gap
parser=argparse.ArgumentParser()
parser.add_argument('-i','--inputfasta')
parser.add_argument('-o','--outputdir',default=os.path.join(os.getcwd(),'ncount_result'))
args=parser.parse_args()

SCAFFOLD_HEADER='>'

try:
    inputfasta=args.inputfasta
    outputdir=args.outputdir
except Exception as e:
    print('woops')
    exit(1)

# inputfasta='./test/test.fasta'
inputfasta_name=os.path.basename(inputfasta)
countpath=os.path.join(outputdir, inputfasta_name + '.Ncount')
infopath=os.path.join(outputdir,inputfasta_name+'.Ninfo')

try:
    os.mkdir(outputdir)
except FileExistsError:
    pass

with open(inputfasta,mode='r')as inputfile, \
        open(countpath, mode='w')as countfile,\
        open(infopath,mode='w')as infofile:

    locate=0
    BASE_LIST=['A','G','C','T','a','c','t','g']
    gap_list=[]
    Nflag=False

    def process_gap(Nflag):
        if Nflag:
            gap.end = locate
            gap_list.append(gap)
        Nflag = False
        return Nflag
    # 对于gap的处理：
    # gap的起始有2种情况： 1.scaffold开始就是N
    #                   2.从ATGC变成N
    # gap的结束也有2种情况：1.从N变成ATGC（包括本行变ATGC和换行变ATGC）
    #                   2.scaffold结束

    for line in inputfile:
        if SCAFFOLD_HEADER in line:
            #如果是scaffold_info行，更新scaffold_id并考虑上个scaffold是否以N结束
            Nflag=process_gap(Nflag)
            locate=0
            scaffold_id=line[1:].strip()
        else:
            if 'N' not in line:
                #对于没有N的行（只含ATGC）考虑上行是否以N结束
                Nflag=process_gap(Nflag)
                locate+=len(line)-1#去掉/n
            else:
                for char in line:
                    if char=='N':
                        locate += 1
                        if not Nflag:#如果是从AGCT变成N，记录gap起点
                            gap=Gap(on_scaffold=scaffold_id,start=locate)
                        Nflag=True
                    elif char in BASE_LIST:
                        # 如果是从N变成AGCT，记录gap终点
                        Nflag=process_gap(Nflag)
                        locate += 1
                    elif char=='\n':
                        continue
                    else:
                        logging.warning('error')

    d={}

    infofile.write('scaffold_id\tstart\tend\n')
    for gap in gap_list:
        infofile.write(gap.to_infostring())
        length=gap.end-gap.start+1
        d[length]=d.get(length,0)+1

    countfile.write('length\tcount\n')
    for i in d:
        countfile.write(str(i)+'\t'+str(d[i])+'\n')