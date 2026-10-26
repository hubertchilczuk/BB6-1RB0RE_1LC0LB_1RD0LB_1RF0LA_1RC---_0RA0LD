from sim import T
SZ=20000
def lrun(t,c):
    y=c; stC=False
    while True:
        if t[y]==0 and stC: t[y+1]=0; return y+1
        o=t[y]; t[y]=1-o; stC=(o==0); y-=1
def emacro(t,x):
    g=0
    while g<5 and t[x+g]==0: g+=1
    if g==0: return None,'halt'
    if g==2: t[x]=1;t[x+1]=0;t[x+2]=0; return x+2,2
    if g==3: t[x]=1;t[x+1]=0;t[x+2]=0;t[x+3]=0; return x+2,3
    if g==4: t[x:x+5]=bytes([1,1,1,0,0]); return x+5,4
    if g==1: t[x]=0;t[x+1]=0; return lrun(t,x-1),1
    t[x:x+5]=bytes([1,1,1,0,1]); return lrun(t,x+5),5
def tm_E_entries(nsteps):
    t=bytearray(SZ); p=SZ//2; st=0
    for _ in range(nsteps):
        if st==4: yield p, bytes(t)
        r=t[p]; tr=T[(st,r)]
        if tr is None: return
        w,d,ns=tr; t[p]=w; p+=d; st=ns
if __name__=='__main__':
    gen=tm_E_entries(3_000_000)
    p0,t0=next(gen)
    t=bytearray(t0); x=p0; k=0
    for p1,t1 in gen:
        x,g=emacro(t,x); k+=1
        if x!=p1 or bytes(t)!=t1: print("MISMATCH at macro",k,g); break
    else: print("OK, verified",k,"macro steps")
