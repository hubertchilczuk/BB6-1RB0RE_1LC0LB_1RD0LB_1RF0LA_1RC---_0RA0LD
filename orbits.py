import sys
from collections import defaultdict
def events(fn):
    ev=[];lastc=None
    for l in open(fn):
        if l.startswith('HALT') or l.startswith('STOP'): print(l.strip()); continue
        a=l.rstrip('\n').split(' ',2)
        if len(a)<3: continue
        st,c,z=int(a[0]),int(a[1]),a[2].strip()
        if c!=lastc: ev.append((st,c,z)); lastc=c
    return ev
def orbits(ev,minc=150):
    byword=defaultdict(list)
    for st,c,z in ev:
        if c<minc: continue
        zone,word=z.split('|'); byword[word.strip()].append((st,c,zone.strip()))
    res={}
    for w,L in byword.items():
        seen={}
        for i,(st,c,zone) in enumerate(L):
            if zone in seen:
                j=seen[zone]; per=L[j][1]-c
                # orbit = zones between j and i
                orb=[x[2] for x in L[j:i]]
                res[w]=(per,len(orb),orb, L[j])
                break
            seen[zone]=i
        else: res[w]=None
        print('word [%s]: %d events'%(w,len(L)), 'orbit period(blocks)=%s, events=%s'%((res[w][0],res[w][1]) if res[w] else ('?','?')))
    return res
if __name__=='__main__':
    ev=events(sys.argv[1]); print(len(ev),'count-change events')
    o=orbits(ev)
    for w,v in o.items():
        if v: print('  canonical (min) zone for [%s]:'%w, min(v[2]))
