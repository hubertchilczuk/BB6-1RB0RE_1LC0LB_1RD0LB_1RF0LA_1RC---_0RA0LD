"""Cross-check lemma A (even/odd), small-M and a sample of small-N lemmas: rerun ssim3 for one instance
and compare it bit-exactly with the concrete simulator fsim started from the same instantiated config."""
import json, random, subprocess, threading
from concurrent.futures import ThreadPoolExecutor
import prover2 as P2
import lemmaA_odd  # registers samples
D = P2.D; proof = P2.proof
CANON = P2.CANON
jobs = []
for node, rec in proof['lemmaA'].items():
    if rec.get('status') == 'OK' and node in P2.samples: jobs.append(('A', node, 0))
for node, rec in proof.get('lemmaA_odd', {}).items():
    if rec.get('status') == 'OK' and node in P2.samples: jobs.append(('A', node, 1))
small = [k for k, v in proof['smallA'].items() if v['ok'] and k.split(' ## ')[0] in P2.samples]
random.seed(7)
for k in random.sample(small, min(400, len(small))): jobs.append(('S', k, None))
print('jobs', len(jobs), flush=True)
lock = threading.Lock(); bad = []; done = [0]
def one(j):
    kind, key, par = j
    node = key.split(' ## ')[0]; fam = P2.is_family(node); s = P2.samples[node]
    kk = P2.K0 + s['k'] % 2 if fam else None
    canon = node.split(' || ')[0]
    tag = 'X' + P2.tagof(kind + key + str(par))
    if kind == 'A':
        N = P2.N0 + 3; M = P2.M0 + par + 4; k = (kk + 2) if fam else None
        expectN = N - proof['lemmaA'][node]['P']
    else:
        N = int(key.split('N=')[1].split()[0]); par = int(key.split('par=')[1]); M = P2.M0 + par + 6; k = (kk + 2) if fam else None
        expectN = N - proof['nodes'].get(node, {}).get('P', proof['lemmaA'][node]['P'])
    inp = D + 'p2_%s_in.txt' % tag; out = D + 'p2_%s_out.txt' % tag
    P2.build(node, N, M, k, inp)
    subprocess.run([D + 'fsim.exe', '20', '1e15', inp, CANON, out], capture_output=True)
    try:
        st2, ck2, fk2 = P2.classify(out, canon)
        ok = (fk2 if fam else ck2) == node and st2['N'] == expectN and st2['M'] == M + proof['lemmaA'][node]['dM'] and (not fam or st2['k'] == k)
    except Exception as e:
        ok = False
    with lock:
        done[0] += 1
        if not ok: bad.append((kind, key[:90], par))
with ThreadPoolExecutor(6) as ex: list(ex.map(one, jobs))
print('checked', done[0], 'mismatches', len(bad))
for b in bad[:10]: print('  ', b)
