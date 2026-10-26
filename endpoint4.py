"""Check every lemma at the most extreme parameter points where verify4 uses it (used_points.json).

The affine results of the lemmas (N1, M1, K1; lemma A: N-P, M+dM) were fitted on a few nonnegative
instances (x = 0, 1, 2, 7), while the proof uses them down to e.g. x = -250 (M = 500). Here ssim4 writes
the final configuration at the extreme points themselves, and its parse must give the predicted node
and counts. (Between the extreme point and the fitted instances all run counts stay affine and >= 1 by
the ssim4 constraints.)
usage: endpoint4.py [workers]
"""
import os, sys, json, subprocess, threading
from concurrent.futures import ThreadPoolExecutor
import rerun4 as R4
import prover2 as P2

D = R4.D
OUT = D + 'r4/'
P = json.load(open(D + 'proof4.json'))
M0, K0, N0 = 1000, 1000, 300
lock = threading.Lock()
jobmap = {(j[0], j[1]): j for j in R4.jobs()}
used = json.load(open(D + 'used_points.json'))


def expect(sect, key, v):
    """(input node, expected target node, family?, N, M, k) after the lemma at variables v"""
    if sect == 'lemmaB':
        B = P['lemmaB'][key]
        ev = lambda c: None if c is None else c[0] + c[1] * v[0] + c[2] * v[1]
        return B['target'], ev(B['N1']), ev(B['M1']), ev(B['K1'])
    node = key.split(' ## ')[0]
    A = P['lemmaA'][node]; fam = ' || FAM ' in node
    kk = K0 + int(node.split('park=')[1][0]) if fam else None
    if sect in ('lemmaA', 'lemmaA_odd'):
        par = 0 if sect == 'lemmaA' else 1
        return node, N0 + v[0] - A['P'], M0 + par + 2 * v[1] + A['dM'], (kk + 2 * v[2]) if fam else None
    if sect == 'smallA':
        n = int(key.split('N=')[1].split()[0]); par = int(key.split('par=')[1])
        Pp = P['nodes'].get(node, {}).get('P', A['P'])
        return node, n - Pp, M0 + par + 2 * v[0] + A['dM'], (kk + 2 * v[1]) if fam else None
    if sect == 'lemmaA_smallM':
        Mv = int(key.split('M=')[1])
        return node, N0 + v[0] - A['P'], Mv + A['dM'], (kk + 2 * v[1]) if fam else None


def one(item):
    sect, key, pts = item
    _, _, tag, canon, varl, _ = jobmap[(sect, key)]
    pts = sorted({tuple(p) for p in pts if p is not None})
    base = D + 'p2_%s_a.txt' % tag
    vars_ = [D + 'p2_%s_%s.txt' % (tag, v) for v in varl] + ['-'] * (3 - len(varl))
    ins = ['%d,%d,%d' % p for p in pts]
    out = subprocess.run([R4.SSIM, '20', '30000000', base] + vars_ + [R4.canon_file(canon), OUT + 'e4_' + tag] + ins,
                         capture_output=True, text=True).stdout
    bad = []
    if 'CANON ' + canon.rstrip() not in out: return [(sect, key[:70], 'no canon')]
    for p, i in zip(pts, ins):
        fn = OUT + 'e4_%s_%s.txt' % (tag, i.replace(',', '_'))
        tnode, n, m, k = expect(sect, key, p)
        try:
            st, ck, fk = P2.classify(fn, canon)
            got_node = fk if ' || FAM ' in tnode else ck
            if got_node != tnode or st['N'] != n or st['M'] != m or (k is not None and st['k'] != k):
                bad.append((sect, key[:70], p, 'got N=%s M=%s k=%s, expected N=%s M=%s k=%s, node ok=%s' % (
                    st['N'], st['M'], st['k'], n, m, k, got_node == tnode)))
        except Exception as e:
            bad.append((sect, key[:70], p, 'parse failed: %r' % (e,)))
        for f in (fn, fn + '.rt'):
            if os.path.exists(f): os.remove(f)
    return bad


if __name__ == '__main__':
    workers = int(sys.argv[1]) if len(sys.argv) > 1 else 6
    items = [(s, k, v) for s, k, v in used]
    allbad = []; cnt = [0]

    def run(it):
        b = one(it)
        with lock:
            allbad.extend(b); cnt[0] += 1
            for x in b: print('MISMATCH', x, flush=True)
            if cnt[0] % 2000 == 0: print('progress %d/%d, mismatches %d' % (cnt[0], len(items), len(allbad)), flush=True)

    with ThreadPoolExecutor(workers) as ex: list(ex.map(run, items))
    npts = sum(len({tuple(p) for p in v if p is not None}) for _, _, v in items)
    print('ENDPOINT4: %d lemmas, %d extreme points checked, %d mismatches' % (len(items), npts, len(allbad)), flush=True)
