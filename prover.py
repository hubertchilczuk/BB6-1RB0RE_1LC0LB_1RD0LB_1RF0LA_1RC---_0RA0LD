"""Symbolic BFS prover.
Abstract state: (context, r, par)  -- canonical point of `context` with front count N=r (0<=r<P)
and M = M0 + par + 2x (x symbolic).  Context = (canonical zone string, T, u, tail) with concrete T.
Lemma A(context): (N+P, M) -> (N, M+dM), proven with N, M symbolic.
Lemma B(state):   (r, M) -> canonical point of some context with N1, M1 affine in x.
All results are produced by ssim (symbolic simulation) and cross-checked by fsim on an instance."""
import os, sys, json, subprocess, threading, re
from concurrent.futures import ThreadPoolExecutor
import gen

D = gen.D
SSIM = D + 'ssim.exe'
CANON = D + 'canon_all.txt'
M0 = 1000
OUT = D + 'proof.json'
lock = threading.Lock()
proof = json.load(open(OUT)) if os.path.exists(OUT) and '--resume' in sys.argv else {'contexts': {}, 'lemmaA': {}, 'lemmaB': {}, 'problems': []}
samples = {}   # ctxkey -> struct sample


def ctxkey(canon, st):
    return canon + ' || ' + ' / '.join(gen.ctx_key(st)[1:])


def save():
    with lock:
        json.dump(proof, open(OUT, 'w'), indent=1)


def run_ssim(cfgs, insts, tag, maxmacro=30000000):
    outp = D + 'pv_%s' % tag
    args = [SSIM, '20', str(maxmacro)] + cfgs + [CANON, outp] + ['%d,%d' % xy for xy in insts]
    r = subprocess.run(args, capture_output=True, text=True)
    out = r.stdout
    res = {'raw': out[-2000:]}
    m = re.search(r'^CANON (.*)$', out, re.M)
    if not m:
        status = out.strip().splitlines()[-1] if out.strip() else 'NO OUTPUT rc=%d' % r.returncode
        res['status'] = status
        return res
    res['status'] = 'CANON'
    res['canon'] = m.group(1) + ' ' if not m.group(1).endswith(' ') else m.group(1)
    cm = re.search(r'^CONSTRAINTS(.*)$', out, re.M)
    res['constraints'] = cm.group(1).strip() if cm else ''
    res['files'] = {xy: outp + '_%d_%d.txt' % xy for xy in insts}
    return res


def exact_roundtrip(fn, canon):
    st = gen.parse_struct(fn, canon)
    gen.rebuild(st, st['N'], st['M'], fn + '.rt')
    a = open(fn).read().split(); b = open(fn + '.rt').read().split()
    return a[1:] == b[1:], st


def xmin_from(cons, var):
    """constraints 'c+ax+by>=0' -> lower bound on var (other var assumed 0 if absent)."""
    lb = -10 ** 18
    for t in cons.split():
        m = re.match(r'(-?\d+)([+-]\d+)x([+-]\d+)y>=0', t)
        if not m: continue
        c, a, b = map(int, m.groups())
        if var == 'x' and a > 0 and b == 0: lb = max(lb, -(c // a))
        if var == 'y' and b > 0 and a == 0: lb = max(lb, -(c // b))
        if a > 0 and b > 0: lb = max(lb, -(c // (a + b)))  # crude: both vars >= bound
    return lb


def lemmaA(ck):
    if ck in proof['lemmaA']: return proof['lemmaA'][ck]
    st = samples[ck]; canon = ck.split(' || ')[0]
    N0 = 300
    tag = 'A%d' % (abs(hash(ck)) % 100000)
    fa, fb, fc = [D + 'pvA_%s_%s.txt' % (tag, q) for q in 'abc']
    gen.rebuild(st, N0, M0, fa); gen.rebuild(st, N0 + 1, M0, fb); gen.rebuild(st, N0, M0 + 2, fc)
    res = run_ssim([fa, fb, fc], [(0, 0), (1, 0), (0, 1), (5, 3)], tag)
    rec = {'status': res['status']}
    if res['status'] == 'CANON':
        if res['canon'] != canon:
            rec['status'] = 'OTHER-CANON'; rec['canon'] = res['canon']
        else:
            vals = {}
            ok = True
            for xy, fn in res['files'].items():
                rt, s2 = exact_roundtrip(fn, canon)
                if not rt or ctxkey(canon, s2) != ck: ok = False; rec['why'] = 'roundtrip/ctx'; break
                vals[xy] = (s2['N'], s2['M'])
            if ok:
                P = N0 - vals[(0, 0)][0]; dM = vals[(0, 0)][1] - M0
                lin = all(vals[(x, y)] == (N0 + x - P, M0 + 2 * y + dM) for (x, y) in vals)
                rec.update(P=P, dM=dM, linear=lin, constraints=res['constraints'],
                           Nmin=N0 + xmin_from(res['constraints'], 'x'), Mmin=M0 + 2 * xmin_from(res['constraints'], 'y'))
                if not lin: rec['status'] = 'NONLINEAR'
    else:
        rec['raw'] = res['raw'][-600:]
    with lock: proof['lemmaA'][ck] = rec
    print('LEMMA A', ck[:70], rec.get('status'), rec.get('P'), rec.get('dM'), rec.get('Nmin'), rec.get('Mmin'), flush=True)
    save()
    return rec


def lemmaAsmall(ck, N, par, P, dM):
    """(N, M) -> (N-P, M+dM) for concrete N in [P, Nmin), M symbolic of parity par."""
    key = '%s ## N=%d par=%d' % (ck, N, par)
    if key in proof.setdefault('lemmaAsmall', {}): return proof['lemmaAsmall'][key]
    st = samples[ck]; canon = ck.split(' || ')[0]
    tag = 'S%d_%d_%d' % (abs(hash(ck)) % 100000, N, par)
    fa, fb = D + 'pv_%s_a.txt' % tag, D + 'pv_%s_b.txt' % tag
    gen.rebuild(st, N, M0 + par, fa); gen.rebuild(st, N, M0 + par + 2, fb)
    res = run_ssim([fa, fb, '-'], [(0, 0), (1, 0), (7, 0)], tag)
    ok = res['status'] == 'CANON' and res['canon'] == canon
    if ok:
        for xy, fn in res['files'].items():
            rt, s2 = exact_roundtrip(fn, canon)
            if not (rt and ctxkey(canon, s2) == ck and s2['N'] == N - P and s2['M'] == M0 + par + 2 * xy[0] + dM):
                ok = False
    rec = {'ok': ok, 'status': res['status'], 'constraints': res.get('constraints', ''),
           'Mmin': M0 + par + 2 * xmin_from(res.get('constraints', ''), 'x') if ok else None}
    with lock: proof['lemmaAsmall'][key] = rec
    return rec


def discover(cfg, tag):
    """concrete run with event log; add new canonical zone strings for long phases."""
    import findcanon
    ev = D + 'pv_%s_ev.txt' % tag
    env = dict(os.environ, RUNS='1')
    with open(ev, 'w') as f:
        subprocess.run([D + 'fsim2.exe', '20', '2e12', cfg, '-', '-', 'events'], stdout=f, env=env)
    with lock:
        known = set(l.rstrip('\n') for l in open(CANON) if l.strip())
        cands = findcanon.candidates(ev, known)
        for w, n, top, z in cands:
            open(CANON, 'a').write(z + '\n'); known.add(z)
            print('NEWCANON [%s] %s' % (w, z), flush=True)
    return bool(cands)


def lemmaB(ck, r, par):
    key = '%s ## r=%d par=%d' % (ck, r, par)
    if key in proof['lemmaB'] and proof['lemmaB'][key]['status'] == 'CANON':
        rec = proof['lemmaB'][key]; new = []
        with lock:
            if rec['target'] not in samples and os.path.exists(rec.get('file', '')):
                samples[rec['target']] = gen.parse_struct(rec['file'], rec['target'].split(' || ')[0]); new.append(rec['target'])
        return rec, new
    st = samples[ck]; canon = ck.split(' || ')[0]
    tag = 'B%d_%d_%d' % (abs(hash(ck)) % 100000, r, par)
    fa, fb = D + 'pv_%s_a.txt' % tag, D + 'pv_%s_b.txt' % tag
    gen.rebuild(st, r, M0 + par, fa); gen.rebuild(st, r, M0 + par + 2, fb)
    res = run_ssim([fa, fb, '-'], [(0, 0), (1, 0), (2, 0), (7, 0)], tag)
    for attempt in range(4):
        if res['status'] == 'CANON' or not res['status'].startswith('LIMIT'): break
        if not discover(fa, tag): break
        res = run_ssim([fa, fb, '-'], [(0, 0), (1, 0), (2, 0), (7, 0)], tag)
    rec = {'status': res['status']}
    new = []
    if res['status'] == 'CANON':
        c2 = res['canon']
        vals = {}; keys = set(); ok = True
        for xy, fn in res['files'].items():
            try:
                rt, s2 = exact_roundtrip(fn, c2)
            except Exception as e:
                ok = False; rec['why'] = 'parse: %s' % e; break
            if not rt: ok = False; rec['why'] = 'roundtrip'; break
            keys.add(ctxkey(c2, s2)); vals[xy[0]] = (s2['N'], s2['M']); last = s2
        if ok and len(keys) != 1:
            ok = False; rec['why'] = 'context depends on x'; rec['keys'] = [k[:200] for k in keys]
        if ok:
            k2 = keys.pop()
            n0, m0 = vals[0]; n1, m1 = vals[1]
            lin = all(vals[x] == (n0 + (n1 - n0) * x, m0 + (m1 - m0) * x) for x in vals)
            rec.update(file=res['files'][(0, 0)], target=k2, N1=[n0, n1 - n0], M1=[m0, m1 - m0], linear=lin, constraints=res['constraints'],
                       Mmin=M0 + par + 2 * xmin_from(res['constraints'], 'x'))
            if not lin: rec['status'] = 'NONLINEAR'
            # cross-check instance x=2 with concrete fsim
            gen.rebuild(st, r, M0 + par + 4, D + 'pv_%s_cx.txt' % tag)
            subprocess.run([D + 'fsim.exe', '20', '1e15', D + 'pv_%s_cx.txt' % tag, CANON, D + 'pv_%s_cxo.txt' % tag], capture_output=True)
            a = open(D + 'pv_%s_cxo.txt' % tag).read().split(); b = open(res['files'][(2, 0)]).read().split()
            rec['crosscheck'] = (a[1], a[2], a[3].rstrip('0')) == (b[1], b[2], b[3].rstrip('0'))
            with lock:
                if k2 not in samples: samples[k2] = last; new.append(k2)
        else:
            rec['status'] = 'BAD'
    else:
        rec['raw'] = res['raw'][-600:]
    with lock: proof['lemmaB'][key] = rec
    print('B', ck[:50], r, par, rec['status'], rec.get('N1'), rec.get('M1'), (rec.get('target') or '')[:60], 'xc=%s' % rec.get('crosscheck'), flush=True)
    return rec, new


def bfs(start_fn, start_canon, workers=5):
    st = gen.parse_struct(start_fn, start_canon)
    ck = ctxkey(start_canon, st); samples[ck] = st
    queue = [ck]; seen = set()
    while queue:
        ck = queue.pop(0)
        if ck in seen: continue
        seen.add(ck)
        A = lemmaA(ck)
        if A.get('status') != 'CANON':
            proof['problems'].append({'ctx': ck, 'lemmaA': A}); save(); continue
        P = A['P']
        proof['contexts'][ck] = {'P': P, 'dM': A['dM']}
        small = [(N, par) for N in range(P, max(P, A['Nmin'])) for par in (0, 1)]
        with ThreadPoolExecutor(workers) as ex:
            srec = list(ex.map(lambda a: lemmaAsmall(ck, a[0], a[1], P, A['dM']), small))
        # r_low: smallest N' such that the step (N'+P -> N') holds for every N >= N'+P (both parities)
        okN = {}
        for (N, par), s_ in zip(small, srec): okN[N] = okN.get(N, True) and s_['ok']
        r_low = max(0, A['Nmin'] - P)
        for N in sorted(okN, reverse=True):
            if okN[N]: r_low = N - P
            else: break
        print('  small-N lemma A checks: %d, r_low=%d' % (len(srec), r_low), flush=True)
        proof['contexts'][ck]['r_low'] = r_low
        jobs = [(ck, r, par) for r in range(r_low, r_low + P) for par in (0, 1)]
        with ThreadPoolExecutor(workers) as ex:
            outs = list(ex.map(lambda j: lemmaB(*j), jobs))
        for rec, new in outs:
            if rec['status'] != 'CANON':
                proof['problems'].append({'ctx': ck, 'B': rec})
            for k2 in new:
                if k2 not in seen: queue.append(k2)
        save()
        print('=== contexts done %d, queue %d, problems %d' % (len(seen), len(queue), len(proof['problems'])), flush=True)


if __name__ == '__main__':
    proof['problems'] = []
    bfs(D + 's_226258280.txt', '1 7 0 0* 4 3 0 0 0 0 0 9 | 8 ', workers=int(sys.argv[1]) if len(sys.argv) > 1 else 5)
    print('FINISHED. problems:', len(proof['problems']))
