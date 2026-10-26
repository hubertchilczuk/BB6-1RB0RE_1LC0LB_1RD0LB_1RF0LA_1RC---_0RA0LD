"""Symbolic BFS prover with k-families.

Node kinds
  concrete context C : canonical zone + explicit T (incl. small k) + u + tail      (variables: N, M)
  family F(park)     : canonical zone + T = '0 4 3^k 2' with k symbolic, parity park (variables: N, M, k)
State = (node, r, parM[, park implied]) at the LAST canonical point (N = r in [r_low, r_low+P)).
Lemma A(node):  (N+P, M[, k]) -> (N, M+dM[, k])           symbolic in N, M (and k)
Lemma B(state): (r, M[, k])   -> first canonical point of the next node, all counts affine in (M[, k]).
Concrete k-contexts with k >= K_fam(family) are covered by the family and are not expanded.
"""
import os, sys, json, subprocess, threading, re, heapq
from concurrent.futures import ThreadPoolExecutor
import gen, gen2

D = gen.D
SSIM = D + 'ssim3.exe'
CANON = D + 'canon_all.txt'
M0, K0, N0 = 1000, 1000, 300
OUT = D + 'proof2.json'
lock = threading.Lock()
proof = json.load(open(OUT)) if os.path.exists(OUT) else {'nodes': {}, 'lemmaA': {}, 'smallA': {}, 'lemmaB': {}}
samples = {}
seq = [0]


def save():
    with lock:
        json.dump(proof, open(OUT, 'w'), indent=1)


def tagof(key):
    import hashlib
    return hashlib.md5(key.encode()).hexdigest()[:8]


def canons():
    return [l.rstrip('\n') for l in open(CANON) if l.strip()]


def run_ssim(base, vars_, insts, tag, maxmacro=30000000):
    outp = D + 'p2_%s' % tag
    v = list(vars_) + ['-'] * (3 - len(vars_))
    args = [SSIM, '20', str(maxmacro), base] + v + [CANON, outp] + ['%d,%d,%d' % tuple(list(i) + [0] * (3 - len(i))) for i in insts]
    out = subprocess.run(args, capture_output=True, text=True).stdout
    res = {'raw': out[-1500:]}
    m = re.search(r'^CANON (.*)$', out, re.M)
    if not m:
        res['status'] = out.strip().splitlines()[-1] if out.strip() else 'NO OUTPUT'
        return res
    res['status'] = 'CANON'
    c = m.group(1)
    res['canon'] = c if c.endswith(' ') else c + ' '
    cm = re.search(r'^CONSTRAINTS(.*)$', out, re.M)
    res['constraints'] = cm.group(1).strip() if cm else ''
    res['files'] = {tuple(i): outp + '_%d_%d_%d.txt' % tuple(list(i) + [0] * (3 - len(i))) for i in insts}
    return res


def bounds(cons, nv=3):
    """sufficient lower bounds b_i for the variables such that all constraints c + sum a_i v_i >= 0 hold."""
    b = [-10 ** 12] * nv
    for t in cons.split():
        m = re.match(r'(-?\d+)' + ''.join(r'([+-]\d+)v%d' % i for i in range(nv)) + r'>=0', t)
        if not m: continue
        c = int(m.group(1)); a = [int(m.group(i + 2)) for i in range(nv)]
        S = sum(x for x in a if x > 0)
        if S == 0: continue
        need = -(c // S)  # ceil(-c/S)
        for i in range(nv):
            if a[i] > 0: b[i] = max(b[i], need)
    return b


def discover(cfg, tag):
    import findcanon
    ev = D + 'p2_%s_ev.txt' % tag
    with open(ev, 'w') as f:
        subprocess.run([D + 'fsim2.exe', '20', '2e12', cfg, '-', '-', 'events'], stdout=f, env=dict(os.environ, RUNS='1'))
    with lock:
        known = set(canons())
        cands = findcanon.candidates(ev, known)
        for w, n, top, z in cands:
            open(CANON, 'a').write(z + '\n')
            print('NEWCANON [%s] %s' % (w, z), flush=True)
    return len(cands)


def classify(fn, canon):
    """returns (st, concrete key, family key or None)."""
    rt, st = gen2.exact_roundtrip(fn, canon)
    if not rt: raise ValueError('roundtrip failed ' + fn)
    fk = gen2.key(canon, st, True) if st['k'] is not None else None
    return st, gen2.key(canon, st, False), fk


def is_family(key): return ' || FAM ' in key


# ---------------- lemmas ----------------
def build(node, N, M, k, fn):
    st = samples[node]
    gen2.rebuild(st, N, M, fn, k if is_family(node) else None)


def lemmaA(node):
    if node in proof['lemmaA']: return proof['lemmaA'][node]
    fam = is_family(node); st = samples[node]; canon = node.split(' || ')[0]
    tag = 'A' + tagof(node); park = st['k'] % 2 if fam else 0
    kk = K0 + park if fam else None
    f = [D + 'p2_%s_%s.txt' % (tag, q) for q in 'abcd']
    build(node, N0, M0, kk, f[0]); build(node, N0 + 1, M0, kk, f[1]); build(node, N0, M0 + 2, kk, f[2])
    vars_ = [f[1], f[2]]
    if fam: build(node, N0, M0, kk + 2, f[3]); vars_.append(f[3])
    insts = [(0, 0, 0), (1, 0, 0), (0, 1, 0), (3, 2, 1 if fam else 0)]
    res = run_ssim(f[0], vars_, insts, tag)
    rec = {'status': res['status']}
    if res['status'] == 'CANON' and res['canon'] == canon:
        ok = True
        vals = {}
        for i, fn in res['files'].items():
            st2, ck2, fk2 = classify(fn, canon)
            if (fk2 if fam else ck2) != node: ok = False; rec['why'] = 'node changed'; break
            vals[i] = (st2['N'], st2['M'], st2['k'])
        if ok:
            n0, m0, k0 = vals[(0, 0, 0)]
            Pp = N0 - n0; dM = m0 - M0
            lin = all(vals[(x, y, z)] == (N0 + x - Pp, M0 + 2 * y + dM, (kk + 2 * z) if fam else k0) for (x, y, z) in vals)
            b = bounds(res['constraints'])
            rec.update(P=Pp, dM=dM, linear=lin, constraints=res['constraints'], Nmin=N0 + b[0], Mmin=M0 + 2 * b[1],
                       Kmin=(kk + 2 * b[2]) if fam else None)
            rec['status'] = 'OK' if lin else 'NONLINEAR'
    elif res['status'] == 'CANON':
        rec['status'] = 'OTHER-CANON'
    else:
        rec['raw'] = res['raw'][-400:]
    with lock: proof['lemmaA'][node] = rec
    print('LEMMA A', node[:110], rec['status'], rec.get('P'), rec.get('dM'), rec.get('Nmin'), rec.get('Mmin'), rec.get('Kmin'), flush=True)
    save()
    return rec


def samples_N(res, canon): return 0


def smallA(node, N, par, Pp, dM):
    key = '%s ## N=%d par=%d' % (node, N, par)
    if key in proof['smallA']: return proof['smallA'][key]
    fam = is_family(node); st = samples[node]; canon = node.split(' || ')[0]
    park = st['k'] % 2 if fam else 0; kk = K0 + park if fam else None
    tag = 'S' + tagof(key)
    f = [D + 'p2_%s_%s.txt' % (tag, q) for q in 'abc']
    build(node, N, M0 + par, kk, f[0]); build(node, N, M0 + par + 2, kk, f[1]); vars_ = [f[1]]
    if fam: build(node, N, M0 + par, kk + 2, f[2]); vars_.append(f[2])
    insts = [(0, 0), (1, 0), (2, 3)] if fam else [(0,), (1,), (5,)]
    res = run_ssim(f[0], vars_, insts, tag)
    ok = res['status'] == 'CANON' and res['canon'] == canon
    if ok:
        for i, fn in res['files'].items():
            st2, ck2, fk2 = classify(fn, canon)
            x = i[0]; z = i[1] if fam else 0
            if (fk2 if fam else ck2) != node or st2['N'] != N - Pp or st2['M'] != M0 + par + 2 * x + dM or (fam and st2['k'] != kk + 2 * z):
                ok = False
    b = bounds(res.get('constraints', ''))
    rec = {'ok': ok, 'status': res['status'], 'Mmin': M0 + par + 2 * b[0] if ok else None, 'Kmin': (kk + 2 * b[1]) if (ok and fam) else None}
    with lock: proof['smallA'][key] = rec
    return rec


def lemmaB(node, r, par):
    key = '%s ## r=%d par=%d' % (node, r, par)
    if key in proof['lemmaB'] and proof['lemmaB'][key]['status'] == 'OK':
        rec = proof['lemmaB'][key]
        with lock:
            for t, fn in rec.get('targets_files', {}).items():
                if t not in samples and os.path.exists(fn):
                    samples[t] = classify(fn, t.split(' || ')[0])[0]
        return rec
    fam = is_family(node); st = samples[node]; canon = node.split(' || ')[0]
    park = st['k'] % 2 if fam else 0; kk = K0 + park if fam else None
    tag = 'B' + tagof(key)
    f = [D + 'p2_%s_%s.txt' % (tag, q) for q in 'abc']
    build(node, r, M0 + par, kk, f[0]); build(node, r, M0 + par + 2, kk, f[1]); vars_ = [f[1]]
    if fam: build(node, r, M0 + par, kk + 2, f[2]); vars_.append(f[2])
    insts = [(0, 0), (1, 0), (0, 1), (2, 3), (5, 1)] if fam else [(0,), (1,), (2,), (7,)]
    for attempt in range(4):
        nc = len(canons())
        res = run_ssim(f[0], vars_, insts, tag)
        if res['status'] == 'CANON' or not res['status'].startswith('LIMIT'): break
        discover(f[0], tag)
        if len(canons()) == nc: break
    rec = {'status': res['status']}
    if res['status'] == 'CANON':
        c2 = res['canon']; vals = {}; keys = set(); fkeys = set(); ok = True
        try:
            for i, fn in res['files'].items():
                st2, ck2, fk2 = classify(fn, c2)
                vals[i] = (st2['N'], st2['M'], st2['k']); keys.add(ck2); fkeys.add(fk2); last = (st2, ck2, fk2, fn)
        except Exception as e:
            ok = False; rec['why'] = str(e)[:200]
        if ok:
            # target node: concrete if the explicit context is the same for all instances, else family
            if len(keys) == 1:
                tnode = keys.pop()
            elif len(fkeys) == 1 and None not in fkeys:
                tnode = fkeys.pop()
            else:
                ok = False; rec['why'] = 'target varies: %d keys' % len(keys)
        if ok:
            def aff(j):
                base = vals[insts[0]][j]
                if base is None: return None
                cx = vals[insts[1]][j] - base
                cy = (vals[insts[2]][j] - base) if fam else 0
                good = all(vals[i][j] == base + cx * i[0] + (cy * i[1] if fam else 0) for i in insts)
                return [base, cx, cy] if good else 'NONAFFINE'
            N1, M1, K1 = aff(0), aff(1), aff(2)
            if 'NONAFFINE' in (N1, M1, K1): ok = False; rec['why'] = 'non-affine'
        if ok:
            b = bounds(res['constraints'])
            rec.update(status='OK', target=tnode, N1=N1, M1=M1, K1=K1, constraints=res['constraints'],
                       Mmin=M0 + par + 2 * b[0], Kmin=(kk + 2 * b[1]) if fam else None)
            # cross-check one instance with the concrete simulator
            i = insts[-1]; xs = i[0]; ys = i[1] if fam else 0
            build(node, r, M0 + par + 2 * xs, (kk + 2 * ys) if fam else None, D + 'p2_%s_cx.txt' % tag)
            subprocess.run([D + 'fsim.exe', '20', '1e15', D + 'p2_%s_cx.txt' % tag, CANON, D + 'p2_%s_cxo.txt' % tag], capture_output=True)
            a = open(D + 'p2_%s_cxo.txt' % tag).read().split(); bb = open(res['files'][i]).read().split()
            rec['crosscheck'] = (a[1], a[2], a[3].rstrip('0')) == (bb[1], bb[2], bb[3].rstrip('0'))
            if not rec['crosscheck']: rec['status'] = 'XCFAIL'
            rec['targets_files'] = {tnode: last[3]}
            with lock:
                if tnode not in samples: samples[tnode] = last[0]
        else:
            rec['status'] = 'BAD'
    else:
        rec['raw'] = res['raw'][-400:]
    with lock: proof['lemmaB'][key] = rec
    print('B', node[:60], r, par, rec['status'], rec.get('N1'), rec.get('M1'), rec.get('K1'), (rec.get('target') or '')[-40:], flush=True)
    return rec


# ---------------- BFS ----------------
def family_of(node):
    """for a concrete k-context, the family key (or None)."""
    st = samples[node]
    if st['k'] is None: return None
    return gen2.key(node.split(' || ')[0], st, True)


def process(node, workers):
    A = lemmaA(node)
    if A['status'] != 'OK': return []
    Pp, dM = A['P'], A['dM']
    small = [(N, par) for N in range(Pp, max(Pp, A['Nmin'])) for par in (0, 1)]
    with ThreadPoolExecutor(workers) as ex:
        srec = list(ex.map(lambda a: smallA(node, a[0], a[1], Pp, dM), small))
    okN = {}
    for (N, par), s_ in zip(small, srec): okN[N] = okN.get(N, True) and s_['ok']
    r_low = max(0, A['Nmin'] - Pp)
    for N in sorted(okN, reverse=True):
        if okN[N]: r_low = N - Pp
        else: break
    proof['nodes'][node] = {'P': Pp, 'dM': dM, 'r_low': r_low, 'family': is_family(node)}
    jobs = [(r, par) for r in range(r_low, r_low + Pp) for par in (0, 1)]
    with ThreadPoolExecutor(workers) as ex:
        recs = list(ex.map(lambda j: lemmaB(node, j[0], j[1]), jobs))
    if is_family(node):
        km = [A.get('Kmin') or 0] + [x['Kmin'] for x in recs if x.get('Kmin') is not None] + [s_['Kmin'] for s_ in srec if s_.get('Kmin') is not None]
        proof['nodes'][node]['K_fam'] = max(km)
    save()
    return [x['target'] for x in recs if x['status'] == 'OK']


def family_A_threshold(fam):
    """k needed for the family's lemma A and small-N checks (for the parity of the family)."""
    A = proof['lemmaA'][fam]
    ks = [A.get('Kmin') or 0] + [s['Kmin'] for kk, s in proof['smallA'].items() if kk.startswith(fam + ' ##') and s.get('Kmin') is not None]
    return max(ks)


def process_partial(node, fam, workers):
    """concrete k-context with k >= family lemma-A threshold: reuse family lemmas where k >= their Kmin."""
    fi = proof['nodes'][fam]; k = samples[node]['k']
    Pp, rl = fi['P'], fi['r_low']
    jobs = []; covered = 0; targets = []
    for r in range(rl, rl + Pp):
        for par in (0, 1):
            FB = proof['lemmaB'].get('%s ## r=%d par=%d' % (fam, r, par))
            if FB and FB['status'] == 'OK' and FB.get('crosscheck') and FB['Kmin'] <= k:
                covered += 1; targets.append(FB['target'])
            else:
                jobs.append((r, par))
    with ThreadPoolExecutor(workers) as ex:
        recs = list(ex.map(lambda j: lemmaB(node, j[0], j[1]), jobs))
    proof['nodes'][node] = {'partial_of': fam, 'P': Pp, 'dM': fi['dM'], 'r_low': rl, 'family': False, 'k': k,
                            'concrete_states': [list(j) for j in jobs]}
    print('  partial node k=%d: %d states covered by family, %d concrete' % (k, covered, len(jobs)), flush=True)
    save()
    return targets + [x['target'] for x in recs if x['status'] == 'OK']


def bfs(start_fn, start_canon, workers):
    st, ck, fk = classify(start_fn, start_canon)
    samples[ck] = st
    pq = [(1, 0, ck)]; done = set()
    while pq:
        pri, _, node = heapq.heappop(pq)
        if node in done: continue
        if node not in samples: continue
        if not is_family(node):
            fam = family_of(node)
            if fam is not None:
                if fam not in done:
                    if fam not in samples:
                        samples[fam] = samples[node]
                    seq[0] += 1; heapq.heappush(pq, (0, seq[0], fam))
                    seq[0] += 1; heapq.heappush(pq, (1, seq[0], node))   # retry after the family
                    continue
                kf = proof['nodes'].get(fam, {}).get('K_fam')
                if kf is not None and samples[node]['k'] >= kf:
                    done.add(node); proof['nodes'][node] = {'covered_by': fam}; continue
                if fam in proof['nodes'] and 'P' in proof['nodes'][fam] and samples[node]['k'] >= family_A_threshold(fam):
                    done.add(node)
                    targets = process_partial(node, fam, workers)
                    for t in targets:
                        if t not in done:
                            seq[0] += 1; heapq.heappush(pq, (0 if is_family(t) else 1, seq[0], t))
                    print('=== done %d, queue %d' % (len(done), len(pq)), flush=True)
                    continue
        done.add(node)
        targets = process(node, workers)
        for t in targets:
            if t not in done:
                seq[0] += 1; heapq.heappush(pq, (0 if is_family(t) else 1, seq[0], t))
        print('=== done %d, queue %d' % (len(done), len(pq)), flush=True)
    save()


if __name__ == '__main__':
    bfs(D + 's_226258280.txt', '1 7 0 0* 4 3 0 0 0 0 0 9 | 8 ', int(sys.argv[1]) if len(sys.argv) > 1 else 6)
    print('FINISHED', flush=True)
