#!/usr/bin/env python3
"""SCK unit re-sale batch appraisal runner (deterministic, Make-free).

Replicates the sck-unit-resale-valuation skill headlessly:
  scope -> live rates + WI -> RPC per project -> engine per unit ->
  deterministic render -> structural validation -> write-back -> re-query verify.

HARD SAFETY RULES (do not relax):
  * NEVER sets "Manual Update" = TRUE anywhere (that fires the legacy Make
    webhook). Completed units get "Manual Update" = NULL, which never fires.
  * Never touches region/project batch trigger tables or any Make webhook.
  * appraise_unit.py is byte-locked (15,844 bytes); this script refuses to run
    if the engine file size differs.

Usage examples:
  python3 run_appraisals.py --region "Orlando MSA" --dry-run
  python3 run_appraisals.py --region "Orlando MSA"
  python3 run_appraisals.py --project "Motocave Tampa Bay" --dry-run
  python3 run_appraisals.py --unit 350
  python3 run_appraisals.py --all
Options: --limit N (cap units), --out DIR (default ./out)

Env: SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY  (GitHub secrets in Actions)
"""
import argparse, csv, datetime, json, os, re, subprocess, sys, tempfile, time
import urllib.parse

try:
    import requests
except ImportError:
    sys.exit("pip install requests (see requirements.txt)")

HERE = os.path.dirname(os.path.abspath(__file__))
ENGINE = os.path.join(HERE, "appraise_unit.py")
ENGINE_BYTES = 15844
sys.path.insert(0, HERE)
from render_report import render, validate  # noqa: E402

UNITS_T = "02 - Units"
PROJECTS_T = "01 - Projects"
REGIONS_T = "Market Coverage - Regions"
STATES_T = "Market Coverage - States"
DEMO_T = "Demographic Data - Project"
STATE_DEMO_T = "Demographic Data - State Level"
FRESH_MARK = "prepared by Storage Condo King"  # renderer disclosure fingerprint


def norm(s):
    if s is None:
        return ""
    return re.sub(r"[\u2013\u2014]", "-", str(s)).strip().lower()


class SB:
    def __init__(self):
        self.url = os.environ.get("SUPABASE_URL", "").rstrip("/")
        key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get("SUPABASE_SERVICE_KEY")
        if not self.url or not key:
            sys.exit("Missing SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY environment variables.")
        self.h = {"apikey": key, "Authorization": "Bearer " + key,
                  "Content-Type": "application/json"}

    def _t(self, table):
        return self.url + "/rest/v1/" + urllib.parse.quote(table)

    def select(self, table, params=None, page=1000):
        rows, offset = [], 0
        params = dict(params or {})
        params.setdefault("select", "*")
        while True:
            h = dict(self.h)
            h["Range"] = "%d-%d" % (offset, offset + page - 1)
            r = requests.get(self._t(table), headers=h, params=params, timeout=120)
            r.raise_for_status()
            batch = r.json()
            rows.extend(batch)
            if len(batch) < page:
                return rows
            offset += page

    def patch_unit(self, index, payload):
        assert payload.get("Manual Update", None) is not True, "SAFETY: never set Manual Update TRUE"
        r = requests.patch(self._t(UNITS_T), headers=self.h,
                           params={"Index": "eq." + str(index)},
                           data=json.dumps(payload), timeout=120)
        r.raise_for_status()

    def rpc(self, name, body):
        r = requests.post(self.url + "/rest/v1/rpc/" + name, headers=self.h,
                          data=json.dumps(body), timeout=180)
        r.raise_for_status()
        return r.json()


def probe_key(row, *fragment_sets):
    """Find the first key whose lowercase name contains every fragment in a set."""
    for frags in fragment_sets:
        for k in row.keys():
            lk = k.lower()
            if all(f in lk for f in frags):
                return k
    return None


def numval(x):
    try:
        return float(re.sub(r"[^0-9.\-]", "", str(x)))
    except (TypeError, ValueError):
        return None


def parse_sale_date(txt):
    import datetime as _dt
    t = str(txt or "").strip()
    try:
        if re.match(r"^\d{4}-", t):
            return _dt.date.fromisoformat(t[:10])
        m = re.match(r"^(\d{1,2})/(\d{1,2})/(\d{2,4})", t)
        if m:
            mo, dy, yr = int(m.group(1)), int(m.group(2)), int(m.group(3))
            if yr < 100:
                yr += 2000
            return _dt.date(yr, mo, dy)
    except ValueError:
        return None
    return None


def extract_location_open(text, max_chars=520):
    """First ~3 sentences of a project Location Summary, cleaned for splicing\n    (long enough to carry the submarket positioning and a named demand driver)."""
    if not text or len(str(text).strip()) < 60:
        return None
    lines = [ln.strip() for ln in str(text).splitlines()
             if ln.strip() and not ln.strip().startswith(("#", "|", "-", "*"))]
    if not lines:
        return None
    prose = " ".join(lines)
    prose = re.sub(r"[\u2013\u2014]", "-", prose)
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z])", prose)
    out = ""
    for pt in parts[:3]:
        if len(out) + len(pt) + 1 > max_chars and out:
            break
        out = (out + " " + pt).strip()
    if not out.endswith("."):
        out = out.rstrip(".,;") + "."
    return out


def load_project_meta(sb):
    """Location Summary extract + submarket per project, for the Unit Summary block."""
    try:
        rows = sb.select(PROJECTS_T)
    except Exception as e:
        print("WARN: could not read '01 - Projects' meta (%s)" % e)
        return {}
    if not rows:
        return {}
    pk = probe_key(rows[0], ("project", "name")) or "Project Name"
    meta = {}
    for p in rows:
        nm = p.get(pk)
        if not nm:
            continue
        meta[norm(nm)] = {
            "location_extract": extract_location_open(p.get("Location Summary")),
            "submarket": p.get("Submarket"),
            # v3.2 Construction bullet inputs. These columns already arrive (this select is
            # "*"); they simply were not carried through before.
            "construction_materials": p.get("Construction Materials"),
            "common_area_finish": p.get("Common Area Finish Level"),
            "flood_zone": p.get("Flood Zone"),
        }
    have = sum(1 for m in meta.values() if m["location_extract"])
    print("Location narratives: %d of %d projects carry a Location Summary "
          "(missing ones fall back to demographic strengths; populate via sck-location-overview)"
          % (have, len(meta)))
    return meta


def compute_ttm(sales, submarket):
    """Trailing-12-month in-submarket sale count + median PSF from the RPC pool.
    Display context only; never feeds the valuation engine."""
    import datetime as _dt
    if not sales or not submarket:
        return None
    cutoff = _dt.date.today() - _dt.timedelta(days=365)
    want = norm(submarket)
    psfs = []
    for s in sales:
        if norm(s.get("Submarket")) != want:
            continue
        d = parse_sale_date(s.get("Sale Date"))
        v = numval(s.get("$ / SF"))
        if d and d >= cutoff and v and v >= 50:
            psfs.append(v)
    if not psfs:
        return None
    psfs.sort()
    n = len(psfs)
    med = psfs[n // 2] if n % 2 else (psfs[n // 2 - 1] + psfs[n // 2]) / 2.0
    return {"count": n, "med_psf": round(med)}


TIER_AUDIT_V = "v_amenity_tier_audit"


def check_tier_audit(sb, projects):
    """Amenity Tier Standard v1.1 compliance surface. Reads v_amenity_tier_audit once
    (a row = stored tier disagrees with the computed tier) and WARNS for any project in
    this run's scope. Advisory only: tier feeds the valuation, so a violation means the
    run may be pricing off a stale tier, but it NEVER blocks and NEVER writes a tier."""
    try:
        rows = sb.select(TIER_AUDIT_V)
    except Exception as e:
        print("WARN: could not read %s (%s); tier compliance unverified this run" % (TIER_AUDIT_V, e))
        return []
    if not rows:
        return []
    want = {norm(p) for p in projects}
    hits = [r for r in rows if norm(r.get("project_name")) in want]
    if hits:
        print("")
        print("!" * 78)
        print("WARN: %d project(s) IN SCOPE violate the SCK Amenity Tier Standard v1.1." % len(hits))
        print("      Amenity Tier feeds the valuation, so these units may price off a stale tier.")
        print("      Not blocking. Resolve via the audit view and re-run if the tier moves.")
        for r in hits:
            print("      - %-38s stored %-14s computed %-14s %s"
                  % (str(r.get("project_name"))[:38], r.get("stored_tier"),
                     r.get("computed_tier"), r.get("social_evidence") or ""))
        print("!" * 78)
        print("")
    out_of_scope = len(rows) - len(hits)
    if out_of_scope:
        print("Tier audit: %d further violation(s) outside this run's scope." % out_of_scope)
    return hits


def load_rates(sb):
    regions = sb.select(REGIONS_T)
    states = sb.select(STATES_T)
    if not regions or not states:
        print("WARN: Market Coverage tables empty or unreadable; blend defaults to 10.0")
        return {}, 10.0, "unresolved"
    rk = probe_key(regions[0], ("appreciation",), ("annual", "rate"), ("rate",), ("growth",))
    nk = probe_key(regions[0], ("region",), ("name",))
    sk = probe_key(states[0], ("appreciation",), ("annual", "rate"), ("rate",), ("growth",))
    state_rate = None
    for srow in states:
        v = numval(srow.get(sk)) if sk else None
        if v is not None:
            state_rate = v
            break
    if state_rate is None:
        state_rate = 10.0
    reg_rates = {}
    if rk and nk:
        for row in regions:
            v = numval(row.get(rk))
            if row.get(nk) and v is not None:
                reg_rates[norm(row[nk])] = v
    print("Rates: regional column %r, statewide %.2f (%d regions resolved)"
          % (rk, state_rate, len(reg_rates)))
    return reg_rates, state_rate, rk or "unresolved"


def blend_rate(region, reg_rates, state_rate):
    reg = reg_rates.get(norm(region))
    if reg is None:
        raw = state_rate
        src = "statewide only (region rate not found)"
    else:
        raw = round(0.5 * reg + 0.5 * state_rate, 2)
        src = "%.2f regional / %.2f statewide" % (reg, state_rate)
    b = min(raw, 10.0)
    return b, src, (raw > 10.0)


def load_wi(sb):
    """Load per-project demographics with Florida-baseline ratios and the
    portfolio wealth-index percentile. Returns (wi_map, demo_map)."""
    try:
        rows = sb.select(DEMO_T)
        st = [x for x in sb.select(STATE_DEMO_T) if str(x.get("state")).upper() == "FL"]
    except Exception as e:
        print("WARN: demographics unavailable (%s); Location lines fall back to generic" % e)
        return {}, {}
    if not rows or not st:
        return {}, {}
    fl = st[0]
    p200_st = 100.0 * fl["hh_income_200k_plus"] / fl["total_households"]
    lux_st = 100.0 * fl["housing_units_750k_plus"] / fl["occupied_housing_units"]
    veh_st = 100.0 * fl["hh_vehicles_3_plus"] / fl["total_households"]
    seas_st = 100.0 * fl["seasonal_units"] / fl["occupied_housing_units"]
    wis = sorted(float(x["wealth_index"]) for x in rows if x.get("wealth_index") is not None)
    wi_map, demo_map = {}, {}
    for x in rows:
        nkey = norm(x.get("project_name"))
        wi = numval(x.get("wealth_index"))
        if wi is not None:
            wi_map[nkey] = wi
        def rat(v, base):
            v = numval(v)
            return round(v / base, 2) if v is not None and base else None
        d = {"wealth_index": wi,
             "wi_pctl": round(100.0 * sum(1 for w in wis if w < wi) / max(len(wis) - 1, 1)) if wi is not None and wis else None,
             "mhv_5mi": numval(x.get("mhv_5mi")), "mhv_ratio": rat(x.get("mhv_5mi"), fl["median_home_value"]),
             "median_hh_income_5mi": numval(x.get("median_hh_income_5mi")),
             "inc_ratio": rat(x.get("median_hh_income_5mi"), fl["median_hh_income"]),
             "pct_hh_200k_plus_5mi": numval(x.get("pct_hh_200k_plus_5mi")),
             "p200_ratio": rat(x.get("pct_hh_200k_plus_5mi"), p200_st),
             "hh200k_5mi": numval(x.get("hh200k_5mi")),
             "lux_housing_share_5mi": numval(x.get("lux_housing_share_5mi")),
             "lux_ratio": rat(x.get("lux_housing_share_5mi"), lux_st),
             "pct_hh_vehicles_3_plus_5mi": numval(x.get("pct_hh_vehicles_3_plus_5mi")),
             "veh3_ratio": rat(x.get("pct_hh_vehicles_3_plus_5mi"), veh_st),
             "seasonal_share_5mi": numval(x.get("seasonal_share_5mi")),
             "seas_ratio": rat(x.get("seasonal_share_5mi"), seas_st),
             "total_households_5mi": numval(x.get("total_households_5mi")),
             "owner_occupancy_rate_5mi": numval(x.get("owner_occupancy_rate_5mi"))}
        demo_map[nkey] = d
    print("Demographics: %d projects with FL-baseline ratios; wealth-index percentiles computed" % len(demo_map))
    return wi_map, demo_map


def resolve_scope(sb, args):
    units = sb.select(UNITS_T, {"select": '"Index","Project","Unit #","Parcel ID","Address",'
                                          '"City","Year Built","Suite Size (SF)","Appraised $ / SF","Appraisal Valuation Comments"'})
    if args.unit:
        picked = [u for u in units if str(u.get("Index")) == str(args.unit)]
    elif args.project:
        picked = [u for u in units if norm(u.get("Project")) == norm(args.project)]
    elif args.region or args.all:
        projects = sb.select(PROJECTS_T)
        if not projects:
            sys.exit("Cannot read '01 - Projects' for region mapping.")
        pk = probe_key(projects[0], ("project", "name")) or "Project Name"
        rk = probe_key(projects[0], ("region",)) or "Region"
        region_of = {norm(p.get(pk)): p.get(rk) for p in projects if p.get(pk)}
        if args.all:
            picked = list(units)
        else:
            want = norm(args.region)
            picked = [u for u in units if norm(region_of.get(norm(u.get("Project")))) == want]
            unmapped = sorted({u.get("Project") for u in units
                               if norm(u.get("Project")) not in region_of})
            if unmapped:
                print("NOTE: %d unit project name(s) not found in '01 - Projects' "
                      "(en-dash/name drift): %s" % (len(unmapped), ", ".join(unmapped[:5])))
    else:
        sys.exit("Give a scope: --region NAME | --project NAME | --unit INDEX | --all")
    picked.sort(key=lambda u: (norm(u.get("Project")), str(u.get("Index"))))
    if args.limit:
        picked = picked[: args.limit]
    return picked


def build_subject(unit, proj_ctx, wi_map):
    pget = lambda *keys: next((proj_ctx.get(k) for k in keys if proj_ctx.get(k) is not None), None)
    return {
        "project": unit.get("Project"),
        "unit_number": unit.get("Unit #"),
        "parcel_id": unit.get("Parcel ID"),
        "address": unit.get("Address"),
        "city": unit.get("City") or pget("City"),
        "year_built": unit.get("Year Built") or pget("Year Built"),
        "unit_size_sf": numval(unit.get("Suite Size (SF)")),
        "region": pget("Region"),
        "submarket": pget("Submarket"),
        "number_of_units": pget("Units", "Number of Units", "# of Units"),
        "amenity_tier": pget("Amenity Tier", "Amenity"),
        "wealth_index": wi_map.get(norm(unit.get("Project"))) or pget("Wealth Index (All)", "Wealth Index"),
    }


def run_engine(input_obj):
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        json.dump(input_obj, f)
        path = f.name
    try:
        r = subprocess.run([sys.executable, ENGINE, path],
                           capture_output=True, text=True, timeout=120)
        if r.returncode != 0:
            raise RuntimeError((r.stderr or "engine failed").strip().splitlines()[-1])
        return json.loads(r.stdout), (r.stderr or "").strip()
    finally:
        os.unlink(path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--region")
    ap.add_argument("--project")
    ap.add_argument("--unit")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--limit", type=int)
    ap.add_argument("--out", default=os.path.join(HERE, "out"))
    args = ap.parse_args()

    if os.path.getsize(ENGINE) != ENGINE_BYTES:
        sys.exit("ENGINE INTEGRITY: appraise_unit.py is %d bytes, expected %d. Refusing to run."
                 % (os.path.getsize(ENGINE), ENGINE_BYTES))

    sb = SB()
    os.makedirs(args.out, exist_ok=True)
    today = datetime.date.today().isoformat()

    units = resolve_scope(sb, args)
    if not units:
        sys.exit("Scope resolved to zero units. Check the region/project spelling.")
    projects = sorted({u.get("Project") for u in units}, key=norm)
    mode = "DRY RUN (no writes)" if args.dry_run else "LIVE (writing to '02 - Units')"
    print("Scope: %d units across %d projects | %s | %s"
          % (len(units), len(projects), mode, today))
    tier_violations = check_tier_audit(sb, projects)

    reg_rates, state_rate, _ = load_rates(sb)
    wi_map, demo_map = load_wi(sb)
    proj_meta = load_project_meta(sb)

    results, failures = [], []
    rpc_cache = {}
    for pname in projects:
        try:
            body = rpc_cache.get(pname)
            if body is None:
                body = sb.rpc("get_comprehensive_market_data", {"input_id": pname})
                rpc_cache[pname] = body
            proj_ctx = (body or {}).get("project") or {}
            sales = (body or {}).get("sales") or []
            if not proj_ctx or not sales:
                raise RuntimeError("RPC returned no project context or no sales")
        except Exception as e:
            for u in [x for x in units if x.get("Project") == pname]:
                failures.append({"Index": u.get("Index"), "Project": pname,
                                 "Unit #": u.get("Unit #"), "error": "RPC: %s" % e})
            continue
        rate, rate_src, rate_capped = blend_rate(proj_ctx.get("Region"), reg_rates, state_rate)
        print("\n== %s : %d units | blended rate %.2f (%s) | %d candidate sales"
              % (pname, sum(1 for u in units if u.get("Project") == pname),
                 rate, rate_src, len(sales)))
        for u in [x for x in units if x.get("Project") == pname]:
            idx = u.get("Index")
            try:
                subject = build_subject(u, proj_ctx, wi_map)
                subject["demo"] = demo_map.get(norm(u.get("Project")))
                pm = proj_meta.get(norm(u.get("Project"))) or {}
                subject["location_extract"] = pm.get("location_extract")
                subject["construction_materials"] = pm.get("construction_materials")
                subject["common_area_finish"] = pm.get("common_area_finish")
                subject["flood_zone"] = pm.get("flood_zone")
                subject["market_ttm"] = compute_ttm(sales, subject.get("submarket") or pm.get("submarket"))
                subject["rate_capped"] = rate_capped
                if not subject["unit_size_sf"]:
                    raise RuntimeError("Suite Size (SF) missing or zero")
                engine_in = {"subject": subject, "appraisal_date": today,
                             "market_growth_pct": rate, "sales_comps": sales}
                out, warn = run_engine(engine_in)
                report = render(out)
                problems = validate(report, out)
                if problems:
                    raise RuntimeError("validation: " + "; ".join(problems))
                new_val = out["estimated_market_value"]
                new_psf = float(out["value_psf"])
                old_psf = numval(u.get("Appraised $ / SF"))
                delta = (new_psf - old_psf) if old_psf else None
                rec = {"Index": idx, "Project": pname, "Unit #": u.get("Unit #"),
                       "old_psf": round(old_psf, 2) if old_psf else None, "new_psf": new_psf,
                       "delta_psf": round(delta, 2) if delta is not None else None,
                       "value_total": new_val, "n_comps": out["narrative_stats"]["n_comps"],
                       "notes": (u.get("Appraisal Valuation Comments") or "").strip(), "warn": warn or ""}
                if args.dry_run:
                    fn = re.sub(r"[^A-Za-z0-9._ -]", "", "%s Unit %s - %s.md"
                                % (pname, u.get("Unit #"), today))
                    open(os.path.join(args.out, fn), "w", encoding="utf-8").write(report)
                else:
                    sb.patch_unit(idx, {"Appraisal": report,
                                        "Appraised $ / SF": new_psf,
                                        "Appraisal Date": today,
                                        "Last Triggered": today,
                                        "Manual Update": None})
                    back = sb.select(UNITS_T, {"select": '"Appraisal","Appraised $ / SF","Appraisal Date"',
                                               "Index": "eq." + str(idx)})
                    bpsf = numval(back[0].get("Appraised $ / SF")) if back else None
                    ok = (back and FRESH_MARK in (back[0].get("Appraisal") or "")
                          and today[:4] in (back[0].get("Appraisal") or "")
                          and bpsf is not None and abs(bpsf - new_psf) < 0.01
                          and back[0].get("Appraisal Date") == today)
                    if not ok:
                        raise RuntimeError("re-query verification failed after write")
                results.append(rec)
                print("  ok  Index %-6s Unit %-6s -> %s/SF (%s total, %d comps)%s%s"
                      % (idx, u.get("Unit #"), "${:,.2f}".format(new_psf),
                         "${:,}".format(new_val), rec["n_comps"],
                         "  [NOTES]" if rec["notes"] else "",
                         "  [" + warn + "]" if warn else ""))
            except Exception as e:
                failures.append({"Index": idx, "Project": pname,
                                 "Unit #": u.get("Unit #"), "error": str(e)})
                print("  FAIL Index %-5s Unit %-6s : %s" % (idx, u.get("Unit #"), e))
            time.sleep(0.05)

    summary = {"date": today, "mode": "dry-run" if args.dry_run else "live",
               "scope": {"region": args.region, "project": args.project,
                         "unit": args.unit, "all": args.all},
               "units_in_scope": len(units), "succeeded": len(results),
               "failed": len(failures), "failures": failures,
               "tier_violations_in_scope": tier_violations}
    json.dump(summary, open(os.path.join(args.out, "summary.json"), "w"), indent=2)
    if results:
        with open(os.path.join(args.out, "summary.csv"), "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(results[0].keys()))
            w.writeheader()
            w.writerows(results)
    print("\n==== DONE: %d succeeded, %d failed (out/summary.csv, out/summary.json)"
          % (len(results), len(failures)))
    deltas = [r["delta_psf"] for r in results if r["delta_psf"] is not None]
    if deltas:
        big = sorted(results, key=lambda r: -abs(r["delta_psf"] or 0))[:5]
        print("Largest PSF moves:")
        for r in big:
            print("  %s Unit %s: %s -> %s/SF (%+.2f)" % (r["Project"], r["Unit #"],
                  ("${:,.2f}".format(r["old_psf"]) if r["old_psf"] else "n/a"),
                  "${:,.2f}".format(r["new_psf"]), r["delta_psf"]))
    noted = [r for r in results if r.get("notes")]
    if noted:
        print("%d unit(s) carry Appraisal Valuation Comments (NOT applied in batch mode; run those through the Cowork skill):" % len(noted))
        for r in noted[:10]:
            print("  Index %s %s Unit %s" % (r["Index"], r["Project"], r["Unit #"]))
    summary["notes_units"] = [r["Index"] for r in noted]
    json.dump(summary, open(os.path.join(args.out, "summary.json"), "w"), indent=2)
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
