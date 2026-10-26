import gen, sys, json, glob
D=gen.D
C031='1 7 0 0* 9 9 3 7 0 0* 2 | 0 3 1 '
# find a sample canonical config with T = 0 4 3^k 2
src=None
for fn in glob.glob(D+'tmp_out_*.txt'):
    try:
        a=open(fn).read().split()
        st=gen.parse_struct(fn,C031)
    except Exception: continue
    if st['T'][:2]==['0','4']: src=st; break
print('sample T',' '.join(src['T']),'u',src['u'],'tail',src['tail'])
import surg
step,s,off,cells=gen.load(fn)
pre,items,tail=surg.parse(cells)
# cells of one '3' item: find in T_cells: T = '0 4 3... 2'
names=src['T']
# compute T cell pieces via reparse of T_cells
def tparts(Tcells):
    # parse T_cells as items starting right after a '1' boundary: prepend '1'
    p,its,tl=surg.parse('1'+Tcells)
    return [(x[0],('1'+Tcells)[x[1]:x[2]]) for x in its]
parts=tparts(src['T_cells'])
print([x[0] for x in parts])
three=[c for n,c in parts if n=='3'][0]
head=''.join(c for n,c in parts[:2]); last=parts[-1][1]
def setk(st,k):
    st=dict(st); st['T_cells']=head+three*k+last; st['T']=['0','4']+['3']*k+['2']; return st
r=int(sys.argv[1]); M0=int(sys.argv[2])
for k in eval(sys.argv[3]):
    st=setk(src,k)
    gen.rebuild(st,r,M0,D+'kin.txt')
    status,c2,_=gen.run_to_canon(D+'kin.txt',D+'canon_all.txt',D+'kout.txt')
    if status=='CANON':
        s2=gen.parse_struct(D+'kout.txt',c2); T2=' '.join(s2['T']); 
        if s2['T'][:2]==['0','4']: T2='0 4 3^%d 2'%(len(s2['T'])-3)
        print('k=%d M=%d ->'%(k,M0),'R8' if '| 8' in c2 else 'R031',T2,'N1=',s2['N'],'M1=',s2['M'],flush=True)
    else: print('k=%d'%k,status,flush=True)
