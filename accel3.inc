// ---------------- cycle acceleration (v3, multi-variable) ----------------
// Light per-step records + full snapshots at candidate steps (front run symbolic or long).
// A recurring candidate (same s,d,bk,|L|,|R|, no events in between) whose stacks agree above the deepest
// touched level, and whose deepest touched runs changed by constant deltas, is repeated t times.
// Soundness conditions: deepest-run dips, no events, head never reaching lo during extrapolation.
const int RING=4096, TOPD=10;
struct Light{ size_t Ls,Rs; Lin Ltop,Rtop; Lin pos; ll ev; };
struct Snap{ int s,d; u64 bk; size_t Ls,Rs; vector<Run> Lt,Rt; Lin pos; ll ev; ll gidx; };
vector<Light> lring(RING); ll gidx=0; ll naccel=0;
unordered_map<u64,Snap> cands;
vector<Run> topk(const vector<Run>&v){ size_t k=min((size_t)TOPD,v.size()); return vector<Run>(v.end()-k,v.end()); }
bool try_accel(){
  Light lt{L.size(),R.size(),L.empty()?L0(0):L.back().n,R.empty()?L0(0):R.back().n,pos,nevents};
  lring[gidx%RING]=lt; ll me=gidx; gidx++;
  vector<Run>&F = d>0?R:L;
  if(F.empty()) return false;
  const Lin&fn=F.back().n;
  if(isconst(fn) && fn.c<16) return false;
  u64 key=((u64)s*2+(d>0))*1000003ULL ^ bk*0x9E3779B97F4A7C15ULL ^ ((u64)L.size()<<40) ^ ((u64)R.size()<<20);
  Snap now{s,d,bk,L.size(),R.size(),topk(L),topk(R),pos,nevents,me};
  auto it=cands.find(key);
  if(it==cands.end() || it->second.s!=s || it->second.d!=d || it->second.bk!=bk || it->second.Ls!=now.Ls || it->second.Rs!=now.Rs
     || it->second.ev!=nevents || me-it->second.gidx>=RING){ cands[key]=now; if(cands.size()>4096) cands.clear(); return false; }
  Snap o=it->second;
  auto fail=[&](){ cands[key]=now; return false; };
  size_t mL=now.Ls,mR=now.Rs; ll minoff=0;
  for(ll q=o.gidx;q<=me;q++){ const Light&a=lring[q%RING]; mL=min(mL,a.Ls); mR=min(mR,a.Rs);
    Lin df=a.pos-o.pos; if(!isconst(df)) return fail(); minoff=min(minoff,df.c); }
  if(mL==0||mR==0) return fail();
  if(now.Ls-(mL-1)>(size_t)TOPD||now.Rs-(mR-1)>(size_t)TOPD) return fail();
  auto cmp=[&](const vector<Run>&A,const vector<Run>&B,size_t sz,size_t m,Lin&delta)->bool{
    size_t base=sz-A.size();
    for(size_t idx=m-1; idx<sz; idx++){ const Run&ra=A[idx-base]; const Run&rb=B[idx-base];
      if(ra.sym!=rb.sym) return false;
      if(idx==m-1) delta=rb.n-ra.n; else if(!same(ra.n,rb.n)) return false; }
    return true; };
  Lin dL=L0(0),dR=L0(0);
  if(!cmp(o.Lt,now.Lt,now.Ls,mL,dL)||!cmp(o.Rt,now.Rt,now.Rs,mR,dR)) return fail();
  if(!isconst(dL)||!isconst(dR)) return fail();
  Lin dpos=now.pos-o.pos; if(!isconst(dpos)) return fail();
  if(dL.c>=0&&dR.c>=0) return fail();
  auto dip=[&](bool left,ll&dp)->bool{ size_t m=left?mL:mR; dp=0;
    const vector<Run>&t0=left?o.Lt:o.Rt; size_t sz0=left?o.Ls:o.Rs; Lin st0=t0[(m-1)-(sz0-t0.size())].n;
    for(ll q=o.gidx;q<=me;q++){ const Light&a=lring[q%RING]; size_t sz=left?a.Ls:a.Rs; if(sz!=m) continue;
      Lin df=(left?a.Ltop:a.Rtop)-st0; if(!isconst(df)) return false; dp=min(dp,df.c); }
    return true; };
  ll dipL,dipR; if(!dip(true,dipL)||!dip(false,dipR)) return fail();
  Lin cL=L[mL-1].n, cR=R[mR-1].n;
  bool haveT=false; Lin t=L0(0);
  auto lim=[&](const Lin&cnt,ll dl,ll dp)->bool{ ll ad=-dl; Lin num=cnt+L0(dp-2);
    if(isconst(num)){ ll tv=num.c>=0? num.c/ad : -1; if(tv<1) return false; Lin tt=L0(tv);
      if(!haveT||!isconst(t)||tt.c<t.c){ t=tt; haveT=true; } return true; }
    if(!allge0(num)) return false;
    bool div=(num.c%ad==0); for(int i=0;i<NV;i++) if(num.a[i]%ad) div=false;
    if(!div){ printf("NEEDSPLIT delta=%lld count=%s\n",dl,ls(cnt).c_str()); exit(7);}
    Lin tt=num; tt.c/=ad; for(int i=0;i<NV;i++) tt.a[i]/=ad;
    if(!haveT){t=tt;haveT=true;} else if(isconst(t)){} else if(!same(t,tt)){ undetermined("two-symbolic-limits",tt);}
    return true; };
  if(dL.c<0 && !lim(cL,dL.c,dipL)) return fail();
  if(dR.c<0 && !lim(cR,dR.c,dipR)) return fail();
  if(!haveT) return fail();
  if(isconst(t)&&t.c<2) return fail();
  if(!isconst(t)) need(t,1);
  if(dpos.c<0){ Lin lowest = now.pos + dpos.c*(t-L0(1)) + L0(minoff-4*K);
    Lin dd=lowest-lo; if(isconst(dd)){ if(dd.c<=0) return fail(); } else if(allge0(dd)){ need(dd,1);} else return fail(); }
  L[mL-1].n = L[mL-1].n + dL.c*t;
  R[mR-1].n = R[mR-1].n + dR.c*t;
  pos = pos + dpos.c*t;
  naccel++;
  cands.clear();
  return true;
}
