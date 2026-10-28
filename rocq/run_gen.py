"""Mass generation of Rocq lemma files with a log of failures (resumable: existing files are skipped).

usage: run_gen.py A [slice k of n]      lemma A for every lemma-A node and both parities -> rocq/A2/A_<tag>_<par>.v
       run_gen.py B [slice k of n]      lemma B jobs (see jobs_B) -> rocq/B3/B_<tag>_r<r>_<par>.v
"""
import os, sys, json, time, ctypes   # ctypes before rocqgen: it puts ROOT (with its own struct.py) on sys.path
import rocqgen as RG
import nodeform as NF

ROOT = RG.ROOT + 'rocq/'
MINPHYS, MINCOMMIT = 2 << 30, 4 << 30   # free RAM and free commit (RAM + page file) needed to start a job


def memfree():
    """(free physical memory, free commit) in bytes (Windows GlobalMemoryStatusEx)"""
    class MS(ctypes.Structure):
        _fields_ = [('len', ctypes.c_ulong), ('load', ctypes.c_ulong)] + \
                   [(f, ctypes.c_ulonglong) for f in ('tphys', 'aphys', 'tpage', 'apage', 'tvirt', 'avirt', 'aext')]
    m = MS(); m.len = ctypes.sizeof(MS)
    ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))
    return m.aphys, m.apage


def wait_memory(log):
    """block while the machine is short of memory instead of failing jobs (or taking Windows down with it)"""
    told = False
    while True:
        ph, cm = memfree()
        if ph >= MINPHYS and cm >= MINCOMMIT: return
        if not told: log.write('WAIT memory: %.1f GB RAM, %.1f GB commit free\n' % (ph / 2**30, cm / 2**30)); log.flush()
        told = True
        time.sleep(30)


def jobs_A():
    for key in json.load(open(ROOT + 'anodes.json')):
        for par in (0, 1):
            yield ('A', key, par), ROOT + 'A2/A_%s_%d.v' % (NF.tagof(key), par)


def jobs_B():
    """one lemma B per state of every reachable non-partial node, and per (family, r, par) used by partial nodes"""
    nodes = NF.P['nodes']
    for bkey in sorted(NF.P['lemmaB']):
        node, rest = bkey.split(' ## ')
        r = int(rest.split('r=')[1].split()[0]); par = int(rest.split('par=')[1])
        yield ('B', bkey), ROOT + 'B3/B_%s_r%d_%d.v' % (NF.tagof(node), r, par)


def main():
    kind = sys.argv[1]
    k, n = (int(sys.argv[2]), int(sys.argv[3])) if len(sys.argv) > 3 else (0, 1)
    jobs = list(jobs_A() if kind == 'A' else jobs_B())[k::n]
    log = open(ROOT + 'gen_%s_%d.log' % (kind, k), 'a')
    import genA2, genB3
    for job, out in jobs:
        if os.path.exists(out): continue
        os.makedirs(os.path.dirname(out), exist_ok=True)
        wait_memory(log)
        t = time.time()
        try:
            if job[0] == 'A': c = genA2.generate(job[1], job[2], out)
            else: c = genB3.generate(job[1], out)
            log.write('OK %s %d %.0f\n' % (os.path.basename(out), c, time.time() - t))
        except Exception as e:
            log.write('FAIL %s %r | %s\n' % (os.path.basename(out), e, '|'.join(map(str, job[1:]))[:300]))
        log.flush()


if __name__ == '__main__':
    main()
