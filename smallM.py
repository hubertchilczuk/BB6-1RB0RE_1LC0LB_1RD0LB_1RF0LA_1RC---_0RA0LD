"""Lemma A first step for small concrete M (N symbolic): (N+P, M) -> (N, M+dM)."""
import json, sys, re
import prover2 as P2
import lemmaA_odd  # noqa: registers samples (and recomputes nothing new)
D = P2.D; proof = P2.proof
proof.setdefault('lemmaA_smallM', {})
needed = [(l.split('|||')[0], int(l.split('|||')[1])) for l in open(D + 'smallM_needed.txt').read().strip().splitlines()]
for anode, Mv in needed:
    key = '%s ## M=%d' % (anode, Mv)
    if key in proof['lemmaA_smallM']: continue
    fam = P2.is_family(anode); s = P2.samples[anode]; canon = anode.split(' || ')[0]
    kk = P2.K0 + s['k'] % 2 if fam else None
    tag = 'Q' + P2.tagof(key)
    f = [D + 'p2_%s_%s.txt' % (tag, q) for q in 'abc']
    P2.build(anode, P2.N0, Mv, kk, f[0]); P2.build(anode, P2.N0 + 1, Mv, kk, f[1]); vars_ = [f[1]]
    if fam: P2.build(anode, P2.N0, Mv, kk + 2, f[2]); vars_.append(f[2])
    insts = [(0, 0), (1, 0), (4, 1)] if fam else [(0,), (1,), (9,)]
    res = P2.run_ssim(f[0], vars_, insts, tag)
    A = proof['lemmaA'][anode]; ok = res['status'] == 'CANON' and res['canon'] == canon
    if ok:
        for i, fn in res['files'].items():
            st2, ck2, fk2 = P2.classify(fn, canon)
            if (fk2 if fam else ck2) != anode or st2['N'] != P2.N0 + i[0] - A['P'] or st2['M'] != Mv + A['dM']:
                ok = False
    proof['lemmaA_smallM'][key] = {'ok': ok, 'status': res['status'], 'constraints': res.get('constraints', '')}
    print('SMALLM', anode[:70], Mv, ok, res.get('constraints', ''), flush=True)
P2.save()
