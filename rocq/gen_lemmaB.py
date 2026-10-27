"""Generate a Rocq proof of one lemma B (node, r, parity of M), for M = M0 + 2x, all x >= 0.

    cfg0 x := node config with N = r, M = M0 + 2x       -->+    first canonical point of the target node

The run is split at every G-th sweep (new-leftmost event). The checkpoint tapes of three instances
x in XS are written as items (k gaps of length one + a terminating gap) and run-length compressed with blocks
of 1..4 items (runs of >= MINRUN copies); the skeletons must agree and every run count must be affine in x.
A run c0 + c1*x with c1 > 0 becomes  B^c0 *> (B^c1)^^x  in Rocq (B = the block's cells in 0..1 orientation),
everything else is concrete. Sub-lemmas between checkpoints are proved by es' (busycoq ES_v3).
usage: gen_lemmaB.py "<lemma-B key>" OUT.v [G]
"""
import os, sys, json, subprocess
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/'
sys.path.insert(0, ROOT)
import samples

EVT = ROOT + 'an/evtapes2.exe'
TMP = ROOT + 'rocq/tmp/'
os.makedirs(TMP, exist_ok=True)
P = json.load(open(ROOT + 'proof4.json'))
S = samples.load()
XS = (50, 100, 150)
MINRUN = 6
MSTAR = 500


def node_tape(key, N, M, k=None):
    st = S[key]
    if ' || FAM ' in key:
        Tc = st['kh'] + st['k3'] * k + st['kl']
    else:
        Tc = st['T_cells']
    return st['zone_cells'] + st['w_cells'] * N + Tc + st['u_cells'] * M + st['tail_cells'].rstrip('0')


def items(tape):
    """tape (from the head, ends with 1) -> (leading zeros, [(k, g)]) with item (k, g) = ('10')*k + '1' + '0'*g"""
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
    """greedy run-length compression with blocks of 1..4 items; returns [(block tuple, count)]"""
    out, i, n = [], 0, len(its)
    while i < n:
        best = None
        for p in range(1, 5):
            b = tuple(its[i:i + p])
            if len(b) < p: break
            r = 1
            while tuple(its[i + r * p:i + (r + 1) * p]) == b: r += 1
            if r >= MINRUN and (best is None or r * p > best[0] * best[1]):
                best = (r, p)
        if best:
            r, p = best
            out.append((tuple(its[i:i + p]), r)); i += r * p
        else:
            out.append(((its[i],), 1)); i += 1
    return out


def affine(tapes):
    """three checkpoint tapes (x = XS) -> [(cells, c0, c1)] pieces (c1 = 0: concrete) or raise"""
    parsed = [items(t) for t in tapes]
    if len({p[0] for p in parsed}) != 1: raise ValueError('leading zeros differ')
    rs = [rle(p[1]) for p in parsed]
    if len({len(r) for r in rs}) != 1 or any(a[0] != b[0] for a, b in zip(rs[0], rs[1])) or any(a[0] != b[0] for a, b in zip(rs[0], rs[2])):
        raise ValueError('skeletons differ')
    pieces = [('0' * parsed[0][0], 1, 0)] if parsed[0][0] else []
    for (blk, c1), (_, c2), (_, c3) in zip(*rs):
        d = c2 - c1
        if c3 - c2 != d or d % (XS[1] - XS[0]): raise ValueError('run not affine')
        b = d // (XS[1] - XS[0]); a = c1 - b * XS[0]
        if a < 0: raise ValueError('negative constant part')
        pieces.append((''.join(item_cells(it) for it in blk), a, b))
    return pieces


def lit(cells):
    return '[' + ';'.join(cells) + ']'


def orient(cells):
    """0..1 orientation of a block: move the trailing zeros to the front"""
    z = len(cells) - len(cells.rstrip('0'))
    return (cells[len(cells) - z:] + cells[:len(cells) - z]) if z else cells


def side(pieces, defs):
    """Rocq right side for a checkpoint. A symbolic run B^(a + b x) with a >= 1 is written in 0..1 orientation:
    B = U V (V = trailing zeros):  B^(a+bx) = U (V U)^(a-1) ((V U)^b)^^x V."""
    out, conc = [], ''
    for cells, a, b in pieces:
        if b == 0:
            conc += cells * a; continue
        blk = orient(cells)
        if a >= 1 and blk != cells:
            z = len(cells) - len(cells.rstrip('0'))
            conc += cells[:len(cells) - z] + blk * (a - 1)
            tailz = cells[len(cells) - z:]
        else:
            conc += cells * a; blk = cells; tailz = ''
        name = defs.setdefault(blk * b, 'R%d' % len(defs))
        if conc: out.append(lit(conc))
        out.append('(%s^^x)' % name)
        conc = tailz
    if conc.rstrip('0'): out.append(lit(conc.rstrip('0')))
    return ' *> '.join(out + ['0inf'])


def run_instance(key, r, M, target, G):
    fn, tf = TMP + 'lb_%d.txt' % os.getpid(), TMP + 'lb_%d_t.txt' % os.getpid()
    open(fn, 'w').write('0 2 0\n%s\n' % node_tape(key, r, M))
    open(tf, 'w').write(target + '\n')
    out = subprocess.run([EVT, fn, '200000000000', '5000000', tf], capture_output=True, text=True,
                         env=dict(os.environ, EVERY=str(G))).stdout.split('\n')
    if not any(l.startswith('REACHED') for l in out): raise RuntimeError('target not reached')
    cps = []
    for i in range(0, len(out) - 1, 2):
        if out[i].startswith('REACHED'): break
        step, state = map(int, out[i].split())
        assert state == 2
        cps.append(out[i + 1])
    return cps


def generate(bkey, outfile, G=25):
    node = bkey.split(' ## ')[0]; r = int(bkey.split('r=')[1].split()[0]); par = int(bkey.split('par=')[1])
    assert ' || FAM ' not in node, 'family source nodes: not yet'
    B = P['lemmaB'][bkey]; tnode = B['target']
    M0 = MSTAR + ((par - MSTAR) % 2)
    runs = []
    for x in XS:
        M = M0 + 2 * x; xx = (M - 1000 - par) // 2
        ev = lambda c: None if c is None else c[0] + c[1] * xx
        tgt = node_tape(tnode, ev(B['N1']), ev(B['M1']), ev(B['K1']) if ' || FAM ' in tnode else None)
        runs.append(run_instance(node, r, M, tgt, G))
    if len({len(c) for c in runs}) != 1: raise ValueError('checkpoint counts differ: %s' % [len(c) for c in runs])
    starts = [node_tape(node, r, M0 + 2 * x) for x in XS]
    cps = [affine(starts)] + [affine([c[i] for c in runs]) for i in range(len(runs[0]))]
    defs = {}
    sides = [side(p, defs) for p in cps]
    v = ['(* generated by rocq/gen_lemmaB.py: lemma B', '   %s' % bkey.replace('*)', '* )'),
         '   M = %d + 2x, %d checkpoints *)' % (M0, len(cps)),
         'From BusyCoq Require Import Individual62 ES_v3.', 'Require Import Lia String NArith.', 'Open Scope list.', '',
         'Definition tm := Eval compute in (TM_from_str "1RB0RE_1LC0LB_1RD0LB_1RF0LA_1RC---_0RA0LD").',
         """Notation "c -->+ c'" := (c -[ tm ]->+ c') (at level 40).""", '']
    for cells, name in sorted(defs.items(), key=lambda kv: kv[1]):
        v.append('Definition %s : list sym := %s.' % (name, lit(cells)))
    v.append('')
    for i, sd in enumerate(sides):
        v.append('Definition cfg%d x : Q * tape := 0inf {{C}}> %s.' % (i, sd))
    v.append('')
    unf = ', '.join(sorted(defs.values()))
    for i in range(len(sides) - 1):
        v += ['Lemma sub%d x : cfg%d x -->+ cfg%d x.' % (i, i, i + 1),
              "Proof. unfold cfg%d, cfg%d, %s. es' x. Qed." % (i, i + 1, unf), '']
    last = len(sides) - 1
    v += ['Theorem lemmaB x : cfg0 x -->+ cfg%d x.' % last, 'Proof.']
    for i in range(last - 1):
        v.append('  eapply progress_trans; [apply sub%d|].' % i)
    v += ['  apply sub%d.' % (last - 1), 'Qed.']
    open(outfile, 'w').write('\n'.join(v) + '\n')
    return len(cps), defs


if __name__ == '__main__':
    n, defs = generate(sys.argv[1], sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 25)
    print('checkpoints', n, 'run blocks', len(defs))
