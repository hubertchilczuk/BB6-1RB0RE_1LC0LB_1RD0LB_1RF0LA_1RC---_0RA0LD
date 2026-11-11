#!/bin/bash
# Axiom check (see genPA.py). Inside coqorg/coq:8.20 with busycoq at /bc and rocq/ at /r:  bash /r/PA/run.sh [JOBS]
# Output: PA/<file>.out per batch, PA/summary.txt
JOBS=${1:-2}
cd /r/PA || exit 1
ulimit -s unlimited
one() {
  f=$1; o=${f%.v}.out
  if [ -s "$o" ] && grep -q '^rc=0' "$o"; then return; fi
  coqc -Q /bc/verify BusyCoq -Q /r/N BB6N -Q /r/F BB6F -Q /r/B3 "" -Q /r/D "" -Q /r/A2 "" -Q /r/S "" -Q /r/C "" "$f" > "$o" 2>&1
  echo "rc=$?" >> "$o"
}
export -f one
ls PA_*.v | xargs -P "$JOBS" -I{} bash -c 'one {}'
{
  echo "batches: $(ls PA_*.v | wc -l), rc=0: $(grep -l '^rc=0' PA_*.out | wc -l)"
  echo "Print Assumptions answers:"
  grep -h -v -E '^(Warning|File |rc=)|applications of Init.Nat|abstract-large' PA_*.out | sort | uniq -c
  echo "Axiom/Admitted/... in any .v file (N F S A2 D B3 C):"
  for d in N F S A2 D B3 C; do
    ls /r/$d | grep '\.v$' | sed "s|^|/r/$d/|" | xargs grep -l -E '^\s*(Axiom|Axioms|Parameter|Parameters|Conjecture|Hypothesis|Hypotheses|Variable|Variables)\b|\bAdmitted\.|\badmit\b' 2>/dev/null
  done
  echo "(end of list)"
} > summary.txt
cat summary.txt
