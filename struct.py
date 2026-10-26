import surg,sys
def items_of(fn):
    a=open(fn).read().split(); cells=a[3]
    pre,items,tail=surg.parse(cells)
    return [x[0] for x in items]
def structure(names,minrep=6,maxp=4):
    out=[];i=0;n=len(names)
    while i<n:
        best=None
        for p in range(1,maxp+1):
            w=names[i:i+p]
            if len(w)<p: break
            k=1
            while names[i+k*p:i+(k+1)*p]==w: k+=1
            if k>=minrep and (best is None or k*p>best[1]*best[0]): best=(p,k)
        if best:
            p,k=best; out.append('(%s)^%d'%(' '.join(names[i:i+p]),k)); i+=p*k
        else:
            out.append(names[i]); i+=1
    return ' '.join(out)
if __name__=='__main__': print(structure(items_of(sys.argv[1]))[:800])
