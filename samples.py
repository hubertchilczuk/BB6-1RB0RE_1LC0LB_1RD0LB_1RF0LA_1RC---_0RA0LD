"""Structure templates (samples) of all proof nodes, from the start configuration and the lemma-B target files.

proof2.json stores absolute paths of the prover's working directory; the files are looked up by basename
in this directory instead.
"""
import os
import prover2 as P2

D = P2.D
START_FILE = D + 's_226258280.txt'
START_CANON = '1 7 0 0* 4 3 0 0 0 0 0 9 | 8 '


def load():
    st, ck, fk = P2.classify(START_FILE, START_CANON)
    P2.samples[ck] = st
    for rec in P2.proof['lemmaB'].values():
        for t, fn in rec.get('targets_files', {}).items():
            if t not in P2.samples:
                P2.samples[t] = P2.classify(D + os.path.basename(fn), t.split(' || ')[0])[0]
    for t in list(P2.samples):
        if not P2.is_family(t) and P2.samples[t]['k'] is not None:
            f = P2.family_of(t)
            if f not in P2.samples: P2.samples[f] = P2.samples[t]
    return P2.samples
