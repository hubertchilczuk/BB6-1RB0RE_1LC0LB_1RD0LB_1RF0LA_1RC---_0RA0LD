import sys, time
from pysat.solvers import Cadical153
def parse(M,mirror):
    tr={}
    for s,part in enumerate(M.split('_')):
        for r in range(2):
            t=part[3*r:3*r+3]
            if t[0]=='-': tr[(s,r)]=None
            else:
                d=1 if t[1]=='R' else -1
                if mirror: d=-d
                tr[(s,r)]=(int(t[0]),d,ord(t[2])-65)
    return tr
def solve(M,n,mirror,timeout=None):
    tr=parse(M,mirror); S=6; N=n*S+1; TOP=N-1
    idx=lambda q,f:q*S+f
    cnt=[0]
    def nv(): cnt[0]+=1; return cnt[0]
    D={(q,b,p):nv() for q in range(n) for b in range(2) for p in range(n)}
    Tm={(b,i,j):nv() for b in range(2) for i in range(N) for j in range(N)}
    A={i:nv() for i in range(N)}
    cl=[]
    for q in range(n):
        for b in range(2):
            cl.append([D[q,b,p] for p in range(n)])
            for p1 in range(n):
                for p2 in range(p1+1,n): cl.append([-D[q,b,p1],-D[q,b,p2]])
    cl.append([D[0,0,0]])
    # BFS symmetry breaking (light): state p>0 first reached ... skip
    cl+= [[Tm[0,TOP,TOP]],[Tm[1,TOP,TOP]],[A[TOP]]]
    for (f,r),t in tr.items():
        if t is None:
            for q in range(n): cl.append([Tm[r,idx(q,f),TOP]])
            continue
        w,d,g=t
        if d==1:
            for q in range(n):
                for p in range(n): cl.append([-D[q,w,p],Tm[r,idx(q,f),idx(p,g)]])
        else:
            for qp in range(n):
                for l in range(2):
                    for q in range(n):
                        dq=-D[qp,l,q]
                        for k in range(N):
                            a=-Tm[l,idx(qp,g),k]
                            for j in range(N):
                                cl.append([dq,a,-Tm[w,k,j],Tm[r,idx(q,f),j]])
    for i in range(N):
        for j in range(N): cl.append([-Tm[0,i,j],-A[j],A[i]])
    for j in range(N): cl.append([-Tm[0,idx(0,0),j],-A[j]])
    s=Cadical153(bootstrap_with=cl)
    t0=time.time(); res=s.solve(); dt=time.time()-t0
    out=None
    if res:
        m=set(x for x in s.get_model() if x>0)
        out=[[next(p for p in range(n) if D[q,b,p] in m) for b in range(2)] for q in range(n)]
    return res,len(cl),dt,out
if __name__=='__main__':
    M=sys.argv[1]; mirror=int(sys.argv[3])
    for n in map(int,sys.argv[2].split(',')):
        res,nc,dt,out=solve(M,n,mirror)
        print('n=%d mirror=%d clauses=%d time=%.1fs -> %s %s'%(n,mirror,nc,dt,'SAT(PROOF)' if res else 'UNSAT',out),flush=True)
