#!/bin/bash
# Compile every .v file of a directory that has no up-to-date .vo, in parallel; one line per file in compile_log.txt:
#   OK <file> <seconds>   or   FAIL <file> <seconds> <first error line>
# usage (inside the coqorg/coq:8.20 container, busycoq at /bc, this repo's rocq dir at /r):
#   compile.sh DIR [JOBS]        extra coqc flags in EXTRA; QEMPTY="dir1 dir2" maps directories to the empty prefix
DIR=$1; JOBS=${2:-3}
cd "$DIR" || exit 1
ulimit -s unlimited   # es' on long lemma B files overflows the default 8 MB stack
one() {
  f=$1
  if [ -e "${f%.v}.vo" ] && [ "${f%.v}.vo" -nt "$f" ]; then return; fi
  if [ -e "${f%.v}.fail" ] && [ "${f%.v}.fail" -nt "$f" ]; then return; fi   # failed already: retried once the .v changes
  s=$(date +%s)
  q=(); for d in $QEMPTY; do q+=(-Q "$d" ""); done
  if out=$(timeout ${TLIM:-1500} coqc -Q /bc/verify BusyCoq -Q /r/N BB6N -Q /r/F BB6F $EXTRA "${q[@]}" "$f" 2>&1); then
    echo "OK $f $(( $(date +%s) - s ))" >> compile_log.txt
  else
    touch "${f%.v}.fail"
    # the error itself (with its location line before it), not the first warning; else the last line (timeout: empty)
    err=$(echo "$out" | grep -m1 -B1 -E 'Error|Killed' | tr '\n' ' ')
    echo "FAIL $f $(( $(date +%s) - s )) ${err:-$(echo "$out" | tail -1)}" >> compile_log.txt
  fi
}
export -f one
ls *.v | xargs -P "$JOBS" -I{} bash -c 'one {}'
echo DONE >> compile_log.txt
