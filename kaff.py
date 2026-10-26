import json,glob,re,subprocess,sys,gen,prover,surg
D=gen.D
P=json.load(open(D+'proof.json'))
def kof(t):
    T=t.split(' || ')[1].split(' / ')[0].split()
    return len(T)-3 if T[:2]==['0','4'] and T[-1]=='2' else None
canons=[l.rstrip('\n') for l in open(D+'canon_all.txt') if l.strip()]
def tparts(Tc):
    p,its,tl=surg.parse('1'+Tc); return [(x[0],('1'+Tc)[x[1]:x[2]]) for x in its]
# find a sample config of a 3^k context
src=None
for fn in glob.glob(D+'pv_B*_a.txt')[:4000]:
    try: st=gen.parse_struct(fn,'1 7 0 0* 9 9 3 7 0 0* 2 | 0 3 1 ')
    except Exception: continue
    if st['T'][:2]==['0','4'] and len(st['T'])>5: src=st; break
parts=tparts(src['T_cells']); three=[c for n,c in parts if n=='3'][0]; head=''.join(c for n,c in parts[:2]); last=parts[-1][1]
r=int(sys.argv[1]); par=int(sys.argv[2])
for k in eval(sys.argv[3]):
    st=dict(src); st['T_cells']=head+three*k+last
    gen.rebuild(st,r,1000+par,D+'ka_in.txt')
    subprocess.run([D+'fsim.exe','20','1e15',D+'ka_in.txt',D+'canon_all.txt',D+'ka_out.txt'],capture_output=True)
    s=None
    for c in canons:
        try: s=gen.parse_struct(D+'ka_out.txt',c); cc=c; break
        except Exception: pass
    print('k=%d -> %s k\'=%s N1=%d M1=%d'%(k,'R8' if '| 8' in cc else 'R031',kof(prover.ctxkey(cc,s)),s['N'],s['M']),flush=True)
