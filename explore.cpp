// Backsymbol macro machine with chain steps. Exact simulation of the TM.
#include <bits/stdc++.h>
using namespace std;
typedef unsigned long long u64; typedef __int128 i128;
static const int W[6][2]={{1,0},{1,0},{1,0},{1,0},{1,-1},{0,0}};
static const int Dd[6][2]={{1,1},{-1,-1},{1,-1},{1,-1},{1,0},{1,-1}};
static const int NX[6][2]={{1,4},{2,1},{3,1},{5,0},{2,-1},{0,3}};
int K;
struct Key{u64 a,b; int s,d; bool operator==(const Key&o)const{return a==o.a&&b==o.b&&s==o.s&&d==o.d;}};
struct KH{size_t operator()(const Key&k)const{return k.a*1000003ULL^k.b*998244353ULL^(k.s*7+k.d);}};
struct Res{u64 b1,b2; int s,d; u64 steps; bool halt;};
unordered_map<Key,Res,KH> cache;
// window cells 0..2K-1 : bit i of (lo | hi<<K)
Res window(u64 left,u64 right,int s,int d){
  Key key{left,right,s,d}; auto it=cache.find(key); if(it!=cache.end())return it->second;
  vector<int> c(2*K); for(int i=0;i<K;i++){c[i]=(left>>i)&1; c[K+i]=(right>>i)&1;}
  int p = d>0?K:K-1; u64 st=0; Res r; r.halt=false;
  while(true){
    int b=c[p];
    if(NX[s][b]<0){r.halt=true;break;}
    c[p]=W[s][b]; p+=Dd[s][b]; s=NX[s][b]; st++;
    if(p<0||p>=2*K)break;
    if(st>100000000ULL){fprintf(stderr,"inner loop\n");exit(2);}
  }
  u64 l=0,rr=0; for(int i=0;i<K;i++){l|=(u64)c[i]<<i; rr|=(u64)c[K+i]<<i;}
  r.b1=l; r.b2=rr; r.s=s; r.d=(p<0)?-1:1; r.steps=st;
  cache[key]=r; return r;
}
struct Run{u64 sym; u64 n;};
vector<Run> L,R;
int s=0,d=1; u64 bk=0; i128 steps=0; u64 macrosteps=0, chains=0;
inline void push(vector<Run>&v,u64 sym,u64 n){ if(!v.empty()&&v.back().sym==sym) v.back().n+=n; else v.push_back({sym,n}); }
string p128(i128 x){ if(x==0)return "0"; string r; while(x>0){r+=char('0'+(int)(x%10)); x/=10;} reverse(r.begin(),r.end()); return r;}
map<u64,int> symid;
int sid(u64 x){ auto it=symid.find(x); if(it!=symid.end())return it->second; int k=symid.size(); symid[x]=k; return k;}
void pr(const Run&r){ if(r.n==1)printf("%d ",sid(r.sym)); else printf("%d^%llu ",sid(r.sym),(unsigned long long)r.n);}
#include "explore_extra.inc"
void showbig(){
  printf("steps=%s | ",p128(steps).c_str());
  u64 small=0;
  auto one=[&](const Run&r){ if(r.n>=8){ if(small){printf("(%llu) ",(unsigned long long)small); small=0;} printf("%d^%llu ",sid(r.sym),(unsigned long long)r.n);} else small+=r.n; };
  for(size_t i=0;i<L.size();i++)one(L[i]); small++;
  for(size_t i=R.size();i-->0;)one(R[i]);
  if(small)printf("(%llu)",(unsigned long long)small);
  printf("\n"); fflush(stdout);
}
void show(){
  printf("steps=%s runs=%zu | ",p128(steps).c_str(),L.size()+R.size());
  for(size_t i=0;i<L.size();i++)pr(L[i]);
  if(d>0){ printf("%d [%c>] ",sid(bk),"ABCDEF"[s]); } else { printf("[<%c] %d ","ABCDEF"[s],sid(bk)); }
  for(size_t i=R.size();i-->0;)pr(R[i]);
  printf("\n"); fflush(stdout);
}
int main(int argc,char**argv){
  K=atoi(argv[1]); double maxsteps=atof(argv[2]); double rep=atof(argv[3]); double fac=atof(argv[4]);
  double nextrep=rep;
  if(argc>9) load_canon(argv[8]);
  if(argc>7 && strcmp(argv[7],"-")){ // load config: "<step> <state> <headoffset>\n<cells>"
    FILE*fin=fopen(argv[7],"r"); long long st0,off; int s0; fscanf(fin,"%lld %d %lld ",&st0,&s0,&off);
    string cells; int ch; while((ch=fgetc(fin))=='0'||ch=='1')cells+=(char)ch; fclose(fin);
    long long h=off; // head cell index; blocks start at h + K*j
    auto getc_=[&](long long i)->int{ return (i>=0&&i<(long long)cells.size())?cells[i]-'0':0; };
    auto blockat=[&](long long start)->u64{ u64 b=0; for(int i=0;i<K;i++) b|=(u64)getc_(start+i)<<i; return b; };
    long long nright=((long long)cells.size()-h+K-1)/K, nleft=(h+K-1)/K;
    for(long long j=nright-1;j>=0;j--) push(R,blockat(h+K*j),1);
    bk=blockat(h-K);
    for(long long j=nleft;j>=2;j--) push(L,blockat(h-K*j),1);
    s=s0; d=1; steps=0;
  }
  while((double)steps<maxsteps){
    vector<Run>&F = d>0?R:L; vector<Run>&B = d>0?L:R;
    u64 x=0; u64 n=~0ULL; bool blank=F.empty();
    if(!blank){x=F.back().sym;n=F.back().n;}
    Res r = d>0 ? window(bk,x,s,d) : window(x,bk,s,d);
    if(r.halt){printf("HALT after ~%s steps\n",p128(steps+r.steps).c_str()); show(); return 0;}
    macrosteps++;
    // in forward-exit: pushed-behind block and new back symbol
    u64 behind = d>0? r.b1 : r.b2;   // block that was 'bk' side
    u64 front  = d>0? r.b2 : r.b1;   // block that was 'x' side
    if(r.d==d){
      if(r.s==s && front==bk){
        if(blank){printf("runs off to infinity (non-halting)\n");return 0;}
        F.pop_back(); push(B,behind,n); steps+=(i128)r.steps*n; chains++;
      } else {
        if(!blank){ if(--F.back().n==0)F.pop_back(); }
        push(B,behind,1); bk=front; s=r.s; steps+=r.steps;
      }
    } else {
      // turned around: head moves onto top of B; new back symbol = 'behind' block; 'front' block goes onto F
      if(!blank){ if(--F.back().n==0)F.pop_back(); }
      push(F,front,1); bk=behind; s=r.s; d=r.d; steps+=r.steps;
    }
    if(argc>9 && canon_check(argv)) return 0;
    if((double)steps>=nextrep && d<0 && L.empty()){ if(argc>6) showbig(); else show(); nextrep*=fac; }
  }
  if(argc>5){ // dump full tape bits (far left..far right), and head info
    FILE*f=fopen(argv[5],"w"); string out;
    auto blk=[&](u64 sym,u64 n){ for(u64 j=0;j<n;j++) for(int i=0;i<K;i++) out+=char('0'+((sym>>i)&1)); };
    for(size_t i=0;i<L.size();i++)blk(L[i].sym,L[i].n);
    size_t headpos;
    if(d>0){ blk(bk,1); headpos=out.size(); } else { headpos=out.size()-1; blk(bk,1);} 
    for(size_t i=R.size();i-->0;)blk(R[i].sym,R[i].n);
    fprintf(f,"%s %d %zu\n%s\n",p128(steps).c_str(),s,headpos,out.c_str()); fclose(f);
  }
  printf("done macrosteps=%llu chains=%llu cache=%zu\n",(unsigned long long)macrosteps,(unsigned long long)chains,cache.size());
  show();
}
