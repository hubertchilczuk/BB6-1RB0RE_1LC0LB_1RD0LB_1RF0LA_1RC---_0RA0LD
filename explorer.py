"""BFS over (regime, context) transition cases.
A context = (canonical zone string, T, u, tail). For each context we measure the period P (blocks of w)
and dM per period, then for every residue r in [0,P) and parity of M we run the transition from the
LAST canonical point (N=r) to the next canonical point of any regime, recording the outcome."""
import json, os, sys, itertools, threading
from concurrent.futures import ThreadPoolExecutor
import gen

D = gen.D
CANON = D + 'canon_all.txt'
canons = [l.rstrip('\n') for l in open(CANON) if l.strip()]
RES = D + 'explore_results.json'
lock = threading.Lock()
results = json.load(open(RES)) if os.path.exists(RES) else {'contexts': {}, 'cases': {}}


def key_str(canon, st):
    return canon + ' || ' + ' / '.join(gen.ctx_key(st)[1:])


def save():
    with lock:
        json.dump(results, open(RES, 'w'), indent=1)


def run_case(st, N, M, tag, maxsteps=3e13):
    cfg = D + 'tmp_in_%s.txt' % tag
    out = D + 'tmp_out_%s.txt' % tag
    gen.rebuild(st, N, M, cfg)
    status, canon, lines = gen.run_to_canon(cfg, CANON, out, maxsteps)
    if status != 'CANON':
        return status, None, None
    st2 = gen.parse_struct(out, canon)
    return status, canon, st2


def measure(canon, st, tag):
    """period P and dM: start with N large, run to next canonical point."""
    N0 = 400
    status, c2, st2 = run_case(st, N0, 1000, tag)
    if status != 'CANON' or c2 != canon or gen.ctx_key(st2) != gen.ctx_key(st):
        return None, (status, c2, gen.ctx_key(st2) if st2 else None)
    return N0 - st2['N'], st2['M'] - 1000


def explore(canon, st, M0=1000, workers=5):
    k = key_str(canon, st)
    if k in results['contexts']:
        return
    P, dM = measure(canon, st, 'm')
    if P is None:
        print('BADCTX', k, dM, flush=True)
        results['contexts'][k] = dict(bad=str(dM)); save(); return
    print('CONTEXT', k, 'P=%d dM=%d' % (P, dM), flush=True)
    results['contexts'][k] = dict(P=P, dM=dM)
    save()
    new = []

    def job(args):
        r, par = args
        tag = '%d_%d_%d' % (abs(hash(k)) % 10000, r, par)
        status, c2, st2 = run_case(st, r, M0 + par, tag)
        rec = dict(status=status)
        if status == 'CANON':
            rec.update(canon=c2, ctx=list(gen.ctx_key(st2)), N1=st2['N'], M1=st2['M'])
            k2 = key_str(c2, st2)
            if k2 not in results['contexts']:
                new.append((c2, st2))
        with lock:
            results['cases']['%s ## r=%d par=%d' % (k, r, par)] = rec
        print(r, par, rec, flush=True)
        return rec

    with ThreadPoolExecutor(workers) as ex:
        list(ex.map(job, [(r, par) for r in range(P) for par in (0, 1)]))
    save()
    seen = set()
    for c2, st2 in new:
        k2 = key_str(c2, st2)
        if k2 in seen or k2 in results['contexts']:
            continue
        seen.add(k2)
        explore(c2, st2, M0, workers)


if __name__ == '__main__':
    fn, canon = sys.argv[1], sys.argv[2]
    st = gen.parse_struct(D + fn, canon)
    explore(canon, st)
    print('DONE contexts:', len(results['contexts']), 'cases:', len(results['cases']))
    bad = {k: v for k, v in results['cases'].items() if v['status'] != 'CANON'}
    print('non-canonical outcomes:', len(bad))
    for k, v in list(bad.items())[:20]:
        print('  ', k, v)
