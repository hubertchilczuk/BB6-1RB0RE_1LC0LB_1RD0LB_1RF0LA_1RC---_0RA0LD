"""Closure of the domain: rocq/C/Close_<tag>_<par>.v for every Dom constructor, and rocq/C/Closure.v.

For a domain state (node t, parity par, r, h[, y]):  x = h - 250 (M = par + 500 + 2x), lemma B (rocq/B3) lands in
the target T with N1, h1[, y1] affine in x[, y]; with q = (N1 - 12) / P and rr = (N1 - 12) mod P of the descent
node, the descent (rocq/D, q applications of lemma A) ends in (12 + rr, h1 + D*q), a domain state again.
Numerical checks (minimal parameters, all coefficients nonnegative) are done here; Rocq checks everything again.
usage: genClose.py [constructor ...]
"""
import os, sys, json, re
import rocqgen as RG
import nodeform as NF
from genD import top_args

OUT = RG.ROOT + 'rocq/C/'
os.makedirs(OUT, exist_ok=True)
DOM = json.load(open(RG.ROOT + 'rocq/F/dom.json'))
NODES = NF.P['nodes']
HMIN, NB = 250, 12
M0P, K0P = 1000, 1000       # bases of the proof's lemma variables x' = (M - 1000 - par)/2, y' = (k - 1000 - park)/2


def family_of(key):
    ni = NODES.get(key, {})
    return ni.get('partial_of') or ni.get('covered_by')


def descent_node(T):
    """node whose lemma A / descent is used for a landing in T"""
    ni = NODES.get(T, {})
    if 'covered_by' in ni: return ni['covered_by']
    if 'partial_of' in ni: return ni['partial_of']
    return T


def domain_node(T):
    ni = NODES.get(T, {})
    return ni['covered_by'] if 'covered_by' in ni else T


def kd_of(fam, r, par):
    """lower bound of k of the family's lemma B (as in genB3)"""
    node = NF.Node(fam)
    kf = NODES[fam]['K_fam']; Kd = kf + ((node.kp - kf) % 2)
    for pk, pi in NODES.items():
        if pi.get('partial_of') == fam and [r, par] not in pi.get('concrete_states', []):
            Kd = min(Kd, pi['k'])
    return Kd


def lin(const, cx, cy):
    """nat expression const + cx*x + cy*y (const may be negative: written as a subtraction)"""
    terms = []
    if cx: terms.append('x' if cx == 1 else '%d * x' % cx)
    if cy: terms.append('y' if cy == 1 else '%d * y' % cy)
    s = ' + '.join(terms) or '0'
    if const > 0: return '(%s + %d)' % (s, const)
    if const < 0: return '(%s - %d)' % (s, -const)
    return '(%s)' % s


def case(c, info, r):
    """Rocq lemma for one case, or raise"""
    t = info['key']; par = info['par']; node = NF.Node(t); kind = info['kind']
    own = '%s ## r=%d par=%d' % (t, r, par)
    if own in NF.P['lemmaB']:
        bkey, S = own, t
    else:
        fam = NODES[t]['partial_of']; bkey = '%s ## r=%d par=%d' % (fam, r, par); S = fam
    B = NF.P['lemmaB'][bkey]
    Snode = NF.Node(S)
    bfile = 'B_%s_%s' % (NF.tagof(S), ('r%d_%d' % (r, par)))
    # lemma B parameters in terms of the domain parameters: x = h - 250; family source: yB = y - yd (or constant)
    yd = None
    if Snode.family_key:
        Kd = kd_of(S, r, par); yd = (Kd - Snode.kp) // 2
    # landing: proof variables x' = x - 250, y' = y - 500 (k = kp + 2y, kp = park)
    park = Snode.kp if Snode.fam else 0
    if kind == 'family':
        ycoef = True; yconst = None
    elif kind == 'kfixed':
        ycoef = False; yconst = info['yfix']
    else:
        ycoef = False; yconst = None
    def ev(cf):    # affine in (x, y): returns (const, cx, cy) with y the domain y (k = kp + 2y)
        if cf is None: return None
        c0, c1, c2 = cf
        const = c0 - 250 * c1; cy = 0
        if Snode.family_key:
            # y' = (k - 1000 - park)/2 = y - 500 (domain y of S, or the fixed y of a partial node)
            if ycoef: const -= 500 * c2; cy = c2
            else: const += c2 * (yconst - 500)
        return (const, c1, cy)
    N1, M1, K1 = ev(B['N1']), ev(B['M1']), ev(B['K1'])
    T = B['target']; TA = descent_node(T); TD = domain_node(T)
    Tn, TAn, TDn = NF.Node(T), NF.Node(TA), NF.Node(TD)
    par1 = M1[0] % 2
    h1 = ((M1[0] - par1) // 2, M1[1] // 2, M1[2] // 2)
    y1 = None
    if TAn.fam:
        y1 = ((K1[0] - TAn.kp) // 2, K1[1] // 2, K1[2] // 2) if K1 is not None else (TAn.kfix - TAn.kp) // 2
        if isinstance(y1, int): y1 = (y1, 0, 0)
    PT, D = NODES[TA]['P'], NODES[TA]['dM'] // 2
    # numerical checks at the minimal parameters (all slopes nonnegative)
    ymin = info.get('yf', 0) if ycoef else 0
    at0 = lambda a: a[0] + a[2] * ymin
    for a in (N1, h1) + ((y1,) if y1 else ()):
        if a[1] < 0 or a[2] < 0: raise ValueError('negative slope')
    if at0(N1) < NB: raise ValueError('N1 below 12')
    q0 = (at0(N1) - NB) // PT
    if at0(h1) + D * q0 < HMIN: raise ValueError('exceptional landing (M < 500)')
    dinfo = DOM['dom_%s_%d' % (TDn.tag, par1)]
    if dinfo['kind'] == 'family' and at0(y1) < dinfo['yf']: raise ValueError('target k below K_fam')
    if dinfo['kind'] == 'kfixed' and (y1[1] or y1[2] or y1[0] != dinfo['yfix']): raise ValueError('target k mismatch')
    # parse the lemma B theorem
    th = next(l for l in open(RG.ROOT + 'rocq/B3/%s.v' % bfile) if l.startswith('Theorem lemmaB'))
    _, sides = th.split(':', 1)
    lhs, rhs = sides.rstrip().rstrip('.').split('-->+')
    offS, offT = lhs.split()[0], rhs.split()[0]
    xs = '(h - %d)' % HMIN
    ys = None
    if Snode.family_key:
        ys = '(y - %d)' % yd if ycoef else '%d' % (yconst - yd)
    sub = lambda a: re.sub(r'\b([xy])\b', lambda m: xs if m.group(1) == 'x' else ys, a)
    la = ' '.join('(%s)' % sub(a) for a in top_args(lhs)); ra = ' '.join('(%s)' % sub(a) for a in top_args(rhs))
    Fsrc = 'F_%s_%d r h%s' % (node.tag, par, ' y' if kind == 'family' else (' %d' % yconst if kind == 'kfixed' else ''))
    Fsrc = Fsrc.replace(' r ', ' %d ' % r)
    N1e = lin(N1[0], N1[1], N1[2]).replace('x', '(h - 250)')
    h1e = lin(*h1).replace('x', '(h - 250)')
    y1e = lin(*y1).replace('x', '(h - 250)') if y1 else None
    yarg = (' ' + y1e) if TAn.fam else ''
    land = 'F_%s_%d (12 + rr + %d * q) %s%s' % (TAn.tag, par1, PT, h1e, yarg)
    fin_A = 'F_%s_%d (12 + rr) (%s + %d * q)%s' % (TAn.tag, par1, h1e, D, yarg)
    fin_D = 'F_%s_%d (12 + rr) (%s + %d * q)%s' % (TDn.tag, par1, h1e, D, yarg if TDn.fam else '')
    ctor = 'dom_%s_%d' % (TDn.tag, par1)
    dargs = '(12 + rr) (%s + %d * q)%s' % (h1e, D, yarg if dinfo['kind'] == 'family' else '')
    hyps = '%d <= h%s' % (HMIN, ' -> %d <= y' % info['yf'] if kind == 'family' else '')
    alias = lambda a, b, p: '' if a == b else 'rewrite (alias_%s_%d); ' % (NF.tagof(a), p)
    v = ['Lemma case_%s_r%d h%s : %s -> exists c, Dom c /\\ %s -->+ c.' % (c, r, ' y' if kind == 'family' else '', hyps, Fsrc),
         'Proof.',
         '  intros Hh%s.' % (' Hy' if kind == 'family' else ''),
         '  pose proof (Nat.div_mod (%s - 12) %d ltac:(lia)) as Hd.' % (N1e, PT),
         '  pose proof (Nat.mod_upper_bound (%s - 12) %d ltac:(lia)) as Hr.' % (N1e, PT),
         '  pose proof (Nat.div_le_lower_bound (%s - 12) %d %d ltac:(lia) ltac:(lia)) as Hq.' % (N1e, PT, q0),
         '  set (q := (%s - 12) / %d) in *. set (rr := (%s - 12) mod %d) in *.' % (N1e, PT, N1e, PT),
         '  exists (%s). split.' % fin_D,
         '  - %sapply (%s %s); lia.' % ('' if TD == TA else '', ctor, dargs) if TD == TA else
         '  - unfold F_%s_%d. apply (%s %s); lia.' % (TDn.tag, par1, ctor, dargs),
         '  - eapply progress_evstep_trans.',
         '    + eapply (%s.last_eq _ (%s %s) (%s %s)).' % (bfile, offS, la, offT, ra),
         '      * unfold F_%s_%d. %sf_equal; lia.' % (node.tag, par, alias(t, S, par)),
         '      * apply (%s.lemmaB %s%s).' % (bfile, xs, (' ' + ys) if ys else ''),
         '      * unfold F_%s_%d. %sf_equal; lia.' % (TAn.tag, par1, alias(T, TA, par1)),
         '    + %s' % ('apply (D_%s_%d.F_%s_%d_descent q (12 + rr) %s%s); lia.' % (TAn.tag, par1, TAn.tag, par1, h1e, yarg)
                       if TD == TA else
                       'replace (%s) with (%s) by (unfold F_%s_%d, F_%s_%d; rewrite (alias_%s_%d); f_equal; lia). apply (D_%s_%d.F_%s_%d_descent q (12 + rr) %s%s); lia.'
                       % (fin_D, fin_A, TDn.tag, par1, TAn.tag, par1, TDn.tag, par1, TAn.tag, par1, TAn.tag, par1, h1e, yarg)),
         'Qed.', '']
    return v, bfile, 'D_%s_%d' % (TAn.tag, par1)


def node_file(c, info):
    node = NF.Node(info['key']); par = info['par']; Pp = info['P']
    body, reqs, fails = [], set(), []
    for r in range(NB, NB + Pp):
        try:
            v, b, d = case(c, info, r); body += v; reqs |= {b, d}
        except Exception as e:
            fails.append((r, repr(e)))
    if fails: return None, fails
    kind = info['kind']
    yv = ' y' if kind == 'family' else ''
    Fn = 'F_%s_%d r h%s' % (node.tag, par, yv if kind == 'family' else (' %d' % info['yfix'] if kind == 'kfixed' else ''))
    disj = ' \\/ '.join('r = %d' % r for r in range(NB, NB + Pp))
    pat = ' | '.join('->' for _ in range(Pp))
    head = ['(* generated by rocq/genClose.py: closure of %s *)' % c, 'From BusyCoq Require Import Individual62.',
            'From BB6N Require Import Nodes.', 'From BB6F Require Import F Dom.', 'Require Import Lia.']
    head += ['Require %s.' % m for m in sorted(reqs)]
    head += ['Open Scope list.', '', 'Definition tm := %s.tm.' % sorted(reqs)[0],
             """Notation "c -->+ c'" := (c -[ tm ]->+ c') (at level 40).""", '']
    tail = ['Lemma close_%s r h%s : 12 <= r < %d -> %d <= h%s -> exists c, Dom c /\\ %s -->+ c.' % (
                c, yv, NB + Pp, HMIN, ' -> %d <= y' % info['yf'] if kind == 'family' else '', Fn),
            'Proof.',
            '  intros Hr Hh%s.' % (' Hy' if kind == 'family' else ''),
            '  assert (%s) as E by lia.' % disj,
            '  repeat destruct E as [E | E]; subst r; [%s].' % ' | '.join(
                'apply case_%s_r%d; assumption' % (c, r) for r in range(NB, NB + Pp)),
            'Qed.']
    return head + body + tail, []


if __name__ == '__main__':
    names = sys.argv[1:] or sorted(DOM)
    bad = 0
    for c in names:
        text, fails = node_file(c, DOM[c])
        if fails:
            bad += 1
            print('FAIL', c, len(fails), fails[:2])
            continue
        open(OUT + 'Close_%s.v' % c[4:], 'w').write('\n'.join(text) + '\n')
    print('constructors %d, failed %d' % (len(names), bad))
