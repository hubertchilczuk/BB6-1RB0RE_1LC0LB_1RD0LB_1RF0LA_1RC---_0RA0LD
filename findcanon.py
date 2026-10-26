"""Find canonical zone strings for long consumption phases in an fsim 'events' log (RUNS=1 format).
For each maximal phase with the same front word lasting >= MINEV events, pick the zone string that
recurs most often (>=3 times); report it if not already in the canonical list."""
import sys
from collections import Counter

MINEV = 400


def phases(fn):
    cur = None; zs = []
    for l in open(fn):
        if not l[0].isdigit():
            continue
        st, z = l.rstrip('\n').split(' ', 1)
        z = z.split('##')[0]
        if not z.endswith(' '):
            z = z + ' ' if z.strip().split('|')[1].strip() else z
        w = z.split('|')[1].strip()
        t = w.split()
        w = ' '.join(min(t[i:] + t[:i] for i in range(len(t)))) if t else ''   # rotation class
        if w != cur:
            if cur is not None:
                yield cur, zs
            cur = w; zs = []
        zs.append(z.rstrip() + ' ')
    if cur is not None:
        yield cur, zs


def candidates(fn, known):
    out = []
    for w, zs in phases(fn):
        if len(zs) < MINEV or not w:
            continue
        c = Counter(zs)
        if any(z in known for z in c):
            continue
        top = max(c.values())
        if top < 3:
            continue
        best = min(z for z, v in c.items() if v == top)
        out.append((w, len(zs), top, best))
    return out


if __name__ == '__main__':
    known = set(l.rstrip('\n') for l in open(sys.argv[2]) if l.strip())
    for w, n, top, z in candidates(sys.argv[1], known):
        print('PHASE [%s] events=%d recur=%d -> %s' % (w, n, top, z))
