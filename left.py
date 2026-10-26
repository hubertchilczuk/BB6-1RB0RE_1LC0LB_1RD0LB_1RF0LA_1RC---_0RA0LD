import sys
from sim import T
def run(n):
    tape=bytearray(200000); p=100000; st=0; lo=hi=p
    for step in range(n):
        r=tape[p]; tr=T[(st,r)]
        if tr is None: print('HALT',step); return
        w,d,ns=tr; tape[p]=w; p+=d; st=ns
        if p<lo:
            lo=p
            s=''.join(map(str,tape[lo:hi+1])).rstrip('0')
            yield step,'L','ABCDEF'[st],s
        if p>hi:
            hi=p
            s=''.join(map(str,tape[lo:hi+1]))
            yield step,'R','ABCDEF'[st],s
for step,side,st,s in run(int(sys.argv[1])):
    if side=='L' and st=='C':
        print(step, s.replace('1000','b').replace('10','a'))
