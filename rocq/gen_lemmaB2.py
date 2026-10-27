"""Lemma B in Rocq with one variable per large run (fast variant of gen_lemmaB.py).

Checkpoints (every G-th sweep) are parsed as in gen_lemmaB.py: pieces (cells, a, b) = run of `a + b*x` copies of a
block, x = (M - M0) / 2. A piece is a *variable run* if b > 0 or it is long (>= BIGV cells). Variable runs of
consecutive checkpoints are matched in order when their x-slopes in cells agree (b*len); matched runs form
lineages, each with one unit block (the longest block of the lineage; shorter blocks are doubled, the remainder
`count mod 2` is a concrete copy written before the run). Every checkpoint gets a canonical definition
    cfg_i z1 .. zk := 0inf {{C}}> ... *> U1^e1 *> (U1^^z1) *> ... *> 0inf        (concrete copies before the run)
and every sub-lemma moves the variables by constant deltas, with a margin of concrete copies on the left:
    sub_i z.. : cfg_i (z + m) .. -->+ cfg_(i+1) (z + m + d) ..          proved by es' (busycoq ES_v3)
The theorem lemmaB x chains them with the variable values at each checkpoint (affine in x).
usage: gen_lemmaB2.py "<lemma-B key>" OUT.v [G]
"""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gen_lemmaB as G1
from gen_lemmaB import items, rle, lit, P, S, node_tape, run_instance, XS, MSTAR

BIGV = 100     # concrete runs with at least this many cells become variable runs
SAFE = 2       # extra copies of margin
CHUNK = 40     # concrete literal pieces longer than this get a shared name


def pieces_of(tapes):
    """three tapes (x in XS) -> list of (cells, a, b); runs keep their block cells"""
    parsed = [items(t) for t in tapes]
    if len({p[0] for p in parsed}) != 1: raise ValueError('leading zeros differ')
    rs = [rle(p[1]) for p in parsed]
    if len({len(r) for r in rs}) != 1 or any(len({r[i][0] for r in rs}) != 1 for i in range(len(rs[0]))):
        raise ValueError('skeletons differ')
    out = [('0' * parsed[0][0], 1, 0)] if parsed[0][0] else []
    for (blk, c1), (_, c2), (_, c3) in zip(*rs):
        d = c2 - c1
        if c3 - c2 != d or d % (XS[1] - XS[0]): raise ValueError('run not affine')
        b = d // (XS[1] - XS[0]); a = c1 - b * XS[0]
        if a < 0: raise ValueError('negative constant part')
        out.append((''.join(G1.item_cells(it) for it in blk), a, b))
    return out


def is_var(p):
    cells, a, b = p
    return b > 0 or (a >= 4 and len(cells) * a >= BIGV)


def match(prev, cur):
    """order-preserving matching of variable runs: indices into prev/cur piece lists"""
    pv = [i for i, p in enumerate(prev) if is_var(p)]
    cv = [i for i, p in enumerate(cur) if is_var(p)]
    res, k = {}, 0
    for j in cv:
        cj, aj, bj = cur[j]
        for t in range(k, len(pv)):
            ci, ai, bi = prev[pv[t]]
            ok = len(ci) * bi == len(cj) * bj and (bi > 0 or ci == cj)
            if ok and max(len(ci), len(cj)) % min(len(ci), len(cj)) == 0:
                res[j] = pv[t]; k = t + 1; break
    return res


def generate(bkey, outfile, Gs=50):
    node = bkey.split(' ## ')[0]; r = int(bkey.split('r=')[1].split()[0]); par = int(bkey.split('par=')[1])
    assert ' || FAM ' not in node, 'family source nodes: not yet'
    B = P['lemmaB'][bkey]; tnode = B['target']
    M0 = MSTAR + ((par - MSTAR) % 2)
    runs = []
    for x in XS:
        M = M0 + 2 * x; xx = (M - 1000 - par) // 2
        ev = lambda c: None if c is None else c[0] + c[1] * xx
        tgt = node_tape(tnode, ev(B['N1']), ev(B['M1']), ev(B['K1']) if ' || FAM ' in tnode else None)
        runs.append(run_instance(node, r, M, tgt, Gs))
    if len({len(c) for c in runs}) != 1: raise ValueError('checkpoint counts differ')
    cps = [pieces_of([node_tape(node, r, M0 + 2 * x) for x in XS])] + [pieces_of([c[i] for c in runs]) for i in range(len(runs[0]))]
    n = len(cps)

    # lineages: lin[i][j] = lineage id of variable piece j of checkpoint i
    lin = [dict() for _ in range(n)]; nl = 0; members = []
    for i in range(n):
        m = match(cps[i - 1], cps[i]) if i else {}
        for j, p in enumerate(cps[i]):
            if not is_var(p): continue
            if j in m: lin[i][j] = lin[i - 1][m[j]]; members[lin[i][j]].append((i, j))
            else: lin[i][j] = nl; members.append([(i, j)]); nl += 1
    unit = {}
    for l, mem in enumerate(members):
        L = max(len(cps[i][j][0]) for i, j in mem)
        cells = next(cps[i][j][0] for i, j in mem if len(cps[i][j][0]) == L)
        unit[l] = L
        for i, j in mem:
            c, a, b = cps[i][j]
            q = L // len(c)
            if b % q: raise ValueError('slope not divisible by the unit ratio')

    names, cdefs = {}, {}

    def nm(cells, pre):
        d = names if pre == 'U' else cdefs
        return d.setdefault(cells, '%s%d' % (pre, len(d)))

    # canonical form of checkpoint i: list of tokens; variable run -> (lineage, value affine (c, b), remainder cells)
    canon = []
    for i in range(n):
        toks, conc, val = [], '', {}
        for j, (c, a, b) in enumerate(cps[i]):
            if j not in lin[i]:
                conc += c * a; continue
            l = lin[i][j]; q = unit[l] // len(c)
            e = a % q
            ublk = G1.orient(c * q)
            pre = c * e     # remainder copies (concrete, before the run)
            # B^(a+bx) with B = U V: U (V U)^(a+bx-1) V; in units of q blocks: U ((V U)^q)^z' (V U)^e' V
            z = len(c) - len(c.rstrip('0'))
            if z and a >= 1:
                Uc, Vc = c[:len(c) - z], c[len(c) - z:]
                vu = Vc + Uc
                cnt_c = a - 1                      # copies of VU besides the variable part
                e = cnt_c % q
                conc += Uc + vu * e
                toks.append(('lit', conc)); conc = Vc
                val[l] = ((cnt_c - e) // q, b // q)
                toks.append(('var', l, nm(vu * q, 'U')))
            else:
                conc += c * e
                toks.append(('lit', conc)); conc = ''
                val[l] = ((a - e) // q, b // q)
                toks.append(('var', l, nm(c * q, 'U')))
        toks.append(('lit', conc.rstrip('0')))
        canon.append((toks, val))

    def render(toks, args):
        out = []
        for t in toks:
            if t[0] == 'lit':
                s = t[1]
                if not s: continue
                out.append(nm(s, 'L') if len(s) > CHUNK else lit(s))
            else:
                out.append('(%s^^%s)' % (t[2], args[t[1]]))
        return ' *> '.join(out + ['0inf'])

    vlist = [sorted({t[1] for t in canon[i][0] if t[0] == 'var'}) for i in range(n)]
    v = ['(* generated by rocq/gen_lemmaB2.py: lemma B', '   %s' % bkey.replace('*)', '* )'),
         '   M = %d + 2x, %d checkpoints, %d run lineages *)' % (M0, n, nl),
         'From BusyCoq Require Import Individual62 ES_v3.', 'Require Import Lia String NArith.', 'Open Scope list.', '',
         'Definition tm := Eval compute in (TM_from_str "1RB0RE_1LC0LB_1RD0LB_1RF0LA_1RC---_0RA0LD").',
         """Notation "c -->+ c'" := (c -[ tm ]->+ c') (at level 40).""", '',
         "Lemma step_eq c1 c1' c2' c2 c3 : c1 = c1' -> c1' -->+ c2' -> c2' = c2 -> c2 -->+ c3 -> c1 -->+ c3.",
         'Proof. intros -> H -> H2. eapply progress_trans; eauto. Qed.',
         "Lemma last_eq c1 c1' c2' c2 : c1 = c1' -> c1' -->+ c2' -> c2' = c2 -> c1 -->+ c2.",
         'Proof. intros -> H ->. exact H. Qed.', '', '@@DEFS@@', '']
    for i in range(n):
        vs = ' '.join('z%d' % l for l in vlist[i])
        v.append('Definition cfg%d %s : Q * tape := 0inf {{C}}> %s.' % (i, vs, render(canon[i][0], {l: 'z%d' % l for l in vlist[i]})))
    v.append('')
    # sub-lemmas
    steps = []
    for i in range(n - 1):
        (_, val0), (_, val1) = canon[i], canon[i + 1]
        common = [l for l in vlist[i] if l in vlist[i + 1]]
        argL, argR, mg = {}, {}, {}
        for l in vlist[i]:
            c0, b0 = val0[l]
            if l in common:
                c1, b1 = val1[l]
                if b0 != b1: raise ValueError('lineage slope changes')
                d = c1 - c0
                m = min(max(0, -d) + SAFE, c0)
                if c0 + d < 0 or m < max(0, -d): raise ValueError('margin')
                mg[l] = (m, d)
                argL[l] = '(z%d + %d)' % (l, m) if m else 'z%d' % l
                argR[l] = '(z%d + %d)' % (l, m + d) if m + d else 'z%d' % l
            else:
                if b0: raise ValueError('vanishing x-dependent run')
                argL[l] = str(c0)
        for l in vlist[i + 1]:
            if l not in common:
                c1, b1 = val1[l]
                if b1: raise ValueError('new x-dependent run')
                argR[l] = str(c1)
        qv = ' '.join('z%d' % l for l in common)
        lhs = 'cfg%d %s' % (i, ' '.join(argL[l] for l in vlist[i]))
        rhs = 'cfg%d %s' % (i + 1, ' '.join(argR[l] for l in vlist[i + 1]))
        v += ['Lemma sub%d %s : %s -->+ %s.' % (i, qv, lhs, rhs),
              "Proof. unfold cfg%d, cfg%d. repeat rewrite lpow_add. repeat rewrite Str_app_assoc. unfold @@NAMES@@. cbn [lpow app]. es' %s. Qed." % (i, i + 1, qv), '']
        steps.append((common, mg, argL, argR))
    # composition: values of the lineages at every checkpoint, affine in x
    def aff(c, b):
        return ('%d' % c) if b == 0 else ('%d + %d * x' % (c, b) if b != 1 else '%d + x' % c)

    def at(i):
        return 'cfg%d %s' % (i, ' '.join('(%s)' % aff(*canon[i][1][l]) for l in vlist[i]))

    v += ['Theorem lemmaB x : %s -->+ %s.' % (at(0), at(n - 1)), 'Proof.']
    # equalities cfg_i args = cfg_i args': argument-wise by lia (reflexivity would unfold and compare whole tapes)
    eqt = lambda i: '(f_equal; lia)' if vlist[i] else 'reflexivity'
    for i in range(n - 1):
        common, mg, argL, argR = steps[i]
        zval = {l: '(%s)' % aff(canon[i][1][l][0] - mg[l][0], canon[i][1][l][1]) for l in common}
        sub = lambda s: s if not common else __import__('re').sub(r'z(\d+)', lambda m_: zval[int(m_.group(1))], s)
        lhs_i = 'cfg%d %s' % (i, ' '.join(sub(argL[l]) for l in vlist[i]))
        rhs_i = 'cfg%d %s' % (i + 1, ' '.join(sub(argR[l]) for l in vlist[i + 1]))
        app = '(sub%d %s)' % (i, ' '.join(zval[l] for l in common)) if common else 'sub%d' % i
        if i < n - 2:
            v.append('  eapply (step_eq _ (%s) (%s) (%s)); [%s | apply %s | %s | ].' % (lhs_i, rhs_i, at(i + 1), eqt(i), app, eqt(i + 1)))
        else:
            v.append('  eapply (last_eq _ (%s) (%s)); [%s | apply %s | %s].' % (lhs_i, rhs_i, eqt(i), app, eqt(i + 1)))
    v += ['Qed.']
    defs = ['Definition %s : list sym := %s.' % (nmv, lit(cells)) for cells, nmv in sorted(list(names.items()) + list(cdefs.items()), key=lambda kv: (kv[1][0], int(kv[1][1:])))]
    allnames = ', '.join(sorted(list(names.values()) + list(cdefs.values()))) or 'tm'
    text = '\n'.join(v).replace('@@DEFS@@', '\n'.join(defs)).replace('@@NAMES@@', allnames)
    open(outfile, 'w').write(text + '\n')
    return n, nl


if __name__ == '__main__':
    n, nl = generate(sys.argv[1], sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 50)
    print('checkpoints', n, 'lineages', nl)
