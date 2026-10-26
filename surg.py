import sys
def parse(cells):
    # returns list of (item, start, end) ; prefix before first 1 kept separately
    i=cells.index('1'); pre=cells[:i+1]; pos=i+1; items=[]; k=0; st=pos
    while True:
        j=cells.find('1',pos)
        if j<0: break
        g=j-pos
        if g==1 and j+1<len(cells) and cells[j+1]=='1':
            items.append(('%d*'%k,st,j+2)); k=0; pos=j+2; st=pos; continue
        if g==1: k+=1; pos=j+1; continue
        if g==3: items.append(('%d'%k,st,j+1))
        else: items.append(('%d(%d)'%(k,g),st,j+1))
        k=0; pos=j+1; st=pos
    tail=cells[st:]
    return pre,items,tail
def load(fn):
    a=open(fn).read().split()
    return int(a[0]),int(a[1]),int(a[2]),a[3]
def build(fn,newN=None,newM=None,out=None):
    step,s,off,cells=load(fn)
    pre,items,tail=parse(cells)
    names=[x[0] for x in items]
    j=next(j for j in range(len(names)-1) if names[j]=='9' and names[j+1]=='8')
    e=j+1
    while names[e]=='8': e+=1
    N=e-j-1
    # M: run of alternating 0 1 items after T
    seg=[cells[a:b] for _,a,b in items]
    zone=pre+''.join(seg[:j+1])
    blk8=seg[j+1]
    rest_items=names[e:]
    # find [0 1]^M run start: first index f>=e where names[f:f+2]==['0','1'] repeating
    f=e
    while not (names[f]=='0' and names[f+1]=='1' and names[f+2]=='0'): f+=1
    g=f
    while g+1<len(names) and names[g]=='0' and names[g+1]=='1': g+=2
    M=(g-f)//2
    T=''.join(seg[e:f]); pair=seg[f]+seg[f+1]; after=''.join(seg[g:])+tail
    info=dict(N=N,M=M,T=names[e:f],after=names[g:],zone=names[:j])
    if out:
        nn=N if newN is None else newN; mm=M if newM is None else newM
        c=zone+blk8*nn+T+pair*mm+after
        open(out,'w').write('%d %d %d\n%s\n'%(step,s,off,c))
    return info
if __name__=='__main__':
    print(build(sys.argv[1]))
