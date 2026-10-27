"""Canonical points of the real trajectory from the blank tape (fsim), classified into proof nodes.

Prints step, node tag, N, M, k for every canonical point up to MAXSTEP; marks nodes that have a lemma A.
usage: early_points.py [MAXSTEP]
"""
import os, sys, json
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/'
sys.path.insert(0, ROOT)
import gen, prover2 as P2
import nodeform as NF

MAXSTEP = float(sys.argv[1]) if len(sys.argv) > 1 else 2.3e8
TMP = ROOT + 'rocq/tmp/'
anodes = set(json.load(open(ROOT + 'rocq/anodes.json')))
cur = TMP + 'ep_0.txt'
open(cur, 'w').write('0 0 0\n0\n')
i = 0
while True:
    nxt = TMP + 'ep_%d.txt' % ((i + 1) % 2)
    st, z, out = gen.run_to_canon(cur, P2.CANON, nxt, 1e12)
    if st != 'CANON': print('stop', st); break
    s2, ck, fk = P2.classify(nxt, z)
    step = int(open(nxt).read().split()[0])
    node = NF.P['nodes'].get(ck, {}).get('covered_by', ck)
    if node not in NF.P['nodes'] and fk in NF.P['nodes']: node = fk
    print('%12d %s %s N=%s M=%s k=%s %s' % (step, NF.tagof(node), 'A' if node in anodes else '-', s2['N'], s2['M'], s2['k'], z.strip()[:40]), flush=True)
    if step > MAXSTEP: break
    cur = nxt; i += 1
