"""Build ssim4dbg.cpp / accel4dbg.inc: ssim4 that also counts (and logs to stderr) accelerations with a symbolic t."""
import os
D = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) + '/'
a = open(D + 'accel4.inc').read()
a = a.replace('ll nmixed=0;', 'll nmixed=0; ll nsym=0;', 1)
a = a.replace('  naccel++;', '  naccel++; if(!isconst(t)) { nsym++; fprintf(stderr,"SYMACCEL t=%s dL=%lld dR=%lld' + '\\' + 'n",ls(t).c_str(),dL.c,dR.c); }', 1)
assert 'nsym++' in a
open(D + 'an/dbg/accel4dbg.inc', 'w', newline='\n').write(a)
s = open(D + 'ssim4.cpp').read().replace('#include "accel4.inc"', '#include "accel4dbg.inc"')
old = 'mixedlimits=%lld' + '\\' + 'n",macro,naccel,nmixed);'
assert old in s, 'printf not found'
s = s.replace(old, 'mixedlimits=%lld symaccel=%lld' + '\\' + 'n",macro,naccel,nmixed,nsym);')
open(D + 'an/dbg/ssim4dbg.cpp', 'w', newline='\n').write(s)
print('ok')
