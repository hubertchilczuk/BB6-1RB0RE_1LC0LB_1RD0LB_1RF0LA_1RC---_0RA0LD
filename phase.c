// load cfg (or blank), run; at each new-leftmost visit parse items; find first long run (period 1..4, reps>=MINREP)
// print "step count zone|word" whenever count or zone changes. Optional stop: zone|word string match -> dump cfg.
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
static const int W[6][2]={{1,0},{1,0},{1,0},{1,0},{1,-1},{0,0}};
static const int Dd[6][2]={{1,1},{-1,-1},{1,-1},{1,-1},{1,0},{1,-1}};
static const int N[6][2]={{1,4},{2,1},{3,1},{5,0},{2,-1},{0,3}};
unsigned char*t; long long lo,hi;
#define MAXI 600
int it[MAXI+8];  // encoded item: k*64 + kind*16 + g (g<16)
int parse(long long from, long long*runend_cells){
  long long i=from; while(i<=hi&&t[i]==0)i++;
  long long pos=i+1; int ni=0,k=0;
  while(pos<=hi+8&&ni<MAXI){ int g=0; while(pos<=hi+8&&t[pos]==0){g++;pos++;} if(pos>hi+8)break; pos++;
    if(g==1){ if(t[pos]==1){it[ni++]=k*64+1*16; k=0; pos++; continue;} k++; continue;}
    if(g==3){it[ni++]=k*64; k=0; continue;}
    it[ni++]=k*64+2*16+(g<15?g:15); k=0; }
  return ni;
}
int sitem(char*b,int v){int k=v>>6,kd=(v>>4)&3,g=v&15; if(kd==0)return sprintf(b,"%d ",k); if(kd==1)return sprintf(b,"%d* ",k); return sprintf(b,"%d(%d) ",k,g);}
int MINREP=12;
int findrun(int ni,int*pi,int*pp,int*reps){
  for(int i=0;i<ni;i++) for(int p=1;p<=4;p++){ int r=1; while(i+(r+1)*p<=ni && memcmp(it+i,it+i+r*p,p*sizeof(int))==0) r++;
      if(r>=MINREP){*pi=i;*pp=p;*reps=r;return 1;} }
  return 0;
}
long long countrun(long long from,int i,int p){ // exact count by reparsing with larger limit not available; approximate via cells
  return 0;}
int main(int argc,char**argv){
  long long maxs=atoll(argv[1]); const char*cfg=argc>2?argv[2]:"-"; const char*stopz=argc>3?argv[3]:NULL; const char*outc=argc>4?argv[4]:NULL;
  long long SZ=1LL<<33; t=calloc(SZ,1); long long p=SZ/2; lo=p;hi=p; int s=0; long long st0=0;
  if(strcmp(cfg,"-")){ FILE*fin=fopen(cfg,"r"); long long off; fscanf(fin,"%lld %d %lld ",&st0,&s,&off); long long i=SZ/2; int ch; while((ch=fgetc(fin))=='0'||ch=='1')t[i++]=ch-'0'; fclose(fin); hi=i-1; p=SZ/2+off; lo=SZ/2; }
  char last[8192]=""; long long lastc=-1;
  for(long long step=0;step<maxs;step++){
    int r=t[p]; if(N[s][r]<0){printf("HALT at %lld\n",step);return 0;}
    int ns=N[s][r]; t[p]=W[s][r]; p+=Dd[s][r]; s=ns; if(p>hi)hi=p;
    if(p<lo){lo=p;
      long long e; int ni=parse(lo,&e); int i,pp,reps;
      char zb[8192]; int zl=0;
      if(!findrun(ni,&i,&pp,&reps)){ i=ni; pp=0; reps=0; }
      for(int z=0;z<i;z++)zl+=sitem(zb+zl,it[z]); zl+=sprintf(zb+zl,"| ");
      for(int z=i;z<i+pp;z++)zl+=sitem(zb+zl,it[z]);
      // count full reps: reparse can't exceed MAXI; count reps in cells by scanning period length in cells
      long long cnt=reps;
      if(pp>0 && reps>=(MAXI-i)/pp-1){ // need longer count: scan cells
        // compute cell length of word and starting cell; brute: walk items again from lo, tracking cell positions
        long long q=lo; while(t[q]==0)q++; q++; int idx=0; long long wstart=-1; int k=0;
        long long pos=q; long long itemstart=q; long long starts[MAXI+8]; int nn=0;
        while(nn<=i+pp && pos<=hi){ int g=0; long long st_=itemstart; while(t[pos]==0){g++;pos++;} pos++;
          if(g==1){ if(t[pos]==1){starts[nn++]=st_; pos++; itemstart=pos; continue;} continue;}
          starts[nn++]=st_; itemstart=pos; }
        long long ws=starts[i], wl=starts[i+pp]-starts[i];
        cnt=0; while(ws+(cnt+1)*wl<=hi && memcmp(t+ws,t+ws+cnt*wl,wl)==0) cnt++;
      }
      if(cnt!=lastc || strcmp(zb,last)){
        printf("%lld %lld %s\n",st0+step,cnt,zb); fflush(stdout);
        if(stopz && step>1000 && strcmp(zb,stopz)==0){ if(outc){FILE*f=fopen(outc,"w"); fprintf(f,"%lld %d %lld\n",st0+step,s,p-lo); for(long long k2=lo;k2<=hi;k2++)fputc('0'+t[k2],f); fprintf(f,"\n"); fclose(f);} printf("STOP\n"); return 0;}
        lastc=cnt; strcpy(last,zb);
      }
    }
  }
}
