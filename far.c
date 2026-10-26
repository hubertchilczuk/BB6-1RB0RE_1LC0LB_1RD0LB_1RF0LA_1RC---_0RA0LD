// FAR (finite automata reduction) with DFA enumeration on left side.
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
typedef uint64_t u64;
int W[6][2],Dd[6][2],Nx[6][2]; // Nx=-1 halt
int n; int dl[16][2];
int NS=6;
static int idx(int q,int f){return q*NS+f;}
long long tried=0;
int check(void){
  int N=n*NS+1, TOP=N-1;
  u64 T[2][64]; memset(T,0,sizeof T);
  T[0][TOP]|=1ULL<<TOP; T[1][TOP]|=1ULL<<TOP;
  for(int f=0;f<NS;f++)for(int r=0;r<2;r++){
    if(Nx[f][r]<0){for(int q=0;q<n;q++)T[r][idx(q,f)]|=1ULL<<TOP;}
    else if(Dd[f][r]==1){for(int q=0;q<n;q++)T[r][idx(q,f)]|=1ULL<<idx(dl[q][W[f][r]],Nx[f][r]);}
  }
  int ch=1;
  while(ch){ch=0;
    for(int f=0;f<NS;f++)for(int r=0;r<2;r++){
      if(Nx[f][r]<0||Dd[f][r]!=-1)continue;
      int g=Nx[f][r], w=W[f][r];
      for(int qp=0;qp<n;qp++)for(int l=0;l<2;l++){
        u64 row=T[l][idx(qp,g)], res=0;
        while(row){int j=__builtin_ctzll(row); row&=row-1; res|=T[w][j];}
        int tgt=idx(dl[qp][l],f);
        if((T[r][tgt]|res)!=T[r][tgt]){T[r][tgt]|=res;ch=1;}
      }
    }
  }
  u64 acc=1ULL<<TOP; ch=1;
  while(ch){ch=0;for(int i=0;i<N;i++)if(!(acc>>i&1)&&(T[0][i]&acc)){acc|=1ULL<<i;ch=1;}}
  return (T[0][idx(0,0)]&acc)==0;
}
int found=0;
void printdfa(void){printf("DFA n=%d: ",n);for(int q=0;q<n;q++)printf("%d%d ",dl[q][0],dl[q][1]);printf("\n");fflush(stdout);}
// enumerate in order positions k=0..2n-1 (q=k/2,b=k%2), dl[0][0]=0
void rec(int k,int maxu){
  if(found)return;
  if(k==2*n){ if(maxu!=n-1)return; tried++; if(check()){found=1;printdfa();} return;}
  int q=k/2,b=k%2;
  if(k==0){dl[0][0]=0;rec(1,0);return;}
  // need: states > maxu must be introduced in time: remaining slots must suffice
  int lim=maxu+1<n?maxu+1:n-1;
  for(int t=0;t<=lim;t++){dl[q][b]=t; 
    // ensure state q+1 introduced before we reach its row
    int nm=t>maxu?t:maxu;
    if(b==1 && nm<q+1 && q+1<n) continue;
    rec(k+1,nm);}
}
int main(int argc,char**argv){
  const char*M=argv[1]; int mirror=argc>3&&atoi(argv[3]);
  for(int s=0;s<6;s++)for(int r=0;r<2;r++){const char*t=M+s*7+r*3;
    if(t[0]=='-'){Nx[s][r]=-1;W[s][r]=1;Dd[s][r]=1;continue;}
    W[s][r]=t[0]-'0';Dd[s][r]=t[1]=='R'?1:-1;if(mirror)Dd[s][r]=-Dd[s][r];Nx[s][r]=t[2]-'A';}
  int maxn=atoi(argv[2]);
  int minn=argc>4?atoi(argv[4]):1; for(n=minn;n<=maxn&&!found;n++){tried=0;rec(0,0);printf("n=%d tried %lld found %d\n",n,tried,found);fflush(stdout);}
}
