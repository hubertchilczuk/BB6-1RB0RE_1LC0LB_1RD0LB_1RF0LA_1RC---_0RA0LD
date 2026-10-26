# Use exact python TM? too slow. Use macro sim in python for ~3e7 TM-step range: macro sim fine.
import sys,re
from macro import emacro
SZ=1<<22
t=bytearray(SZ); c=SZ//2; t[c]=1; x=c-1
lo=x; hi=c
def items(t,x,hi):
    s=bytes(t[x:hi+1]).decode('latin1').translate({0:48,1:49})
    gs=[len(z) for z in s.split('1')][:-1]
    out=[];k=0;i=1
    while i<len(gs):
        h=gs[i]
        if h==1 and i+1<len(gs) and gs[i+1]==0: out.append('%d*'%k);k=0;i+=2;continue
        if h==1: k+=1
        elif h==3: out.append(str(k));k=0
        else: out.append('%d(%d)'%(k,h));k=0
        i+=1
    out.append('+%d'%k)
    return out
N=int(sys.argv[1]); lastN=None
for k in range(N):
    nx,g=emacro(t,x)
    if g=='halt': print("HALT");break
    if nx<lo:
        lo=nx
        while any(t[hi+1:hi+8]): hi+=1
        it=items(t,nx,hi+8)
        # find '9' followed by run of '8'
        try:
            j=next(j for j in range(len(it)-1) if it[j]=='9' and it[j+1]=='8')
        except StopIteration:
            continue
        e=j+1
        while e<len(it) and it[e]=='8': e+=1
        n8=e-j-1
        if n8!=lastN:
            M=sum(1 for z in it[e:] if z in('0','1'))
            print(k,'zone:',' '.join(it[:j]),'| N=',n8,'rest',' '.join(it[e:e+4]),'len',len(it)-e,flush=True)
            lastN=n8
    else:
        if nx>hi: hi=nx
    x=nx
