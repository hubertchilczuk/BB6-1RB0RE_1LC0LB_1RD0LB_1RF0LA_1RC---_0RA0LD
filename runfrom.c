#include <stdio.h>
#include <stdlib.h>
#include <string.h>
static const int W[6][2]={{1,0},{1,0},{1,0},{1,0},{1,-1},{0,0}};
static const int Dd[6][2]={{1,1},{-1,-1},{1,-1},{1,-1},{1,0},{1,-1}};
static const int N[6][2]={{1,4},{2,1},{3,1},{5,0},{2,-1},{0,3}};
unsigned char*t; long long lo,hi;
// item encoding: value k*4 + kind (0=b,1=c(star),2=other gap)
int items[1<<16]; int extra[1<<16];
int parse(long long from,int maxitems,long long *endpos){
  long long i=from; while(t[i]==0&&i<=hi)i++;
  // gaps after first 1
  int ni=0,k=0; long long pos=i+1; int g=0;
  int gs[8]; 
  while(pos<=hi+8 && ni<maxitems){
    // read next gap
    g=0; while(pos<=hi+8 && t[pos]==0){g++;pos++;} if(pos>hi+8)break; pos++;
    if(g==1){ // check c: next gap 0
      if(t[pos]==1){ items[ni]=k*4+1; extra[ni]=0; ni++; k=0; pos++; continue;}
      k++; continue;}
    if(g==3){items[ni]=k*4;extra[ni]=0;ni++;k=0;continue;}
    items[ni]=k*4+2; extra[ni]=g; ni++; k=0;
  }
  *endpos=pos; return ni;
}
int sitem(char*b,int j){int k=items[j]>>2,kd=items[j]&3; if(kd==0)return sprintf(b,"%d ",k); else if(kd==1)return sprintf(b,"%d* ",k); else return sprintf(b,"%d(%d) ",k,extra[j]);}
void pitem(int j){int k=items[j]>>2,kd=items[j]&3; if(kd==0)printf("%d ",k); else if(kd==1)printf("%d* ",k); else printf("%d(%d) ",k,extra[j]);}
int main(int argc,char**argv){ FILE*fin=fopen(argv[3],"r"); long long st0; int s0; long long off; fscanf(fin,"%lld %d %lld ",&st0,&s0,&off);
  long long maxs=atoll(argv[1]);
  long long SZ=1LL<<32; t=calloc(SZ,1);
  long long p=SZ/2; lo=p;hi=p; int s=s0; { int ch; long long i=SZ/2; while((ch=fgetc(fin))=='0'||ch=='1'){t[i++]=ch-'0';} hi=i-1; p=SZ/2+off; lo=SZ/2; } int lastN=-1; long long cnt=0;
  int verbose=argc>2?atoi(argv[2]):1;
  for(long long step=0;step<maxs;step++){
    int r=t[p];
    if(s==4&&r==1){printf("HALT at %lld\n",step);return 0;}
    int ns=N[s][r]; t[p]=W[s][r]; p+=Dd[s][r]; s=ns;
    if(p>hi)hi=p;
    if(p<lo){lo=p;
      long long e; int ni=parse(lo,60,&e);
      int j; for(j=0;j+1<ni;j++) if(items[j]==9*4&&items[j+1]==8*4)break;
      if(j+1>=ni){ if(lastN!=-2 && verbose){printf("step %lld no-9-8: ",step); for(int q=0;q<ni&&q<40;q++)pitem(q); printf("\n");} lastN=-2; continue;}
      // count 8s
      int ni2=parse(lo,j+2+40000,&e); int q=j+1; while(q<ni2&&items[q]==8*4)q++;
      int n8=q-j-1;
      if(n8!=lastN){ cnt++;
        if(argc>6){ char zb[4096]; int zl=0; for(int z=0;z<j;z++)zl+=sitem(zb+zl,z); if(zl>0)zb[zl-1]=0; else zb[0]=0;
          if(step>1000 && strcmp(zb,argv[6])==0){ printf("ZSTAR N=%d at %lld\n",n8,step); FILE*f=fopen(argv[5],"w"); fprintf(f,"%lld %d %lld\n",step,s,p-lo); for(long long i=lo;i<=hi;i++)fputc(48+t[i],f); fprintf(f,"\n"); fclose(f); return 0;} }
        if(verbose){ printf("step %lld N=%d zone: ",step,n8); for(int z=0;z<j;z++)pitem(z); printf("| "); for(int z=q;z<q+4&&z<ni2;z++)pitem(z); printf("\n"); fflush(stdout);}
        lastN=n8; }
    }
  }
}
