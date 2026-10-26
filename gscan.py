import os
import subprocess, surg, sys
D=os.path.dirname(os.path.abspath(__file__)) + '/'
ZS="1 7 0 0* 4 3 0 0 0 0 0"
SRC={'3':'s_226258280.txt','702':'s_2671967394.txt'}
def G(r,M,T,maxsteps=2*10**10,tag='x'):
    cfg=D+'cfg_g_%s.txt'%tag; outc=D+'cfg_gz_%s.txt'%tag
    surg.build(D+SRC[T],newN=r,newM=M,out=cfg)
    out=subprocess.run([D+'runfrom.exe',str(maxsteps),'0',cfg,'999999999',outc,ZS],capture_output=True,text=True).stdout.strip().splitlines()
    last=out[-1] if out else 'LIMIT'
    if last.startswith('ZSTAR'):
        i=surg.build(outc); return (i['N'],i['M'],''.join(i['T']),' '.join(i['after']),int(last.split()[-1]))
    return last
if __name__=='__main__':
    T=sys.argv[1]; rs=eval(sys.argv[2]); Ms=eval(sys.argv[3])
    for r in rs:
        for M in Ms:
            print(T,r,M,G(r,M,T,tag=T+'_'+sys.argv[4] if len(sys.argv)>4 else T),flush=True)
