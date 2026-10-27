"""Probe: does the number of sweeps of a lemma B depend on M?

For a lemma B (node, r, par) run plain simulations from (r, M) for two values of M up to the predicted
first canonical point of the target node; print the number of new-leftmost events of each run.
usage: probe_lemmaB.py [count]
"""
import os, sys, json, random, subprocess
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/'
sys.path.insert(0, ROOT)
import samples
import prover2 as P2

S = samples.load()
P = json.load(open(ROOT + 'proof4.json'))
EVT = ROOT + 'an/evtapes.exe'
TMP = ROOT + 'rocq/tmp/'


def events_until(cfgtape, target):
    fn = TMP + 'probe_%d.txt' % os.getpid()
    open(fn, 'w').write('0 2 0\n%s\n' % cfgtape)
    out = subprocess.run([EVT, fn, '20000000000', '2000000'], capture_output=True, text=True).stdout.split('\n')
    for i in range(0, len(out) - 1, 2):
        if out[i + 1] == target: return i // 2 + 1
    return None


def tape(st, N, M, k=None):
    Tc = st['kh'] + st['k3'] * k + st['kl'] if k is not None else st['T_cells']
    return st['zone_cells'] + st['w_cells'] * N + Tc + st['u_cells'] * M + st['tail_cells'].rstrip('0')


random.seed(int(sys.argv[2]) if len(sys.argv) > 2 else 1)
keys = [k for k in P['lemmaB'] if ' || FAM ' not in k and 'partial_of' not in P['nodes'].get(k.split(' ## ')[0], {})]
for key in random.sample(keys, int(sys.argv[1]) if len(sys.argv) > 1 else 6):
    node = key.split(' ## ')[0]; r = int(key.split('r=')[1].split()[0]); par = int(key.split('par=')[1])
    B = P['lemmaB'][key]; t = B['target']
    if ' || FAM ' in t or t not in S: continue
    res = []
    for M in (600 + par, 640 + par):
        x = (M - 1000 - par) // 2
        ev = lambda c: c[0] + c[1] * x
        n1, m1 = ev(B['N1']), ev(B['M1'])
        res.append(events_until(tape(S[node], r, M), tape(S[t], n1, m1)))
    print('%s r=%d par=%d: sweeps %s  (N1 coef %d)' % (node[:40], r, par, res, B['N1'][1]), flush=True)
