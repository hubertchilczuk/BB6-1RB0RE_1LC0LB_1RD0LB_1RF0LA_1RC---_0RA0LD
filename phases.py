import sys
fn=sys.argv[1]
last=None;cnt=0;first=None;prev=None;prun=''
def rot(w):
    t=w.split(); return ' '.join(min(t[i:]+t[:i] for i in range(len(t)))) if t else '-'
for l in open(fn):
    if not l[0].isdigit(): print(l.strip()[:120]); continue
    st,z=l.rstrip('\n').split(' ',1)
    w=rot(z.split('|')[1].split('##')[0].strip())
    runs=z.split('##')[1].strip() if '##' in z else ''
    if w!=last:
        if last is not None: print('%14s .. %14s front=[%s] events=%d runs@end=%s'%(first,prev,last,cnt,prun))
        last=w;cnt=0;first=st
    cnt+=1; prev=st; prun=runs
print('%14s .. %14s front=[%s] events=%d runs@end=%s'%(first,prev,last,cnt,prun))
