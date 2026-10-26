"""Mutation tests for verify4.py: each mutation breaks proof2.json in one place; verify4 must report errors."""
import os, sys, json, random, subprocess, re

D = os.path.dirname(os.path.abspath(__file__)) + '/'
SRC = open(D + 'verify4.py').read()
HOOK = "P = json.load(open(D + 'proof2.json'))"
assert HOOK in SRC
random.seed(1)
P = json.load(open(D + 'proof2.json'))
Bkeys = [k for k, b in P['lemmaB'].items() if b['status'] == 'OK']
xdep = [k for k in Bkeys if P['lemmaB'][k]['N1'][1] == 1]
small_keys = list(P['smallA'])

MUTATIONS = {
    'drop a lemma B': "del P['lemmaB'][%r]" % random.choice(Bkeys),
    'lemma B not crosschecked': "P['lemmaB'][%r]['crosscheck'] = False" % random.choice(Bkeys),
    'impossible lemma B constraint': "P['lemmaB'][%r]['constraints'] += ' -100000+0v0+0v1+0v2>=0'" % random.choice(Bkeys),
    'drop all small-N lemmas of one N': "[P['smallA'].pop(k) for k in [k for k in list(P['smallA']) if k.endswith(' ## N=%s par=0')]]" % '{}',
    'tighter lemma A constraints (all nodes)': "[a.__setitem__('constraints', a['constraints'] + ' -1000000+1v0+0v1+0v2>=0') for a in P['lemmaA'].values()]",
    'drop odd lemma A': "P['lemmaA_odd'].clear()",
    'drop small-M lemmas': "P['lemmaA_smallM'].clear()",
    'M1 drops by a lot (one x-dependent lemma)': "P['lemmaB'][%r]['M1'][0] -= 5000" % random.choice(xdep),
    'odd dM': "next(n for n in P['nodes'].values() if 'P' in n)['dM'] += 1",
}


def run(mut, mstar='500'):
    src = SRC.replace(HOOK, HOOK + '\n' + mut)
    fn = D + '_mut_tmp.py'
    open(fn, 'w').write(src)
    out = subprocess.run([sys.executable, fn, mstar], capture_output=True, text=True)
    os.remove(fn)
    o = out.stdout + out.stderr
    m = re.search(r'errors (\d+)', o)
    return (int(m.group(1)) if m else None), ('in domain: True' in o), o


# small-N mutation: pick an N that is actually used (from the descent of many nodes): N = r_low + P of the common node shape
MUTATIONS['drop all small-N lemmas of one N'] = MUTATIONS['drop all small-N lemmas of one N'].format(52)
for name, mut in MUTATIONS.items():
    e, ok, o = run(mut)
    caught = (e is None) or e > 0 or not ok
    print('%-45s errors=%s start_ok=%s -> %s' % (name, e, ok, 'CAUGHT' if caught else 'NOT CAUGHT'), flush=True)
    if e is None: print(o[-500:])
for ms in ('300', '400'):
    e, ok, o = run('', ms)
    print('%-45s errors=%s start_ok=%s' % ('MSTAR=' + ms + ' (verify3 had errors here)', e, ok), flush=True)
