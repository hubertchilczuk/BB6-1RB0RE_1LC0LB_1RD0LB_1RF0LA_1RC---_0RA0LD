#include <stdio.h>
#include <stdlib.h>
static const int W[6][2]={{1,0},{1,0},{1,0},{1,0},{1,-1},{0,0}};
static const int Dd[6][2]={{1,1},{-1,-1},{1,-1},{1,-1},{1,0},{1,-1}};
static const int N[6][2]={{1,4},{2,1},{3,1},{5,0},{2,-1},{0,3}};
int main(int argc,char**argv){ long long S=atoll(argv[1]); long long SZ=1LL<<32; unsigned char*t=calloc(SZ,1);
 long long p=SZ/2,lo=p,hi=p; int s=0;
 for(long long st=0;st<S;st++){int r=t[p]; int ns=N[s][r]; t[p]=W[s][r]; p+=Dd[s][r]; s=ns; if(p<lo)lo=p; if(p>hi)hi=p;}
 while(lo<p && t[lo]==0)lo++; while(hi>p && t[hi]==0)hi--;
 printf("%d %lld\n",s,p-lo); for(long long i=lo;i<=hi;i++)putchar('0'+t[i]); putchar('\n');}
