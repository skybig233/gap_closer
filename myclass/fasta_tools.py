# -*- coding: utf-8 -*-
# @Time : 2020/9/29 14:24
# @Author : Jiangzhesheng
# @File : fasta_tools.py
# @Software: PyCharm

import sys
import myclass
import os

class Fastafile(myclass.File_object):

    def __init__(self, path: str) -> None:
        super().__init__(path)

    def delete_linebreak(self,overwriteflag:bool=False):
        filename = os.path.basename(self.path)
        tmp_filename=filename+'.delblank'
        tmp_filepath=os.path.join(os.path.dirname(self.path), tmp_filename)
        with open(self.path,mode='r') as sourcefasta,open(tmp_filepath,mode='w') as newfile:
            newfile.write(sourcefasta.readline())
            s=''
            for line in sourcefasta:
                if myclass.SCAFFOLD_HEADER in line:
                    if s!='':
                        newfile.write(s+'\n')
                    newfile.write(line)
                else:
                    s=s+line.strip()
                if s!='':
                    newfile.write(s+'\n')
            if overwriteflag:
                os.remove(self.path)
                os.rename(tmp_filepath,filename)

class Fasta_unit:
    def __init__(self,info='') -> None:
        tmp=info.split('\n')
        self.id=tmp[0]
        self.base=tmp[1]
        self.PEinfo=''
        self.barcode=self.id[self.id.find(myclass.BARCODE_HEADER):self.id.find(myclass.BARCODE_TAIL)] \
            if myclass.BARCODE_HEADER in self.id and myclass.BARCODE_TAIL in self.id \
            else ''
    def setPE(self):
        if self.id[-1] in ['1','2']:
            self.PEinfo=self.id[-1]

    def __str__(self) -> str:
        return '\n'.join([self.id,self.base])

def main(argv):
    pass


if __name__ == '__main__':
    main(sys.argv)
