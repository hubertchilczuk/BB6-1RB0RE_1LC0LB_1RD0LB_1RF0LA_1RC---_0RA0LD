"""Build proof4.json from proof2.json and the ssim4 re-derivation (rerun4_results.jsonl).

Every lemma takes its constraints from ssim4; small-N lemmas (which store only bounds) get Mmin / Kmin
recomputed from the ssim4 constraints exactly as the prover did. Any lemma that ssim4 could not
reproduce (other canon, other output) is marked not OK, so verify4 cannot use it.
"""
import os, json, re
from collections import Counter

D = os.path.dirname(os.path.abspath(__file__)) + '/'
P = json.load(open(D + 'proof2.json'))
M0, K0 = 1000, 1000


def bounds(cons, nv=3):
    """sufficient lower bounds b_i for the variables such that all constraints c + sum a_i v_i >= 0 hold
    (same as prover2.bounds)."""
    b = [-10 ** 12] * nv
    for t in cons.split():
        m = re.match(r'(-?\d+)' + ''.join(r'([+-]\d+)v%d' % i for i in range(nv)) + r'>=0', t)
        if not m: continue
        c = int(m.group(1)); a = [int(m.group(i + 2)) for i in range(nv)]
        S = sum(x for x in a if x > 0)
        if S == 0: continue
        need = -(c // S)
        for i in range(nv):
            if a[i] > 0: b[i] = max(b[i], need)
    return b


res = {}
for l in open(D + 'rerun4_results.jsonl'):
    d = json.loads(l); res[(d['sect'], d['key'])] = d

stat = Counter()
for sect in ('lemmaA', 'lemmaA_odd', 'lemmaA_smallM', 'lemmaB', 'smallA'):
    for key, rec in P[sect].items():
        used = rec.get('status') == 'OK' if sect in ('lemmaA', 'lemmaA_odd', 'lemmaB') else rec.get('ok')
        if not used: continue
        r = res.get((sect, key))
        if r is None or r['status'] != 'CANON' or not r['same_outputs']:
            stat[sect + ' NOT REPRODUCED'] += 1
            if 'ok' in rec: rec['ok'] = False
            else: rec['status'] = 'NOT-REPRODUCED-BY-SSIM4'
            continue
        if r.get('mixed'): stat[sect + ' with mixed cycle limits'] += 1
        if sect == 'smallA':
            node = key.split(' ## ')[0]; par = int(key.split('par=')[1])
            fam = ' || FAM ' in node
            kk = K0 + int(node.split('park=')[1][0]) if fam else None
            b = bounds(r['constraints'])
            Mmin, Kmin = M0 + par + 2 * b[0], (kk + 2 * b[1]) if fam else None
            if Mmin != rec['Mmin'] or Kmin != rec['Kmin']:
                stat['smallA bounds changed'] += 1
                rec['Mmin'] = max(Mmin, rec['Mmin']); rec['Kmin'] = None if Kmin is None else max(Kmin, rec['Kmin'] or Kmin)
            rec['constraints'] = r['constraints']
        else:
            if r['constraints'] != rec.get('constraints'):
                stat[sect + ' constraints changed'] += 1
            rec['constraints'] = r['constraints']
        stat[sect + ' reproduced'] += 1
json.dump(P, open(D + 'proof4.json', 'w'), indent=1)
for k in sorted(stat): print('%-45s %d' % (k, stat[k]))
