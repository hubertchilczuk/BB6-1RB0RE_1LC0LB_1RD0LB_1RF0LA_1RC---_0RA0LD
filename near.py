# for each time E has g=2 followed by gap 3 (danger zone), what's the context to the LEFT (u tail) and right
import sys
from collections import Counter
from macro import emacro
from mstats import nextgaps
SZ=1<<20
t=bytearray(SZ); c=SZ//2; t[c]=1; x=c-1
C=Counter()
for k in range(int(sys.argv[1])):
    ng=nextgaps(t,x,3)
    if ng[:2]==(2,3):
        left=''.join(map(str,t[x-12:x])); C[(left,ng)]+=1
    x,g=emacro(t,x)
for k,v in C.most_common(25): print(v,k)
