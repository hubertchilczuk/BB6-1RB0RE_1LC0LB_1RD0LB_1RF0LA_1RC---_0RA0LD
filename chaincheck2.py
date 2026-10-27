"""Concrete end-to-end checks of the proof with fsim (replaces chaincheck.py).

chaincheck.py built the concrete configuration of every predicted chain state; M grows ~9x per cycle,
so the 3rd-6th cycles needed 10^8-10^9-cell tapes (3 GB input, >4 GB output). Here every concrete
configuration is bounded by MAXCELLS, and two kinds of checks are run:

1. trajectory: the real machine, from the start configuration (226258281 steps from the blank tape,
   see start_check.c), canonical point by canonical point; every point must be exactly the one the
   lemmas predict (lemma A steps (N, M) -> (N - P, M + dM), lemma B landings, verify4 cycle results);
2. random cycles: random domain states (all reachable nodes, all r, both parities of M, M spread over
   residues mod 2P, random family k) with small M; each full cycle (lemma B + whole lemma-A descent)
   is run concretely and compared with the prediction of verify4.step.
"""
import os, sys, random, subprocess, threading, io, contextlib
from concurrent.futures import ThreadPoolExecutor
import prover2 as P2
import gen
import verify4 as V

D = P2.D
CANON = P2.CANON
TMP = D + 'cc_tmp/'
os.makedirs(TMP, exist_ok=True)
MAXCELLS = 3 * 10 ** 6
NCYCLES = int(sys.argv[1]) if len(sys.argv) > 1 else 3000
lock = threading.Lock()

# samples (structure templates) of all nodes: lemma-B target files, the start config, family members
import samples
samples.load()
START_FILE = samples.START_FILE


def cells(t, N, M, k):
    s = P2.samples[t]
    T = len(s['T_cells']) if k is None or not P2.is_family(t) else len(s['kh']) + k * len(s['k3']) + len(s['kl'])
    return len(s['zone_cells']) + N * len(s['w_cells']) + T + M * len(s['u_cells']) + len(s['tail_cells'])


def run(cfg, out):
    """fsim to the next canonical point; returns (node candidates, N, M, k) or a string on failure"""
    status, z, lines = gen.run_to_canon(cfg, CANON, out, 1e15)
    if status != 'CANON': return status
    st2, ck2, fk2 = P2.classify(out, z)
    return {V.resolve(ck2), ck2, fk2}, st2['N'], st2['M'], st2['k']


def kconst(k):
    return None if k is None else (k, 0, 0)


def predict(t, r, M, k):
    """verify4 prediction for one concrete state: lemma-B landing (t2, n1, m1, k1) and cycle end (t2, r2, M2)"""
    S = (t, r, (M, 0, 0), kconst(k) if V.nodes[t].get('family') or 'partial_of' in V.nodes[t] else None)
    src, B = V.lemmaB_for(t, r, M % 2)
    x = ((M - V.M0 - M % 2) // 2, 0, 0)
    y = V.kvar(src, S[3])
    n1, m1 = V.aff_eval(B['N1'], x, y)[0], V.aff_eval(B['M1'], x, y)[0]
    k1 = V.aff_eval(B['K1'], x, y)[0] if B['K1'] is not None else None
    nerr = len(V.errs)
    land = V.step(S, ('cc',))
    if land is None or len(V.errs) > nerr: return None
    t2, r2, M2, k2 = land
    return (t2, n1, m1, k1), (t2, r2, M2[0], None if k2 is None else k2[0])


def cycle(t, r, M, k, tag, cfg=None):
    """run one cycle concretely from (t, r, M, k) (built from the sample unless cfg is given).
    returns (ok, message, end state, end file)"""
    with lock:
        pr = predict(t, r, M, k)
    if pr is None: return False, 'verify4 has no prediction', None, None
    (t2, n1, m1, k1), (_, r2, M2, k2) = pr
    ti = V.nodes[t2]
    Pp, dM, rl = ti['P'], ti['dM'], ti['r_low']
    if cells(t, r, M, k) > MAXCELLS or cells(t2, n1, m1 + ((n1 - rl) // Pp) * dM, k1) > MAXCELLS:
        return None, 'too large', None, None
    files = [TMP + '%s_%d.txt' % (tag, i) for i in range(2)]
    if cfg is None:
        P2.build(t, r, M, k, files[0]); cfg = files[0]
    res = run(cfg, files[1])
    if isinstance(res, str): return False, 'lemma B run: ' + res, None, None
    nodes_, N, Mc, kc = res
    if t2 not in nodes_ or (N, Mc) != (n1, m1) or (k1 is not None and kc != k1):
        return False, 'lemma B landing differs: got N=%d M=%d k=%s, lemma says N=%d M=%d k=%s' % (N, Mc, kc, n1, m1, k1), None, None
    cur = 1
    while N >= rl + Pp:                                    # lemma-A descent, one canonical point at a time
        res = run(files[cur], files[1 - cur]); cur = 1 - cur
        if isinstance(res, str): return False, 'lemma A run: ' + res, None, None
        nodes2, N2, M2c, k2c = res
        if t2 not in nodes2 or (N2, M2c, k2c) != (N - Pp, Mc + dM, kc):
            return False, 'lemma A step differs at N=%d M=%d: got N=%d M=%d' % (N, Mc, N2, M2c), None, None
        N, Mc = N2, M2c
    if (N, Mc) != (r2, M2):
        return False, 'cycle end differs: got (%d, %d), verify4 says (%d, %d)' % (N, Mc, r2, M2), None, None
    return True, 'ok', (t2, N, Mc, kc), files[cur]


def trajectory():
    """the real machine from the start configuration, as far as MAXCELLS allows"""
    t = V.start
    print('trajectory: start node, N=224, M=2045 (step 226258281 from the blank tape)', flush=True)
    # start descent with lemma A, run concretely from the actual start file
    ti = V.nodes[t]; N, M = 224, 2045
    cur, files = START_FILE, [TMP + 'traj_%d.txt' % i for i in range(2)]
    i = 0
    while N >= ti['r_low'] + ti['P']:
        res = run(cur, files[i % 2]); cur = files[i % 2]; i += 1
        nodes_, N2, M2, k2 = res
        if t not in nodes_ or (N2, M2) != (N - ti['P'], M + ti['dM']):
            print('  START DESCENT MISMATCH', N2, M2); return False
        N, M = N2, M2
    print('  start descent concretely -> (N, M) = (%d, %d)  [verify4: (24, 5533)]' % (N, M), flush=True)
    if (N, M) != (24, 5533): return False
    k = None; c = 0
    while True:
        tag = 'trajc%d' % c
        ok, msg, end, endfile = cycle(t, N, M, k, tag, cfg=cur)
        if ok is None:
            print('  cycle %d from (N=%d, M=%d): next configuration exceeds %d cells, stopping' % (c, N, M, MAXCELLS)); return True
        if not ok:
            print('  cycle %d from (N=%d, M=%d): MISMATCH: %s' % (c, N, M, msg)); return False
        t2, N2, M2, k2 = end
        print('  cycle %d: (N=%d, M=%d) -> node %s.. (N=%d, M=%d) as predicted' % (c, N, M, t2[:30], N2, M2), flush=True)
        t, N, M, k, cur, c = t2, N2, M2, k2, endfile, c + 1


def random_cycles():
    random.seed(2026)
    with contextlib.redirect_stdout(io.StringIO()):
        V.main()                                           # computes V.reach
    if V.errs: print('verify4 reported errors, aborting'); return False
    states = [(t, r, par) for t in sorted(V.reach) for r in range(V.nodes[t]['r_low'], V.nodes[t]['r_low'] + V.nodes[t]['P']) for par in (0, 1)]
    jobs = []
    for i, (t, r, par) in enumerate(random.sample(states, min(NCYCLES, len(states)))):
        ti = V.nodes[t]
        Mw = V.MSTAR + ((par - V.MSTAR) % 2)
        M = Mw + 2 * random.randrange(0, 2 * ti['P'])
        kd = V.domain_k(t)
        k = None if kd is None else kd[0] + kd[2] * random.randrange(0, 6)
        jobs.append((t, r, M, k, 'rc%d' % i))
    res = {'ok': 0, 'skip': 0, 'bad': []}

    def one(j):
        try:
            ok, msg, _, _ = cycle(*j)
        except Exception as e:
            ok, msg = False, 'exception %r' % (e,)
        with lock:
            if ok: res['ok'] += 1
            elif ok is None: res['skip'] += 1
            else: res['bad'].append((j[0][:60], j[1], j[2], j[3], msg))
            n = res['ok'] + res['skip'] + len(res['bad'])
            if n % 250 == 0: print('  random cycles: %d/%d done, %d mismatches' % (n, len(jobs), len(res['bad'])), flush=True)
        for f in os.listdir(TMP):
            if f.startswith(j[4] + '_'): os.remove(TMP + f)

    with ThreadPoolExecutor(6) as ex: list(ex.map(one, jobs))
    print('random cycles: %d checked, %d ok, %d skipped (too large), %d mismatches' % (len(jobs), res['ok'], res['skip'], len(res['bad'])))
    for b in res['bad'][:20]: print('  ', b)
    return not res['bad']


if __name__ == '__main__':
    a = trajectory()
    b = random_cycles()
    print('CHAINCHECK2', 'OK' if a and b else 'FAILED')
