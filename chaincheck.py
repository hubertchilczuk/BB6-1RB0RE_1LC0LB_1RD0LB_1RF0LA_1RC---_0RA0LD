import json, subprocess, re
import prover2 as P2
import lemmaA_odd  # samples
D = P2.D; P = P2.proof
exec(open(D + 'verify3.py').read().split("start = next(")[0].replace("MSTAR = int(sys.argv[1]) if len(sys.argv) > 1 else 500", "MSTAR = 500"))
start = next(k for k in P['lemmaA'] if k.startswith('1 7 0 0* 4 3 0 0 0 0 0 9 | 8  || 3 / 0 1 / 0 / 6542ed25be'))
t, r, M, k = start, 24, 5533, None
for it in range(6):
    pred = step(t, r, M, k, ('chain', it))
    # concrete: build the last canonical config and run fsim to the next canonical point, then descend with fsim
    src, B = lemmaB_for(t, r, M % 2, k)
    node = t; s = P2.samples[node] if node in P2.samples else None
    cfg = D + 'chain_in.txt'; out = D + 'chain_out.txt'
    P2.build(node if node in P2.samples else src, r, M, k if P2.is_family(node if node in P2.samples else src) else None, cfg)
    subprocess.run([D + 'fsim.exe', '20', '1e17', cfg, P2.CANON, out], capture_output=True)
    c2 = B['target'].split(' || ')[0]
    st2, ck2, fk2 = P2.classify(out, c2)
    ev = lambda c: None if c is None else c[0] + c[1] * ((M - 1000 - M % 2) // 2) + c[2] * (kvar(src, k))
    print('cycle %d: from r=%d M=%d k=%s | lemma predicts N1=%s M1=%s k1=%s | fsim gives N1=%d M1=%d k1=%s' % (
        it, r, M, k, ev(B['N1']), ev(B['M1']), ev(B['K1']), st2['N'], st2['M'], st2['k']))
    if pred is None: print('chain error', errs[-3:]); break
    t, r, M, k = pred
print('errors', len(errs))
