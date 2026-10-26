import gen, sys
D=gen.D
C8='1 7 0 0* 4 3 0 0 0 0 0 9 | 8 '
src=gen.parse_struct(D+sys.argv[1],sys.argv[2])
r=int(sys.argv[3])
for M in eval(sys.argv[4]):
    gen.rebuild(src,r,M,D+'min.txt')
    status,c2,_=gen.run_to_canon(D+'min.txt',D+'canon_all.txt',D+'mout.txt')
    if status=='CANON':
        s2=gen.parse_struct(D+'mout.txt',c2); T2=' '.join(s2['T'])
        if s2['T'][:2]==['0','4']: T2='0 4 3^%d 2'%(len(s2['T'])-3)
        print('M=%d ->'%M,'R8' if '| 8' in c2 else 'R031',T2,'N1=',s2['N'],'M1=',s2['M'],flush=True)
    else: print('M=%d'%M,status)
