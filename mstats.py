import sys
from collections import Counter
from macro import emacro
SZ=1<<20
t=bytearray(SZ); c=SZ//2; t[c]=1; x=c-1
def nextgaps(t,x,k):
    out=[];g=0;i=x
    while len(out)<k:
        if t[i]==1: out.append(g); g=0
        else:
            g+=1
            if g>12: out.append(99); break
        i+=1
    return tuple(out)
if __name__=='__main__':
  C=Counter()
  N=int(sys.argv[1])
  for k in range(N):
    ng=nextgaps(t,x,4)
    x,g=emacro(t,x)
    C[ng]+=1
  for k,v in sorted(C.items()): print(k,v)
