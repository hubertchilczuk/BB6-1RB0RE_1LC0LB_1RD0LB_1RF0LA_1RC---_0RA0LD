// run until first left-edge visit at/after step S; dump: step state headoffset cells(lo..hi)
#include <stdio.h>
#include <stdlib.h>
static const int W[6][2]={{1,0},{1,0},{1,0},{1,0},{1,-1},{0,0}};
static const int Dd[6][2]={{1,1},{-1,-1},{1,-1},{1,-1},{1,0},{1,-1}};
static const int N[6][2]={{1,4},{2,1},{3,1},{5,0},{2,-1},{0,3}};
int main(int argc,char**argv){
  long long S=atoll(argv[1]); long long SZ=1LL<<32; unsigned char*t=calloc(SZ,1);
  long long p=SZ/2,lo=p,hi=p; int s=0;
  for(long long step=0;;step++){
    int r=t[p]; if(s==4&&r==1){printf("HALT\n");return 1;}
    int ns=N[s][r]; t[p]=W[s][r]; p+=Dd[s][r]; s=ns; if(p>hi)hi=p;
    if(p<lo){lo=p; if(step>=S){ FILE*f=fopen(argv[2],"w"); fprintf(f,"%lld %d %lld\n",step+1,s,p-lo);
        for(long long i=lo;i<=hi;i++)fputc('0'+t[i],f); fprintf(f,"\n"); fclose(f); return 0;}}
  }
}
