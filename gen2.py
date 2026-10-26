"""Structure helpers with support for the k-family  T = '0 4 3^k 2'."""
import hashlib
import gen, surg
gen.LAST_RUN = True

D = gen.D


def tparts(Tc):
    p, its, tl = surg.parse('1' + Tc)
    return [(x[0], ('1' + Tc)[x[1]:x[2]]) for x in its], tl


def parse(fn, canon):
    st = gen.parse_struct(fn, canon)
    T = st['T']
    st['k'] = None
    if len(T) >= 4 and T[:2] == ['0', '4'] and T[-1] == '2' and all(x == '3' for x in T[2:-1]):
        parts, tl = tparts(st['T_cells'])
        names = [n for n, c in parts]
        assert names == T, (names, T)
        st['k'] = len(T) - 3
        st['kh'] = parts[0][1] + parts[1][1]
        st['k3'] = parts[2][1]
        st['kl'] = parts[-1][1] + tl
        assert st['kh'] + st['k3'] * st['k'] + st['kl'] == st['T_cells']
    return st


def rebuild(st, N, M, out, k=None):
    st2 = dict(st)
    if k is not None:
        assert st.get('k') is not None
        st2['T_cells'] = st['kh'] + st['k3'] * k + st['kl']
    gen.rebuild(st2, N, M, out)


def _h(*parts):
    return hashlib.md5(':'.join(parts).encode()).hexdigest()[:10]


def key(canon, st, family):
    """concrete key (explicit T) or family key (k abstracted, parity kept)."""
    if family:
        assert st['k'] is not None
        h = _h(str(st['state']), st['zone_cells'], st['w_cells'], st['kh'], st['k3'], st['kl'], st['u_cells'], st['tail_cells'].rstrip('0'))
        return canon + ' || FAM 0 4 3^* 2 park=%d / %s / %s / %s' % (st['k'] % 2, ' '.join(st['u']), ' '.join(st['tail']), h)
    return canon + ' || ' + ' / '.join(gen.ctx_key(st)[1:])


def exact_roundtrip(fn, canon):
    st = parse(fn, canon)
    rebuild(st, st['N'], st['M'], fn + '.rt', st['k'])
    a = open(fn).read().split(); b = open(fn + '.rt').read().split()
    return a[1:] == b[1:], st
