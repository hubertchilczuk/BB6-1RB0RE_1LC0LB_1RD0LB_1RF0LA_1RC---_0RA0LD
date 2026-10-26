"""Re-derive every lemma of proof2.json with ssim4 (= ssim3 + the two assumptions ssim3 did not record)
from the original input files, and build proof4.json with the ssim4 constraints.

For every lemma: same simulator inputs and instances as the prover used; the canon file holds only the
lemma's own target canon (the prover's canon list grew during the run; the first hit of the target canon
is the original stopping point). Checked: CANON reached, same target canon, every instance output file
byte-identical to the original. Recorded: ssim4 constraints and whether a mixed cycle limit occurred.
usage: rerun4.py [workers]      (resumable: results go to rerun4_results.jsonl)
"""
import os, sys, json, re, hashlib, subprocess, threading, filecmp
from concurrent.futures import ThreadPoolExecutor

D = os.path.dirname(os.path.abspath(__file__)) + '/'
OUT = D + 'r4/'
os.makedirs(OUT, exist_ok=True)
RES = D + 'rerun4_results.jsonl'
SSIM = D + 'ssim4.exe'
P = json.load(open(D + 'proof2.json'))
tagof = lambda key: hashlib.md5(key.encode()).hexdigest()[:8]
is_family = lambda node: ' || FAM ' in node
lock = threading.Lock()


def jobs():
    J = []
    for kind, sect in (('A', 'lemmaA'), ('O', 'lemmaA_odd')):
        for node, rec in P[sect].items():
            if rec.get('status') != 'OK': continue
            fam = is_family(node)
            J.append((sect, node, kind + tagof(node), node.split(' || ')[0], 'bcd' if fam else 'bc',
                      [(0, 0, 0), (1, 0, 0), (0, 1, 0), (3, 2, 1 if fam else 0)]))
    for key, rec in P['smallA'].items():
        if not rec['ok']: continue
        node = key.split(' ## ')[0]; fam = is_family(node)
        J.append(('smallA', key, 'S' + tagof(key), node.split(' || ')[0], 'bc' if fam else 'b',
                  [(0, 0), (1, 0), (2, 3)] if fam else [(0,), (1,), (5,)]))
    for key, rec in P['lemmaA_smallM'].items():
        if not rec['ok']: continue
        node = key.split(' ## ')[0]; fam = is_family(node)
        J.append(('lemmaA_smallM', key, 'Q' + tagof(key), node.split(' || ')[0], 'bc' if fam else 'b',
                  [(0, 0), (1, 0), (4, 1)] if fam else [(0,), (1,), (9,)]))
    for key, rec in P['lemmaB'].items():
        node = key.split(' ## ')[0]; fam = is_family(node)
        J.append(('lemmaB', key, 'B' + tagof(key), rec['target'].split(' || ')[0], 'bc' if fam else 'b',
                  [(0, 0), (1, 0), (0, 1), (2, 3), (5, 1)] if fam else [(0,), (1,), (2,), (7,)]))
    return J


canon_files = {}


def canon_file(c):
    with lock:
        if c not in canon_files:
            fn = OUT + 'canon_%s.txt' % tagof(c)
            open(fn, 'w').write(c + '\n')
            canon_files[c] = fn
        return canon_files[c]


def one(job):
    sect, key, tag, canon, varl, insts = job
    base = D + 'p2_%s_a.txt' % tag
    vars_ = [D + 'p2_%s_%s.txt' % (tag, v) for v in varl]
    vars_ += ['-'] * (3 - len(vars_))
    ins = ['%d,%d,%d' % tuple(list(i) + [0] * (3 - len(i))) for i in insts]
    out = subprocess.run([SSIM, '20', '30000000', base] + vars_ + [canon_file(canon), OUT + 'p4_' + tag] + ins,
                         capture_output=True, text=True).stdout
    r = {'sect': sect, 'key': key}
    m = re.search(r'^CANON (.*)$', out, re.M)
    if not m:
        r['status'] = (out.strip().splitlines() or ['NO OUTPUT'])[-1]
        return r
    c = m.group(1); c = c if c.endswith(' ') else c + ' '
    r['status'] = 'CANON' if c == canon else 'OTHER CANON'
    cm = re.search(r'^CONSTRAINTS(.*)$', out, re.M)
    r['constraints'] = cm.group(1).strip() if cm else ''
    mm = re.search(r'mixedlimits=(\d+)', out)
    r['mixed'] = int(mm.group(1)) if mm else None
    same = True
    for i in ins:
        a, b = D + 'p2_%s_%s.txt' % (tag, i.replace(',', '_')), OUT + 'p4_%s_%s.txt' % (tag, i.replace(',', '_'))
        if not (os.path.exists(a) and os.path.exists(b) and filecmp.cmp(a, b, shallow=False)): same = False
        if os.path.exists(b): os.remove(b)
    r['same_outputs'] = same
    r['old_constraints'] = P[sect][key].get('constraints')
    return r


if __name__ == '__main__':
    workers = int(sys.argv[1]) if len(sys.argv) > 1 else 6
    done = set()
    if os.path.exists(RES):
        for l in open(RES):
            d = json.loads(l); done.add((d['sect'], d['key']))
    J = [j for j in jobs() if (j[0], j[1]) not in done]
    print('jobs total %d, to do %d' % (len(jobs()), len(J)), flush=True)
    f = open(RES, 'a'); cnt = [0]

    def run(j):
        r = one(j)
        with lock:
            f.write(json.dumps(r) + '\n'); f.flush(); cnt[0] += 1
            if r['status'] != 'CANON' or not r['same_outputs']:
                print('PROBLEM', r['sect'], r['key'][:80], r['status'], r.get('same_outputs'), flush=True)
            if cnt[0] % 500 == 0: print('progress %d/%d' % (cnt[0], len(J)), flush=True)

    with ThreadPoolExecutor(workers) as ex: list(ex.map(run, J))
    print('RERUN4 FINISHED', flush=True)
