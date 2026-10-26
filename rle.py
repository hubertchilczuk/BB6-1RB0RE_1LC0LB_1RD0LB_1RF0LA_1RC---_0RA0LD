import surg,sys
def rle(fn,limit=700):
    a=open(fn).read().split(); cells=a[3]
    pre,items,tail=surg.parse(cells)
    names=[x[0] for x in items]
    out=[];i=0
    while i<len(names):
        j=i
        while j<len(names) and names[j]==names[i]: j+=1
        if j-i>1: out.append('%s^%d'%(names[i],j-i)); i=j; continue
        if i+3<len(names) and names[i]==names[i+2] and names[i+1]==names[i+3]:
            k=i
            while k+3<len(names) and names[k]==names[k+2] and names[k+1]==names[k+3]: k+=2
            out.append('[%s %s]^%d'%(names[i],names[i+1],(k-i)//2+1)); i=k+2; continue
        out.append(names[i]); i+=1
    return ' '.join(out)[:limit]
if __name__=='__main__': print(rle(sys.argv[1]))
