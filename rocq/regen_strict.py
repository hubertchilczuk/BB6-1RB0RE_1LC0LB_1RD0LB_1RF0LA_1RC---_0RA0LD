"""Regenerate the lemma B files whose compilation failed (a .fail marker newer than the .v) in strict mode:
constant runs shorter than STRICT blocks stay concrete (es' cannot always carry such a run symbolically).
usage: regen_strict.py [STRICT]        the compile loop then retries the new files
"""
import os, sys
import run_gen, genB3

STRICT = int(sys.argv[1]) if len(sys.argv) > 1 else 200
for job, out in run_gen.jobs_B():
    fail = out[:-2] + '.fail'
    if not (os.path.exists(fail) and os.path.getmtime(fail) > os.path.getmtime(out)): continue
    tmp = out + '.new'
    genB3.generate(job[1], tmp, strict=STRICT)
    os.replace(tmp, out)
    print('regenerated', os.path.basename(out))
