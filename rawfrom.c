#include <stdio.h>
#include <stdlib.h>
static const int W[6][2]={{1,0},{1,0},{1,0},{1,0},{1,-1},{0,0}};
static const int Dd[6][2]={{1,1},{-1,-1},{1,-1},{1,-1},{1,0},{1,-1}};
static const int N[6][2]={{1,4},{2,1},{3,1},{5,0},{2,-1},{0,3}};
int main(int argc,char**argv){ long long S=atoll(argv[1]); long long SZ=1LL<<32; unsigned char*t=calloc(SZ,1);
 FILE*fin=fopen(argv[2],"r"); long long st0,off; int s; fscanf(fin,"%lld %d %lld ",&st0,&s,&off);
 long long i=SZ/2; int ch; while((ch=fgetc(fin))=='0'||ch=='1')t[i++]=ch-'0';
 long long p=SZ/2+off,lo=SZ/2,hi=i-1;
 for(long long st=0;st<S;st++){int r=t[p]; if(N[s][r]<0){printf("HALT\n");return 0;} int ns=N[s][r]; t[p]=W[s][r]; p+=Dd[s][r]; s=ns; if(p<lo)lo=p; if(p>hi)hi=p;}
 while(lo<p && t[lo]==0)lo++; while(hi>p && t[hi]==0)hi--;
 printf("%d %lld\n",s,p-lo); for(long long i=lo;i<=hi;i++)putchar('0'+t[i]); putchar('\n');}
