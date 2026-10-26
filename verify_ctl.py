import sys, json
M="1RB0RE_1LC0LB_1RD0LB_1RF0LA_1RC---_0RA0LD"
def parse(M):
    tr={}
    for s,part in enumerate(M.split('_')):
        for r in range(2):
            t=part[3*r:3*r+3]
            tr[(s,r)]=None if t[0]=='-' else (int(t[0]),1 if t[1]=='R' else -1,ord(t[2])-65)
    return tr
def verify(sol,M=M):
    tr=parse(M); DL=sol['DL']; DR=sol['DR']; A=set(map(tuple,sol['A']))
    n=len(DL); m=len(DR)
    assert DL[0][0]==0 and DR[0][0]==0, "blank-absorbing start states"
    assert (0,0,0,0) in A, "initial config"
    for (ql,f,r,qr) in A:
        t=tr[(f,r)]
        assert t is not None, ("halting tuple in invariant",ql,f,r,qr)
        w,d,g=t
        if d==1:
            q2=DL[ql][w]
            for qr2 in range(m):
                for r2 in range(2):
                    if DR[qr2][r2]==qr: assert (q2,g,r2,qr2) in A, ("not closed R",ql,f,r,qr)
        else:
            q2=DR[qr][w]
            for ql2 in range(n):
                for l in range(2):
                    if DL[ql2][l]==ql: assert (ql2,g,l,q2) in A, ("not closed L",ql,f,r,qr)
    return True
if __name__=='__main__':
    print("VERIFIED" if verify(json.load(open(sys.argv[1]))) else "FAIL")
