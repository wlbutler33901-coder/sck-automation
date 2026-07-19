#!/usr/bin/env python3
import json, sys, datetime
MIN_PSF       = 50
STALE_MONTHS  = 60
A_CORE_MAX    = 12
TARGET_MIN    = 8
MAX_COMPS     = 15
NONSUBJ_CAP   = 4
EXTEND_A_MOS  = 24
TIER_STEP = {"Track-Side":4,"Premium":3,"Standard":2,"Flex":1}
AMEN_ADJ  = {("Track-Side","Track-Side"):0,
             ("Premium","Premium"):0,("Premium","Standard"):15,("Premium","Flex"):20,
             ("Standard","Premium"):-15,("Standard","Standard"):0,("Standard","Flex"):10,
             ("Flex","Premium"):-15,("Flex","Standard"):-5,("Flex","Flex"):0}
def tier_word(a):
 if not a: return None
 a=str(a).lower()
 return "Track-Side" if "track" in a else "Premium" if "prem" in a else "Standard" if "stand" in a else "Flex" if ("flex" in a or "basic" in a) else None
def size_cat(sf):
 if sf is None: return None
 return "Small" if sf<=900 else "Medium" if sf<=1400 else "Large"
def parse_date(s):
 if not s: return None
 s=str(s).strip()
 for fmt in ("%m/%d/%y","%m/%d/%Y"):
  try: return datetime.datetime.strptime(s,fmt).date()
  except: pass
 try: return datetime.date.fromisoformat(s[:10])
 except: return None
def months_ago(d, today):
 if d is None: return None
 m=(today.year-d.year)*12+(today.month-d.month)
 if today.day<d.day: m-=1
 return max(m,0)
def num(x):
 try: return float(x)
 except: return None
def norm_parcel(pid):
 if pid is None: return None
 s="".join(ch for ch in str(pid) if ch.isalnum()).upper().lstrip("0")
 return s or None
def norm_wi(w):
 w=num(w)
 if w is None: return None
 return w/10.0 if w>10 else w
def rec_score(m):
 if m is None: return 5
 return 10 if m<=6 else 9 if m<=12 else 8 if m<=18 else 7 if m<=24 else 5 if m<=36 else 3 if m<=48 else 1
CLASS_PTS = {"A":10,"B":7,"C":4,"D":2}
CS_MIN_SCORE_45 = 6.5
CS_TIER_STEP = {"Track-Side":4,"Premium":3,"Standard":2,"Flex":1}
def competitive_set(subj, cands, sel_rows, get_raw, get_amen, get_wi, get_mos, get_psf, get_sf):
 def wnorm(x):
  try: x=float(x)
  except: return None
  return x/10.0 if x>10 else x
 groups={}
 for c in cands:
  pn=(get_raw(c) or {}).get("Project Name")
  if not pn or pn==subj["project"]: continue
  groups.setdefault(pn,[]).append(c)
 swi=wnorm(subj.get("wealth_index")); st=subj.get("amenity_word")
 sband=size_cat(subj.get("unit_size_sf")); o={"Small":0,"Medium":1,"Large":2}
 rows=[]
 for pn,cs in groups.items():
  tiers=[get_amen(c) for c in cs if get_amen(c)]
  tier=max(set(tiers),key=tiers.count) if tiers else None
  tp = {0:10,1:6,2:3}.get(abs(CS_TIER_STEP.get(tier,0)-CS_TIER_STEP.get(st,0)),1) if (tier and st) else 5
  subs=[(get_raw(c) or {}).get("Submarket") for c in cs]; regs=[(get_raw(c) or {}).get("Region") for c in cs]
  sub=max(set(s for s in subs if s),key=subs.count) if any(subs) else None
  reg=max(set(r for r in regs if r),key=regs.count) if any(regs) else None
  lp=10 if (sub and sub==subj.get("submarket")) else 6 if (reg and reg==subj.get("region")) else 2
  avg_sf=sum(get_sf(c) for c in cs)/len(cs); band=size_cat(avg_sf)
  sp={0:10,1:6,2:3}[abs(o[band]-o[sband])] if (band and sband) else 5
  mos_min=min((get_mos(c) for c in cs if get_mos(c) is not None),default=None)
  rp=10 if (mos_min is not None and mos_min<=12) else 7 if (mos_min is not None and mos_min<=24) \
           else 5 if (mos_min is not None and mos_min<=36) else 2
  wis=[wnorm(get_wi(c)) for c in cs if wnorm(get_wi(c)) is not None]
  pwi=(sum(wis)/len(wis)) if wis else None
  wp=(10 if abs(swi-pwi)<=0.5 else 7 if abs(swi-pwi)<=1.5 else 4 if abs(swi-pwi)<=3 else 1) \
           if (swi is not None and pwi is not None) else 5
  rows.append({"project":pn,"submarket":sub,"region":reg,
   "tier":(tier if tier in (None,"Track-Side") else tier+"-Tier"),
   "avg_psf":round(sum(get_psf(c) for c in cs)/len(cs),2),"n_sales":len(cs),
   "avg_sf":round(avg_sf),"wi":(round(pwi,1) if pwi is not None else None),
   "mos_since_last":mos_min,
   "score":round(tp*0.30+lp*0.25+rp*0.20+sp*0.15+wp*0.10,2)})
 contrib={}
 for r in sel_rows:
  pn=r.get("project")
  if not pn or pn==subj["project"]: continue
  c=contrib.setdefault(pn,{"n":0,"s":0.0})
  c["n"]+=1; c["s"]+=float(r.get("score") or 0)
 for row in rows:
  c=contrib.get(row["project"])
  row["comps_used"]=c["n"] if c else 0
  if c: row["score"]=round(c["s"]/c["n"],2)
 A=[r for r in rows if r["comps_used"]>0]
 sreg=(subj.get("region") or "").strip().lower()
 B=[r for r in rows if r["comps_used"]==0 and (r.get("region") or "").strip().lower()==sreg]
 A.sort(key=lambda r:(-r["comps_used"],-r["score"], r["mos_since_last"] if r["mos_since_last"] is not None else 999))
 B.sort(key=lambda r:(-r["score"], r["mos_since_last"] if r["mos_since_last"] is not None else 999))
 sel=A[:5]
 for r in B:
  if len(sel)>=5: break
  if len(sel)<3 or r["score"]>=CS_MIN_SCORE_45: sel.append(r)
 for i,r in enumerate(sel): r["rank"]=i+1
 return {"selected":sel,"candidates_considered":len(rows),"rank_4_5_threshold":CS_MIN_SCORE_45,
  "basis":"regional buyer-pool grouping: projects supplying selected valuation comps rank first (comps used, then average selection score); remaining SAME-REGION projects backfill by five-factor comparability. Never pad across regions.",
  "weights":"backfill scoring: Amenity Tier 30% / Location 25% / Market Activity 20% / Unit-Size Profile 15% / Wealth Index 10%",
  "note":("only %d competing project(s) in the subject's region" % len(sel) if len(sel)<3 else None)}
def size_score(a,b):
 o={"Small":0,"Medium":1,"Large":2}
 if a is None or b is None: return 4
 return {0:10,1:7,2:3}[abs(o[a]-o[b])]
def classify(subj,c,aw):
 if c.get("Project Name")==subj["project"]: return "A"
 same_tier = (aw is not None and aw==subj["amenity_word"])
 yb_s=num(subj.get("year_built")); yb_c=num(c.get("Year Built"))
 vintage_ok = (yb_s is not None and yb_c is not None and abs(yb_s-yb_c)<=10)
 loc_ok = (c.get("Submarket")==subj["submarket"] or c.get("Region")==subj["region"])
 if same_tier and vintage_ok and loc_ok: return "B"
 if c.get("Region")==subj["region"]:
  ss=TIER_STEP.get(subj["amenity_word"]); cs=TIER_STEP.get(aw)
  if ss and cs and abs(ss-cs)<=1: return "C"
 return "D"
GROWTH_PCT = 5.0
def timing_adj(m):
 m=m or 0
 a = ((1.0 + GROWTH_PCT/100.0) ** (m/12.0) - 1.0) * 100.0
 return max(-25.0, min(a, 25.0))
def size_adj(csf,ssf): return max(-20.0,min(20.0,((csf-ssf)/100.0)*2.0))
def wi_adj(s,c):
 if s is None or c is None: return 0.0
 return max(-25.0,min(25.0,(s-c)*4.0))
def type_adj(comp_sale_type):
 return 5.0 if comp_sale_type=="New Construction" else 0.0
def main():
 data=json.load(open(sys.argv[1]))
 subj=data["subject"]; today=parse_date(data["appraisal_date"]) or datetime.date.today()
 subj["amenity_word"]=tier_word(subj.get("amenity_tier"))
 subj["sale_type"]="Re-Sale"
 subj["wealth_index"]=norm_wi(subj.get("wealth_index"))
 global GROWTH_PCT
 g=num(data.get("market_growth_pct"))
 if g is not None and 0 < g < 40: GROWTH_PCT=min(float(g),10.0)  # CAP10
 else: sys.stderr.write("WARNING: no blended appreciation rate supplied; timing adjustment using 5.0%/yr default.\n")
 subj_parcel=norm_parcel(subj.get("parcel_id"))
 ssf=float(subj["unit_size_sf"])
 pool=[]
 for c in data["sales_comps"]:
  psf=num(c.get("$ / SF")); sf=num(c.get("Sq. Ft.")); price=num(c.get("Sale Price"))
  d=parse_date(c.get("Sale Date")); m=months_ago(d,today)
  if psf is None or psf<MIN_PSF or sf is None or sf<=0 or price is None or price<=0: continue
  if m is None or m>STALE_MONTHS: continue
  pool.append({"raw":c,"psf":psf,"sf":sf,"price":price,"date":d,"mos":m})
 best={}
 for i,p in enumerate(pool):
  pid=norm_parcel(p["raw"].get("Parcel ID"))
  key=pid if pid else ("__u__",p["raw"].get("Project Name"),str(p["raw"].get("Unit")),i if p["raw"].get("Unit") is None else None)
  if key not in best: best[key]=p; continue
  cur=best[key]
  keep,drop=(p,cur) if (p["date"] or datetime.date.min)>(cur["date"] or datetime.date.min) else (cur,p)
  for f in ("Wealth Index (All)","Amenity","Sale Type","Region","Submarket","Project Name","Year Built","Address"):
   if keep["raw"].get(f) is None and drop["raw"].get(f) is not None:
    keep["raw"][f]=drop["raw"][f]
  best[key]=keep
 pool=list(best.values())
 comps=[]
 for p in pool:
  aw=tier_word(p["raw"].get("Amenity")); cls=classify(subj,p["raw"],aw)
  cwi=norm_wi(p["raw"].get("Wealth Index (All)"))
  own = (subj_parcel is not None and norm_parcel(p["raw"].get("Parcel ID"))==subj_parcel) or \
              (p["raw"].get("Project Name")==subj["project"] and str(p["raw"].get("Unit"))==str(subj.get("unit_number")))
  sc = round(rec_score(p["mos"])*0.50 + CLASS_PTS[cls]*0.35
                   + size_score(size_cat(ssf),size_cat(p["sf"]))*0.15, 2)
  comps.append({**p,"amen":aw,"cls":cls,"wi":cwi,"own":own,"score":sc,
                      "szgap":abs(p["sf"]-ssf)})
 if not comps:
  sys.stderr.write("ERROR: no eligible comps after pre-screen; cannot appraise.\n"); sys.exit(1)
 def select(cands):
  a=[c for c in cands if c["cls"]=="A"]
  a.sort(key=lambda x:((x["mos"] if x["mos"] is not None else 999),x["szgap"]))
  sel=a[:A_CORE_MAX]
  for c in a:
   if c["own"] and c not in sel: sel.append(c)
  if len(sel)<TARGET_MIN:
   per={}
   others=[c for c in cands if c["cls"]!="A"]
   others.sort(key=lambda x:(-x["score"],{"B":0,"C":1,"D":2}[x["cls"]],x["mos"] if x["mos"] is not None else 999))
   for c in others:
    if len(sel)>=TARGET_MIN: break
    pr=c["raw"].get("Project Name")
    if per.get(pr,0)>=NONSUBJ_CAP: continue
    sel.append(c); per[pr]=per.get(pr,0)+1
  for c in a:
   if len(sel)>=MAX_COMPS: break
   if c in sel or c["mos"] is None or c["mos"]>EXTEND_A_MOS: continue
   sel.append(c)
  if len(comps)<5: sel=list(cands)
  sel.sort(key=lambda x:(-x["score"],x["mos"] if x["mos"] is not None else 999,x["szgap"]))
  return sel[:MAX_COMPS]
 cands=list(comps); sel=select(cands); excluded=[]
 for _ in range(2):
  if len(sel)<3: break
  v=sorted(c["psf"] for c in sel); n=len(v)
  med = v[n//2] if n%2 else (v[n//2-1]+v[n//2])/2.0
  outs=[]
  for c in sel:
   r=c["psf"]/med
   if len(sel)<7:
    if r<0.50: outs.append((c,f"raw $/SF {c['psf']} is >50% below the set median {round(med,2)} (data error / non-arm's-length)"))
   else:
    if r<0.60: outs.append((c,f"raw $/SF {c['psf']} is >40% below the set median {round(med,2)} (data error / non-arm's-length)"))
    elif r>1.60: outs.append((c,f"raw $/SF {c['psf']} is >60% above the set median {round(med,2)}"))
    elif r>1.40 and not (c["cls"]=="A" and c["mos"] is not None and c["mos"]<=24):
     outs.append((c,f"raw $/SF {c['psf']} is 40-60% above the set median {round(med,2)} and not a recent same-project sale"))
  if not outs: break
  for c,reason in outs:
   excluded.append({"project":c["raw"].get("Project Name"),"unit":c["raw"].get("Unit"),
                             "psf":c["psf"],"sale_date":str(c["raw"].get("Sale Date")),"class":c["cls"],"reason":reason})
  out_ids={id(c) for c,_ in outs}
  cands=[c for c in cands if id(c) not in out_ids]
  sel=select(cands)
 swi=subj.get("wealth_index"); rows=[]
 for c in sel:
  a_time=round(timing_adj(c["mos"]),2)
  a_amen=round(float(AMEN_ADJ.get((subj["amenity_word"],c["amen"]),0)),2)
  a_type=round(type_adj(c["raw"].get("Sale Type")),2)
  a_size=round(size_adj(c["sf"],ssf),2); a_wi=round(wi_adj(swi,c["wi"]),2)
  net=round(a_time+a_amen+a_type+a_size+a_wi,2)
  rows.append({"project":c["raw"].get("Project Name"),"unit":c["raw"].get("Unit"),
   "address":c["raw"].get("Address"),
   "class":c["cls"],"own_sale":c["own"],"mos":c["mos"],"wi":c["wi"],
   "region":c["raw"].get("Region"),"submarket":c["raw"].get("Submarket"),
   "amenity":c["raw"].get("Amenity"),"sale_type":c["raw"].get("Sale Type"),
   "year_built":c["raw"].get("Year Built"),"size":c["sf"],"psf":c["psf"],"score":c["score"],
   "wi_adj":a_wi,"time_adj":a_time,"amen_adj":a_amen,"size_adj":a_size,"type_adj":a_type,
   "net_adj":net,"adj_psf":round(c["psf"]*(1+net/100.0),2),"flagged":abs(net)>50})
 kept=[r for r in rows if not r["flagged"]]
 if kept and len(kept)!=len(rows):
  drop={(r["project"],str(r["unit"])) for r in rows if r["flagged"]}
  for r in rows:
   if r["flagged"]:
    excluded.append({"project":r["project"],"unit":r["unit"],"psf":r["psf"],
                                 "sale_date":None,"class":r["class"],"reason":f"|Net Adj| {abs(r['net_adj'])}% exceeds 50% flag threshold"})
  rows=kept; sel=[c for c in sel if (c["raw"].get("Project Name"),str(c["raw"].get("Unit"))) not in drop]
 n=len(rows)
 if n==0: sys.stderr.write("ERROR: all comps flagged/excluded; cannot appraise.\n"); sys.exit(1)
 mean=lambda k: round(sum(r[k] for r in rows)/n,2)
 avg_psf=mean("psf"); avg_size=round(sum(r["size"] for r in rows)/n)
 avg_value=round(sum(c["price"] for c in sel)/n)
 wi_vals=[r["wi"] for r in rows if r["wi"] is not None]
 avg_wi=round(sum(wi_vals)/len(wi_vals),1) if wi_vals else None
 avg_mos=round(sum((r["mos"] or 0) for r in rows)/n,1); avg_score=mean("score")
 adj_avgs={k:mean(k) for k in ("wi_adj","time_adj","amen_adj","size_adj","type_adj","net_adj")}
 total_adj=adj_avgs["net_adj"]
 subj_psf=round(avg_psf*(1+total_adj/100.0),2)
 value=int(round(ssf*subj_psf/1000.0)*1000)
 adj_vals=[r["adj_psf"] for r in rows]
 n_a=sum(1 for r in rows if r["class"]=="A")
 out={"subject":subj,"appraisal_date":str(today),
  "table1":{"comp_avg_size":avg_size,"comp_avg_value":avg_value,"comp_avg_psf":avg_psf,
                  "wi_adj":adj_avgs["wi_adj"],"time_adj":adj_avgs["time_adj"],"amen_adj":adj_avgs["amen_adj"],
                  "size_adj":adj_avgs["size_adj"],"type_adj":adj_avgs["type_adj"],"total_adj":total_adj,
                  "subject_psf":subj_psf,"subject_value":value},
  "table2_avg":{"mos":avg_mos,"wi":avg_wi,"size":avg_size,"psf":avg_psf,"score":avg_score},
  "table3_avg":adj_avgs,"comps":rows,"excluded_outliers":excluded,
  "competitive_set":competitive_set(subj,comps,rows,
   lambda c:c["raw"],lambda c:c.get("amen"),lambda c:c.get("wi"),
   lambda c:c.get("mos"),lambda c:c["psf"],lambda c:c["sf"]),
  "estimated_market_value":value,"value_psf":subj_psf,"growth_pct_used":GROWTH_PCT,
  "finish_level_band":{"low_psf":min(adj_vals),"high_psf":max(adj_vals),
                             "low_value":int(round(ssf*min(adj_vals)/1000.0)*1000),
                             "high_value":int(round(ssf*max(adj_vals)/1000.0)*1000)},
  "narrative_stats":{"n_comps":n,"class_a":n_a,"class_b":sum(1 for r in rows if r["class"]=="B"),
   "class_c":sum(1 for r in rows if r["class"]=="C"),"class_d":sum(1 for r in rows if r["class"]=="D"),
   "own_sale_included":any(r["own_sale"] for r in rows),
   "n_projects":len({r["project"] for r in rows}),
   "new_construction":sum(1 for r in rows if r["sale_type"]=="New Construction"),
   "resale":sum(1 for r in rows if r["sale_type"]=="Re-Sale"),
   "score_min":min(r["score"] for r in rows),"score_max":max(r["score"] for r in rows),
   "largest_adj":sorted((kv for kv in adj_avgs.items() if kv[0]!="net_adj"),key=lambda kv:-abs(kv[1]))[:2],
   "adj_psf_min":min(adj_vals),"adj_psf_max":max(adj_vals),
   "excluded_outliers":len(excluded),
   "comp_depth_confidence":("High" if n_a>=3 and n>=8 else "Medium" if n_a>=1 or n>=8 else "Low")}}
 print(json.dumps(out,indent=2))
if __name__=="__main__": main()
