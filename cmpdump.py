import os
import sys
D=os.path.dirname(os.path.abspath(__file__)) + '/'
a=open(D+'bdump.txt').read().split(); b=open(D+'rawdump.txt').read().split()
st,s1,hp,cells=a[0],int(a[1]),int(a[2]),a[3]
s2,hp2,cells2=int(b[0]),int(b[1]),b[2]
lo=0
while lo<hp and cells[lo]=='0': lo+=1
hi=len(cells)-1
while hi>hp and cells[hi]=='0': hi-=1
c1=cells[lo:hi+1]; h1=hp-lo
print('steps',st,'state',s1,s2,'head',h1,hp2,'len',len(c1),len(cells2),'EQUAL' if (s1,h1,c1)==(s2,hp2,cells2) else 'DIFFERENT')
