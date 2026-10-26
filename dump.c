#include <stdio.h>
#include <stdlib.h>
#include <string.h>
static const int W[6][2]={{1,0},{1,0},{1,0},{1,0},{1,-1},{0,0}};
static const int Dd[6][2]={{1,1},{-1,-1},{1,-1},{1,-1},{1,0},{1,-1}};
static const int N[6][2]={{1,4},{2,1},{3,1},{5,0},{2,-1},{0,3}};
long long SZ; unsigned char*t;
void dumptape(long long lo,long long hi,long long step){
  // gaps -> tokens a(1) b(3) c(1,0) else (g); then encode count of a's before b/c etc with RLE
  static char buf[1<<24]; int bl=0;
  static int gs[1<<22]; int ng=0; int g=0;
  long long i=lo; while(i<=hi && t[i]==0)i++;
  int lead=i-lo;
  for(;i<=hi;i++){ if(t[i]){gs[ng++]=g;g=0;} else g++; }
  // tokens
  static char tk[1<<22]; static int tv[1<<22]; int nt=0;
  for(int j=1;j<ng;j++){ int h=gs[j];
    if(h==1 && j+1<ng && gs[j+1]==0){tk[nt]='c';tv[nt++]=0;j++;}
    else if(h==1){tk[nt]='a';tv[nt++]=0;} else if(h==3){tk[nt]='b';tv[nt++]=0;}
    else {tk[nt]='x';tv[nt++]=h;} }
  // compress: numbers k = a's before b ; c -> k*, x -> k(h)
  static char item[1<<22][12]; int ni=0; int k=0;
  for(int j=0;j<nt;j++){ if(tk[j]=='a'){k++;continue;}
    if(tk[j]=='b') sprintf(item[ni++],"%d",k); else if(tk[j]=='c') sprintf(item[ni++],"%d*",k); else sprintf(item[ni++],"%d(%d)",k,tv[j]); k=0;}
  sprintf(item[ni++],"+%d",k);
  printf("step %lld width %lld: ",step,hi-lo);
  int j=0; int printed=0;
  while(j<ni){ int e=j; while(e<ni && strcmp(item[e],item[j])==0)e++;
    // also detect period-2 repetition
    if(e-j==1 && j+3<ni && strcmp(item[j],item[j+2])==0 && strcmp(item[j+1],item[j+3])==0){
      int r=j; while(r+3<ni && strcmp(item[r],item[r+2])==0&&strcmp(item[r+1],item[r+3])==0) r+=2;
      int reps=(r-j)/2+1; printf("[%s %s]^%d ",item[j],item[j+1],reps); j+=2*reps; continue;}
    if(e-j==1)printf("%s ",item[j]); else printf("%s^%d ",item[j],e-j); j=e;
    if(++printed>200){printf("...");break;} }
  printf("\n"); fflush(stdout);
}
int main(int argc,char**argv){
  long long maxs=atoll(argv[1]); double fac=atof(argv[2]);
  SZ=1LL<<31; t=calloc(SZ,1);
  long long p=SZ/2,lo=p,hi=p; int s=0; double next=1000;
  for(long long step=0;step<maxs;step++){
    int r=t[p];
    if(s==4&&r==1){printf("HALT at %lld\n",step);return 0;}
    int ns=N[s][r]; t[p]=W[s][r]; p+=Dd[s][r]; s=ns;
    if(p>hi)hi=p;
    if(p<lo){lo=p; if(step>=next){ dumptape(lo,hi,step); next*=fac; }}
  }
}
