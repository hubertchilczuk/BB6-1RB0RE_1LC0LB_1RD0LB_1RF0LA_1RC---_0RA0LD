#!/bin/bash
# Compile every .v file of a directory that has no up-to-date .vo, in parallel; one line per file in compile_log.txt:
#   OK <file> <seconds>   or   FAIL <file> <seconds> <first error line>
# usage (inside the coqorg/coq:8.20 container, busycoq at /bc, this repo's rocq dir at /r):
#   compile.sh DIR [JOBS]        extra coqc flags in EXTRA; QEMPTY="dir1 dir2" maps directories to the empty prefix
DIR=$1; JOBS=${2:-3}
cd "$DIR" || exit 1
one() {
  f=$1
  if [ -e "${f%.v}.vo" ] && [ "${f%.v}.vo" -nt "$f" ]; then return; fi
  s=$(date +%s)
  q=(); for d in $QEMPTY; do q+=(-Q "$d" ""); done
  if out=$(timeout 7200 coqc -Q /bc/verify BusyCoq -Q /r/N BB6N -Q /r/F BB6F $EXTRA "${q[@]}" "$f" 2>&1); then
    echo "OK $f $(( $(date +%s) - s ))" >> compile_log.txt
  else
    echo "FAIL $f $(( $(date +%s) - s )) $(echo "$out" | grep -m1 -E 'Error|Killed|line [0-9]+')" >> compile_log.txt
  fi
}
export -f one
ls *.v | xargs -P "$JOBS" -I{} bash -c 'one {}'
echo DONE >> compile_log.txt
