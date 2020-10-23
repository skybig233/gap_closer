import multiprocessing
import os
import time
import re
import random
import traceback


# 正则学习
# s='q1=/ldfssz1/ST_OCEAN/USER/jiangzhesheng/tmp/read_split_result/test.fastq.1.fastq\nq2=/ldfssz1/ST_OCEAN/USER/jiangzhesheng/tmp/read_split_result/test.fastq.2.fastq'
# m=pattern.sub(,string=s,repl='q1=',count=1)
# print(m)

#多线程线程池学习
i=1
def add(i:int):
    i+=1
    start=time.perf_counter()
    time.sleep(2)
    end=time.perf_counter()
    cost=end-start
    print('进程', os.getpid(),'于%s创建' % start, '对i+1结果为%s,花了%s秒' % (i,cost))
    return

def lock_raise_error(i,l):
    try:
        rand=random.randrange(0,2)
        ans=10/rand
        time.sleep(1)
        l.acquire()
        print(os.getpid(),':',i,'sucess result is',ans)
        l.release()
        return ans
    except Exception as e:
        print(os.getpid(),'failed',e)
        return -1

def raise_error(i):
    try:
        rand=random.randrange(0,2)
        ans=10/rand
        time.sleep(1)
        print(os.getpid(),':',i,'sucess result is',ans,'parent',os.getppid())
        return ans
    except Exception as e:
        print(traceback.print_exc())
        # print(os.getpid(),':',i,'failed',e,'parent',os.getppid())
        return -1

if __name__ == '__main__':
    d=[1,1,1,2,3]
    ans=[]

    print(time.asctime())
    print('Parent process %s.' % os.getpid())
    pool=multiprocessing.Pool(processes=3)
    lock=multiprocessing.Manager().Lock()
    for i in range(10):
        a=pool.apply_async(func=raise_error,args=(i,))
    pool.close()
    pool.join()
    print(a.successful())
    print('done')