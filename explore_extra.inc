// ---- canonical-zone detection (included into explore.cpp) ----
set<string> canon; long long minstep_canon=1000;
string zonestr(){
  string c; c.reserve(1400);
  auto add=[&](u64 sym,u64 n){ for(u64 j=0;j<n && c.size()<1300;j++) for(int i=0;i<K;i++) c+=char('0'+((sym>>i)&1)); };
  for(size_t i=0;i<L.size()&&c.size()<1300;i++)add(L[i].sym,L[i].n);
  add(bk,1);
  for(size_t i=R.size();i-->0 && c.size()<1300;)add(R[i].sym,R[i].n);
  size_t i=0; while(i<c.size()&&c[i]=='0')i++;
  size_t pos=i+1; vector<string> it; int k=0;
  while(pos+8<c.size() && it.size()<500){ int g=0; while(pos<c.size()&&c[pos]=='0'){g++;pos++;} if(pos>=c.size())break; pos++;
    char b[32];
    if(g==1){ if(pos<c.size()&&c[pos]=='1'){sprintf(b,"%d*",k); it.push_back(b); k=0; pos++; continue;} k++; continue;}
    if(g==3){sprintf(b,"%d",k); it.push_back(b); k=0; continue;}
    sprintf(b,"%d(%d)",k,g); it.push_back(b); k=0; }
  int n=it.size();
  for(int a=0;a<n;a++) for(int p=1;p<=4;p++){ int r=1;
      while(a+(r+1)*p<=n){ bool eq=true; for(int q=0;q<p;q++) if(it[a+q]!=it[a+r*p+q]){eq=false;break;} if(!eq)break; r++; }
      if(r>=12){ string z; for(int q=0;q<a;q++){z+=it[q];z+=' ';} z+="| "; for(int q=0;q<p;q++){z+=it[a+q]; if(q+1<p) z+=' ';} return z; } }
  return "?";
}
void dumpcfg(const char*fn){
  FILE*f=fopen(fn,"w"); string out;
  auto blk=[&](u64 sym,u64 n){ for(u64 j=0;j<n;j++) for(int i=0;i<K;i++) out+=char('0'+((sym>>i)&1)); };
  for(size_t i=0;i<L.size();i++)blk(L[i].sym,L[i].n);
  size_t headpos;
  if(d>0){ blk(bk,1); headpos=out.size(); } else { headpos=out.size()-1; blk(bk,1);}
  for(size_t i=R.size();i-->0;)blk(R[i].sym,R[i].n);
  size_t lo=0; while(lo<headpos && out[lo]=='0')lo++;
  fprintf(f,"%s %d %zu\n%s\n",p128(steps).c_str(),s,headpos-lo,out.c_str()+lo); fclose(f);
}
// trigger: largest run on the right being consumed (decreased by >= DROP since its max) -> dump cfg
u64 trig_sym=0, trig_max=0; long long DROP=110;
bool consume_check(char**argv){
  if(!(d<0 && L.empty())) return false;
  u64 big=0, sym=0; for(auto&r:R) if(r.n>big){big=r.n; sym=r.sym;}
  if(big<DROP) return false;
  if(sym!=trig_sym){ trig_sym=sym; trig_max=big; return false; }
  if(big>trig_max) trig_max=big;
  if(trig_max-big>=(u64)DROP && big>=(u64)DROP){ printf("CONSUMING %llu (max %llu)\n",(unsigned long long)big,(unsigned long long)trig_max); dumpcfg(argv[9]); return true; }
  return false;
}
bool canon_check(char**argv){
  if(getenv("CONSUME")) return consume_check(argv);
  if(!(d<0 && L.empty()) || (long long)steps<=minstep_canon) return false;
  string z=zonestr();
  if(getenv("ZDBG")){ u64 big=0; for(auto&r:R) if(r.n>big) big=r.n; static string lastz; if(z!=lastz){ printf("%s %llu Z[%s]\n",p128(steps).c_str(),(unsigned long long)big,z.c_str()); lastz=z; } }
  if(canon.count(z)){ printf("CANON %s\n",z.c_str()); dumpcfg(argv[9]); return true; }
  return false;
}
void load_canon(const char*fn){
  FILE*cf=fopen(fn,"r"); char line[8192];
  while(fgets(line,sizeof line,cf)){ string z=line; while(!z.empty()&&(z.back()=='\n'||z.back()=='\r'))z.pop_back(); if(!z.empty())canon.insert(z);}
  fclose(cf);
}
