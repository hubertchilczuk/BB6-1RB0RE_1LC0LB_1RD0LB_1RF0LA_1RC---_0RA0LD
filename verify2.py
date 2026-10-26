import os
"""Verify closure of the symbolic proof in proof2.json.

Domain of a node:
  concrete C : canonical configurations of C with N >= r_low(C), M >= MSTAR
  family F   : canonical configurations of F with N >= r_low(F), M >= MSTAR, k >= K_fam(F), k = park (mod 2)
Claim checked here: every configuration in the domain of a reachable node reaches (by the recorded lemmas)
a configuration in the domain of a reachable node.  Together with the start configuration being in the
domain of the start node, this gives non-halting (each lemma is a finite, halt-free TM computation).
"""
import json, sys
from collections import deque

D = os.path.dirname(os.path.abspath(__file__)) + '/'
P = json.load(open(D + 'proof2.json'))
MSTAR = int(sys.argv[1]) if len(sys.argv) > 1 else 3000
M0, K0 = 1000, 1000
nodes = P['nodes']
start = next(k for k in P['lemmaA'] if k.startswith('1 7 0 0* 4 3 0 0 0 0 0 9 | 8  || 3 / 0 1 / 0 / 6542ed25be'))
errs = []; reach = set(); q = deque([start]); nB = 0; exceptional = []


def resolve(t):
    """follow 'covered_by' to the family node"""
    n = nodes.get(t, {})
    return n.get('covered_by', t)


while q:
    nd = q.popleft()
    if nd in reach: continue
    reach.add(nd)
    info = nodes.get(nd)
    partial = info is not None and 'partial_of' in info
    anode = info['partial_of'] if partial else nd          # node whose lemma A applies
    A = P['lemmaA'].get(anode)
    if not info or 'P' not in info or not A or A['status'] != 'OK':
        errs.append(('node not proven', nd[:100])); continue
    fam = info['family'] or partial; Pp, dM, rl = info['P'], info['dM'], info['r_low']
    # KF: the k-bound of the domain (family: K_fam; partial node: its exact k)
    KF = info['k'] if partial else (info.get('K_fam') if fam else None)
    if A['Mmin'] > MSTAR: errs.append(('A Mmin', nd[:80], A['Mmin']))
    if fam and A['Kmin'] > KF: errs.append(('A Kmin', nd[:80]))
    for N in range(rl + Pp, A['Nmin']):
        for par in (0, 1):
            s = P['smallA'].get('%s ## N=%d par=%d' % (anode, N, par))
            if not s or not s['ok']: errs.append(('smallA', nd[:80], N, par)); continue
            if s['Mmin'] > MSTAR or (fam and s['Kmin'] > KF): errs.append(('smallA bounds', nd[:80], N))
    parks = [int(anode.split('park=')[1][0])] if fam else [0]
    conc = set(tuple(x) for x in info.get('concrete_states', [])) if partial else None
    for r in range(rl, rl + Pp):
        for par in (0, 1):
            nB += 1
            if partial and (r, par) not in conc:
                B = P['lemmaB'].get('%s ## r=%d par=%d' % (anode, r, par))   # family lemma, valid since k >= its Kmin
            elif partial:
                B = P['lemmaB'].get('%s ## r=%d par=%d' % (nd, r, par))
                if B and B['status'] == 'OK':
                    # concrete lemma for this exact k: evaluate with y = 0 semantics
                    B = dict(B); B['Kmin'] = None
            else:
                B = P['lemmaB'].get('%s ## r=%d par=%d' % (nd, r, par))
            if not B or B['status'] != 'OK' or B.get('crosscheck') is not True:
                errs.append(('B', nd[:80], r, par, B and B['status'])); continue
            if B['Mmin'] > MSTAR or (fam and B.get('Kmin') is not None and B['Kmin'] > KF): errs.append(('B bounds', nd[:80], r, par, B['Mmin'], B.get('Kmin')))
            x = -(-(MSTAR - M0 - par) // 2)                  # smallest x with M >= MSTAR
            if fam and B.get('Kmin') is not None:
                y = -(-(KF - K0 - parks[0]) // 2)            # smallest y with k >= KF (exact k for partial nodes)
            else:
                y = 0
            def val(c):
                if c is None: return None
                if c[1] < 0 or c[2] < 0: errs.append(('negative coefficient', nd[:80], r, par, c))
                return c[0] + c[1] * x + c[2] * y
            n1, m1, k1 = val(B['N1']), val(B['M1']), val(B['K1'])
            t = resolve(B['target']); q.append(t)
            ti = nodes.get(t)
            if not ti or 'P' not in ti: continue  # reported when t is processed
            if n1 < ti['r_low']: errs.append(('N1 < r_low', nd[:80], r, par, n1))
            At2 = P['lemmaA'].get(ti.get('partial_of', t))
            if (n1 - ti['r_low']) // ti['P'] > 0 and At2 and m1 < At2['Mmin']:
                errs.append(('M1 below lemma-A threshold of target', nd[:60], r, par, m1, At2['Mmin']))
            mlast = m1 + ti['dM'] * max(0, (n1 - ti['r_low']) // ti['P'])
            if mlast < MSTAR:
                # landing below the domain: only legitimate if N1 and M1 do not depend on x (else the
                # worst case is exact); then follow the concrete chain explicitly
                if B['N1'][1] == 0 and B['M1'][1] == 0:
                    exceptional.append((t, n1, m1, B['K1'], (x, y), (nd[:60], r, par)))
                else:
                    errs.append(('M below MSTAR', nd[:60], r, par, n1, m1, mlast))
            if ti['family']:
                if k1 is None: errs.append(('family target without k', nd[:80], r, par)); continue
                if k1 < ti['K_fam']: errs.append(('k below K_fam', nd[:60], r, par, k1, ti['K_fam']))
                c = B['K1']
                if (c[1] % 2) or (c[2] % 2) or (c[0] % 2 != int(t.split('park=')[1][0])):
                    errs.append(('k parity', nd[:60], r, par, c))

def follow(t, n, m, kinfo, depth, path):
    """explicitly follow a concrete (N, M) state of node t (k: lower bound from kinfo) until it is in the domain."""
    if depth > 40: errs.append(('exceptional chain too long', path)); return
    t = resolve(t); ti = nodes.get(t); A = P['lemmaA'].get(ti.get('partial_of', t)) if ti else None
    if not ti or 'P' not in ti or not A: errs.append(('exceptional: node missing', t[:60])); return
    Pp, dM, rl = ti['P'], ti['dM'], ti['r_low']
    if n < rl: errs.append(('exceptional: N below r_low', t[:60], n)); return
    steps = (n - rl) // Pp; r = n - steps * Pp; M = m + steps * dM
    if steps > 0 and A['Mmin'] > m: errs.append(('exceptional: lemma A M', t[:60], m, A['Mmin'])); return
    par = M % 2
    partial = 'partial_of' in ti
    conc = set(tuple(z) for z in ti.get('concrete_states', [])) if partial else set()
    src = ti['partial_of'] if (partial and (r, par) not in conc) else t
    B = P['lemmaB'].get('%s ## r=%d par=%d' % (src, r, par))
    if not B or B['status'] != 'OK': errs.append(('exceptional: no lemma B', t[:60], r, par)); return
    if B['Mmin'] > M: errs.append(('exceptional: lemma B needs M', t[:60], r, par, M, B['Mmin'])); return
    xx = (M - M0 - par) // 2
    fam = ti['family'] or partial
    if fam and B.get('Kmin') is not None:
        kb = ti['k'] if partial else ti['K_fam']
        yy = -(-(kb - K0 - int(src.split('park=')[1][0])) // 2) if 'park=' in src else 0
    else:
        yy = 0
    n2 = B['N1'][0] + B['N1'][1] * xx + B['N1'][2] * yy
    m2 = B['M1'][0] + B['M1'][1] * xx + B['M1'][2] * yy
    t2 = resolve(B['target']); t2i = nodes.get(t2, {})
    print('   exceptional step: %s N=%d M=%d -> r=%d M\'=%d -> %s N1=%d M1=%d' % (t[:50], n, m, r, M, t2[:50], n2, m2))
    if t2i.get('family'):
        c = B['K1']
        if c is None or c[1] < 0 or c[2] < 0: errs.append(('exceptional: bad K1', t[:60])); return
        k2 = c[0] + c[1] * xx + c[2] * yy
        if k2 < t2i['K_fam'] or (c[1] % 2) or (c[2] % 2) or c[0] % 2 != int(t2.split('park=')[1][0]):
            errs.append(('exceptional: k bound/parity', t[:60], k2)); return
    m2last = m2 + t2i.get('dM', 0) * max(0, (n2 - t2i.get('r_low', 0)) // max(1, t2i.get('P', 1)))
    A2 = P['lemmaA'].get(t2i.get('partial_of', t2), {})
    if (n2 - t2i.get('r_low', 0)) // max(1, t2i.get('P', 1)) > 0 and m2 < A2.get('Mmin', 10 ** 9):
        errs.append(('exceptional: M1 below target lemma A', t2[:60], m2)); return
    if m2last >= MSTAR and n2 >= t2i.get('r_low', 0):
        return
    follow(t2, n2, m2, B['K1'], depth + 1, path + [(t2[:40], n2, m2)])


for (t, n1, m1, kinfo, xy, origin) in exceptional:
    follow(t, n1, m1, kinfo, 0, [origin])
print('exceptional landings followed explicitly:', len(exceptional))

print('reachable nodes: %d (families %d), lemma-B states: %d, errors: %d' % (
    len(reach), sum(1 for n in reach if nodes.get(n, {}).get('family')), nB, len(errs)))
for e in errs[:40]: print('  ', e)
