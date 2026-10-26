import random, ctlsat
random.seed(1)
mism=0; sat=0; tot=0
for it in range(150):
    parts=[]
    for s in range(6):
        p=''
        for r in range(2):
            if random.random()<0.08: p+='---'
            else: p+=random.choice('01')+random.choice('LR')+random.choice('ABC' if s<3 else 'ABCDEF')
        parts.append(p)
    M='_'.join(parts)
    for nm in [(2,2),(3,2),(3,3)]:
        ctlsat.SYM=0; r0=ctlsat.solve(M,*nm)[0]
        ctlsat.SYM=1; r1=ctlsat.solve(M,*nm)[0]
        tot+=1; sat+=r0
        if r0!=r1: mism+=1; print('MISMATCH',M,nm,r0,r1)
print('total',tot,'sat',sat,'mismatches',mism)
