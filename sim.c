#include <stdio.h>
#include <stdlib.h>
#include <string.h>
// 1RB0RE_1LC0LB_1RD0LB_1RF0LA_1RC---_0RA0LD
// A=0..F=5
static const int W[6][2]={{1,0},{1,0},{1,0},{1,0},{1,-1},{0,0}};
static const int Dd[6][2]={{1,1},{-1,-1},{1,-1},{1,-1},{1,0},{1,-1}};
static const int N[6][2]={{1,4},{2,1},{3,1},{5,0},{2,-1},{0,3}};
int main(int argc,char**argv){
  long long maxs=atoll(argv[1]);
  long long SZ=1LL<<31; unsigned char*t=calloc(SZ,1);
  long long p=SZ/2,lo=p,hi=p; int s=0;
  long long cnt[6][2]={0};
  long long step=0, nextrep=1;
  for(step=0;step<maxs;step++){
    int r=t[p];
    cnt[s][r]++;
    if(s==4&&r==1){printf("HALT at step %lld\n",step);break;}
    int ns=N[s][r]; t[p]=W[s][r]; p+=Dd[s][r]; s=ns;
    if(p<lo)lo=p; if(p>hi)hi=p;
    if(p<=0||p>=SZ-1){printf("tape overflow\n");break;}
    if(step==nextrep){ long long ones=0; for(long long i=lo;i<=hi;i++)ones+=t[i];
      printf("step %lld width %lld (L %lld R %lld) ones %lld\n",step,hi-lo+1,SZ/2-lo,hi-SZ/2,ones); fflush(stdout); nextrep*=4;}
  }
  for(int i=0;i<6;i++)printf("%c: %lld %lld\n",'A'+i,cnt[i][0],cnt[i][1]);
}
