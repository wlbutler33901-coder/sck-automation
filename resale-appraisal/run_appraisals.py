#!/usr/bin/env python3
"""SCK unit re-sale batch appraisal runner (deterministic, Make-free).

Replicates the unit-resale-appraisal-system skill headlessly:
  scope -> live rates + WI -> RPC per project -> engine per unit ->
  deterministic render -> structural validation -> write-back -> re-query verify.

HARD SAFETY RULES (do not relax):
  * NEVER sets "Manual Update" = TRUE anywhere (that fires the legacy Make
    webhook). Completed units get "Manual Update" = NULL, which never fires.
  * Never touches region/project batch trigger tables or any Make webhook.
  * appraise_unit.py is byte-locked (15,142 bytes); this script refuses to run
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
ENGINE_BYTES = 15142
sys.path.insert(0, HERE)
from render_report import render, validate  # noqa: E402

UNITS_T = "02 - Units"
PROJECTS_T = "01 - Projects"
REGIONS_T = "Market Coverage - Regions"
STATES_T = "Market Coverage - States"
DEMO_T = "Demographic Data - Project"
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
        b = min(state_rate, 10.0)
        src = "statewide only (region rate not found)"
    else:
        b = min(round(0.5 * reg + 0.5 * state_rate, 2), 10.0)
        src = "%.2f regional / %.2f statewide" % (reg, state_rate)
    return b, src


def load_wi(sb):
    try:
        rows = sb.select(DEMO_T)
    except Exception as e:
        print("WARN: could not read %r (%s); subject WI will be null" % (DEMO_T, e))
        return {}
    if not rows:
        return {}
    nk = probe_key(rows[0], ("project",))
    wk = probe_key(rows[0], ("wealth", "all"), ("wealth",))
    out = {}
    if nk and wk:
        for r in rows:
            v = numval(r.get(wk))
            if r.get(nk) and v is not None:
                out[norm(r[nk])] = v
    print("Wealth Index: column %r resolved for %d projects" % (wk, len(out)))
    return out


def resolve_scope(sb, args):
    units = sb.select(UNITS_T, {"select": '"Index","Project","Unit #","Parcel ID","Address",'
                                          '"City","Year Built","Suite Size (SF)","Appraised Value $"'})
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

    reg_rates, state_rate, _ = load_rates(sb)
    wi_map = load_wi(sb)

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
        rate, rate_src = blend_rate(proj_ctx.get("Region"), reg_rates, state_rate)
        print("\n== %s : %d units | blended rate %.2f (%s) | %d candidate sales"
              % (pname, sum(1 for u in units if u.get("Project") == pname),
                 rate, rate_src, len(sales)))
        for u in [x for x in units if x.get("Project") == pname]:
            idx = u.get("Index")
            try:
                subject = build_subject(u, proj_ctx, wi_map)
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
                old_val = numval(u.get("Appraised Value $"))
                delta = (new_val - old_val) if old_val else None
                rec = {"Index": idx, "Project": pname, "Unit #": u.get("Unit #"),
                       "old_value": int(old_val) if old_val else None, "new_value": new_val,
                       "delta": int(delta) if delta is not None else None,
                       "value_psf": out["value_psf"], "n_comps": out["narrative_stats"]["n_comps"],
                       "warn": warn or ""}
                if args.dry_run:
                    fn = re.sub(r"[^A-Za-z0-9._ -]", "", "%s Unit %s - %s.md"
                                % (pname, u.get("Unit #"), today))
                    open(os.path.join(args.out, fn), "w", encoding="utf-8").write(report)
                else:
                    sb.patch_unit(idx, {"Appraisal": report,
                                        "Appraised Value $": str(new_val),
                                        "Manual Update": None})
                    back = sb.select(UNITS_T, {"select": '"Appraisal","Appraised Value $"',
                                               "Index": "eq." + str(idx)})
                    ok = (back and FRESH_MARK in (back[0].get("Appraisal") or "")
                          and today[:4] in (back[0].get("Appraisal") or "")
                          and numval(back[0].get("Appraised Value $")) == float(new_val))
                    if not ok:
                        raise RuntimeError("re-query verification failed after write")
                results.append(rec)
                print("  ok  Index %-6s Unit %-6s -> %s (%s/SF, %d comps)%s"
                      % (idx, u.get("Unit #"), "${:,}".format(new_val),
                         "${:,.2f}".format(out["value_psf"]), rec["n_comps"],
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
               "failed": len(failures), "failures": failures}
    json.dump(summary, open(os.path.join(args.out, "summary.json"), "w"), indent=2)
    if results:
        with open(os.path.join(args.out, "summary.csv"), "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(results[0].keys()))
            w.writeheader()
            w.writerows(results)
    print("\n==== DONE: %d succeeded, %d failed (out/summary.csv, out/summary.json)"
          % (len(results), len(failures)))
    deltas = [r["delta"] for r in results if r["delta"] is not None]
    if deltas:
        big = sorted(results, key=lambda r: -abs(r["delta"] or 0))[:5]
        print("Largest value moves:")
        for r in big:
            print("  %s Unit %s: %s -> %s (%+d)" % (r["Project"], r["Unit #"],
                  "${:,}".format(r["old_value"]) if r["old_value"] else "n/a",
                  "${:,}".format(r["new_value"]), r["delta"]))
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
