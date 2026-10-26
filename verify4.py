"""Class-based exact verification of the inductive non-halting proof stored in proof2.json.

verify3 checks every domain state (node, r, parity of M) only at the worst case (smallest M, k).
That is not enough on its own: N1 usually depends on M, so for different M the lemma-A descent
lands in different residues mod P, uses different small-N lemmas, etc.

Here a state is a CLASS
    S = (node, r, M = c + a*tau + b*ups, k = c' + a'*tau + b'*ups or None),   tau, ups >= 0 integers,
and every check is done for the whole class:
  * every lemma constraint has nonnegative coefficients, and all slopes are nonnegative, so a
    constraint that holds at the base point (tau = ups = 0) holds on the whole class;
  * the class is split by residues (tau = i + q*tau') until N1 has slopes divisible by P, M and k
    have even slopes; then the descent lands in one residue r2 and M keeps its parity;
  * when the descent has a different shape at the base point than further out (N1 below the
    symbolic lemma-A threshold, small-M lemma A, M below MSTAR), the base point is peeled off
    (tau = 0 as its own class, the rest is shifted by one) and both parts are checked again;
  * symbolic lemma-A steps j = 0..js: the constraint is affine in (j, tau, ups) and nondecreasing
    along every unbounded edge of {0 <= j <= js(tau, ups)}, so checking j = 0 and j = js at the
    base point covers all steps of all class members;
  * the small lemma-A steps visit the same N values for all class members (fixed residue), with
    M and k nondecreasing, so their Mmin / Kmin bounds are checked at the base point.
A landing class is in the domain if M >= MSTAR on the whole class (base point) and k is in the
family domain; otherwise it is followed exactly (exceptional chain).
"""
import os, sys, json, re
from math import gcd
from collections import deque

D = os.path.dirname(os.path.abspath(__file__)) + '/'
PROOF = os.environ.get('BB6_PROOF', 'proof2.json')
P = json.load(open(D + PROOF))
MSTAR = int(sys.argv[1]) if __name__ == '__main__' and len(sys.argv) > 1 else 500
M0, K0, N0 = 1000, 1000, 300
nodes = P['nodes']
errs = []
stats = dict(classes=0, splits=0, peels=0, exceptional=0, smallM=0, maxdepth=0)
USED = None     # set to {} to record, per lemma, the most extreme parameter points it is used at


def use(sect, key, pt):
    """record pt (lemma variables v0, v1, v2) if it is the smallest so far in some coordinate"""
    if USED is None: return
    cur = USED.setdefault((sect, key), [None, None, None])
    for i in range(3):
        if cur[i] is None or (pt[i], sum(pt)) < (cur[i][i], sum(cur[i])): cur[i] = pt


class Split(Exception):
    """the class must be partitioned: ('res', var, q) or ('peel', var)."""


def aff_eval(coef, x, y):
    """coef = [c0, cx, cy]; x, y affine (c, a, b) -> affine"""
    return tuple(coef[0] * (i == 0) + coef[1] * x[i] + coef[2] * y[i] for i in range(3))


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
    """affine k-variable of the family lemmas ((k - K0 - park) / 2)"""
    if k is None or 'FAM' not in anode: return (0, 0, 0)
    pk = park_of(anode)
    if (k[0] - K0 - pk) % 2 or k[1] % 2 or k[2] % 2: raise ValueError('k parity')
    return ((k[0] - K0 - pk) // 2, k[1] // 2, k[2] // 2)


def lemmaB_for(t, r, par):
    ti = nodes[t]
    if 'partial_of' in ti and [r, par] not in ti.get('concrete_states', []):
        return ti['partial_of'], P['lemmaB'].get('%s ## r=%d par=%d' % (ti['partial_of'], r, par))
    return t, P['lemmaB'].get('%s ## r=%d par=%d' % (t, r, par))


def nz_var(v):
    """first variable (1 = tau, 2 = ups) with a nonzero slope in affine v"""
    return 1 if v[1] else 2


def descent(t, n, m, k, ctx):
    """lemma-A descent of the class (t, N = n, M = m, k) to the last canonical point.
    returns (r2, M2) or None (error recorded); raises Split."""
    ti = nodes.get(t)
    if not ti or 'P' not in ti: errs.append(('descent: unknown node', t[:70], ctx)); return None
    anode = ti.get('partial_of', t)
    Pp, dM, rl = ti['P'], ti['dM'], ti['r_low']
    if dM < 0 or dM % 2: errs.append(('dM not even/nonneg', t[:60])); return None
    if n[0] < rl: errs.append(('descent: N below r_low', t[:60], n, ctx)); return None
    if n[1] % Pp or n[2] % Pp: raise Split(('res', 1 if n[1] % Pp else 2, Pp // gcd(n[1] if n[1] % Pp else n[2], Pp)))
    if m[1] % 2 or m[2] % 2: raise Split(('res', 1 if m[1] % 2 else 2, 2))
    Nsmall = P['lemmaA'][anode]['Nmin']
    nconst = n[1] == 0 and n[2] == 0
    if not nconst and n[0] < Nsmall: raise Split(('peel', nz_var(n)))
    T = ((n[0] - rl) // Pp, n[1] // Pp, n[2] // Pp)
    if T == (0, 0, 0): return n[0], m
    par = m[0] % 2
    A = P['lemmaA'][anode] if par == 0 else P.get('lemmaA_odd', {}).get(anode)
    if not A or A.get('status') != 'OK': errs.append(('descent: no lemma A for parity', t[:60], par, ctx)); return None
    kv = kvar(anode, k)
    js = (n[0] - Nsmall) // Pp if n[0] >= Nsmall else -1
    if js >= 0:
        for j in sorted({0, js}):
            Nj = n[0] - j * Pp; Mj = m[0] + j * dM
            if cons_ok(A['constraints'], [Nj - N0, (Mj - M0 - par) // 2, kv[0]]):
                use('lemmaA' if par == 0 else 'lemmaA_odd', anode, (Nj - N0, (Mj - M0 - par) // 2, kv[0])); continue
            if j == 0:
                # first step with a small concrete M: dedicated lemma (N symbolic, M concrete)
                if m[1] or m[2]: raise Split(('peel', nz_var(m)))
                sm = P.get('lemmaA_smallM', {}).get('%s ## M=%d' % (anode, m[0]))
                if sm and sm['ok'] and cons_ok(sm['constraints'], [n[0] - N0, kv[0], 0]):
                    stats['smallM'] += 1
                    use('lemmaA_smallM', '%s ## M=%d' % (anode, m[0]), (n[0] - N0, kv[0], 0))
                    return descent(t, (n[0] - Pp,) + n[1:], (m[0] + dM,) + m[1:], k, ctx)
            errs.append(('descent: lemma A constraint', t[:60], Nj, Mj, ctx)); return None
    for j in range(js + 1, T[0]):
        Nj = n[0] - j * Pp; Mj = m[0] + j * dM
        s = P['smallA'].get('%s ## N=%d par=%d' % (anode, Nj, par))
        if not s or not s['ok']: errs.append(('descent: small lemma missing', t[:60], Nj, par, ctx)); return None
        if s['Mmin'] > Mj or (s.get('Kmin') is not None and k is not None and s['Kmin'] > k[0]):
            errs.append(('descent: small lemma bound', t[:60], Nj, Mj, ctx)); return None
        use('smallA', '%s ## N=%d par=%d' % (anode, Nj, par), ((Mj - M0 - par) // 2, kv[0], 0))
    r2 = n[0] - T[0] * Pp
    if not rl <= r2 < rl + Pp: errs.append(('descent: residue out of range', t[:60], r2)); return None
    return r2, (m[0] + T[0] * dM, m[1] + T[1] * dM, m[2] + T[2] * dM)


def split(S, how):
    t, r, M, k = S
    if how[0] == 'res':
        _, v, q = how
        sub = lambda a, i: None if a is None else tuple(
            (a[0] + a[v] * i) if j == 0 else (a[j] * q if j == v else a[j]) for j in range(3))
        return [(t, r, sub(M, i), sub(k, i)) for i in range(q)]
    _, v = how
    zero = lambda a: None if a is None else tuple(0 if j == v else a[j] for j in range(3))
    shift = lambda a: None if a is None else (a[0] + a[v],) + a[1:]
    return [(t, r, zero(M), zero(k)), (t, r, shift(M), shift(k))]


def process(S, ctx, depth=0, budget=None):
    """check the whole class S (a set of states at a last canonical point); returns nothing,
    records errors, enqueues reached nodes."""
    budget = budget if budget is not None else [400]
    stats['classes'] += 1; stats['maxdepth'] = max(stats['maxdepth'], depth)
    try:
        landing = step(S, ctx)
    except Split as e:
        budget[0] -= 1
        if budget[0] < 0: errs.append(('split budget exhausted', S[0][:60], S[1:], ctx)); return
        stats['splits' if e.args[0][0] == 'res' else 'peels'] += 1
        for S2 in split(S, e.args[0]): process(S2, ctx, depth, budget)
        return
    if landing is not None: land(landing, ctx, depth, budget)


def land(S2, ctx, depth, budget):
    t2, r2, M2, k2 = S2
    if M2[0] >= MSTAR:
        if t2 not in reach: q.append(t2)
        return
    if M2[1] or M2[2]:                                  # part of the class is below MSTAR: peel
        budget[0] -= 1
        if budget[0] < 0: errs.append(('peel budget exhausted (landing)', t2[:60], ctx)); return
        stats['peels'] += 1
        for S3 in split(S2, ('peel', nz_var(M2))): land(S3, ctx, depth, budget)
        return
    stats['exceptional'] += 1
    if depth >= 30: errs.append(('exceptional chain too long', t2[:60], ctx)); return
    process(S2, ctx + ('exc',), depth + 1, budget)


def step(S, ctx):
    """lemma B + descent for the class S; returns the landing class or None (error)."""
    t, r, M, k = S
    if any(v < 0 for v in M[1:]) or (k is not None and any(v < 0 for v in k[1:])):
        errs.append(('negative slope', t[:60], S[1:], ctx)); return None
    if M[1] % 2 or M[2] % 2: raise Split(('res', 1 if M[1] % 2 else 2, 2))
    if k is not None and (k[1] % 2 or k[2] % 2): raise Split(('res', 1 if k[1] % 2 else 2, 2))
    par = M[0] % 2
    src, B = lemmaB_for(t, r, par)
    if not B or B['status'] != 'OK' or B.get('crosscheck') is not True:
        errs.append(('no valid lemma B', t[:60], r, par, ctx)); return None
    x = ((M[0] - M0 - par) // 2, M[1] // 2, M[2] // 2)
    try:
        y = kvar(src, k)
    except ValueError:
        errs.append(('k parity mismatch', t[:60], k, ctx)); return None
    if not cons_ok(B['constraints'], [x[0], y[0], 0]): errs.append(('lemma B constraint', t[:60], r, M, k, ctx)); return None
    use('lemmaB', '%s ## r=%d par=%d' % (src, r, par), (x[0], y[0], 0))
    for c in (B['N1'], B['M1'], B['K1']):
        if c is not None and (c[1] < 0 or c[2] < 0): errs.append(('negative coefficient', t[:60], r, c)); return None
    n1, m1 = aff_eval(B['N1'], x, y), aff_eval(B['M1'], x, y)
    k1 = aff_eval(B['K1'], x, y) if B['K1'] is not None else None
    t2 = resolve(B['target']); t2i = nodes.get(t2, {})
    if 'P' not in t2i: errs.append(('unproven target', t2[:80], ctx)); return None
    if t2i.get('family'):
        if k1 is None: errs.append(('family target without k', t[:60], r, ctx)); return None
        if k1[1] % 2 or k1[2] % 2: raise Split(('res', 1 if k1[1] % 2 else 2, 2))
        if k1[0] % 2 != park_of(t2): errs.append(('family target k parity', t[:60], r, k1, ctx)); return None
        if k1[0] < t2i['K_fam']:
            if k1[1] or k1[2]: raise Split(('peel', nz_var(k1)))
            errs.append(('family target k below K_fam', t[:60], r, k1, ctx)); return None
        k2 = k1
    elif 'partial_of' in t2i:
        if k1 is None or k1 != (t2i['k'], 0, 0): errs.append(('partial target k mismatch', t[:60], r, k1, t2i['k'], ctx)); return None
        k2 = k1
    else:
        k2 = None
    d = descent(t2, n1, m1, k2, ctx)
    if d is None: return None
    return (t2, d[0], d[1], k2)


start = next(k for k in P['lemmaA'] if k.startswith('1 7 0 0* 4 3 0 0 0 0 0 9 | 8  || 3 / 0 1 / 0 / 6542ed25be'))
reach = set(); q = deque()


def domain_k(t):
    """k of the domain class of node t: family k = kw + 2*ups, partial exact k, else None"""
    ti = nodes[t]
    if ti.get('family'):
        return (ti['K_fam'] + ((park_of(t) - ti['K_fam']) % 2), 0, 2)
    if 'partial_of' in ti:
        return (ti['k'], 0, 0)
    return None


def main():
    q.append(start); nroots = 0
    while q:
        t = q.popleft()
        if t in reach: continue
        reach.add(t)
        ti = nodes.get(t)
        if not ti or 'P' not in ti: errs.append(('unproven node', t[:80])); continue
        for r in range(ti['r_low'], ti['r_low'] + ti['P']):
            for par in (0, 1):
                nroots += 1
                Mw = MSTAR + ((par - MSTAR) % 2)          # smallest M >= MSTAR with this parity
                process((t, r, (Mw, 2, 0), domain_k(t)), (t[:40], r, par))

    print('MSTAR %d: reachable nodes %d (families %d, partial %d); domain classes %d' % (
        MSTAR, len(reach), sum(1 for n in reach if nodes[n].get('family')),
        sum(1 for n in reach if 'partial_of' in nodes[n]), nroots))
    print('classes processed %(classes)d, residue splits %(splits)d, peels %(peels)d, exceptional steps %(exceptional)d, '
          'small-M lemma uses %(smallM)d, max exceptional depth %(maxdepth)d' % stats)
    print('errors %d' % len(errs))
    for e in errs[:30]: print('  ', e)

    # start: the configuration after 226258281 steps from the blank tape (checked by start_check.c)
    # is the start node with N = 224, M = 2045; its descent must land in the domain
    nerr = len(errs)
    d = descent(start, (224, 0, 0), (2045, 0, 0), None, ('start',))
    print('start (N=224, M=2045) descent ->', d, ' in domain:', d is not None and d[1][0] >= MSTAR and len(errs) == nerr)


if __name__ == '__main__':
    main()
