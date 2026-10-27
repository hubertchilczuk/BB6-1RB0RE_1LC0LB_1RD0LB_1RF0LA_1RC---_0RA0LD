"""Generate Rocq proofs of lemma A for every node the closure uses (rocq/A/A_<tag>.v).

Lemma A of node (Z, w, T, u, tail, P, dM):
    0inf {{C}}> Z *> w^P *> w^^n *> T *> u^^m *> tail *> 0inf  -->+  0inf {{C}}> Z *> w^^n *> T *> u^^(m+dM) *> tail *> 0inf
for all n, m (families: T = kh *> k3^^k *> kl, for all k).
Split into sub-lemmas between sweep checkpoints (every G-th new-leftmost event), found by plain simulation of
two instances with different (n, m, k); every checkpoint must be  prefix *> w^(e+n) *> T(k) *> u^(d+m) *> tail
with prefix, e, d independent of the instance. Each sub-lemma is proved by es' (busycoq ES_v3).
usage: gen_lemmaA_all.py [G] [node-index ...]
"""
import os, sys, json, subprocess, hashlib
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/'
sys.path.insert(0, ROOT)
import samples

EVT = ROOT + 'an/evtapes.exe'
TMP = ROOT + 'rocq/tmp/'
OUTD = ROOT + 'rocq/A/'
os.makedirs(TMP, exist_ok=True); os.makedirs(OUTD, exist_ok=True)
P = json.load(open(ROOT + 'proof4.json'))
S = samples.load()
tagof = lambda key: hashlib.md5(key.encode()).hexdigest()[:8]
INST = [(7, 11, 5), (12, 19, 8)]
ROT = json.load(open(ROOT + 'rocq/rot.json')) if os.path.exists(ROOT + 'rocq/rot.json') else {}   # node -> rotation of k3


def lit(cells):
    return '[' + ';'.join(cells) + ']'


class Node:
    def __init__(self, key):
        st = S[key]; self.key = key
        self.fam = ' || FAM ' in key
        self.Z, self.w, self.u = st['zone_cells'], st['w_cells'], st['u_cells']
        self.tail = st['tail_cells'].rstrip('0')
        if self.fam:
            self.kh, self.k3, self.kl = st['kh'], st['k3'], st['kl']
            while self.kh.endswith(self.k3): self.kh = self.kh[:-len(self.k3)]   # k counts every copy of k3
            j = ROT.get(key, 0)
            if j:   # k3 = a b:  kh k3^(k+1) kl = (kh a) (b a)^k (b kl), so that the shift rule over the run closes
                a_, b_ = self.k3[:j], self.k3[j:]
                self.kh, self.k3, self.kl = self.kh + a_, b_ + a_, b_ + self.kl
                while self.kh.endswith(self.k3): self.kh = self.kh[:-len(self.k3)]
        else:
            self.T = st['T_cells']
        self.P, self.dM = P['nodes'][key]['P'], P['nodes'][key]['dM']
        assert st['state'] == 2

    def Tc(self, k):
        return self.kh + self.k3 * k + self.kl if self.fam else self.T

    def tape(self, N, M, k):
        return self.Z + self.w * N + self.Tc(k) + self.u * M + self.tail

    def split(self, tape, n, m, k):
        """tape = prefix + w^(e+n) + T(k) + u^(d+m) + tail -> (prefix, e, d), greedy from the right"""
        assert tape.endswith(self.tail), 'tail'
        rest = tape[:len(tape) - len(self.tail)]
        uc = 0
        while rest.endswith(self.u): rest = rest[:-len(self.u)]; uc += 1
        if self.fam:
            assert rest.endswith(self.kl), 'kl'
            rest = rest[:-len(self.kl)]
            kc = 0
            while rest.endswith(self.k3): rest = rest[:-len(self.k3)]; kc += 1
            assert kc == k, 'k changed'
            assert rest.endswith(self.kh), 'kh'
            rest = rest[:-len(self.kh)]
        else:
            assert rest.endswith(self.T), 'T'
            rest = rest[:-len(self.T)]
        wc = 0
        while rest.endswith(self.w): rest = rest[:-len(self.w)]; wc += 1
        return rest, wc - n, uc - m

    def checkpoints(self, n, m, k):
        cfg = TMP + 'inst_%s_%d_%d_%d.txt' % (tagof(self.key), n, m, k)
        open(cfg, 'w').write('0 2 0\n%s\n' % self.tape(self.P + n, m, k))
        target = self.tape(n, m + self.dM, k)
        out = subprocess.run([EVT, cfg, '2000000000', '200000'], capture_output=True, text=True).stdout.split('\n')
        os.remove(cfg)
        cps = []
        for i in range(0, len(out) - 1, 2):
            step, state = map(int, out[i].split())
            assert state == 2, 'checkpoint not in state C'
            cps.append(self.split(out[i + 1], n, m, k))
            if out[i + 1] == target: return cps
        raise RuntimeError('target not reached')

    def side(self, prefix, e, d):
        parts = [lit(prefix + self.w * e), '(w^^n)']
        parts += ['kh', '(k3^^k)', 'kl'] if self.fam else ['T']
        parts.append('(u^^m)')
        if self.tail: parts.append('tl')
        return ' *> '.join(parts) + ' *> 0inf'

    def generate(self, G):
        a, b = [self.checkpoints(*i) for i in INST]
        assert len(a) == len(b), 'event counts differ'
        assert a == b, 'checkpoints depend on n, m, k'
        n0, m0, k0 = INST[0]
        cps = [self.split(self.tape(self.P + n0, m0, k0), n0, m0, k0)] + [a[i] for i in range(G - 1, len(a) - 1, G)] + [a[-1]]
        assert cps[-1][0] + self.w * cps[-1][1] == cps[0][0] + self.w * (cps[0][1] - self.P) and cps[-1][2] - cps[0][2] == self.dM
        vars_ = 'n m k' if self.fam else 'n m'
        defs = ['Definition w : list sym := %s.' % lit(self.w), 'Definition u : list sym := %s.' % lit(self.u)]
        if self.fam:
            defs += ['Definition kh : list sym := %s.' % lit(self.kh), 'Definition k3 : list sym := %s.' % lit(self.k3),
                     'Definition kl : list sym := %s.' % lit(self.kl)]
        else:
            defs.append('Definition T : list sym := %s.' % lit(self.T))
        if self.tail: defs.append('Definition tl : list sym := %s.' % lit(self.tail))
        unf = 'w, u, ' + ('kh, k3, kl' if self.fam else 'T') + (', tl' if self.tail else '')
        v = ['(* generated by rocq/gen_lemmaA_all.py: lemma A of node', '   %s' % self.key.replace('*)', '* )'),
             '   P = %d, dM = %d, %d sweeps, %d sub-lemmas *)' % (self.P, self.dM, len(a), len(cps) - 1),
             'From BusyCoq Require Import Individual62 ES_v3.', 'Require Import Lia String NArith.', 'Open Scope list.', '',
             'Definition tm := Eval compute in (TM_from_str "1RB0RE_1LC0LB_1RD0LB_1RF0LA_1RC---_0RA0LD").',
             """Notation "c -->+ c'" := (c -[ tm ]->+ c') (at level 40).""", ''] + defs + ['',
             'Lemma u_add m d r : (u^^(m+d)) *> r = (u^^m) *> (u^^d) *> r.',
             'Proof. rewrite lpow_add, Str_app_assoc. reflexivity. Qed.', '']
        for i, (p_, e_, d_) in enumerate(cps):
            v.append('Definition cfg%d %s : Q * tape := 0inf {{C}}> %s.' % (i, vars_, self.side(p_, e_, 0)))
        v.append('')
        deltas = []
        for i in range(len(cps) - 1):
            dlt = cps[i + 1][2] - cps[i][2]; deltas.append(dlt)
            v += ['Lemma sub%d %s : cfg%d %s -->+ cfg%d %s.' % (i, vars_, i, vars_, i + 1, vars_.replace('m', '(m + %d)' % dlt)),
                  "Proof. unfold cfg%d, cfg%d. rewrite u_add. unfold %s. cbn [lpow app]. es' %s. Qed." % (i, i + 1, unf, vars_), '']
        last = len(cps) - 1
        v += ['Theorem lemmaA %s : cfg0 %s -->+ cfg%d %s.' % (vars_, vars_, last, vars_.replace('m', '(m + %d)' % self.dM)),
              'Proof.', '  replace (m + %d) with (m%s) by lia.' % (self.dM, ''.join(' + %d' % x for x in deltas))]
        acc = 'm'
        for i in range(last - 1):
            v.append('  eapply progress_trans; [apply (sub%d %s)|].' % (i, vars_.replace('m', '(%s)' % acc)))
            acc = '%s + %d' % (acc, deltas[i])
        v += ['  apply (sub%d %s).' % (last - 1, vars_.replace('m', '(%s)' % acc)), 'Qed.', '']
        rest = (' *> kh *> (k3^^k) *> kl' if self.fam else ' *> T') + ' *> (u^^m)' + (' *> tl' if self.tail else '') + ' *> 0inf'
        v += ['Lemma cfg0_eq %s : cfg0 %s = 0inf {{C}}> %s *> (w^^n)%s.' % (vars_, vars_, lit(self.Z + self.w * self.P), rest),
              'Proof. reflexivity. Qed.',
              'Lemma cfgF_eq %s : cfg%d %s = 0inf {{C}}> %s *> (w^^n)%s.' % (vars_, last, vars_, lit(self.Z), rest),
              'Proof. reflexivity. Qed.']
        fn = OUTD + 'A_%s.v' % tagof(self.key)
        open(fn, 'w').write('\n'.join(v) + '\n')
        return fn, len(a), len(cps) - 1


if __name__ == '__main__':
    G = int(sys.argv[1]) if len(sys.argv) > 1 else 25
    nodes = json.load(open(ROOT + 'rocq/anodes.json'))
    idx = [int(x) for x in sys.argv[2:]] or range(len(nodes))
    index = {}
    for i in idx:
        key = nodes[i]
        if os.environ.get('SKIP_EXISTING') and os.path.exists(OUTD + 'A_%s.v' % tagof(key)):
            index[tagof(key)] = key; continue
        try:
            fn, ev, ns = Node(key).generate(G)
            index[tagof(key)] = key
            print('%3d %s sweeps %d sub-lemmas %d' % (i, os.path.basename(fn), ev, ns), flush=True)
        except Exception as e:
            print('%3d FAILED %s: %r' % (i, key[:70], e), flush=True)
    json.dump({tagof(k): k for k in nodes}, open(OUTD + 'index.json', 'w'), indent=1)
