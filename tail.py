import sys,re
from collections import Counter
from macro import emacro
from mstats import nextgaps
SZ=1<<20
t=bytearray(SZ); c=SZ//2; t[c]=1; x=c-1
C=Counter()
def tailtok(s):
    # s = u after last '00' (starting right after the 00 pair's second zero... we take from the last '00' inclusive)
    s=s.replace('1110','Q').replace('10','P')
    s=re.sub('P{3,}','P*',s)
    return s
for k in range(int(sys.argv[1])):
    seg=bytes(t[x-3000:x]).decode('latin1').translate({0:48,1:49})
    i=seg.rfind('00')
    tl=seg[i+2:] if i>=0 else '#'+seg
    ng=nextgaps(t,x,1)[0]
    C[(tailtok(tl), ng)]+=1
    x,g=emacro(t,x)
for k,v in sorted(C.items(),key=lambda kv:-kv[1])[:60]: print(v,k)
print(len(C))
