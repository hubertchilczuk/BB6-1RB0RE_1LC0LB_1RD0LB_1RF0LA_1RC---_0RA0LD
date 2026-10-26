import os
D=os.path.dirname(os.path.abspath(__file__)) + '/'
s=open(D+'runfrom.c').read()
NL=chr(92)+'n'
s=s.replace('void pitem(int j){','int sitem(char*b,int j){int k=items[j]>>2,kd=items[j]&3; if(kd==0)return sprintf(b,"%d ",k); else if(kd==1)return sprintf(b,"%d* ",k); else return sprintf(b,"%d(%d) ",k,extra[j]);}\nvoid pitem(int j){')
old='        if(verbose){ printf("step %lld N=%d zone: ",step,n8);'
new=('        if(argc>6){ char zb[4096]; int zl=0; for(int z=0;z<j;z++)zl+=sitem(zb+zl,z); if(zl>0)zb[zl-1]=0; else zb[0]=0;\n'
     '          if(step>1000 && strcmp(zb,argv[6])==0){ printf("ZSTAR N=%d at %lld'+NL+'",n8,step); FILE*f=fopen(argv[5],"w"); fprintf(f,"%lld %d %lld'+NL+'",step,s,p-lo); for(long long i=lo;i<=hi;i++)fputc(48+t[i],f); fprintf(f,"'+NL+'"); fclose(f); return 0;} }\n'
     + old)
assert old in s
s=s.replace(old,new)
open(D+'runfrom.c','w').write(s)
