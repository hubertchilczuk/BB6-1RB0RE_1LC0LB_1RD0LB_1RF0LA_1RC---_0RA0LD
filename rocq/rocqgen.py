"""Shared machinery for the Rocq proof generators (lemma A, lemma B).

Tapes are always written from the head (state C, head at the new leftmost cell) to the rightmost 1.

Representation
  * a tape is parsed into items (k gaps of length one + a terminating gap) and run-length compressed with
    blocks of 1..4 items (runs of >= MINRUN copies) -> pieces (block cells, count);
  * a family of tapes (instances that differ in some integer parameters) gives pieces with counts affine in the
    parameters; the skeleton (blocks in order) must be the same for all instances;
  * a *variable run* is a piece whose count depends on a parameter, or is long, or is forced (node runs);
  * every variable run is written with a unit block of UNIT cells (blocks of UNIT/2 cells are doubled; the
    remainder copies are concrete), in 0..1 orientation (trailing zeros of the block moved to the front),
    with all concrete copies *before* the repeater, as ES_v3 normalizes them:
        B^c (B = U V, V the trailing zeros)  =  U (V U)^(c-1) V  =  U (VU)^e ((VU)^q)^^z V
  * a checkpoint is rendered as  0inf {{C}}> lit *> (R^^z) *> lit *> ... *> 0inf  with one Rocq variable per
    variable run.

Node configurations (the interface between lemmas A, B and the closure) use the same rules, so the first and last
checkpoint of every lemma are *the* node form  off(node, parity; values of its runs).
"""
import os, sys, json, re, subprocess
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/'
sys.path.insert(0, ROOT)

EVT = ROOT + 'an/evtapes2.exe'
TMP = ROOT + 'rocq/tmp/'
os.makedirs(TMP, exist_ok=True)
MINRUN = 6
BIGV = 100      # concrete runs with at least this many cells are variable runs
UNIT = 20       # cells of a unit block
SAFE = 2        # extra margin copies
CHUNK = 40      # literals longer than this get a shared name


# ---------------------------------------------------------------- parsing
def items(tape):
    lead = len(tape) - len(tape.lstrip('0'))
    ones = [i for i, c in enumerate(tape) if c == '1']
    gaps = [b - a - 1 for a, b in zip(ones, ones[1:])] + [0]
    its, k = [], 0
    for idx, g in enumerate(gaps):
        if g == 1 and idx < len(gaps) - 1: k += 1; continue
        its.append((k, g)); k = 0
    return lead, its


def item_cells(it):
    k, g = it
    return '10' * k + '1' + '0' * g


def rle(its):
    out, i, n = [], 0, len(its)
    while i < n:
        best = None
        for p in range(1, 5):
            b = tuple(its[i:i + p])
            if len(b) < p: break
            r = 1
            while tuple(its[i + r * p:i + (r + 1) * p]) == b: r += 1
            if r >= MINRUN and (best is None or r * p > best[0] * best[1]): best = (r, p)
        if best:
            r, p = best; out.append((tuple(its[i:i + p]), r)); i += r * p
        else:
            out.append(((its[i],), 1)); i += 1
    return out


def family(tapes, design):
    """tapes[i] = tape at parameter vector design[i] (design[0] = base, then one step per parameter, extra rows
    are checks). Returns pieces [(cells, const, coeffs)] with count = const + sum coeffs[j] * param[j]."""
    parsed = [items(t) for t in tapes]
    if len({p[0] for p in parsed}) != 1: raise ValueError('leading zeros differ')
    rs = [rle(p[1]) for p in parsed]
    if len({len(r) for r in rs}) != 1 or any(len({r[i][0] for r in rs}) != 1 for i in range(len(rs[0]))):
        raise ValueError('skeletons differ')
    npar = len(design[0])
    base = design[0]
    out = [('0' * parsed[0][0], 1, (0,) * npar)] if parsed[0][0] else []
    for idx in range(len(rs[0])):
        blk = rs[0][idx][0]; cnt = [r[idx][1] for r in rs]
        coef = []
        for j in range(npar):
            row = 1 + j
            dp = design[row][j] - base[j]
            dc = cnt[row] - cnt[0]
            if dc % dp: raise ValueError('run not affine')
            coef.append(dc // dp)
        const = cnt[0] - sum(c * p for c, p in zip(coef, base))
        for row in range(len(design)):
            if const + sum(c * p for c, p in zip(coef, design[row])) != cnt[row]: raise ValueError('run not affine (check)')
        out.append((''.join(item_cells(it) for it in blk), const, tuple(coef)))
    return out


# ---------------------------------------------------------------- canonical rendering
def orient(cells):
    z = len(cells) - len(cells.rstrip('0'))
    return (cells[len(cells) - z:] + cells[:len(cells) - z]) if z else cells


def is_var(piece, forced=False):
    cells, a, coef = piece
    return forced or any(coef) or (a >= 4 and len(cells) * a >= BIGV)


def canon(pieces, varmask):
    """pieces + which of them are variable runs -> (tokens, values) where tokens are ('lit', cells) or
    ('var', index, unitcells) and values[index] = (const, coeffs) of the variable in units"""
    toks, conc, vals = [], '', {}
    for j, (c, a, coef) in enumerate(pieces):
        if not varmask[j]:
            conc += c * a; continue
        q = UNIT // len(c)
        if q * len(c) != UNIT: raise ValueError('block length %d does not divide the unit' % len(c))
        if any(x % q for x in coef): raise ValueError('slope not divisible by the unit ratio')
        z = len(c) - len(c.rstrip('0'))
        if z:
            Uc, Vc = c[:len(c) - z], c[len(c) - z:]
            # the form needs count >= 1; for parameter-dependent runs the value may have a negative constant part
            if a < 1 and not any(coef): raise ValueError('rotated run needs a constant copy')
            cnt = a - 1; e = cnt % q
            conc += Uc + (Vc + Uc) * e
            toks.append(('lit', conc)); conc = Vc
            vals[j] = ((cnt - e) // q, tuple(x // q for x in coef))
            toks.append(('var', j, (Vc + Uc) * q))
        else:
            e = a % q
            conc += c * e
            toks.append(('lit', conc)); conc = ''
            vals[j] = ((a - e) // q, tuple(x // q for x in coef))
            toks.append(('var', j, c * q))
    toks.append(('lit', conc.rstrip('0')))
    return toks, vals


# ---------------------------------------------------------------- lineages
def match(prev, pmask, cur, cmask):
    """order-preserving matching of variable runs of consecutive checkpoints (same slope in cells; constant runs
    only with the same block)"""
    pv = [i for i in range(len(prev)) if pmask[i]]
    cv = [i for i in range(len(cur)) if cmask[i]]
    res, k = {}, 0
    for j in cv:
        cj, aj, fj = cur[j]
        for t in range(k, len(pv)):
            ci, ai, fi = prev[pv[t]]
            if tuple(len(ci) * x for x in fi) == tuple(len(cj) * x for x in fj) and (any(fi) or ci == cj):
                res[j] = pv[t]; k = t + 1; break
    return res


# ---------------------------------------------------------------- simulation
def run_to(tape, target, every):
    fn, tf = TMP + 'rg_%d.txt' % os.getpid(), TMP + 'rg_%d_t.txt' % os.getpid()
    open(fn, 'w').write('0 2 0\n%s\n' % tape)
    open(tf, 'w').write(target + '\n')
    out = subprocess.run([EVT, fn, '200000000000', '20000000', tf], capture_output=True, text=True,
                         env=dict(os.environ, EVERY=str(every))).stdout.split('\n')
    if not any(l.startswith('REACHED') for l in out): raise RuntimeError('target not reached')
    cps = []
    for i in range(0, len(out) - 1, 2):
        if out[i].startswith('REACHED'): break
        if int(out[i].split()[1]) != 2: raise RuntimeError('checkpoint not in state C')
        cps.append(out[i + 1])
    return cps


# ---------------------------------------------------------------- Rocq text
def lit(cells):
    return '[' + ';'.join(cells) + ']'


class Names:
    def __init__(self, prefix=''):
        self.units, self.lits, self.prefix = {}, {}, prefix

    def unit(self, cells):
        return self.units.setdefault(cells, '%sU%d' % (self.prefix, len(self.units)))

    def lit(self, cells):
        if len(cells) <= CHUNK: return lit(cells)
        return self.lits.setdefault(cells, '%sL%d' % (self.prefix, len(self.lits)))

    def defs(self):
        order = lambda kv: (kv[1][len(self.prefix)], int(kv[1][len(self.prefix) + 1:]))
        return ['Definition %s : list sym := %s.' % (n, lit(c)) for c, n in
                sorted(list(self.units.items()) + list(self.lits.items()), key=order)]

    def all(self):
        return sorted(list(self.units.values()) + list(self.lits.values()))


def render(toks, args, names):
    out = []
    for t in toks:
        if t[0] == 'lit':
            if t[1]: out.append(names.lit(t[1]))
        else:
            out.append('(%s^^%s)' % (names.unit(t[2]), args[t[1]]))
    return ' *> '.join(out + ['0inf'])


def aff(const, coef, pnames):
    terms = ['%d' % const] if const or not any(coef) else []
    for c, p in zip(coef, pnames):
        if c: terms.append(p if c == 1 else '%d * %s' % (c, p))
    return ' + '.join(terms) if terms else '0'


HEADER = ['From BusyCoq Require Import Individual62 ES_v3.', 'Require Import Lia String NArith.', 'Open Scope list.', '',
          'Definition tm := Eval compute in (TM_from_str "1RB0RE_1LC0LB_1RD0LB_1RF0LA_1RC---_0RA0LD").',
          """Notation "c -->+ c'" := (c -[ tm ]->+ c') (at level 40).""", '',
          "Lemma step_eq c1 c1' c2' c2 c3 : c1 = c1' -> c1' -->+ c2' -> c2' = c2 -> c2 -->+ c3 -> c1 -->+ c3.",
          'Proof. intros -> H -> H2. eapply progress_trans; eauto. Qed.',
          "Lemma last_eq c1 c1' c2' c2 : c1 = c1' -> c1' -->+ c2' -> c2' = c2 -> c1 -->+ c2.",
          'Proof. intros -> H ->. exact H. Qed.', '']


def chain(cps, masks, pnames, theorem, names, ends=None, extra_unfold=()):
    """cps[i]: pieces of checkpoint i (affine in pnames), masks[i]: variable runs. Returns Rocq lines: checkpoint
    definitions, sub-lemmas, and the theorem  theorem : cfg0 (values) -->+ cfg_last (values).
    ends = {i: name}: checkpoint i is the external definition `name` (a node form, arguments in tape order)."""
    n = len(cps)
    ends = ends or {}
    cfgname = lambda i: ends.get(i, 'cfg%d' % i)
    can = [canon(cps[i], masks[i]) for i in range(n)]
    lin = [dict() for _ in range(n)]; nl = 0
    for i in range(n):
        m = match(cps[i - 1], masks[i - 1], cps[i], masks[i]) if i else {}
        for j in range(len(cps[i])):
            if not masks[i][j]: continue
            if j in m: lin[i][j] = lin[i - 1][m[j]]
            else: lin[i][j] = nl; nl += 1
    toks = [[(t[0], lin[i][t[1]], t[2]) if t[0] == 'var' else t for t in can[i][0]] for i in range(n)]
    vals = [{lin[i][j]: v for j, v in can[i][1].items()} for i in range(n)]
    vl = [[t[1] for t in toks[i] if t[0] == 'var'] for i in range(n)]     # tape order
    out = []
    for i in range(n):
        if i in ends: continue
        out.append('Definition %s %s : Q * tape := 0inf {{C}}> %s.' % (
            cfgname(i), ' '.join('z%d' % l for l in vl[i]), render(toks[i], {l: 'z%d' % l for l in vl[i]}, names)))
    out.append('')
    steps = []
    for i in range(n - 1):
        common = [l for l in vl[i] if l in vals[i + 1]]
        aL, aR, mg = {}, {}, {}
        for l in vl[i]:
            c0, f0 = vals[i][l]
            if l in common:
                c1, f1 = vals[i + 1][l]
                if f0 != f1: raise ValueError('lineage slope changes')
                d = c1 - c0
                m = min(max(0, -d) + SAFE, c0)
                if m < max(0, -d): raise ValueError('margin')
                mg[l] = m
                aL[l] = '(z%d + %d)' % (l, m) if m else 'z%d' % l
                aR[l] = '(z%d + %d)' % (l, m + d) if m + d else 'z%d' % l
            else:
                if any(f0): raise ValueError('vanishing parameter-dependent run')
                aL[l] = str(c0)
        for l in vl[i + 1]:
            if l not in common:
                c1, f1 = vals[i + 1][l]
                if any(f1): raise ValueError('new parameter-dependent run')
                aR[l] = str(c1)
        qv = ' '.join('z%d' % l for l in common)
        lhs = '%s %s' % (cfgname(i), ' '.join(aL[l] for l in vl[i]))
        rhs = '%s %s' % (cfgname(i + 1), ' '.join(aR[l] for l in vl[i + 1]))
        out += ['Lemma %s_sub%d %s : %s -->+ %s.' % (theorem, i, qv, lhs, rhs),
                "Proof. unfold %s, %s. repeat rewrite lpow_add. repeat rewrite Str_app_assoc. unfold @@NAMES@@%s. cbn [lpow app]. es' %s. Qed."
                % (cfgname(i), cfgname(i + 1), ''.join(', ' + e for e in extra_unfold), qv), '']
        steps.append((common, mg, aL, aR))
    at = lambda i: '%s %s' % (cfgname(i), ' '.join('(%s)' % aff(*vals[i][l], pnames) for l in vl[i]))
    eqt = lambda i: '(f_equal; lia)' if vl[i] else 'reflexivity'
    out += ['Theorem %s %s : %s -->+ %s.' % (theorem, ' '.join(pnames), at(0), at(n - 1)), 'Proof.']
    for i in range(n - 1):
        common, mg, aL, aR = steps[i]
        zv = {l: '(%s)' % aff(vals[i][l][0] - mg[l], vals[i][l][1], pnames) for l in common}
        sub = lambda s: re.sub(r'z(\d+)', lambda mm: zv[int(mm.group(1))], s)
        lhs = '%s %s' % (cfgname(i), ' '.join(sub(aL[l]) for l in vl[i]))
        rhs = '%s %s' % (cfgname(i + 1), ' '.join(sub(aR[l]) for l in vl[i + 1]))
        app = '(%s_sub%d %s)' % (theorem, i, ' '.join(zv[l] for l in common)) if common else '%s_sub%d' % (theorem, i)
        if i < n - 2:
            out.append('  eapply (step_eq _ (%s) (%s) (%s)); [%s | apply %s | %s | ].' % (lhs, rhs, at(i + 1), eqt(i), app, eqt(i + 1)))
        else:
            out.append('  eapply (last_eq _ (%s) (%s)); [%s | apply %s | %s].' % (lhs, rhs, eqt(i), app, eqt(i + 1)))
    out.append('Qed.')
    return out, vals, vl
