"""Lemma A for odd M (base M0+1) for every reachable non-partial node of proof2.json."""
import json, sys, threading
from concurrent.futures import ThreadPoolExecutor
import prover2 as P2
D = P2.D
proof = P2.proof
nodes = proof['nodes']
# register samples via lemma B target files and the start config
st, ck, fk = P2.classify(D + 's_226258280.txt', '1 7 0 0* 4 3 0 0 0 0 0 9 | 8 ')
P2.samples[ck] = st
for rec in proof['lemmaB'].values():
    for t, fn in rec.get('targets_files', {}).items():
        if t not in P2.samples:
            try: P2.samples[t] = P2.classify(fn, t.split(' || ')[0])[0]
            except Exception as e: print('sample fail', t[:60], e)
# families: samples come from concrete members
for t in list(P2.samples):
    if not P2.is_family(t) and P2.samples[t]['k'] is not None:
        f = P2.family_of(t)
        if f not in P2.samples: P2.samples[f] = P2.samples[t]
todo = [n for n, v in nodes.items() if 'P' in v and 'partial_of' not in v]
print('nodes needing odd-M lemma A:', len(todo), 'missing samples:', sum(1 for n in todo if n not in P2.samples), flush=True)
proof.setdefault('lemmaA_odd', {})
M0 = P2.M0
def one(node):
    if node in proof['lemmaA_odd'] or node not in P2.samples: return
    P2.M0 = M0  # base stays even; we pass M0+1 explicitly below
    fam = P2.is_family(node); s = P2.samples[node]; canon = node.split(' || ')[0]
    tag = 'O' + P2.tagof(node); park = s['k'] % 2 if fam else 0; kk = P2.K0 + park if fam else None
    N0 = P2.N0; Mb = M0 + 1
    f = [D + 'p2_%s_%s.txt' % (tag, q) for q in 'abcd']
    P2.build(node, N0, Mb, kk, f[0]); P2.build(node, N0 + 1, Mb, kk, f[1]); P2.build(node, N0, Mb + 2, kk, f[2])
    vars_ = [f[1], f[2]]
    if fam: P2.build(node, N0, Mb, kk + 2, f[3]); vars_.append(f[3])
    insts = [(0, 0, 0), (1, 0, 0), (0, 1, 0), (3, 2, 1 if fam else 0)]
    res = P2.run_ssim(f[0], vars_, insts, tag)
    rec = {'status': res['status']}
    A = proof['lemmaA'][node]
    if res['status'] == 'CANON' and res['canon'] == canon:
        vals = {}; ok = True
        for i, fn in res['files'].items():
            st2, ck2, fk2 = P2.classify(fn, canon)
            if (fk2 if fam else ck2) != node: ok = False; break
            vals[i] = (st2['N'], st2['M'], st2['k'])
        if ok:
            lin = all(vals[(x, y, z)] == (N0 + x - A['P'], Mb + 2 * y + A['dM'], (kk + 2 * z) if fam else vals[(0,0,0)][2]) for (x, y, z) in vals)
            rec.update(status='OK' if lin else 'NONLINEAR', constraints=res['constraints'])
        else:
            rec['status'] = 'NODE-CHANGED'
    with P2.lock: proof['lemmaA_odd'][node] = rec
    print('ODD-A', rec['status'], node[:90], flush=True)
with ThreadPoolExecutor(6) as ex: list(ex.map(one, todo))
P2.save()
from collections import Counter
print(Counter(v['status'] for v in proof['lemmaA_odd'].values()))
