from macro import emacro
from mstats import nextgaps
SZ=1<<16
t=bytearray(SZ); c=SZ//2; t[c]=1; x=c-1
hist=[]
shown=0
def show(t,x,lo=30,hi=30):
    s=''.join('.#'[b] for b in t[x-lo:x])+'|'+''.join('.#'[b] for b in t[x:x+hi]); return s
for k in range(200000):
    ng=nextgaps(t,x,3)
    snap=(show(t,x),ng)
    hist.append(snap); hist=hist[-6:]
    if 0 in ng[1:3] and ng[ng.index(0,1)-1]==3 and ng.index(0,1)>0:
        for h in hist: print(h)
        print('----'); shown+=1
        if shown>=4: break
    x,g=emacro(t,x)
