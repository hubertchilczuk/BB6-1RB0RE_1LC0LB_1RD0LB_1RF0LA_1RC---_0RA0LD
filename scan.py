import os
import subprocess, surg, sys
M=int(sys.argv[1]); lo,hi=int(sys.argv[2]),int(sys.argv[3]); src=sys.argv[4] if len(sys.argv)>4 else 'snap29.txt'
D=os.path.dirname(os.path.abspath(__file__)) + '/'
for N0 in range(lo,hi+1):
    surg.build(D+src,newN=N0,newM=M,out=D+'cfg_tmp.txt')
    thr=max(N0+5,M//4)
    out=subprocess.run([D+'runfrom.exe','20000000000','0',D+'cfg_tmp.txt',str(thr),D+'cfg_new_%d_%d.txt'%(M,N0)],capture_output=True,text=True).stdout.strip().splitlines()
    last=out[-1] if out else 'no output (step limit)'
    info=''
    if last.startswith('NEWCYCLE'):
        i=surg.build(D+'cfg_new_%d_%d.txt'%(M,N0)); info='newN=%d T=%s M=%d after=%s'%(i['N'],' '.join(i['T']),i['M'],' '.join(i['after']))
    print(N0,last,info,flush=True)
