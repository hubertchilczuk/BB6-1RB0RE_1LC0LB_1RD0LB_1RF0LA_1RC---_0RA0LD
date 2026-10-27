"""Exceptional states: landings below the domain (M < 500) with constant N and M in a family (k free).

Scans all closure cases (genClose, dry), registers every such landing state (family, parity, r, h, smallest y) in
rocq/F/exc.json (they become extra Dom constructors, see genF.py) and generates their lemma B with the fixed M
(rocq/B3/BX_<tag>_r<r>_<par>_h<h>.v).
usage: genExc.py
"""
import json
import rocqgen as RG
import nodeform as NF
import genClose as GC
import genB3

GC.DRY = True
found = {}
for c, info in sorted(GC.DOM.items()):
    kind = info['kind']; yinfo = info.get('yf') if kind == 'family' else info.get('yfix')
    for r in range(GC.NB, GC.NB + info['P']):
        try:
            GC.case('x', info['key'], info['par'], r, kind, yinfo)
        except GC.Exceptional as e:
            d = e.args[1]
            k = (d['key'], d['par'], d['r'], d['h'])
            found[k] = min(found.get(k, d['ymin']), d['ymin'])
            print('exceptional landing from', c, 'r', r, '->', NF.tagof(d['key']), d['par'], d['r'], d['h'], 'y >=', d['ymin'])
        except Exception:
            pass
exc = []
for (key, par, r, h), ymin in sorted(found.items()):
    node = NF.Node(key)
    tag = node.tag
    e = dict(key=key, par=par, r=r, h=h, ymin=ymin, ctor='domx_%s_%d_r%d_h%d' % (tag, par, r, h),
             bfile='BX_%s_r%d_%d_h%d' % (tag, r, par, h))
    bkey = '%s ## r=%d par=%d' % (key, r, par)
    n = genB3.generate(bkey, RG.ROOT + 'rocq/B3/%s.v' % e['bfile'], 200, Mfix=par + 2 * h, Kmin=node.kp + 2 * ymin)
    print('lemma B for', e['ctor'], 'checkpoints', n)
    exc.append(e)
json.dump(exc, open(RG.ROOT + 'rocq/F/exc.json', 'w'), indent=1)
print('exceptional states:', len(exc))
