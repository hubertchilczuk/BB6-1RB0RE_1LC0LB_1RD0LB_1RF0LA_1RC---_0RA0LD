import sys
from macro import emacro
SZ=1<<16
t=bytearray(SZ); c=SZ//2
# start: TM first E entry state
t[c]=1; x=c-1  # from earlier: first E at -1 with tape 1 at 0
def gaps(seg):
    s=''.join(map(str,seg)); return s
lo=x;hi=x
seq=[]
N=int(sys.argv[1])
for k in range(N):
    ox=x
    x,g=emacro(t,x)
    if g=='halt': print('HALT'); break
    seq.append((g,ox,x))
    lo=min(lo,x);hi=max(hi,x+6)
# print sequence compressed: rule type and whether jump back
out=[]
for g,ox,nx in seq[-int(sys.argv[2]):]:
    out.append(str(g) if nx>ox else '%d<%d'%(g,ox-nx))
print(' '.join(out))
