import sys
M="1RB0RE_1LC0LB_1RD0LB_1RF0LA_1RC---_0RA0LD"
T={}
for i,s in enumerate(M.split('_')):
    for r in range(2):
        t=s[3*r:3*r+3]
        T[(i,r)]=None if t[0]=='-' else (int(t[0]),1 if t[1]=='R' else -1,ord(t[2])-65)
def run(n, show=None):
    tape={}; p=0; st=0
    for step in range(n):
        if show and show(step,st,p,tape): pass
        r=tape.get(p,0); tr=T[(st,r)]
        if tr is None: return ('halt',step,tape,p,st)
        w,d,ns=tr; tape[p]=w; p+=d; st=ns
    return ('run',n,tape,p,st)
def fmt(tape,p,st):
    if not tape: return ''
    lo=min(min(tape),p); hi=max(max(tape),p)
    s=''
    for i in range(lo,hi+1):
        c=str(tape.get(i,0))
        s+= ('['+'ABCDEF'[st]+c+']') if i==p else c
    return s
if __name__=='__main__':
    n=int(sys.argv[1])
    lastL=[0]; 
    def show(step,st,p,tape):
        # print when head at new leftmost or rightmost
        if tape:
            lo=min(tape); hi=max(tape)
            if p<lo or p>hi:
                print(step, 'ABCDEF'[st], fmt(tape,p,st))
    r=run(n,show)
    print(r[0],r[1])
