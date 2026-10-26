// Macro machine (block size K) with chain steps. Exact simulation of the TM.
#include <bits/stdc++.h>
using namespace std;
typedef unsigned long long u64; typedef __int128 i128;
static const int W[6][2]={{1,0},{1,0},{1,0},{1,0},{1,-1},{0,0}};
static const int Dd[6][2]={{1,1},{-1,-1},{1,-1},{1,-1},{1,0},{1,-1}};
static const int NX[6][2]={{1,4},{2,1},{3,1},{5,0},{2,-1},{0,3}};
int K;
struct Res{uint32_t y; int s; int d; u64 steps; bool halt;};
unordered_map<u64,Res> cache;
Res macro(uint32_t x,int s,int d){
  u64 key=((u64)x<<4)|(s<<1)|(d>0);
  auto it=cache.find(key); if(it!=cache.end())return it->second;
  int p=d>0?0:K-1; u64 st=0; Res r;
  while(true){
    int b=(x>>p)&1;
    if(NX[s][b]<0){r={x,s,d,st,true};break;}
    if(W[s][b])x|=1u<<p; else x&=~(1u<<p);
    p+=Dd[s][b]; s=NX[s][b]; st++;
    if(p<0){r={x,s,-1,st,false};break;}
    if(p>=K){r={x,s,1,st,false};break;}
    if(st>100000000ULL){fprintf(stderr,"inner loop\n");exit(2);}
  }
  cache[key]=r; return r;
}
struct Run{uint32_t sym; u64 n;};
vector<Run> L,R; // L: top = adjacent to head (back), R likewise
int s=0,d=1; i128 steps=0; u64 macrosteps=0, chains=0;
inline void push(vector<Run>&v,uint32_t sym,u64 n){ if(!v.empty()&&v.back().sym==sym) v.back().n+=n; else v.push_back({sym,n}); }
string p128(i128 x){ if(x==0)return "0"; string r; while(x>0){r+=char('0'+(int)(x%10)); x/=10;} reverse(r.begin(),r.end()); return r;}
map<uint32_t,int> symid;
int sid(uint32_t x){ auto it=symid.find(x); if(it!=symid.end())return it->second; int k=symid.size(); symid[x]=k; return k;}
void show(){
  // print tape from far left to far right
  printf("steps=%s L-runs=%zu R-runs=%zu | ",p128(steps).c_str(),L.size(),R.size());
  for(size_t i=0;i<L.size();i++){ if(L[i].n==1)printf("%d ",sid(L[i].sym)); else printf("%d^%llu ",sid(L[i].sym),L[i].n);}
  printf("[%c%c] ","ABCDEF"[s],d>0?'>':'<');
  for(size_t i=R.size();i-->0;){ if(R[i].n==1)printf("%d ",sid(R[i].sym)); else printf("%d^%llu ",sid(R[i].sym),R[i].n);}
  printf("\n"); fflush(stdout);
}
int main(int argc,char**argv){
  K=atoi(argv[1]); double maxsteps=atof(argv[2]); double rep=atof(argv[3]); double fac=atof(argv[4]);
  double nextrep=rep;
  while((double)steps<maxsteps){
    vector<Run>&F = d>0?R:L; vector<Run>&B = d>0?L:R;
    uint32_t x=0; u64 n=~0ULL; bool blank=F.empty();
    if(!blank){x=F.back().sym;n=F.back().n;}
    Res r=macro(x,s,d);
    if(r.halt){printf("HALT after %s steps\n",p128(steps+r.steps).c_str()); show(); return 0;}
    macrosteps++;
    if(r.s==s && r.d==d){
      if(blank){ // chain over infinite blank: would run forever -> nonhalting translated cycler
        printf("runs off to infinity in state %d dir %d (non-halting)\n",s,d); return 0;}
      F.pop_back(); push(B,r.y,n); steps+=(i128)r.steps*n; chains++;
    } else {
      if(!blank){ if(--F.back().n==0)F.pop_back(); }
      if(r.d==d) push(B,r.y,1); else push(F,r.y,1);
      steps+=r.steps; s=r.s; d=r.d;
    }
    if((double)steps>=nextrep && d<0 && L.empty()){ show(); nextrep*=fac; }
  }
  printf("done macrosteps=%llu chains=%llu cache=%zu\n",macrosteps,chains,cache.size());
  show();
}
