"""Axiom check in pieces: rocq/PA/PA_<k>.v (Print Assumptions of the close_* lemmas, BATCH per file) and PA/PA_misc.v.

Print Assumptions Final.nonhalt needs every lemma B module in memory plus every opaque proof body (> 12.5 GB; killed
after 7 h on a 16 GB machine). The assumptions of nonhalt are the union of the assumptions of the constants its proof
refers to: the close_* lemmas (through closure), Start.start, the start descent, the busycoq lemmas, Dom and the
machine; Final.v itself declares no axiom (checked by grep together with all other .v files, see PA/run.sh).
usage: genPA.py [BATCH]          then: bash /r/PA/run.sh inside the container
"""
import os, re, sys
import rocqgen as RG

ROOT = RG.ROOT + 'rocq/'
OUT = ROOT + 'PA/'
BATCH = int(sys.argv[1]) if len(sys.argv) > 1 else 40
os.makedirs(OUT, exist_ok=True)
final = open(ROOT + 'C/Final.v').read()
refs = re.findall(r'eapply (Close_\S+?)\.(close_\S+?);', final)
start = re.search(r'exact (Start\.\S+?) ', final).group(1)
desc = re.search(r'apply (D_\S+?_descent);', final).group(1)
assert len(refs) == len(set(refs)) == final.count('eapply Close_'), 'unexpected Final.v shape'
for k in range(0, len(refs), BATCH):
    part = refs[k:k + BATCH]
    v = ['Require %s.' % m for m, _ in part] + ['Print Assumptions %s.%s.' % (m, c) for m, c in part]
    open(OUT + 'PA_%03d.v' % (k // BATCH), 'w').write('\n'.join(v) + '\n')
misc = ['From BusyCoq Require Import Individual62.', 'From BB6F Require Import F Dom.', 'Require Import String.',
        'Require Start %s.' % desc.split('.')[0],
        'Print Assumptions %s.' % start, 'Print Assumptions %s.' % desc,
        'Print Assumptions multistep_nonhalt.', 'Print Assumptions progress_nonhalt.', 'Print Assumptions evstep_trans.',
        'Print Assumptions Dom.',
        'Definition tm := TM_from_str "1RB0RE_1LC0LB_1RD0LB_1RF0LA_1RC---_0RA0LD".', 'Print Assumptions tm.']
open(OUT + 'PA_misc.v', 'w').write('\n'.join(misc) + '\n')
print('%d close lemmas in %d files, + PA_misc.v' % (len(refs), (len(refs) + BATCH - 1) // BATCH))
