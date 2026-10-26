"""Monte-Carlo sampling of transition branches: random context, residue r, k (3^k block), M.
Looks for any branch that HALTs (or fails to reach a canonical point)."""
import glob, random, sys, json, threading
from concurrent.futures import ThreadPoolExecutor
import gen, surg

D = gen.D
CANONS = [l.rstrip('\n') for l in open(D + 'canon_all.txt') if l.strip()]
P = {CANONS[0]: 100, CANONS[1]: 40}


def tparts(Tcells):
    p, its, tl = surg.parse('1' + Tcells)
    return [(x[0], ('1' + Tcells)[x[1]:x[2]]) for x in its]


# collect one sample struct per context type
samples = {}
for fn in sorted(glob.glob(D + 'tmp_out_*.txt')) + [D + 's_226258280.txt', D + 'cfg_out.txt']:
    for c in CANONS:
        try:
            st = gen.parse_struct(fn, c)
        except Exception:
            continue
        T = st['T']
        if st['u'] == ['3']:
            continue
        if T[:2] == ['0', '4'] and T[-1] == '2' and all(x == '3' for x in T[2:-1]):
            typ = 'R031:0 4 3^k 2'
            parts = tparts(st['T_cells'])
            st['_three'] = [cc for n, cc in parts if n == '3'][0] if len(T) > 3 else None
            st['_head'] = ''.join(cc for n, cc in parts[:2]); st['_last'] = parts[-1][1]
            if st['_three'] is None:
                continue
        else:
            typ = ('R8:' if '| 8' in c else 'R031:') + ' '.join(T) + '|' + ' '.join(st['u']) + '|' + ' '.join(st['tail'])
        st['_canon'] = c
        samples.setdefault(typ, st)
        break
print('context types:', list(samples), flush=True)

lock = threading.Lock()
stats = {}
found = []


def one(i):
    rnd = random.Random(i * 7919 + 13)
    typ = rnd.choice(list(samples))
    st = dict(samples[typ])
    c = st['_canon']
    r = rnd.randrange(P[c])
    M = rnd.randrange(500, 4000)
    k = None
    if typ.endswith('3^k 2'):
        k = rnd.randrange(0, 3000)
        st['T_cells'] = st['_head'] + st['_three'] * k + st['_last']
    cfg = D + 'smp_in_%d.txt' % (i % 16)
    out = D + 'smp_out_%d.txt' % (i % 16)
    gen.rebuild(st, r, M, cfg)
    status, c2, lines = gen.run_to_canon(cfg, D + 'canon_all.txt', out, 3e13)
    with lock:
        stats[status] = stats.get(status, 0) + 1
        if status != 'CANON':
            found.append(dict(i=i, typ=typ, r=r, M=M, k=k, status=status))
            open(D + 'smp_bad_%d.txt' % i, 'w').write(open(cfg).read())
        if i % 50 == 0 or status != 'CANON':
            print(i, typ, 'r=%d M=%d k=%s' % (r, M, k), status, 'totals', stats, flush=True)


n = int(sys.argv[1])
with ThreadPoolExecutor(int(sys.argv[2]) if len(sys.argv) > 2 else 4) as ex:
    list(ex.map(one, range(n)))
print('FINAL', stats)
json.dump(found, open(D + 'sampler_found.json', 'w'), indent=1)
