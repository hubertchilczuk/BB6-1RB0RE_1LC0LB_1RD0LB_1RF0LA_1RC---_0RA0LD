import sys
from sim import T
def ngramcps(n, maxcfg=5_000_000):
    z=(0,)*n
    GL={(0,)*(n+1)}; GR={(0,)*(n+1)}
    # index: prefix n-gram -> set of next symbols
    def ext(G,w): return [x for x in (0,1) if w+(x,) in G]
    start=(0,z,0,z)
    seen={start}; todo=[start]
    changed=True
    while changed:
        changed=False
        todo=list(seen)
        while todo:
            s,lw,h,rw=todo.pop()
            tr=T[(s,h)]
            if tr is None: return False, len(seen), (s,lw,h,rw)
            w,d,ns=tr
            if d==1:
                g=lw+(w,)  # left side n+1-gram, ordering: far ... near
                if g not in GL: GL.add(g); changed=True
                nlw=g[1:]
                # pop from right: rw[0] is new head; reveal x beyond
                g2=rw
                for x in (0,1):
                    if rw+(x,) in GR:
                        c=(ns,nlw,rw[0],rw[1:]+(x,))
                        if c not in seen: seen.add(c); todo.append(c)
            else:
                g=(w,)+rw  # right side n+1-gram ordering near ... far
                if g not in GR: GR.add(g); changed=True
                nrw=g[:n]
                for x in (0,1):
                    if (x,)+lw in GL:
                        c=(ns,(x,)+lw[:-1],lw[-1],nrw)
                        if c not in seen: seen.add(c); todo.append(c)
            if len(seen)>maxcfg: return None,len(seen),None
    return True,len(seen),None
for n in range(1,int(sys.argv[1])+1):
    r=ngramcps(n)
    print(n,r[0],r[1],r[2],flush=True)
