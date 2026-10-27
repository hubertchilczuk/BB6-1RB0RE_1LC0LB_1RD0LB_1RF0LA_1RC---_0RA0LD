"""Node configurations in the canonical representation shared by lemma A, lemma B and the closure.

A node config is  Z w^N T(k) u^M tail  (sample cells, T(k) = kh k3^(k + kshift) kl for nodes with the k-structure).
Parameters: N, h with M = par + 2h, and (k-structure) y with k = kp + 2y, kp = the parity of k.
The node form off(node, par) is the rocqgen canonical rendering of these tapes in which exactly the runs that depend
on (N, h, y) are variable runs; its Rocq arguments are the run values (in units), affine in (N, h, y).
"""
import json
import rocqgen as RG
import samples

P = json.load(open(RG.ROOT + 'proof4.json'))
S = samples.load()


def tagof(key):
    import hashlib
    return hashlib.md5(key.encode()).hexdigest()[:8]


class Node:
    """fam: the node has the k-structure (family keys: k symbolic; other nodes: k = kfix)"""
    def __init__(self, key):
        self.key = key; self.tag = tagof(key)
        st = S[key]
        self.family_key = ' || FAM ' in key
        self.fam = st.get('k') is not None
        self.Z, self.w, self.u = st['zone_cells'], st['w_cells'], st['u_cells']
        self.tail = st['tail_cells'].rstrip('0')
        if self.fam:
            self.kh, self.k3, self.kl = st['kh'], st['k3'], st['kl']
            self.kshift = 0                        # copies of k3 at the end of kh
            while self.kh.endswith(self.k3):
                self.kh = self.kh[:-len(self.k3)]; self.kshift += 1
            self.kp = (int(key.split('park=')[1][0]) if self.family_key else st['k']) % 2
            self.kfix = None if self.family_key else st['k']
        else:
            self.T = st['T_cells']
        ni = P['nodes'].get(key, {})
        self.P, self.dM, self.rlow = ni.get('P'), ni.get('dM'), ni.get('r_low')

    def tape(self, N, M, k=None):
        if self.fam:
            k = self.kfix if k is None else k
            Tc = self.kh + self.k3 * (k + self.kshift) + self.kl
        else:
            Tc = self.T
        return self.Z + self.w * N + Tc + self.u * M + self.tail

    def tape_p(self, par, N, h, y=None):
        return self.tape(N, par + 2 * h, self.kp + 2 * y if self.fam and y is not None else None)

    def params(self):
        return ('N', 'h', 'y') if self.fam else ('N', 'h')

    def design(self):
        base = (60, 150, 20)[:len(self.params())]
        steps = (7, 11, 6)[:len(base)]
        rows = [base]
        for j in range(len(base)):
            r = list(base); r[j] += steps[j]; rows.append(tuple(r))
        rows.append(tuple(b + 2 + j for j, b in enumerate(base)))
        return rows

    def pieces(self, par):
        rows = self.design()
        return RG.family([self.tape_p(par, *r) for r in rows], rows)

    def mask(self, par):
        return [any(coef) for _, _, coef in self.pieces(par)]

    def form(self, par):
        """(tokens, values) of the node form: values[j] = (const, coeffs over params) in units"""
        pcs = self.pieces(par)
        return RG.canon(pcs, [any(c) for _, _, c in pcs])

    def name(self, par):
        return 'off_%s_%d' % (self.tag, par)

    def check_skeleton(self, pieces, par):
        mine = self.pieces(par)
        if [p[0] for p in mine] != [p[0] for p in pieces]:
            raise ValueError('checkpoint skeleton differs from the node form of %s' % self.key[:60])
        return [any(c) for _, _, c in mine]

    def values(self, par, N, h, y=None):
        """Rocq arguments of the node form (tape order) for given parameters"""
        toks, vals = self.form(par)
        args = []
        for t in toks:
            if t[0] == 'var':
                c, f = vals[t[1]]
                args.append(c + sum(a * b for a, b in zip(f, (N, h, y)[:len(f)])))
        return args
