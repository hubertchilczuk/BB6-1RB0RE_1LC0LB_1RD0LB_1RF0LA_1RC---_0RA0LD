# For each entry into E (A read 1), collect local context: previous 6 transitions and window around head
from sim import T
from collections import Counter
tape=bytearray(400000); p=200000; st=0
hist=[]
c=Counter(); c2=Counter()
for step in range(30000000):
    r=tape[p]; tr=T[(st,r)]
    if tr is None: print("HALT"); break
    if st==0 and r==1:
        # window p-4..p+6 and last transitions
        win=''.join(map(str,tape[p-3:p+5]))
        c[(tuple(hist[-4:]), win[:3]+'['+win[3]+']'+win[4:])]+=1
    hist.append('ABCDEF'[st]+str(r)); 
    if len(hist)>10: hist.pop(0)
    w,d,ns=tr; tape[p]=w; p+=d; st=ns
for k,v in c.most_common(40): print(v,k)
