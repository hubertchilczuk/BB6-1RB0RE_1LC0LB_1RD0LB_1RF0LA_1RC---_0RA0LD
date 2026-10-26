import os
"""Exact verification of the inductive non-halting proof stored in proof2.json.

Induction domain (per node, at LAST canonical points):
    N = r in [r_low, r_low+P),  M >= MSTAR,  and for families k >= K_fam, k = park (mod 2);
    for a partial node: its exact k.
For every reachable node and every (r, parity of M) we check:
  * lemma B applies: all its recorded constraints hold at the worst case (smallest M, smallest k);
  * its landing configuration (first canonical point of the target node) at the worst case;
  * the descent of the target by lemma A down to its last canonical point: every lemma-A step is justified
    (symbolic lemma A of the right parity of M with constraints checked exactly; or a small-N lemma),
  * the final state is again in the domain (or an explicitly followed exceptional chain ends in it).
Monotonicity: all coefficients of N1, M1, K1 are >= 0 and all constraints have nonnegative coefficients,
so the worst case (smallest parameters) implies all larger parameters.
"""
import json, sys, re
from collections import deque

D = os.path.dirname(os.path.abspath(__file__)) + '/'
P = json.load(open(D + 'proof2.json'))
MSTAR = int(sys.argv[1]) if len(sys.argv) > 1 else 500
M0, K0, N0 = 1000, 1000, 300
nodes = P['nodes']
errs = []
USED_SMALLM = []


def cons_ok(cons, vals):
    for t in cons.split():
        m = re.match(r'(-?\d+)([+-]\d+)v0([+-]\d+)v1([+-]\d+)v2>=0', t)
        if not m: errs.append(('unparsed constraint', t)); return False
        c, a, b, e = map(int, m.groups())
        if min(a, b, e) < 0: errs.append(('negative constraint coefficient', t)); return False
        if c + a * vals[0] + b * vals[1] + e * vals[2] < 0: return False
    return True


def resolve(t):
    return nodes.get(t, {}).get('covered_by', t)


def park_of(key):
    return int(key.split('park=')[1][0]) if 'park=' in key else 0


def kvar(anode, k):
    """value of the k-variable of family lemmas for an actual k"""
    if k is None or 'FAM' not in anode: return 0
    return (k - K0 - park_of(anode)) // 2


def descent(t, N, M, k, ctx):
    """apply lemma A of node t from (N, M) down to the last canonical point. returns (r, M_r) or None."""
    ti = nodes.get(t)
    if not ti or 'P' not in ti: errs.append(('descent: unknown node', t[:70], ctx)); return None
    anode = ti.get('partial_of', t)
    Pp, dM, rl = ti['P'], ti['dM'], ti['r_low']
    if N < rl: errs.append(('descent: N below r_low', t[:60], N, ctx)); return None
    T = (N - rl) // Pp
    if T == 0: return N, M
    par = M % 2
    A = P['lemmaA'][anode] if par == 0 else P.get('lemmaA_odd', {}).get(anode)
    if not A or A.get('status') not in ('OK',): errs.append(('descent: no lemma A for parity', t[:60], par, ctx)); return None
    Nsmall = P['lemmaA'][anode]['Nmin']            # small-N lemmas exist for N in [P, Nsmall)
    kv = kvar(anode, k)
    # symbolic steps: N_j = N - j*P >= Nsmall, j = 0..js
    js = (N - Nsmall) // Pp if N >= Nsmall else -1
    for j in sorted({0, max(0, js)}) if js >= 0 else []:
        Nj = N - j * Pp; Mj = M + j * dM
        if not cons_ok(A['constraints'], [Nj - N0, (Mj - M0 - par) // 2, kv]):
            # first step with a small concrete M: dedicated lemma (N symbolic, M concrete)
            sm = P.get('lemmaA_smallM', {}).get('%s ## M=%d' % (anode, M))
            if j == 0 and sm and sm['ok'] and cons_ok(sm['constraints'], [N - N0, kv, 0]) and ctx[-1] != 'Mvar':
                USED_SMALLM.append((anode[:50], M, N))
                return descent(t, N - Pp, M + dM, k, ctx)
            errs.append(('descent: lemma A constraint', t[:60], Nj, Mj, ctx)); return None
    # small steps
    for j in range(js + 1, T):
        Nj = N - j * Pp; Mj = M + j * dM
        s = P['smallA'].get('%s ## N=%d par=%d' % (anode, Nj, par))
        if not s or not s['ok']: errs.append(('descent: small lemma missing', t[:60], Nj, par, ctx)); return None
        # small lemma constraints: recorded only as bounds Mmin/Kmin
        if s['Mmin'] > Mj or (s.get('Kmin') is not None and k is not None and s['Kmin'] > k):
            errs.append(('descent: small lemma bound', t[:60], Nj, Mj, ctx)); return None
    return N - T * Pp, M + T * dM


def lemmaB_for(t, r, par, k):
    ti = nodes[t]
    if 'partial_of' in ti and [r, par] not in ti.get('concrete_states', []):
        return ti['partial_of'], P['lemmaB'].get('%s ## r=%d par=%d' % (ti['partial_of'], r, par))
    return t, P['lemmaB'].get('%s ## r=%d par=%d' % (t, r, par))


def step(t, r, M, k, ctx):
    """from last canonical point (t, r, M, k) apply lemma B and the descent. returns (t2, r2, M2, k2) or None."""
    src, B = lemmaB_for(t, r, M % 2, k)
    if not B or B['status'] != 'OK' or B.get('crosscheck') is not True:
        errs.append(('no valid lemma B', t[:60], r, M % 2, ctx)); return None
    par = M % 2
    x = (M - M0 - par) // 2; y = kvar(src, k)
    if not cons_ok(B['constraints'], [x, y, 0]): errs.append(('lemma B constraint', t[:60], r, M, k, ctx)); return None
    for c in (B['N1'], B['M1'], B['K1']):
        if c is not None and (c[1] < 0 or c[2] < 0): errs.append(('negative coefficient', t[:60], r, c)); return None
    ev = lambda c: None if c is None else c[0] + c[1] * x + c[2] * y
    n1, m1, k1 = ev(B['N1']), ev(B['M1']), ev(B['K1'])
    t2 = resolve(B['target']); t2i = nodes.get(t2, {})
    if t2i.get('family'):
        if k1 is None or k1 < t2i['K_fam'] or k1 % 2 != park_of(t2): errs.append(('family target k', t[:60], r, k1, ctx)); return None
    elif 'partial_of' in t2i:
        k1 = t2i['k']
    d = descent(t2, n1, m1, k1, ctx + (('Mvar',) if B['M1'][1] or B['M1'][2] else ('Mconst',)))
    if d is None: return None
    return t2, d[0], d[1], k1


start = next(k for k in P['lemmaA'] if k.startswith('1 7 0 0* 4 3 0 0 0 0 0 9 | 8  || 3 / 0 1 / 0 / 6542ed25be'))
reach = set(); q = deque([start]); nstates = 0; nexc = 0
while q:
    t = q.popleft()
    if t in reach: continue
    reach.add(t)
    ti = nodes.get(t)
    if not ti or 'P' not in ti: errs.append(('unproven node', t[:80])); continue
    fam = ti.get('family'); partial = 'partial_of' in ti
    kmin = ti['K_fam'] if fam else (ti['k'] if partial else None)
    for r in range(ti['r_low'], ti['r_low'] + ti['P']):
        for par in (0, 1):
            nstates += 1
            Mw = MSTAR + ((par - MSTAR) % 2)          # smallest M >= MSTAR with this parity
            kw = kmin
            if fam and kw % 2 != park_of(t): kw += 1
            res = step(t, r, Mw, kw, (t[:40], r, par))
            if res is None: continue
            t2, r2, M2, k2 = res
            q.append(t2)
            chain = 0
            while M2 < MSTAR:                          # exceptional: follow exactly
                nexc += 1; chain += 1
                if chain > 30: errs.append(('exceptional chain too long', t[:60], r)); break
                res = step(t2, r2, M2, k2, ('exc', t[:40], r, par))
                if res is None: break
                t2, r2, M2, k2 = res; q.append(t2)

print('reachable nodes %d (families %d, partial %d); states %d; exceptional steps %d; errors %d' % (
    len(reach), sum(1 for n in reach if nodes.get(n, {}).get('family')),
    sum(1 for n in reach if 'partial_of' in nodes.get(n, {})), nstates, nexc, len(errs)))
for e in errs[:30]: print('  ', e)
# start configuration: C0 = (start, N=224, M=2045) at step 226258281; descent to the last canonical point
d = descent(start, 224, 2045, None, 'start')
print('small-M first steps used:', len(USED_SMALLM), sorted(set(USED_SMALLM))[:6])
print('start descent ->', d, ' in domain:', d is not None and d[1] >= MSTAR)
