import os
"""Check closure and induction conditions of the symbolic proof stored in proof.json.

Induction claim: for every reachable context C and every canonical configuration of C with
N >= r_low(C) and M >= MSTAR, the machine reaches (without halting) a canonical configuration of some
reachable context C' with N' >= r_low(C') and M' >= MSTAR.
"""
import json, sys, re
from collections import deque

D = os.path.dirname(os.path.abspath(__file__)) + '/'
P = json.load(open(D + 'proof.json'))
MSTAR = int(sys.argv[1]) if len(sys.argv) > 1 else 3000
M0 = 1000
START = None
for k in P['lemmaA']:
    if k.startswith('1 7 0 0* 4 3 0 0 0 0 0 9 | 8  || 3 / 0 1 / 0 / 6542ed25be'):
        START = k
assert START, 'start context missing'

errors = []
reach = set(); q = deque([START])
nB = 0
while q:
    ck = q.popleft()
    if ck in reach: continue
    reach.add(ck)
    A = P['lemmaA'].get(ck)
    if not A or A.get('status') != 'CANON' or not A.get('linear'):
        errors.append(('lemmaA', ck[:90], A and A.get('status'))); continue
    ctx = P['contexts'].get(ck, {})
    if 'r_low' not in ctx:
        errors.append(('no r_low', ck[:90])); continue
    Pp, dM, rl = A['P'], A['dM'], ctx['r_low']
    if A['Mmin'] > MSTAR: errors.append(('lemmaA Mmin', ck[:60], A['Mmin']))
    # small-N checks needed for N in [rl+P, Nmin)
    for N in range(rl + Pp, A['Nmin']):
        for par in (0, 1):
            s = P.get('lemmaAsmall', {}).get('%s ## N=%d par=%d' % (ck, N, par))
            if not s or not s['ok']: errors.append(('smallA', ck[:60], N, par))
            elif s['Mmin'] is not None and s['Mmin'] > MSTAR: errors.append(('smallA Mmin', ck[:60], N, s['Mmin']))
    for r in range(rl, rl + Pp):
        for par in (0, 1):
            key = '%s ## r=%d par=%d' % (ck, r, par)
            B = P['lemmaB'].get(key)
            nB += 1
            if not B or B['status'] != 'CANON' or not B.get('linear') or B.get('crosscheck') is not True:
                errors.append(('lemmaB', ck[:60], r, par, B and B.get('status'), B and B.get('crosscheck'))); continue
            if B['Mmin'] > MSTAR: errors.append(('lemmaB Mmin', ck[:60], r, par, B['Mmin']))
            t = B['target']
            q.append(t)
            # growth: worst case M = MSTAR (or MSTAR+1 for parity): x = (M - M0 - par)/2
            x = (MSTAR + (MSTAR - par) % 2 - M0 - par) // 2
            n1 = B['N1'][0] + B['N1'][1] * x
            m1 = B['M1'][0] + B['M1'][1] * x
            if B['N1'][1] < 0 or B['M1'][1] < 0: errors.append(('negative slope', ck[:60], r, par))
            At = P['lemmaA'].get(t); ct = P['contexts'].get(t, {})
            if not At or 'P' not in At or 'r_low' not in ct:
                continue  # reported when target processed
            if n1 < ct['r_low']: errors.append(('N1 below r_low', ck[:60], r, par, n1))
            steps = max(0, (n1 - ct['r_low']) // At['P'])
            mlast = m1 + At['dM'] * steps
            if mlast < MSTAR: errors.append(('M drops below MSTAR', ck[:60], r, par, n1, m1, mlast))

print('reachable contexts:', len(reach), ' lemma B states:', nB, ' errors:', len(errors))
for e in errors[:40]: print('  ', e)
