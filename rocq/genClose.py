"""Closure of the domain: rocq/C/Close_<ctor>.v for every Dom constructor.

Domain state (node t, parity par, N = r, M = par + 2h[, k = kp + 2y]), x = h - 250 (M = par + 500 + 2x):
  1. F_t r h [y] = start of lemma B (rocq/B3; partial nodes outside their concrete states: the family's record,
     through the alias off_t = off_family),
  2. lemma B lands in the target T at N1, h1[, y1] (affine in x[, y]),
  3. with q = (N1 - 12) / P, rr = (N1 - 12) mod P of the descent node TA, the descent (q lemma-A steps) ends in
     F_TA (12 + rr) (h1 + D q) [y1],
  4. which is the domain state of TD (= T, or the family of a covered T; partial T through the alias), or one of the
     registered exceptional states (rocq/F/exc.json: constant r and h below the domain, k free).
Exceptional states (family, r, h, k = kp + 2y, y >= ymin) get their own lemma B with the fixed M (rocq/B3/BX_*.v)
and the same treatment (Close_x_*.v).
Numerical checks (minimal parameters, nonnegative slopes) are done here; Rocq checks everything again.
usage: genClose.py [--dry] [constructor ...]
"""
import os, sys, json, re
import rocqgen as RG
import nodeform as NF
from genD import top_args

OUT = RG.ROOT + 'rocq/C/'
os.makedirs(OUT, exist_ok=True)
DOM = json.load(open(RG.ROOT + 'rocq/F/dom.json'))
EXCF = RG.ROOT + 'rocq/F/exc.json'
EXC = {('%s|%d|%d|%d' % (e['key'], e['par'], e['r'], e['h'])): e for e in (json.load(open(EXCF)) if os.path.exists(EXCF) else [])}
NODES = NF.P['nodes']
HMIN, NB = 250, 12
DRY = False


class Exceptional(ValueError):
    pass


def descent_node(T):
    ni = NODES.get(T, {})
    return ni.get('covered_by') or ni.get('partial_of') or T


def domain_node(T):
    return NODES.get(T, {}).get('covered_by', T)


def kd_of(fam, r, par):
    """lower bound of k of the family's lemma B (as in genB3)"""
    node = NF.Node(fam)
    kf = NODES[fam]['K_fam']; Kd = kf + ((node.kp - kf) % 2)
    for pk, pi in NODES.items():
        if pi.get('partial_of') == fam and [r, par] not in pi.get('concrete_states', []):
            Kd = min(Kd, pi['k'])
    return Kd


def lin(const, cx, cy, xs='x', ys='y'):
    """nat expression const + cx*X + cy*Y (const may be negative: written as a subtraction)"""
    terms = []
    if cx: terms.append(xs if cx == 1 else '%d * %s' % (cx, xs))
    if cy: terms.append(ys if cy == 1 else '%d * %s' % (cy, ys))
    s = ' + '.join(terms) or '0'
    if const > 0: return '(%s + %d)' % (s, const)
    if const < 0: return '(%s - %d)' % (s, -const)
    return '(%s)' % s


def case(name, t, par, r, kind, yinfo, exc_src=None):
    """Rocq lemma for one domain state class.
    kind: 'family' (y >= yinfo), 'kfixed' (y = yinfo), 'plain'; exc_src: exceptional state record (h fixed)."""
    node = NF.Node(t)
    own = '%s ## r=%d par=%d' % (t, r, par)
    if own in NF.P['lemmaB']:
        bkey, S = own, t
    else:
        S = NODES[t]['partial_of']; bkey = '%s ## r=%d par=%d' % (S, r, par)
    B = NF.P['lemmaB'][bkey]
    Snode = NF.Node(S)
    yd = None
    if exc_src:
        bfile = exc_src['bfile']; yd = exc_src['ymin']
    else:
        bfile = 'B_%s_r%d_%d' % (NF.tagof(S), r, par)
        if Snode.family_key:
            yd = (kd_of(S, r, par) - Snode.kp) // 2
    # proof variables: x' = (M - 1000 - par)/2, y' = (k - 1000 - park)/2 = y - 500 (k = kp + 2y)
    if exc_src:
        xconst = (par + 2 * exc_src['h'] - 1000 - par) // 2
    def ev(cf):
        """(const, cx, cy): affine in x = h - 250 and the domain y"""
        if cf is None: return None
        c0, c1, c2 = cf
        if exc_src: const, cx = c0 + c1 * xconst, 0
        else: const, cx = c0 - 250 * c1, c1
        cy = 0
        if Snode.family_key:
            if kind == 'family': const -= 500 * c2; cy = c2
            else: const += c2 * (yinfo - 500)
        return (const, cx, cy)
    N1, M1, K1 = ev(B['N1']), ev(B['M1']), ev(B['K1'])
    T = B['target']; TA = descent_node(T); TD = domain_node(T)
    TAn, TDn = NF.Node(TA), NF.Node(TD)
    par1 = M1[0] % 2
    h1 = ((M1[0] - par1) // 2, M1[1] // 2, M1[2] // 2)
    y1 = None
    if TAn.fam:
        y1 = ((K1[0] - TAn.kp) // 2, K1[1] // 2, K1[2] // 2) if K1 is not None else ((TAn.kfix - TAn.kp) // 2, 0, 0)
    PT, D = NODES[TA]['P'], NODES[TA]['dM'] // 2
    ymin = yinfo if kind == 'family' else 0
    at0 = lambda a: a[0] + a[2] * ymin
    for a in (N1, h1) + ((y1,) if y1 else ()):
        if a[1] < 0 or a[2] < 0: raise ValueError('negative slope')
    if at0(N1) < NB: raise ValueError('N1 below 12')
    q0 = (at0(N1) - NB) // PT
    exc = None
    if at0(h1) + D * q0 < HMIN:
        r2, h2 = NB + (N1[0] - NB) % PT, h1[0] + D * q0
        info = dict(key=TD, par=par1, r=r2, h=h2, ymin=at0(y1) if y1 else None)
        if N1[1] or N1[2] or h1[1] or h1[2] or not TDn.family_key: raise Exceptional('exceptional landing', info)
        exc = EXC.get('%s|%d|%d|%d' % (TD, par1, r2, h2))
        if exc is None or at0(y1) < exc['ymin']: raise Exceptional('exceptional landing', info)
        ctor = exc['ctor']
    else:
        ctor = 'dom_%s_%d' % (TDn.tag, par1)
        dinfo = DOM[ctor]
        if dinfo['kind'] == 'family' and at0(y1) < dinfo['yf']: raise ValueError('target k below K_fam')
        if dinfo['kind'] == 'kfixed' and (y1[1] or y1[2] or y1[0] != dinfo['yfix']): raise ValueError('target k mismatch')
    if DRY: return [], None, None
    # the lemma B theorem
    th = next(l for l in open(RG.ROOT + 'rocq/B3/%s.v' % bfile) if l.startswith('Theorem lemmaB'))
    _, sides = th.split(':', 1)
    lhs, rhs = sides.rstrip().rstrip('.').split('-->+')
    offS, offT = lhs.split()[0], rhs.split()[0]
    hexpr = '%d' % exc_src['h'] if exc_src else 'h'
    xs = '(h - %d)' % HMIN
    ys = None
    if Snode.family_key:
        ys = '(y - %d)' % yd if kind == 'family' else '%d' % (yinfo - yd)
    sub = lambda a: re.sub(r'\b([xy])\b', lambda m: xs if m.group(1) == 'x' else ys, a)
    la = ' '.join('(%s)' % sub(a) for a in top_args(lhs)); ra = ' '.join('(%s)' % sub(a) for a in top_args(rhs))
    bargs = ' '.join(([] if exc_src else [xs]) + ([ys] if ys else []))
    Fsrc = 'F_%s_%d %d %s%s' % (node.tag, par, r, hexpr, ' y' if kind == 'family' else (' %d' % yinfo if kind == 'kfixed' else ''))
    E = lambda a: lin(*a, xs='(h - 250)')
    N1e, h1e = E(N1), E(h1)
    yarg = (' ' + E(y1)) if TAn.fam else ''
    land = 'F_%s_%d (12 + rr + %d * q) %s%s' % (TAn.tag, par1, PT, h1e, yarg)
    fin_A = 'F_%s_%d (12 + rr) (%s + %d * q)%s' % (TAn.tag, par1, h1e, D, yarg)
    fin_D = 'F_%s_%d (12 + rr) (%s + %d * q)%s' % (TDn.tag, par1, h1e, D, yarg if TDn.fam else '')
    if exc:
        dom = 'replace (12 + rr) with %d by lia. replace (%s + %d * q) with %d by lia. apply (%s%s); lia.' % (
            exc['r'], h1e, D, exc['h'], ctor, yarg)
    else:
        dargs = '(12 + rr) (%s + %d * q)%s' % (h1e, D, yarg if DOM[ctor]['kind'] == 'family' else '')
        dom = 'apply (%s %s); lia.' % (ctor, dargs)
    alias = lambda a, b, p: '' if a == b else 'rewrite (alias_%s_%d); ' % (NF.tagof(a), p)
    desc = 'apply (D_%s_%d.F_%s_%d_descent q (12 + rr) %s%s); lia.' % (TAn.tag, par1, TAn.tag, par1, h1e, yarg)
    if TD != TA:
        desc = 'replace (%s) with (%s) by (unfold F_%s_%d, F_%s_%d; %sf_equal; lia). %s' % (
            fin_D, fin_A, TDn.tag, par1, TAn.tag, par1, alias(TD, TA, par1), desc)
    params = ('' if exc_src else ' h') + (' y' if kind == 'family' else '')
    hyps = ([] if exc_src else ['%d <= h' % HMIN]) + (['%d <= y' % yinfo] if kind == 'family' else [])
    v = ['Lemma case_%s%s : %s exists c, Dom c /\\ %s -->+ c.' % (name, params, ''.join(hh + ' -> ' for hh in hyps), Fsrc),
         'Proof.',
         '  intros%s.' % ''.join(' H%d' % i for i in range(len(hyps))) if hyps else '  idtac.',
         '  pose proof (Nat.div_mod (%s - 12) %d ltac:(lia)) as Hd.' % (N1e, PT),
         '  pose proof (Nat.mod_upper_bound (%s - 12) %d ltac:(lia)) as Hr.' % (N1e, PT),
         '  pose proof (Nat.div_le_lower_bound (%s - 12) %d %d ltac:(lia) ltac:(lia)) as Hq.' % (N1e, PT, q0),
         '  set (q := (%s - 12) / %d) in *. set (rr := (%s - 12) mod %d) in *.' % (N1e, PT, N1e, PT),
         '  exists (%s). split.' % fin_D,
         '  - %s' % dom,
         '  - apply (progress_evstep_trans _ _ (%s)).' % land,
         '    + eapply (%s.last_eq _ (%s %s) (%s %s)).' % (bfile, offS, la, offT, ra),
         '      * unfold F_%s_%d. %sf_equal; lia.' % (node.tag, par, alias(t, S, par)),
         '      * apply (%s.lemmaB %s).' % (bfile, bargs),
         '      * unfold F_%s_%d. %sf_equal; lia.' % (TAn.tag, par1, alias(T, TA, par1)),
         '    + %s' % desc,
         'Qed.', '']
    return v, bfile, 'D_%s_%d' % (TAn.tag, par1)


HEAD = ['From BusyCoq Require Import Individual62.', 'From BB6N Require Import Nodes.', 'From BB6F Require Import F Dom.',
        'Require Import Lia.']


def wrap(title, body, reqs):
    reqs = sorted(r for r in reqs if r)
    return ['(* generated by rocq/genClose.py: %s *)' % title] + HEAD + ['Require %s.' % m for m in reqs] + [
        'Open Scope list.', '', 'Definition tm := %s.tm.' % reqs[0],
        """Notation "c -->+ c'" := (c -[ tm ]->+ c') (at level 40).""", ''] + body


def node_file(c, info):
    node = NF.Node(info['key']); par = info['par']; Pp = info['P']; kind = info['kind']
    yinfo = info.get('yf') if kind == 'family' else info.get('yfix')
    body, reqs, fails = [], set(), []
    for r in range(NB, NB + Pp):
        try:
            v, b, d = case('%s_r%d' % (c, r), info['key'], par, r, kind, yinfo); body += v; reqs |= {b, d}
        except Exception as e:
            fails.append((r, repr(e)))
    if fails or DRY: return None, fails
    yv = ' y' if kind == 'family' else ''
    Fn = 'F_%s_%d r h%s' % (node.tag, par, yv if kind == 'family' else (' %d' % yinfo if kind == 'kfixed' else ''))
    hy = ' -> %d <= y' % yinfo if kind == 'family' else ''
    body += ['Lemma close_%s r h%s : 12 <= r < %d -> %d <= h%s -> exists c, Dom c /\\ %s -->+ c.' % (c, yv, NB + Pp, HMIN, hy, Fn),
             'Proof.',
             '  intros Hr Hh%s.' % (' Hy' if kind == 'family' else ''),
             '  assert (%s) as E by lia.' % ' \\/ '.join('r = %d' % r for r in range(NB, NB + Pp)),
             '  repeat destruct E as [E | E]; subst r; [%s].' % ' | '.join(
                 'apply case_%s_r%d; assumption' % (c, r) for r in range(NB, NB + Pp)),
             'Qed.']
    return wrap('closure of ' + c, body, reqs), []


def exc_file(e):
    v, b, d = case(e['ctor'], e['key'], e['par'], e['r'], 'family', e['ymin'], exc_src=e)
    if DRY: return None
    v += ['Lemma close_%s y : %d <= y -> exists c, Dom c /\\ F_%s_%d %d %d y -->+ c.' % (
              e['ctor'], e['ymin'], NF.tagof(e['key']), e['par'], e['r'], e['h']),
          'Proof. apply case_%s. Qed.' % e['ctor']]
    return wrap('closure of the exceptional state ' + e['ctor'], v, {b, d})


if __name__ == '__main__':
    args = sys.argv[1:]
    if args and args[0] == '--dry': DRY = True; args = args[1:]
    names = args or sorted(DOM)
    bad = 0; exc_found = {}
    for c in names:
        text, fails = node_file(c, DOM[c])
        for r, msg in fails:
            if 'exceptional landing' in msg: pass
        if fails:
            bad += 1; print('FAIL', c, len(fails), fails[:2])
            continue
        if text: open(OUT + 'Close_%s.v' % c[4:], 'w').write('\n'.join(text) + '\n')
    for e in EXC.values():
        if e['ctor'] in names or not args:
            try:
                text = exc_file(e)
                if text: open(OUT + 'Close_%s.v' % e['ctor'], 'w').write('\n'.join(text) + '\n')
            except Exception as ex:
                bad += 1; print('FAIL', e['ctor'], repr(ex))
    print('constructors %d (+%d exceptional), failed %d' % (len(names), len(EXC), bad))
