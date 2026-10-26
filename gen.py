"""Generic structure parsing / surgery / transition running for the BB6 machine study."""
import subprocess, os, json, sys
import surg

D = os.path.dirname(os.path.abspath(__file__)) + os.sep
FSIM = D + 'fsim.exe'
LAST_RUN = False   # gen2 sets True: u = last long run (the M-run)


def load(fn):
    a = open(fn).read().split()
    return int(a[0]), int(a[1]), int(a[2]), a[3]


def parse_struct(fn, canon):
    """Split config at canonical point into zone | w^N | T | u^M | tail (cell strings)."""
    step, s, off, cells = load(fn)
    assert off == 0, "expected head at leftmost cell"
    pre, items, tail = surg.parse(cells)
    names = [x[0] for x in items]
    zpart, wpart = canon.split('|')
    zone = zpart.split()
    word = wpart.split()
    k, p = len(zone), len(word)
    assert names[:k] == zone, (names[:k], zone)
    N = 0
    while names[k + N * p:k + (N + 1) * p] == word:
        N += 1
    e = k + N * p
    # second run
    # greedy run decomposition after e; pick the run with the largest repetition count
    best = None
    f = e
    while f < len(names):
        loc = None
        for q in range(1, 5):
            u = names[f:f + q]
            if len(u) < q:
                break
            r = 1
            while names[f + r * q:f + (r + 1) * q] == u:
                r += 1
            if r >= 4 and (loc is None or r * q > loc[1] * loc[2]):
                loc = (f, q, r)
        if loc:
            if best is None or loc[2] > best[2] or LAST_RUN:
                best = loc
            f += loc[1] * loc[2]
        else:
            f += 1
    if best is None:
        f, q, M = len(names), 0, 0
    else:
        f, q, M = best
    span = lambda a, b: cells[items[a][1]:items[b - 1][2]] if b > a else ''
    st = dict(step=step, state=s,
              zone_cells=pre + span(0, k), w=word, w_cells=span(k, k + p), N=N,
              T=names[e:f], T_cells=span(e, f), u=names[f:f + q], u_cells=span(f, f + q) if q else '', M=M,
              tail=names[f + q * M:], tail_cells=(cells[items[f + q * M][1]:] if f + q * M < len(items) else tail))
    return st


def rebuild(st, N, M, out):
    c = st['zone_cells'] + st['w_cells'] * N + st['T_cells'] + st['u_cells'] * M + st['tail_cells']
    open(out, 'w').write('%d %d %d\n%s\n' % (st['step'], st['state'], 0, c))


def run_to_canon(cfg, canonfile, outcfg, maxsteps=1e14):
    r = subprocess.run([FSIM, '20', '%g' % maxsteps, cfg, canonfile, outcfg], capture_output=True, text=True)
    out = r.stdout.strip().splitlines()
    for l in out:
        if l.startswith('CANON'):
            return 'CANON', l[6:] + ' ' if not l.endswith(' ') else l[6:], out
        if l.startswith('HALT'):
            return 'HALT', None, out
    return 'LIMIT', None, out


def ctx_key(st):
    import hashlib
    zh = hashlib.md5((str(st['state']) + ':' + st['zone_cells'] + ':' + st['w_cells'] + ':' + st['T_cells'] + ':' + st['u_cells'] + ':' + st['tail_cells'].rstrip('0')).encode()).hexdigest()[:10]
    return (' '.join(st['w']), ' '.join(st['T']), ' '.join(st['u']), ' '.join(st['tail']), zh)
