// fsim: backsymbol macro machine (block K) with chain steps, absolute positions and exact
// "new leftmost cell" events (identical to the raw simulator), zone decoding and canonical stop.
// usage: fsim K maxsteps cfg|- canonfile|- outcfg [mode]
//   mode "events": print every zone-string change at new-leftmost events (like phase.c)
#include <bits/stdc++.h>
using namespace std;
typedef unsigned long long u64; typedef long long ll; typedef __int128 i128;
static const int W[6][2]={{1,0},{1,0},{1,0},{1,0},{1,-1},{0,0}};
static const int Dd[6][2]={{1,1},{-1,-1},{1,-1},{1,-1},{1,0},{1,-1}};
static const int NX[6][2]={{1,4},{2,1},{3,1},{5,0},{2,-1},{0,3}};
int K;
struct Key{u64 a,b; int s,d; bool operator==(const Key&o)const{return a==o.a&&b==o.b&&s==o.s&&d==o.d;}};
struct KH{size_t operator()(const Key&k)const{return k.a*1000003ULL^k.b*998244353ULL^(k.s*7+k.d);}};
struct Res{u64 b1,b2; int s,d; u64 steps; bool halt; int minp;};
unordered_map<Key,Res,KH> cache;
Res window(u64 left,u64 right,int s,int d){
  Key key{left,right,s,d}; auto it=cache.find(key); if(it!=cache.end())return it->second;
  int c[64]; for(int i=0;i<K;i++){c[i]=(left>>i)&1; c[K+i]=(right>>i)&1;}
  int p=d>0?K:K-1; u64 st=0; Res r; r.halt=false; int minp=p;
  while(true){
    int b=c[p];
    if(NX[s][b]<0){r.halt=true;break;}
    c[p]=W[s][b]; p+=Dd[s][b]; s=NX[s][b]; st++;
    if(p<minp)minp=p;
    if(p<0||p>=2*K)break;
    if(st>100000000ULL){fprintf(stderr,"inner loop\n");exit(2);}
  }
  u64 l=0,rr=0; for(int i=0;i<K;i++){l|=(u64)c[i]<<i; rr|=(u64)c[K+i]<<i;}
  r.b1=l; r.b2=rr; r.s=s; r.d=(p<0)?-1:1; r.steps=st; r.minp=minp;
  cache[key]=r; return r;
}
struct Run{u64 sym; u64 n;};
vector<Run> L,R;
int s=0,d=1; u64 bk=0; i128 steps=0; ll pos=0, lo=0;
inline void push(vector<Run>&v,u64 sym,u64 n){ if(!v.empty()&&v.back().sym==sym) v.back().n+=n; else v.push_back({sym,n}); }
string p128(i128 x){ if(x==0)return "0"; string r; bool neg=x<0; if(neg)x=-x; while(x>0){r+=char('0'+(int)(x%10)); x/=10;} if(neg)r+='-'; reverse(r.begin(),r.end()); return r;}
set<string> canon; bool events_mode=false; const char* outcfg=0; i128 base_steps=0;
// ---- zone decoding identical to phase.c ----
#define MAXI 600
string decode_zone(const vector<int>&c, size_t from){
  size_t i=from; while(i<c.size()&&c[i]==0)i++;
  size_t p=i+1; vector<int> it; int k=0;
  auto at=[&](size_t q){return q<c.size()?c[q]:0;};
  size_t hi=c.size()-1; // cells beyond are zero
  while(p<=hi+8 && (int)it.size()<MAXI){ int g=0; while(p<=hi+8 && at(p)==0){g++;p++;} if(p>hi+8)break; p++;
    if(g==1){ if(at(p)==1){it.push_back(k*64+16); k=0; p++; continue;} k++; continue;}
    if(g==3){it.push_back(k*64); k=0; continue;}
    it.push_back(k*64+32+(g<15?g:15)); k=0; }
  int ni=it.size(); int ri=ni,rp=0;
  bool found=false;
  for(int a=0;a<ni&&!found;a++) for(int pp=1;pp<=4;pp++){ int r=1; while(a+(r+1)*pp<=ni && equal(it.begin()+a,it.begin()+a+pp,it.begin()+a+r*pp)) r++;
      if(r>=12){ri=a;rp=pp;found=true;break;} }
  string z; char b[32];
  auto si=[&](int v){int kk=v>>6,kd=(v>>4)&3,g=v&15; if(kd==0)sprintf(b,"%d ",kk); else if(kd==1)sprintf(b,"%d* ",kk); else sprintf(b,"%d(%d) ",kk,g); z+=b;};
  for(int q=0;q<ri;q++)si(it[q]); z+="| "; for(int q=ri;q<ri+rp;q++)si(it[q]);
  return z;
}
// build cell vector of whole tape starting at absolute 'start' using window cells wc (absolute base wb) and stacks
// For event decoding we only need cells from lo up to ~2000 cells.
void expand_right(vector<int>&c, size_t limit){ // append R stack (top first = adjacent)
  for(size_t i=R.size();i-->0 && c.size()<limit;){ u64 nn=R[i].n; if(d>0 && i==R.size()-1) nn--; // front block is in the window
    for(u64 j=0;j<nn && c.size()<limit;j++) for(int b=0;b<K;b++) c.push_back((R[i].sym>>b)&1); }
}
void dump_full(const char*fn, const int*wc, ll wb, int headcell, int st_state){
  // full tape: L stack, then window (2K cells at wb), then R stack. L assumed blank in event context.
  // the front block (top of L if d<0, top of R if d>0) is inside the window: skip one copy of it
  vector<Run> LL=L, RR=R;
  if(d<0 && !LL.empty()){ if(--LL.back().n==0) LL.pop_back(); }
  if(d>0 && !RR.empty()){ if(--RR.back().n==0) RR.pop_back(); }
  string out; for(size_t i=0;i<LL.size();i++) for(u64 j=0;j<LL[i].n;j++) for(int b=0;b<K;b++) out+=char('0'+((LL[i].sym>>b)&1));
  ll start = wb - (ll)out.size();
  for(int i=0;i<2*K;i++) out+=char('0'+wc[i]);
  for(size_t i=RR.size();i-->0;) for(u64 j=0;j<RR[i].n;j++) for(int b=0;b<K;b++) out+=char('0'+((RR[i].sym>>b)&1));
  ll h = headcell - start; // index of head
  if(h<0){ out=string(-h,'0')+out; start-=(-h); h=0; } // head left of the window (p<0): unvisited zero cells
  ll first=min<ll>(h, (ll)(out.find('1')==string::npos? h : out.find('1')));
  if(lo-start < first) first = lo-start; if(first<0) first=0;
  FILE*f=fopen(fn,"w"); fprintf(f,"%s %d %lld\n%s\n",p128(base_steps+steps).c_str(),st_state,h-first,out.c_str()+first); fclose(f);
}
string lastz; long long nevents=0;
// simulate window uncached with event checks; returns Res like window(); may stop (returns halt=false, s=-9) on canon
Res window_events(u64 left,u64 right,int s0,int d0, ll wb, bool &stopped){
  int c[64]; for(int i=0;i<K;i++){c[i]=(left>>i)&1; c[K+i]=(right>>i)&1;}
  int p=d0>0?K:K-1; int s=s0; u64 st=0; Res r; r.halt=false; int minp=p; stopped=false;
  while(true){
    int b=c[p];
    if(NX[s][b]<0){r.halt=true;break;}
    c[p]=W[s][b]; p+=Dd[s][b]; s=NX[s][b]; st++;
    if(p<minp)minp=p;
    ll ap=wb+p;
    if(ap<lo){ lo=ap; nevents++;
      // decode: cells from lo: window part from max(0,p) .. then R stack
      vector<int> cc; for(int i=0;i<2*K;i++) cc.push_back(c[i]);
      expand_right(cc, 2600);
      // window starts at wb; lo >= wb? if p<0 the head left the window: then cells left of window are zero anyway
      size_t from = p>0? p:0;
      string z=decode_zone(cc,from);
      if(z!=lastz){ if(events_mode){ printf("%s %s",p128(base_steps+steps+st).c_str(),z.c_str());
          if(getenv("RUNS")){ printf(" ##"); for(size_t q=R.size();q-->0;) if(R[q].n>=4) printf(" %llu",(unsigned long long)R[q].n); }
          printf("\n"); } lastz=z;
        if(canon.count(z) && getenv("TRACE")){ vector<u64> cs; for(auto&rr:R) cs.push_back(rr.n); sort(cs.rbegin(),cs.rend());
          printf("HIT %s [%s] runs:",p128(base_steps+steps+st).c_str(),z.c_str()); for(size_t q=0;q<cs.size()&&q<3;q++) printf(" %llu",(unsigned long long)cs[q]); printf("\n"); fflush(stdout); }
        else if(canon.count(z) && (steps+st)>1000){ steps+=st; printf("CANON %s\n",z.c_str());
          if(outcfg) dump_full(outcfg,c,wb,wb+p,s); stopped=true; return r; } }
    }
    if(p<0||p>=2*K)break;
  }
  u64 l=0,rr=0; for(int i=0;i<K;i++){l|=(u64)c[i]<<i; rr|=(u64)c[K+i]<<i;}
  r.b1=l; r.b2=rr; r.s=s; r.d=(p<0)?-1:1; r.steps=st; r.minp=minp;
  return r;
}
int main(int argc,char**argv){
  K=atoi(argv[1]); double maxsteps=atof(argv[2]);
  if(argc>3 && strcmp(argv[3],"-")){
    FILE*fin=fopen(argv[3],"r"); char sb[64]; long long off; int s0; fscanf(fin,"%63s %d %lld ",sb,&s0,&off);
    for(char*q=sb;*q;q++) base_steps=base_steps*10+(*q-'0');
    string cells; int ch; while((ch=fgetc(fin))=='0'||ch=='1')cells+=(char)ch; fclose(fin);
    ll h=off; auto gc=[&](ll i)->int{ return (i>=0&&i<(ll)cells.size())?cells[i]-'0':0; };
    auto blockat=[&](ll st)->u64{ u64 b=0; for(int i=0;i<K;i++) b|=(u64)gc(st+i)<<i; return b; };
    ll nright=((ll)cells.size()-h+K-1)/K, nleft=(h+K-1)/K;
    for(ll j=nright-1;j>=0;j--) push(R,blockat(h+K*j),1);
    bk=blockat(h-K);
    for(ll j=nleft;j>=2;j--) push(L,blockat(h-K*j),1);
    s=s0; d=1; pos=h; lo=0; // absolute coords = index in cells; cells[0] is the leftmost visited cell
  }
  if(argc>4 && strcmp(argv[4],"-")){ FILE*cf=fopen(argv[4],"r"); char line[8192]; while(fgets(line,sizeof line,cf)){ string z=line; while(!z.empty()&&(z.back()=='\n'||z.back()=='\r'))z.pop_back(); if(!z.empty())canon.insert(z);} fclose(cf);}
  if(argc>5 && strcmp(argv[5],"-")) outcfg=argv[5];
  if(argc>6 && !strcmp(argv[6],"events")) events_mode=true;
  while((double)steps<maxsteps){
    vector<Run>&F = d>0?R:L; vector<Run>&B = d>0?L:R;
    u64 x=0; u64 n=~0ULL; bool blank=F.empty();
    if(!blank){x=F.back().sym;n=F.back().n;}
    ll wb = d>0 ? pos-K : pos-K+1;
    Res r = d>0 ? window(bk,x,s,d) : window(x,bk,s,d);
    if(wb + r.minp < lo || r.halt){
      bool stopped=false;
      r = d>0 ? window_events(bk,x,s,d,wb,stopped) : window_events(x,bk,s,d,wb,stopped);
      if(stopped){ printf("stopped at steps=%s events=%lld\n",p128(base_steps+steps).c_str(),nevents); return 0; }
    }
    if(r.halt){printf("HALT after ~%s steps\n",p128(base_steps+steps+r.steps).c_str()); return 0;}
    u64 behind = d>0? r.b1 : r.b2;
    u64 front  = d>0? r.b2 : r.b1;
    ll exitpos = wb + (r.d>0 ? 2*K : -1);
    if(r.d==d){
      if(r.s==s && front==bk){
        if(blank){printf("runs off to infinity (non-halting)\n");return 0;}
        F.pop_back(); push(B,behind,n); steps+=(i128)r.steps*n;
        pos += (ll)(d>0?K:-K)*(ll)n;
      } else {
        if(!blank){ if(--F.back().n==0)F.pop_back(); }
        push(B,behind,1); bk=front; s=r.s; steps+=r.steps;
        pos += d>0?K:-K;
      }
    } else {
      if(!blank){ if(--F.back().n==0)F.pop_back(); }
      push(F,front,1); bk=behind; s=r.s; d=r.d; steps+=r.steps;
      // turned: head now on the block beyond the window on the other side
      pos = exitpos;
    }
  }
  printf("done steps=%s events=%lld cache=%zu\n",p128(base_steps+steps).c_str(),nevents,cache.size());
}
