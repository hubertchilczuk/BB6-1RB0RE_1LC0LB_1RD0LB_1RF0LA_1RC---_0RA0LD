# fast macro sim in python with incremental tracking; dump round-start token words to file
import sys
from macro import emacro
SZ=1<<22
t=bytearray(SZ); c=SZ//2; t[c]=1; x=c-1
lo=x; hi=c
def tok(t,x,hi):
    s=bytes(t[x:hi+1]).decode('latin1').translate({0:48,1:49})
    gs=[len(z) for z in s.split('1')][:-1]
    out=[];i=0
    while i<len(gs):
        h=gs[i]
        if h==1 and i+1<len(gs) and gs[i+1]==0: out.append('c'); i+=2; continue  # c = a0
        out.append({1:'a',3:'b'}.get(h,'(%d)'%h)); i+=1
    return ''.join(out)
N=int(sys.argv[1]); f=open(sys.argv[2],'w'); R=0
for k in range(N):
    nx,g=emacro(t,x)
    if g=='halt': print("HALT");break
    if nx<lo:
        lo=nx; R+=1
        while t[hi+1] or t[hi+2] or t[hi+3] or t[hi+4] or t[hi+5] or t[hi+6]: hi+=1
        f.write(tok(t,nx,hi+6)+'\n')
    else:
        if nx>hi: hi=nx
    x=nx
print('rounds',R)
