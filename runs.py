from sim import T
from collections import Counter
tape=bytearray(400000); p=200000; st=0
runs=[]; mode='R'; start=p
Lc=Counter(); Rc=Counter()
for step in range(20000000):
    r=tape[p]; tr=T[(st,r)]
    if tr is None: print("HALT"); break
    w,d,ns=tr
    if st==2 and r==0:  # C0: end of L-run
        Lc[start-p]+=1; start=p
    if ns==1 and st!=1: # entering B from A0 or C1
        Rc[p-start]+=1; start=p
    tape[p]=w; p+=d; st=ns
print("L-run lengths", sorted(Lc.items())[:40], len(Lc))
print("R-run lengths", sorted(Rc.items())[:40], len(Rc))
