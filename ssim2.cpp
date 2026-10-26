// ssim: SYMBOLIC backsymbol macro machine (block K) with chain steps.
// Run counts and positions are affine:  c + a*x + b*y  (x,y symbolic, assumed large).
// Symbolic variables are introduced by diffing configs: cfgA (base), cfgB (= base with one run +1 -> x),
// optional cfgC (= base with another run +1 -> y).
// Simulates until a canonical zone string is reached at an exact "new leftmost cell" event (as raw sim),
// or halts, or something undetermined happens. Then instantiates the final configuration for
// requested (x,y) values and writes cfg files, and prints the symbolic run list + constraints.
// usage: ssim K maxmacro cfgA cfgB cfgC|- canonfile outprefix x1,y1 x2,y2 ...
#include <bits/stdc++.h>
using namespace std;
typedef unsigned long long u64; typedef long long ll;
static const int W[6][2]={{1,0},{1,0},{1,0},{1,0},{1,-1},{0,0}};
static const int Dd[6][2]={{1,1},{-1,-1},{1,-1},{1,-1},{1,0},{1,-1}};
static const int NX[6][2]={{1,4},{2,1},{3,1},{5,0},{2,-1},{0,3}};
int K;
struct Lin{ ll c,a,b; };
Lin L0(ll c){return {c,0,0};}
Lin operator+(Lin p,Lin q){return {p.c+q.c,p.a+q.a,p.b+q.b};}
Lin operator-(Lin p,Lin q){return {p.c-q.c,p.a-q.a,p.b-q.b};}
Lin operator*(ll k,Lin p){return {k*p.c,k*p.a,k*p.b};}
bool isconst(const Lin&p){return p.a==0&&p.b==0;}
string ls(const Lin&p){ char b[96]; string s=to_string(p.c); if(p.a){sprintf(b,"%+lldx",p.a); s+=b;} if(p.b){sprintf(b,"%+lldy",p.b); s+=b;} return s;}
void undetermined(const char*why,const Lin&p){ printf("UNDETERMINED %s %s\n",why,ls(p).c_str()); exit(3); }
// constraints: symbolic Lin >= T assumed. record minimal (c - T) per (a,b)
map<pair<ll,ll>,ll> cons;
void need(const Lin&p,ll T){ if(isconst(p)){ if(p.c<T){printf("INTERNAL need const %lld<%lld\n",p.c,T);exit(4);} return; }
  if(p.a<0||p.b<0) undetermined("need-sign",p);
  auto k=make_pair(p.a,p.b); ll v=p.c-T; auto it=cons.find(k); if(it==cons.end()||v<it->second) cons[k]=v; }
// sign test: is p < q ?  (q usually const)
bool lessLin(const Lin&p,const Lin&q){ Lin d=q-p; // p<q  <=> d>0
  if(isconst(d)) return d.c>0;
  if(d.a>=0&&d.b>=0){ need(d,1); return true; }
  if(d.a<=0&&d.b<=0){ need(L0(0)-d,0); return false; }
  undetermined("compare",d); return false; }
struct Key{u64 a,b; int s,d; bool operator==(const Key&o)const{return a==o.a&&b==o.b&&s==o.s&&d==o.d;}};
struct KH{size_t operator()(const Key&k)const{return k.a*1000003ULL^k.b*998244353ULL^(k.s*7+k.d);}};
struct Res{u64 b1,b2; int s,d; bool halt; int minp;};
unordered_map<Key,Res,KH> cache;
Res window(u64 left,u64 right,int s,int d){
  Key key{left,right,s,d}; auto it=cache.find(key); if(it!=cache.end())return it->second;
  int c[64]; for(int i=0;i<K;i++){c[i]=(left>>i)&1; c[K+i]=(right>>i)&1;}
  int p=d>0?K:K-1; u64 st=0; Res r; r.halt=false; int minp=p;
  while(true){ int b=c[p]; if(NX[s][b]<0){r.halt=true;break;}
    c[p]=W[s][b]; p+=Dd[s][b]; s=NX[s][b]; st++; if(p<minp)minp=p; if(p<0||p>=2*K)break;
    if(st>100000000ULL){fprintf(stderr,"inner loop\n");exit(2);} }
  u64 l=0,rr=0; for(int i=0;i<K;i++){l|=(u64)c[i]<<i; rr|=(u64)c[K+i]<<i;}
  r.b1=l; r.b2=rr; r.s=s; r.d=(p<0)?-1:1; r.minp=minp; cache[key]=r; return r;
}
struct Run{u64 sym; Lin n;};
vector<Run> L,R; int s=0,d=1; u64 bk=0; Lin pos=L0(0), lo=L0(0); ll macro=0;
inline void push(vector<Run>&v,u64 sym,Lin n){ if(!v.empty()&&v.back().sym==sym) v.back().n=v.back().n+n; else v.push_back({sym,n}); }
// decrement top run of v by one copy (it must exist)
void dec(vector<Run>&v){ Lin&n=v.back().n; if(isconst(n)){ if(--n.c==0) v.pop_back(); } else { n.c--; need(n,1);} }
set<string> canon;
#define MAXI 600
string decode_zone(const vector<int>&c, size_t from){
  size_t i=from; while(i<c.size()&&c[i]==0)i++;
  size_t p=i+1; vector<int> it; int k=0; auto at=[&](size_t q){return q<c.size()?c[q]:0;}; size_t hi=c.size()-1;
  while(p<=hi+8 && (int)it.size()<MAXI){ int g=0; while(p<=hi+8 && at(p)==0){g++;p++;} if(p>hi+8)break; p++;
    if(g==1){ if(at(p)==1){it.push_back(k*64+16); k=0; p++; continue;} k++; continue;}
    if(g==3){it.push_back(k*64); k=0; continue;}
    it.push_back(k*64+32+(g<15?g:15)); k=0; }
  int ni=it.size(); int ri=ni,rp=0; bool found=false;
  for(int a=0;a<ni&&!found;a++) for(int pp=1;pp<=4;pp++){ int r=1; while(a+(r+1)*pp<=ni && equal(it.begin()+a,it.begin()+a+pp,it.begin()+a+r*pp)) r++;
      if(r>=12){ri=a;rp=pp;found=true;break;} }
  string z; char b[32];
  auto si=[&](int v){int kk=v>>6,kd=(v>>4)&3,g=v&15; if(kd==0)sprintf(b,"%d ",kk); else if(kd==1)sprintf(b,"%d* ",kk); else sprintf(b,"%d(%d) ",kk,g); z+=b;};
  for(int q=0;q<ri;q++)si(it[q]); z+="| "; for(int q=ri;q<ri+rp;q++)si(it[q]);
  return z;
}
const ll EXPAND=40; // symbolic runs are expanded to this many copies for zone decoding (assumed >= EXPAND)
void expand_right(vector<int>&c,size_t limit){
  for(size_t i=R.size();i-->0 && c.size()<limit;){ Lin nn=R[i].n; if(d>0 && i==R.size()-1) nn.c--;
    ll m; if(isconst(nn)) m=nn.c; else { need(nn,EXPAND); m=EXPAND; }
    for(ll j=0;j<m && c.size()<limit;j++) for(int b=0;b<K;b++) c.push_back((R[i].sym>>b)&1); }
}
// final state storage for instantiation
struct Final{ vector<Run> L,R; int wc[64]; Lin wb; Lin headcell; int st; int d; } fin;
string lastz; ll nevents=0;
#include "accel2.inc"
Res window_events(u64 left,u64 right,int s0,int d0, Lin wb, bool&stopped){
  if(!isconst(wb)) undetermined("event-window-pos",wb);
  int c[64]; for(int i=0;i<K;i++){c[i]=(left>>i)&1; c[K+i]=(right>>i)&1;}
  int p=d0>0?K:K-1; int s=s0; Res r; r.halt=false; int minp=p; stopped=false;
  while(true){ int b=c[p]; if(NX[s][b]<0){r.halt=true;break;}
    c[p]=W[s][b]; p+=Dd[s][b]; s=NX[s][b]; if(p<minp)minp=p;
    ll ap=wb.c+p;
    if(!isconst(lo)) undetermined("lo",lo);
    if(ap<lo.c){ lo=L0(ap); nevents++;
      vector<int> cc; for(int i=0;i<2*K;i++) cc.push_back(c[i]); expand_right(cc,2600);
      string z=decode_zone(cc,p>0?p:0);
      if(z!=lastz){ lastz=z; if(getenv("SDBG")) printf("EV %lld %s\n",macro,z.c_str());
        if(canon.count(z) && macro>50){ printf("CANON %s\n",z.c_str());
          fin.L=L; fin.R=R; memcpy(fin.wc,c,sizeof c); fin.wb=wb; fin.headcell=L0(wb.c+p); fin.st=s; fin.d=d0; stopped=true; return r; } }
    }
    if(p<0||p>=2*K)break; }
  u64 l=0,rr=0; for(int i=0;i<K;i++){l|=(u64)c[i]<<i; rr|=(u64)c[K+i]<<i;}
  r.b1=l; r.b2=rr; r.s=s; r.d=(p<0)?-1:1; r.minp=minp; return r;
}
// ---- loading ----
struct Cfg{ vector<Run> L,R; u64 bk; int s; };
Cfg loadcfg(const char*fn){
  FILE*fin=fopen(fn,"r"); if(!fin){printf("cannot open %s\n",fn);exit(5);} char sb[64]; long long off; int s0;
  fscanf(fin,"%63s %d %lld ",sb,&s0,&off); string cells; int ch; while((ch=fgetc(fin))=='0'||ch=='1')cells+=(char)ch; fclose(fin);
  ll h=off; auto gc=[&](ll i)->int{ return (i>=0&&i<(ll)cells.size())?cells[i]-'0':0; };
  auto blockat=[&](ll st)->u64{ u64 b=0; for(int i=0;i<K;i++) b|=(u64)gc(st+i)<<i; return b; };
  ll nright=((ll)cells.size()-h+K-1)/K, nleft=(h+K-1)/K;
  Cfg c; c.s=s0;
  for(ll j=nright-1;j>=0;j--) push(c.R,blockat(h+K*j),L0(1));
  c.bk=blockat(h-K);
  for(ll j=nleft;j>=2;j--) push(c.L,blockat(h-K*j),L0(1));
  if(off!=0){printf("expect head offset 0\n");exit(5);}
  return c;
}
// make 'base' symbolic using 'other' (one run count +1) -> variable (0=x,1=y)
void symb(Cfg&base,const Cfg&other,int var){
  if(base.L.size()!=other.L.size()||base.R.size()!=other.R.size()||base.bk!=other.bk){
    // allow: other has an extra run? not supported
    printf("DIFF-SHAPE var %d: L %zu/%zu R %zu/%zu\n",var,base.L.size(),other.L.size(),base.R.size(),other.R.size()); exit(6);}
  int nd=0;
  for(int side=0;side<2;side++){ auto&A=side?base.R:base.L; auto&B=side?other.R:other.L;
    for(size_t i=0;i<A.size();i++){ if(A[i].sym!=B[i].sym){printf("DIFF-SYM\n");exit(6);}
      Lin dlt=L0(B[i].n.c-A[i].n.c); if(dlt.c==0&&dlt.a==0&&dlt.b==0) continue;
      if(dlt.c!=1||dlt.a||dlt.b){printf("DIFF-COUNT %s\n",ls(dlt).c_str());exit(6);}
      if(var==0) A[i].n.a+=1; else A[i].n.b+=1; nd++; } }
  if(nd!=1){printf("DIFF-NRUNS %d\n",nd);exit(6);}
}
string inst(const vector<Run>&LL,const int*wc,const vector<Run>&RR,ll x,ll y,int dd){
  auto ev=[&](Lin n){return n.c+n.a*x+n.b*y;};
  string out; vector<Run> l2=LL, r2=RR;
  if(dd<0 && !l2.empty()){ l2.back().n.c--; } if(dd>0 && !r2.empty()){ r2.back().n.c--; }
  for(auto&r:l2){ ll m=ev(r.n); for(ll j=0;j<m;j++) for(int b=0;b<K;b++) out+=char('0'+((r.sym>>b)&1)); }
  for(int i=0;i<2*K;i++) out+=char('0'+wc[i]);
  for(size_t i=r2.size();i-->0;){ ll m=ev(r2[i].n); for(ll j=0;j<m;j++) for(int b=0;b<K;b++) out+=char('0'+((r2[i].sym>>b)&1)); }
  return out;
}
int main(int argc,char**argv){
  K=atoi(argv[1]); ll maxmacro=atoll(argv[2]);
  Cfg A=loadcfg(argv[3]); Cfg B=loadcfg(argv[4]); symb(A,B,0);
  if(strcmp(argv[5],"-")){ Cfg C=loadcfg(argv[5]); symb(A,C,1); }
  { FILE*cf=fopen(argv[6],"r"); char line[8192]; while(fgets(line,sizeof line,cf)){ string z=line; while(!z.empty()&&(z.back()=='\n'||z.back()=='\r'))z.pop_back(); if(!z.empty())canon.insert(z);} fclose(cf); }
  const char*outp=argv[7];
  L=A.L; R=A.R; bk=A.bk; s=A.s; d=1; pos=L0(0); lo=L0(0);
  // the head is at cell 0 = leftmost visited; L holds nothing (offset 0)
  bool stopped=false;
  while(macro<maxmacro){ macro++; if(try_accel()) continue;
    vector<Run>&F = d>0?R:L; vector<Run>&Bk = d>0?L:R;
    u64 x=0; Lin n=L0(0); bool blank=F.empty();
    if(!blank){x=F.back().sym;n=F.back().n;}
    Lin wb = d>0 ? pos-L0(K) : pos-L0(K-1);
    Res r = d>0 ? window(bk,x,s,d) : window(x,bk,s,d);
    bool ev = r.halt || lessLin(wb+L0(r.minp),lo);
    if(ev){ r = d>0 ? window_events(bk,x,s,d,wb,stopped) : window_events(x,bk,s,d,wb,stopped);
      if(stopped) break; }
    if(r.halt){ printf("HALT (symbolic) after %lld macro steps\n",macro); return 1; }
    if(getenv("MDBG") && macro>atoll(getenv("MDBG")) && macro<atoll(getenv("MDBG"))+40)
      printf("M%lld s=%d d=%d bk=%05llx x=%05llx n=%s -> s'=%d d'=%d b1=%05llx b2=%05llx\n",macro,s,d,(unsigned long long)bk,(unsigned long long)x,ls(n).c_str(),r.s,r.d,(unsigned long long)r.b1,(unsigned long long)r.b2);
    u64 behind = d>0? r.b1 : r.b2; u64 front = d>0? r.b2 : r.b1;
    Lin exitpos = wb + L0(r.d>0 ? 2*K : -1);
    if(r.d==d){
      if(r.s==s && front==bk){ if(blank){printf("RUNOFF (non-halting)\n");return 0;}
        F.pop_back(); push(Bk,behind,n); pos = pos + (d>0?K:-K)*n;
      } else { if(!blank) dec(F); push(Bk,behind,L0(1)); bk=front; s=r.s; pos = pos + L0(d>0?K:-K); }
    } else { if(!blank) dec(F); push(F,front,L0(1)); bk=behind; s=r.s; d=r.d; pos=exitpos; }
  }
  if(!stopped){ printf("LIMIT macro=%lld\n",macro); return 2; }
  printf("macro=%lld\n",macro);
  // symbolic run list
  printf("RUNS L:"); for(auto&r:fin.L) printf(" %llx^%s",(unsigned long long)r.sym,ls(r.n).c_str());
  printf(" | R:"); for(size_t i=fin.R.size();i-->0;) printf(" %llx^%s",(unsigned long long)fin.R[i].sym,ls(fin.R[i].n).c_str()); printf("\n");
  printf("CONSTRAINTS"); for(auto&kv:cons) printf("  %lld%+lldx%+lldy>=0",kv.second,kv.first.first,kv.first.second); printf("\n");
  // instantiate
  for(int i=8;i<argc;i++){ ll xv=0,yv=0; sscanf(argv[i],"%lld,%lld",&xv,&yv);
    string out=inst(fin.L,fin.wc,fin.R,xv,yv,fin.d);
    // head index: L part length + (headcell - wb)
    ll Lcells=0; { vector<Run> l2=fin.L; if(fin.d<0&&!l2.empty()) l2.back().n.c--; for(auto&r:l2) Lcells+=(r.n.c+r.n.a*xv+r.n.b*yv)*K; }
    ll h=Lcells+(fin.headcell.c-fin.wb.c);
    if(h<0){ out=string(-h,'0')+out; h=0; } // head left of the window: unvisited zero cells
    // cells left of head are unvisited zeros at a new-leftmost event: trim to start at head
    char fn[512]; sprintf(fn,"%s_%lld_%lld.txt",outp,xv,yv); FILE*f=fopen(fn,"w");
    fprintf(f,"0 %d 0\n%s\n",fin.st,out.c_str()+h); fclose(f); printf("WROTE %s\n",fn); }
  return 0;
}
