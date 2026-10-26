import sys, time, json
from pysat.solvers import Cadical153
from farsat import parse
SYM=1
def solve(M,n,m):
    tr=parse(M,0); S=6
    cnt=[0]
    def nv(): cnt[0]+=1; return cnt[0]
    DL={(q,b,p):nv() for q in range(n) for b in range(2) for p in range(n)}
    DR={(q,b,p):nv() for q in range(m) for b in range(2) for p in range(m)}
    A={(ql,f,r,qr):nv() for ql in range(n) for f in range(S) for r in range(2) for qr in range(m)}
    cl=[]
    def onehot(D,k):
        for q in range(k):
            for b in range(2):
                cl.append([D[q,b,p] for p in range(k)])
                for p1 in range(k):
                    for p2 in range(p1+1,k): cl.append([-D[q,b,p1],-D[q,b,p2]])
    onehot(DL,n); onehot(DR,m)
    def bfs(D,k):
        if k<2: return
        t={(i,j):nv() for i in range(k) for j in range(i+1,k)}
        P={(j,i):nv() for j in range(1,k) for i in range(j)}
        for (i,j),v in t.items():
            cl.append([-v,D[i,0,j],D[i,1,j]]); cl.append([v,-D[i,0,j]]); cl.append([v,-D[i,1,j]])
        for j in range(1,k):
            cl.append([P[j,i] for i in range(j)])
            for i in range(j):
                v=P[j,i]
                cl.append([-v,t[i,j]])
                for kk in range(i): cl.append([-v,-t[kk,j]])
                cl.append([v,-t[i,j]]+[t[kk,j] for kk in range(i)])
        for j in range(1,k-1):
            for i in range(j):
                for kk in range(i): cl.append([-P[j,i],-P[j+1,kk]])
                cl.append([-P[j,i],-P[j+1,i],D[i,0,j]]); cl.append([-P[j,i],-P[j+1,i],D[i,1,j+1]])
    if SYM: bfs(DL,n); bfs(DR,m)
    cl.append([DL[0,0,0]]); cl.append([DR[0,0,0]])
    cl.append([A[0,0,0,0]])
    for (f,r),t in tr.items():
        if t is None:
            for ql in range(n):
                for qr in range(m): cl.append([-A[ql,f,r,qr]])
            continue
        w,d,g=t
        for ql in range(n):
            for qr in range(m):
                a=A[ql,f,r,qr]
                if d==1:
                    for q2 in range(n):
                        for qr2 in range(m):
                            for r2 in range(2):
                                cl.append([-a,-DL[ql,w,q2],-DR[qr2,r2,qr],A[q2,g,r2,qr2]])
                else:
                    for q2 in range(m):
                        for ql2 in range(n):
                            for l in range(2):
                                cl.append([-a,-DR[qr,w,q2],-DL[ql2,l,ql],A[ql2,g,l,q2]])
    s=Cadical153(bootstrap_with=cl)
    t0=time.time(); res=s.solve(); dt=time.time()-t0
    sol=None
    if res:
        mm=set(x for x in s.get_model() if x>0)
        sol={'DL':[[next(p for p in range(n) if DL[q,b,p] in mm) for b in range(2)] for q in range(n)],
             'DR':[[next(p for p in range(m) if DR[q,b,p] in mm) for b in range(2)] for q in range(m)],
             'A':[k for k,v in A.items() if v in mm]}
    return res,len(cl),dt,sol
if __name__=='__main__':
    M=sys.argv[1]
    for nm in sys.argv[2].split(','):
        n,m=map(int,nm.split('x'))
        res,nc,dt,sol=solve(M,n,m)
        print('%dx%d clauses=%d time=%.1fs -> %s'%(n,m,nc,dt,'SAT(PROOF)' if res else 'UNSAT'),flush=True)
        if res: json.dump(sol,open('ctl_sol_%dx%d.json'%(n,m),'w')); break
