#!/bin/bash
# Build the whole Rocq proof from the generated .v files and check it. Run inside coqorg/coq:8.20 with
#   busycoq (github.com/ccz181078/busycoq, commit 0bd6d38) at /bc and this repo's rocq/ directory at /r:
#
#   docker run --rm -v <busycoq>:/bc -v <repo>/rocq:/r coqorg/coq:8.20 bash /r/build_all.sh [JOBS]
#
# Resumable: files with an up-to-date .vo are skipped (logs: <dir>/compile_log.txt; a failed file gets a .fail marker
# and is not retried until its .v changes). Needs ~12 GB RAM for Final.v, ~2.5 GB per job elsewhere.
# Rough cost (6 cores): lemma B ~200 h CPU, Close ~25 h CPU, everything else under an hour.
set -e
JOBS=${1:-4}
C="bash /r/compile.sh"
ulimit -s unlimited
FLAGS=(-Q /bc/verify BusyCoq -Q /r/N BB6N -Q /r/F BB6F)
step() { echo "== $(date '+%F %T') $*"; }
cc() {      # compile one file unless its .vo is up to date (a recompiled dependency would not match the other .vo)
  [ -e "${1%.v}.vo" ] && [ "${1%.v}.vo" -nt "$1" ] && return
  shift_args=("${@:2}"); coqc "${FLAGS[@]}" "${shift_args[@]}" "$1"
}
check() {   # every file of the pattern has an up-to-date .vo
  local bad=0
  for f in $1; do [ -e "${f%.v}.vo" ] && [ "${f%.v}.vo" -nt "$f" ] || { echo "NOT COMPILED: $f"; bad=1; }; done
  [ $bad = 0 ] || { echo "stopping: see compile_log.txt in $(pwd)"; exit 1; }
}

step "busycoq (Individual62, ES_v3 and their dependencies)"
cd /bc/verify
[ -e Makefile.coq ] || coq_makefile -f _CoqProject -o Makefile.coq
make -f Makefile.coq -j "$JOBS" Individual62.vo ES_v3.vo

step "nodes, domain shapes, domain predicate, start"
cd /r/N; cc Nodes.v
cd /r/F; cc F.v; cc Dom.v
cd /r/S; cc Start.v

step "lemma A (410)"
PAT='A_*.v' $C /r/A2 "$JOBS"; cd /r/A2; check 'A_*.v'
step "descent (410)"
QEMPTY=/r/A2 PAT='D_*.v' $C /r/D "$JOBS"; cd /r/D; check 'D_*.v'
step "lemma B (20 122 + 2 exceptional)"
TLIM=7200 PAT='B*_*.v' $C /r/B3 "$JOBS"; cd /r/B3; check 'B*_*.v'
step "closure (772)"
TLIM=3600 QEMPTY="/r/B3 /r/D /r/A2" PAT='Close_*.v' $C /r/C "$JOBS"; cd /r/C; check 'Close_*.v'

[ -n "$SKIP_FINAL" ] && { step "SKIP_FINAL set: stopping before Final.v"; exit 0; }
step "main theorem"
cd /r/C; cc Final.v -Q /r/B3 "" -Q /r/D "" -Q /r/A2 "" -Q /r/S "" -Q /r/C ""
step "axiom check (in pieces, see genPA.py)"
rm -f /r/PA/PA_*.out /r/PA/summary.txt    # the repo carries the outputs of our run: check again, do not reuse them
bash /r/PA/run.sh "$JOBS"
step "done: rocq/C/Final.vo proves  nonhalt : ~ halts tm c0;  axiom check in rocq/PA/summary.txt"
