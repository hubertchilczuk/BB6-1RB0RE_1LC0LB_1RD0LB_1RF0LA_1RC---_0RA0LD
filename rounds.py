import sys
from macro import emacro
SZ=1<<20
t=bytearray(SZ); c=SZ//2; t[c]=1; x=c-1
lo=x
def tok(t,x):
    # gaps from x to end
    gs=[];g=0;i=x;end=max(i for i in range(x,x+400000) if t[i]) if any(t[x:x+400000]) else x
    while i<=end:
        if t[i]: gs.append(g); g=0
        else: g+=1
        i+=1
    s=[];i=0
    while i<len(gs):
        h=gs[i]
        if h==3 and i+1<len(gs) and gs[i+1]==0: s.append('d'); i+=2; continue
        s.append({1:'a',3:'b'}.get(h,'(%d)'%h)); i+=1
    return ''.join(s)
N=int(sys.argv[1]); R=0
for k in range(N):
    nx,g=emacro(t,x)
    if g=='halt': print("HALT");break
    if nx<lo:
        lo=nx; R+=1
        if R>=int(sys.argv[2]): print(R,k,tok(t,nx)[:int(sys.argv[3])],flush=True)
    x=nx
