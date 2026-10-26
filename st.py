import sys
from sim import T
a,b=int(sys.argv[1]),int(sys.argv[2])
tape=bytearray(4000); p=2000; st=0; lo=hi=p
rows=[]
for step in range(b):
    if step>=a:
        rows.append((step,p,st,bytes(tape)))
    r=tape[p]; w,d,ns=T[(st,r)]; tape[p]=w; p+=d; st=ns; lo=min(lo,p); hi=max(hi,p)
for step,pp,s,tp in rows:
    line=''
    for i in range(lo,hi+1):
        c='.#'[tp[i]]
        line+= 'ABCDEF'[s] if i==pp else c
    print('%6d %s'%(step,line))
