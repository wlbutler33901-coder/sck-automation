#!/usr/bin/env python3
"""Deterministic report renderer for the SCK unit re-sale appraisal engine.

Implements references/report-template.md (mirror of the Cowork skill
sck-unit-resale-valuation's spec of record; 18,549 bytes, md5
2407cfbaabf1bf783714ee5ac7d90249 as of the v2.9 Build Quality pass). The template
is never read at runtime: the sentence builders below emit the prose, so the
template and this file must always be edited together.
Fills that spec from the engine's JSON output. No model in the loop: every number comes from the engine, every
sentence is a fixed pattern with slot filling. validate() enforces the
structural contract the website parser depends on before anything is written.

Usage:  python3 render_report.py computed.json > report.md
Import: from render_report import render, validate
"""
import json, sys, datetime

DASHES = ("\u2014", "\u2013")

def money(v):
    return "${:,}".format(int(round(float(v))))

def psf(v):
    return "${:,.2f}".format(float(v))

def pct(v):
    return "{:+.2f}%".format(float(v))

def b(s):
    return "**" + str(s) + "**"

def row(*cells):
    return "| " + " | ".join("" if c is None else str(c) for c in cells) + " |"

DRIVER_NAME = {"time_adj": "sale timing", "type_adj": "sale type",
               "amen_adj": "amenity tier", "size_adj": "unit size",
               "wi_adj": "wealth index", "bq_adj": "build quality"}

def driver_clause(key, val, growth):
    v = pct(val)
    if key == "time_adj":
        return "sale timing (" + b(v) + ", compounded at the measured " + b("{:.1f}%".format(growth)) + " rate)"
    if key == "type_adj":
        return "sale type (" + b(v) + ", the 5.0% pre-construction incentive added to new-construction comps)"
    if key == "amen_adj":
        return "amenity tier (" + b(v) + ", tier gaps translated to the subject's tier)"
    if key == "size_adj":
        return "unit size (" + b(v) + ", size differences at 2% per 100 SF)"
    return "wealth index (" + b(v) + ", micro-location differences at 4.0% per point)"

def driver_fact(key, growth):
    """The explanatory fact for the dominant driver. Category RATE DEFINITIONS are
    omitted: the five bullets below the prose already define every category rate.
    Only sale timing carries a fact here, because its figure is the rate the engine
    actually measured and applied this run (growth_pct_used), not a fixed definition."""
    if key == "time_adj":
        return "compounded at the measured " + b("{:.1f}%".format(growth)) + " rate"
    return ""


# Hard caps the engine enforces per category. A category that lands exactly on its cap
# is disclosed in the Adjustments prose; silent when nothing is capped.
ADJ_CAPS = (("time_adj", 25.0), ("wi_adj", 25.0), ("size_adj", 20.0))


def capped_categories(comps):
    """Categories where at least one comparable's adjustment landed exactly on the cap,
    read from the engine's own per-comp values. Returns [(name, cap), ...]."""
    hits = []
    for key, cap in ADJ_CAPS:
        for c in comps:
            try:
                v = abs(float(c.get(key, 0) or 0))
            except (TypeError, ValueError):
                continue
            if abs(v - cap) < 0.005:
                hits.append((DRIVER_NAME[key], cap))
                break
    return hits


def rank_drivers(t3):
    """All six average adjustments ranked by absolute size (v2.9 adds build quality). Same figures the engine
    produced (out["table3_avg"]); ranking happens here, never in the engine."""
    keys = ("time_adj", "wi_adj", "amen_adj", "bq_adj", "type_adj", "size_adj")
    return sorted(((k, float(t3.get(k, 0) or 0)) for k in keys), key=lambda kv: -abs(kv[1]))


def fmt_date_long(iso):
    d = datetime.date.fromisoformat(str(iso)[:10])
    return d.strftime("%B ") + str(d.day) + d.strftime(", %Y")

def tier_label(t):
    if not t:
        return "N/A"
    t = str(t)
    if t == "Track-Side" or t.endswith("-Tier"):
        return t
    return t + "-Tier"

DISCLOSURE = ("*This report is a market analysis prepared by Storage Condo King "
              "from recorded comparable sales. It is not an appraisal and was not "
              "prepared by a licensed appraiser. Values shown are estimates and "
              "are not a substitute for an appraisal.*")

METHODOLOGY = ("This valuation employs a comparable sales approach anchored on sales "
               "within the subject's own project, drawing on 1,600+ Florida garage "
               "condominium transactions. Comparables are scored on three weighted "
               "factors (Recency 50%, Same-Project Class 35%, Size Match 15%) with a "
               "same-project core of up to 12 sales and adjacent-project backfill; an "
               "asymmetric outlier guard removes data errors while preserving genuine "
               "finish-level dispersion. Six standardized adjustments follow, and the "
               "final value is the comp average $/SF adjusted by the equal-weighted "
               "total adjustment, times subject square footage.")


def _table5_intro(out):
    cs = out["competitive_set"]
    sel = cs.get("selected") or []
    ns = out["narrative_stats"]
    subj = out["subject"]
    region = subj.get("region") or "regional"
    vpsf = float(out["value_psf"])
    if not sel:
        s1 = ("All " + b(ns["n_comps"]) + " valuation comps come from inside " +
              b(subj["project"]) + ", and no competing projects in the subject's "
              "region recorded qualifying sales in the analysis window.")
        return s1
    contributed = [r for r in sel if r.get("comps_used", 0) > 0]
    tiers = []
    for r in sel:
        t = tier_label(r.get("tier"))
        if t not in tiers:
            tiers.append(t)
    tier_mix = tiers[0] if len(tiers) == 1 else (", ".join(tiers[:-1]) + " and " + tiers[-1])
    # v3.0: sentence one counts the ranked projects BY TIER rather than listing a tier-mix phrase.
    _tc = {}
    for r in sel:
        t = tier_label(r.get("tier"))
        _tc[t] = _tc.get(t, 0) + 1
    _parts = [b(v) + " " + k for k, v in sorted(_tc.items(), key=lambda kv: -kv[1])]
    tier_counts = _parts[0] if len(_parts) == 1 else (", ".join(_parts[:-1]) + " and " + _parts[-1])
    note = cs.get("note")
    if contributed:
        # v3.0 compressed sentence one (35-45 words), connective padding cut. The
        # region-honesty rule is preserved exactly: when ranked projects sit outside the
        # subject's region, the scope drops the region claim and the count is disclosed.
        subj_region = str(subj.get("region") or "")
        off = sum(1 for r in sel if str(r.get("region") or "") != subj_region)
        scope = (region + " projects competing for the same regional buyer pool") if off == 0 else \
                "projects competing for the subject's buyer pool"
        cross = "" if off == 0 else (" (" + b(off) + " of the ranked projects sit outside " + region + ")")
        _used = sum(int(r.get("comps_used", 0) or 0) for r in contributed)
        _back = len(sel) - len(contributed)
        s1 = ("The subject's competitive set is the " + b(len(sel)) + " " + scope + cross +
              ", ranked by comps used and then by comparability: " + b(len(contributed)) +
              (" supplying " if len(contributed) == 1 else " supplying ") + b(_used) +
              (" valuation comp" if _used == 1 else " valuation comps") +
              ((" and " + b(_back) + " by backfill") if _back else "") +
              ", spanning " + tier_counts + ".")
    else:
        s1 = ("All " + b(ns["n_comps"]) + " valuation comps come from inside " +
              b(subj["project"]) + "; the table below ranks the " + b(len(sel)) +
              " same-region " + ("project" if len(sel) == 1 else "projects") +
              " competing for its buyer pool, all placed by comparability, "
              "spanning " + tier_mix + ".")
    if note:
        s1 = s1[:-1] + ", " + note + "."
    avgs = [float(r["avg_psf"]) for r in sel]
    lo, hi = min(avgs), max(avgs)
    nearest = min(sel, key=lambda r: abs(float(r["avg_psf"]) - vpsf))
    npsf = float(nearest["avg_psf"])
    gap = abs(vpsf - npsf)
    mos = nearest.get("mos_since_last")
    recency = (", which last traded " + b(mos) + (" month" if mos == 1 else " months") + " ago"
               ) if mos is not None else ""
    # v3.0 sentence two (50-65 words): position against the range ONCE, then keep the full
    # timing explanation and its figures.
    if vpsf > hi:
        pos = ("sits above the set's " + b(psf(lo)) + " to " + b(psf(hi)) +
               "/SF range, a " + b(psf(gap)) + "/SF premium to " + nearest["project"] +
               ", the nearest-priced project" + recency)
    elif vpsf < lo:
        pos = ("sits below the set's " + b(psf(lo)) + " to " + b(psf(hi)) +
               "/SF range, a " + b(psf(gap)) + "/SF discount to " + nearest["project"] +
               ", the nearest-priced project" + recency)
    else:
        side = "above" if vpsf >= npsf else "below"
        pos = ("sits within the set's " + b(psf(lo)) + " to " + b(psf(hi)) +
               "/SF range, " + b(psf(gap)) + "/SF " + side + " " + nearest["project"] +
               ", the nearest-priced project" + recency)
    _g = float(out.get("growth_pct_used", 0) or 0)
    timing = ("; the set averages above are unadjusted for sale timing, so older prints "
              "understate today's market at the measured " + b("{:.1f}%".format(_g)) +
              " annual rate the engine applied")
    s2 = "The subject's valued " + b(psf(vpsf) + "/SF") + " " + pos + timing + "."
    return s1 + " " + s2



def _ord(n):
    n = int(n)
    return str(n) + ("th" if 10 <= n % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th"))

def _k(v):
    return "${:,.0f}K".format(round(float(v) / 1000))

def demo_strengths(d):
    """Rank a project's demographic signals vs Florida baselines. Returns
    (wi_clause_or_None, ordered strength phrases). Only true strengths qualify;
    every figure comes from 'Demographic Data - Project' ratios supplied in d."""
    if not d:
        return None, []
    sig = []
    def add(key, ratio, thresh, score, phrase):
        r = d.get(ratio) if isinstance(ratio, str) else ratio
        if r is not None and float(r) >= thresh:
            sig.append((key, float(score), phrase))
    g = d.get
    if g("seas_ratio") and g("seasonal_share_5mi") is not None:
        add("seas", "seas_ratio", 1.5, float(g("seas_ratio")) * 0.85,
            "a " + b("{:.1f}%".format(float(g("seasonal_share_5mi")))) + " second home share (" +
            b("{:.1f}x".format(float(g("seas_ratio")))) + " the Florida rate)")
    if g("lux_ratio") and g("lux_housing_share_5mi") is not None:
        add("lux", "lux_ratio", 1.5, float(g("lux_ratio")) * 0.9,
            "luxury homes at " + b("{:.1f}%".format(float(g("lux_housing_share_5mi")))) +
            " of local stock (" + b("{:.1f}x".format(float(g("lux_ratio")))) + " the Florida share)")
    if g("p200_ratio") and g("pct_hh_200k_plus_5mi") is not None:
        add("p200", "p200_ratio", 1.4, float(g("p200_ratio")),
            b("{:.1f}%".format(float(g("pct_hh_200k_plus_5mi")))) + " of households earning " +
            b("$200K+") + " (" + b("{:.1f}x".format(float(g("p200_ratio")))) + " the state share)")
    if g("mhv_ratio") and g("mhv_5mi") is not None:
        add("mhv", "mhv_ratio", 1.25, float(g("mhv_ratio")),
            "a " + b(_k(g("mhv_5mi"))) + " median home value (" +
            b("{:.1f}x".format(float(g("mhv_ratio")))) + " the Florida median)")
    if g("inc_ratio") and g("median_hh_income_5mi") is not None and not any(k == "p200" for k, _, _ in sig):
        add("inc", "inc_ratio", 1.25, float(g("inc_ratio")),
            "median household income of " + b(_k(g("median_hh_income_5mi"))) + " (" +
            b("{:.1f}x".format(float(g("inc_ratio")))) + " the state)")
    if g("veh3_ratio") and g("pct_hh_vehicles_3_plus_5mi") is not None:
        add("veh3", "veh3_ratio", 1.2, float(g("veh3_ratio")) * 1.15,
            b("{:.1f}%".format(float(g("pct_hh_vehicles_3_plus_5mi")))) +
            " of households keeping three or more vehicles (" +
            b("{:.1f}x".format(float(g("veh3_ratio")))) + " the state rate)")
    if g("hh200k_5mi") is not None and float(g("hh200k_5mi")) >= 3000:
        sig.append(("depth", 1.0 + float(g("hh200k_5mi")) / 20000,
            b("{:,.0f}".format(float(g("hh200k_5mi")))) + " households earning " + b("$200K+") +
            " within five miles"))
    if g("total_households_5mi") is not None and float(g("total_households_5mi")) >= 50000:
        sig.append(("scale", 1.05,
            "a " + b("{:,.0f}".format(float(g("total_households_5mi")))) + " household trade area"))
    sig.sort(key=lambda x: -x[1])
    keys = [k for k, _, _ in sig]
    if "depth" in keys and "scale" in keys:
        d_i = keys.index("depth")
        merged = (b("{:,.0f}".format(float(g("hh200k_5mi")))) + " households earning " + b("$200K+") +
                  " across a " + b("{:,.0f}".format(float(g("total_households_5mi")))) +
                  " household trade area")
        sig[d_i] = ("depth", sig[d_i][1], merged)
        sig = [x for x in sig if x[0] != "scale"]
    wi_clause = None
    if g("wealth_index") is not None and g("wi_pctl") is not None:
        pct, wi = float(g("wi_pctl")), float(g("wealth_index"))
        if pct >= 60:
            wi_clause = ("ranks in the " + b(_ord(pct) + " percentile") + " of " +
                         b("Storage Condo King") + "'s Florida footprint on wealth index (" +
                         b("{:.1f}/10".format(wi)) + ")")
        elif pct >= 40:
            wi_clause = ("carries a mid pack " + b("{:.1f}/10".format(wi)) + " wealth index across " +
                         b("Storage Condo King") + "'s Florida footprint")
    return wi_clause, [(k, ph) for k, _, ph in sig]


# v3.1: the ANCHORS map and DEVELOPER_SALES_URL are RETIRED. The Unit Summary block no longer
# authors any link. The website renders the tab strip and the listing calls to action, so an
# authored "#tab-..." or "/pre-sale-deals" link duplicated a live control. Sections now end on
# their last prose sentence or last bullet. Do not reintroduce authored links here.
# The "# Unit Summary" delimiter string is UNCHANGED: it is a frontend parsing contract.


def pw(v):
    """Whole-dollar PSF for owner-facing block copy ($708)."""
    return "${:,.0f}".format(round(float(v)))


def rw(lo, hi):
    return (pw(lo) + " to " + pw(hi) + "/SF") if abs(float(hi) - float(lo)) >= 0.5 else (pw(lo) + "/SF")


def sub_prose(s):
    """Render DB submarket values as prose: 'Naples; Bonita Springs' -> 'Naples and Bonita Springs'."""
    parts = [p.strip() for p in str(s or "").split(";") if p.strip()]
    if not parts:
        return "N/A"
    if len(parts) == 1:
        return parts[0]
    if len(parts) == 2:
        return parts[0] + " and " + parts[1]
    return ", ".join(parts[:-1]) + ", and " + parts[-1]


def month_year_before(iso_date, months_ago):
    import datetime as _dt
    d = _dt.date.fromisoformat(str(iso_date)[:10])
    m = d.year * 12 + (d.month - 1) - int(months_ago)
    return _dt.date(m // 12, m % 12 + 1, 1).strftime("%B %Y")


def _cap(phrase):
    for i, ch in enumerate(phrase):
        if ch.isalpha():
            return phrase[:i] + ch.upper() + phrase[i + 1:]
    return phrase

def _range_phrase(lo, hi):
    return (psf(lo) + " to " + psf(hi) + "/SF") if abs(hi - lo) >= 0.01 else (psf(lo) + "/SF")

def _set_size(k):
    return ("a single competing" if k == 1 else ("a " + str(k) + " project")) 

SFHA_ZONES = ("A", "AE", "AH", "AO", "AR", "A99", "V", "VE")


def flood_read(zone):
    """FEMA zone with its plain-language risk read. Returns '-' when unset, so the
    Construction bullet always keeps three slots (v3.2)."""
    z = str(zone or "").strip().upper()
    if not z or z in ("N/A", "NONE"):
        return "-"
    risk = "high risk" if z in SFHA_ZONES else "low risk"
    return "FEMA Flood Zone " + z + " (" + risk + ")"


def construction_line(subj):
    """v3.2 Construction bullet, mirroring the developer sale Construction Materials bullet:
    materials, common area finish, flood zone + risk. Any null component renders '-' in its
    slot; the component and the bullet are never dropped."""
    mats = str(subj.get("construction_materials") or "").strip() or "-"
    fin = str(subj.get("common_area_finish") or "").strip()
    fin = (fin + " common areas") if fin else "-"
    return ", ".join([mats, fin, flood_read(subj.get("flood_zone"))]) + "."


def unit_summary_block(out):
    """Owner-facing Unit Summary block. Copy and disclosure per website-chat review:
    concentration disclosure over 80% same-project share, exact comp-source shares,
    prior-sale trend line when the unit's own sale is in the set, honest cap language,
    whole-dollar PSF, prose submarket names, deduped bullets. v3.1: NO authored links in
    any section, and Unit Highlights emits exactly five priority-ordered bullets.
    Every figure from engine output; no valuation math here."""
    subj = out["subject"]
    ns = out["narrative_stats"]
    t1 = out["table1"]
    band = out["finish_level_band"]
    comps = out["comps"]
    proj = str(subj["project"])
    bp = b(proj)
    unit = str(subj.get("unit_number") or "N/A")
    vpsf = float(out["value_psf"])
    value = out["estimated_market_value"]
    n = ns["n_comps"]
    a = ns["class_a"]
    share = round(100.0 * a / n) if n else 0
    tier = tier_label(subj.get("amenity_tier"))
    subp = sub_prose(subj.get("submarket"))
    region = str(subj.get("region") or "Florida")
    sel = out["competitive_set"].get("selected") or []
    contributed = [r for r in sel if r.get("comps_used", 0) > 0]
    growth = float(out.get("growth_pct_used", 0))
    wi_clause, strengths = demo_strengths(subj.get("demo"))
    ssf = int(round(float(subj["unit_size_sf"])))
    own_comp = next((c for c in comps if c.get("own_sale")), None)
    own = ", including this unit's own prior sale" if ns.get("own_sale_included") else ""

    L = []
    L.append("---")
    L.append("")
    L.append("# Unit Summary")
    L.append("")

    # 1. Unit Value Summary
    L.append("## Unit Value Summary")
    sent = (b("Storage Condo King") + " values Unit " + b(unit) + " at " + bp + " at " +
            b(money(value)) + " (" + b(pw(vpsf) + "/SF") + ") as of " +
            fmt_date_long(out["appraisal_date"]) + ". Sales recorded in this market support " +
            b(money(band["low_value"])) + " to " + b(money(band["high_value"])) +
            " depending on interior buildout.")
    if own_comp:
        prior = round(float(own_comp["psf"]) * float(own_comp["size"]))
        chg = 100.0 * (float(value) - prior) / prior
        sent += (" The unit last sold for " + b(money(prior)) + " in " +
                 month_year_before(out["appraisal_date"], own_comp["mos"]) +
                 "; today's estimate marks a " + b("{:+.1f}%".format(chg)) + " change.")
    side = "above" if vpsf >= float(t1["comp_avg_psf"]) else "below"
    bow_bits = tier + " product"
    if wi_clause:
        bow_bits += " on one of " + b("Storage Condo King") + "'s top wealth markets"
    elif strengths:
        bow_bits += " in a demand-deep " + subp + " trade area"
    sent += (" It is " + bow_bits + ", valued " + side + " its comp set's " +
             b(pw(t1["comp_avg_psf"]) + "/SF") + " average.")
    # v3.2 action orientation: tie the value to what the unit has earned and the owner's
    # option to act on it. Prose only, no link, never hard-sell.
    _earned = ("built real equity over its last recorded sale" if own_comp
               else "held its value against the surrounding market")
    _act = (" The unit has " + _earned + ", and owners ready to harvest that equity can list "
            "it for sale on " + b("Storage Condo King") + ".")
    if n and share > 80:
        if a == n:
            sent += (" All " + b(n) + " comparables are sales within " + bp + own +
                     "; concentration in a single project anchors the value in direct "
                     "evidence, though it gives less to cross-check against other projects.")
        else:
            sent += (" " + b(a) + " of " + b(n) + " comparables (" + b(str(share) + "%") +
                     ") are sales within " + bp + own +
                     "; that concentration anchors the value in direct evidence, though it gives less to cross-check against other projects.")
    L.append(sent + _act)
    L.append("")

    # 2. Your Unit (v3.2). The lead carries PRODUCT CHARACTER ONLY. It must not repeat the unit
    # number, size, year built or tier pill: the site's hero grid renders all of those directly
    # above this tab. Then EXACTLY four bold-headed bullets.
    L.append("## Your Unit")
    _corridor = (subp + " corridor") if subp and subp != "N/A" else (region + " market")
    L.append(bp + " is " + tier.replace("-Tier", "-tier") + " garage condo product in the " +
             _corridor + ", built for owners who store and work on vehicles they care about.")
    addr = subj.get("address")
    pid = subj.get("parcel_id")
    if addr or pid:
        idbits = []
        if addr:
            idbits.append(str(addr))
        if pid:
            idbits.append("parcel " + str(pid))
        L.append("- " + b("Unit Profile:") + " " + ", ".join(idbits) + ".")
    L.append("- " + b("Construction:") + " " + construction_line(subj))
    if a:
        vb = b(n) + " recorded comparable sales, " + b(a) + " inside " + bp + " itself" + own + "."
    else:
        vb = ("All " + b(n) + " comparables come from neighboring projects, as " + bp +
              " has no sales recorded in the last 60 months.")
    L.append("- " + b("Value Basis:") + " " + vb)
    L.append("- " + b("Finish-Level Range:") + " " + b(money(band["low_value"])) + " to " +
             b(money(band["high_value"])) + " (" + b(rw(band["low_psf"], band["high_psf"])) +
             "), reflecting buildout differences not visible in recorded sales.")
    L.append("")

    # 3. Market Summary (v3.2: moved ABOVE Location, matching the developer sale listing order)
    L.append("## Market Summary")
    ttm = subj.get("market_ttm")
    if a == n and n:
        comp_src = "all " + b(n) + " from inside " + bp
    elif a:
        comp_src = (b(a) + " from inside " + bp + " and " + b(n - a) + " from competing projects")
    elif contributed:
        comp_src = ("drawn from " + b(len(contributed)) + " competing " +
                    ("project" if len(contributed) == 1 else "projects") +
                    " in the " + subp + " submarket")
    else:
        comp_src = "drawn from neighboring projects"
    # v3.2 opener: market depth read as LIQUIDITY. The depth claim is earned, not automatic:
    # under 10 trailing sales the count is still reported, without the claim.
    mo = ""
    if ttm:
        mo = ("The " + subp + " submarket recorded " + b(ttm["count"]) +
              (" sale" if ttm["count"] == 1 else " sales") +
              " in the trailing twelve months at a " + b("${:,.0f}".format(ttm["med_psf"]) + "/SF") +
              " median")
        mo += (", a re-sale market deep enough to price and absorb a listing. "
               if ttm["count"] >= 10 else ". ")
    mo += ("Unit " + b(unit) + "'s " + b(pw(vpsf) + "/SF") + " value rests on " + b(n) +
           " comparable sales, " + comp_src + ", averaging " +
           b(pw(t1["comp_avg_psf"]) + "/SF") + " before adjustments and " +
           b(pct(t1["total_adj"])) + " after, using recent sales, weighted toward the newest.")
    if sel:
        avgs = [float(r["avg_psf"]) for r in sel]
        lo, hi = min(avgs), max(avgs)
        pos = "above" if vpsf > hi else ("below" if vpsf < lo else "within")
        setspan = ("spanning " + b(rw(lo, hi))) if abs(hi - lo) >= 0.5 else ("at " + b(pw(lo) + "/SF"))
        mo += (" Against " + _set_size(len(sel)) + " " + region + " competitive set " + setspan +
               ", the unit prices " + pos + " the set on tier and quality.")
    # v3.2 closer: state the owner's position as equity, never as advice.
    if own_comp:
        _p = round(float(own_comp["psf"]) * float(own_comp["size"]))
        _c = 100.0 * (float(value) - _p) / _p
        mo += (" For the owner that is " + b("{:+.1f}%".format(_c)) + " of compounded growth "
               "since the last recorded sale, held as equity in the unit today.")
    else:
        mo += (" For the owner that value sits in the unit as equity, priced off what this "
               "market has actually paid.")
    L.append(mo)
    L.append("")

    # 4. Location Overview
    L.append("## Location Overview")
    narrative = subj.get("location_extract")
    if narrative:
        loc = str(narrative).rstrip(".") + ". Its five mile trade area"
        if wi_clause:
            loc += " " + wi_clause
            if strengths:
                loc += ", with " + strengths[0][1]
                if len(strengths) > 1:
                    loc += " and " + strengths[1][1]
        elif strengths:
            loc += " carries " + strengths[0][1]
            if len(strengths) > 1:
                loc += " and " + strengths[1][1]
        else:
            loc += " anchors the " + subp + " submarket of " + region
        L.append(loc + ".")
    else:
        loc = bp + " sits in the " + subp + " submarket of " + region
        if wi_clause:
            loc += ", a trade area that " + wi_clause
            if strengths:
                loc += ", with " + strengths[0][1]
                if len(strengths) > 1:
                    loc += " and " + strengths[1][1]
        elif strengths:
            loc += ", a trade area with " + strengths[0][1]
            if len(strengths) > 1:
                loc += " and " + strengths[1][1]
        else:
            d = subj.get("demo") or {}
            if d.get("total_households_5mi"):
                loc += (", a " + b("{:,.0f}".format(float(d["total_households_5mi"]))) +
                        " household trade area" +
                        ((" with " + b("{:.1f}%".format(float(d["owner_occupancy_rate_5mi"]))) +
                          " owner occupancy") if d.get("owner_occupancy_rate_5mi") else ""))
            else:
                loc += ", where " + b("Storage Condo King") + " tracks every recorded garage condo sale"
        L.append(loc + ".")
    L.append("")

    # 5. Unit Highlights (v3.1). EXACTLY five bullets, chosen by a fixed priority order: the
    # first five candidates that qualify are emitted and the rest are dropped silently. Bullets
    # are never merged to fit. Prior Sale Trend qualifies only when the unit's own prior sale is
    # in the comp set; when it suppresses, the next candidate moves up.
    L.append("## Unit Highlights")
    candidates = []

    # 1. Prior Sale Trend - conditional.
    if own_comp:
        prior = round(float(own_comp["psf"]) * float(own_comp["size"]))
        chg = 100.0 * (float(value) - prior) / prior
        candidates.append("- " + b("Prior Sale Trend:") + " Last sold for " + b(money(prior)) + " in " +
                          month_year_before(out["appraisal_date"], own_comp["mos"]) +
                          "; today's " + b(money(value)) + " estimate marks a " +
                          b("{:+.1f}%".format(chg)) + " change.")

    # 2. Current Value - always qualifies.
    candidates.append("- " + b("Current Value:") + " " + b(money(value)) + " at " + b(pw(vpsf) + "/SF") +
                      ", effective " + fmt_date_long(out["appraisal_date"]) + ".")

    # 3. Value Anchor - always qualifies; keeps the >80% concentration clause.
    dpct = 100.0 * (vpsf - float(t1["comp_avg_psf"])) / float(t1["comp_avg_psf"])
    va = ("Sits " + b("{:+.1f}%".format(dpct)) + " " + ("above" if dpct >= 0 else "below") +
          " the comp set's average before adjustments of " + b(pw(t1["comp_avg_psf"]) + "/SF"))
    if n and share > 80:
        va += (", on evidence drawn " + ("entirely" if a == n else "predominantly") +
               " from inside the project")
    candidates.append("- " + b("Value Anchor:") + " " + va + ".")

    # 4. Trophy Quality Product - always qualifies; keeps the finish-level range.
    candidates.append("- " + b("Trophy Quality Product:") + " " + tier + " unit at " + bp +
                      ", finish level carrying a " + b(rw(band["low_psf"], band["high_psf"])) +
                      " value range from shell to full custom buildout.")

    # 5. Competitive Positioning - always qualifies; never names a project.
    if sel:
        avgs = [float(r["avg_psf"]) for r in sel]
        lo, hi = min(avgs), max(avgs)
        pos = "above" if vpsf > hi else ("below" if vpsf < lo else "within")
        rng = (b(rw(lo, hi)) + " range") if abs(hi - lo) >= 0.5 else (b(pw(lo) + "/SF") + " mark")
        candidates.append("- " + b("Competitive Positioning:") + " Values " + pos + " the " + region +
                          " competitive set's " + rng + " on tier and quality.")
    else:
        candidates.append("- " + b("Competitive Positioning:") + " No competing " + region +
                          " projects have sales recorded in the last 60 months.")

    # 6. Dynamic Growth Market - keeps the honest-cap language when it renders.
    if subj.get("rate_capped"):
        candidates.append("- " + b("Dynamic Growth Market:") + " Sale timing compounded at " +
                          b("{:.1f}%".format(growth)) + " annually, the policy ceiling; the measured "
                          "blended rate was higher and was capped.")
    else:
        candidates.append("- " + b("Dynamic Growth Market:") + " Sale timing compounded at the measured " +
                          b("{:.1f}%".format(growth)) + " blended annual appreciation rate.")

    # 7. Local Demand Drivers.
    if strengths:
        dd = [ph for k, ph in strengths if k not in ("scale",)]
        candidates.append("- " + b("Local Demand Drivers:") + " " + _cap(dd[0] if dd else strengths[0][1]) + ".")
    elif subj.get("demo") and (subj["demo"].get("total_households_5mi")):
        candidates.append("- " + b("Local Demand Drivers:") + " A " +
                          b("{:,.0f}".format(float(subj["demo"]["total_households_5mi"]))) +
                          " household five mile trade area.")
    else:
        candidates.append("- " + b("Local Demand Drivers:") + " " + subp +
                          " submarket demand tracked across every recorded garage condo sale.")

    chosen = candidates[:5]
    if len(chosen) != 5:
        raise AssertionError("Unit Highlights must emit exactly 5 bullets, got %d" % len(chosen))
    L.extend(chosen)
    L.append("")
    L.append(DISCLOSURE)
    L.append("")
    return "\n".join(L)

def render(out):
    subj = out["subject"]
    t1 = out["table1"]
    ns = out["narrative_stats"]
    comps = out["comps"]
    band = out["finish_level_band"]
    growth = float(out.get("growth_pct_used", 0))
    n = ns["n_comps"]
    value = out["estimated_market_value"]
    vpsf = float(out["value_psf"])
    ssf = int(round(float(subj["unit_size_sf"])))
    sub_tier = tier_label(subj.get("amenity_tier"))
    eff_long = fmt_date_long(out["appraisal_date"])

    L = []
    L.append("# Luxury Garage Condo Unit Market Value Report")
    L.append("")
    L.append("## 1. Property Summary")
    wi = subj.get("wealth_index")
    L += ["- " + b("Project Name:") + " " + str(subj["project"]),
          "- " + b("Address:") + " " + str(subj.get("address") or "N/A"),
          "- " + b("Unit Number:") + " " + str(subj.get("unit_number") or "N/A"),
          "- " + b("Parcel ID:") + " " + str(subj.get("parcel_id") or "N/A"),
          "- " + b("City:") + " " + str(subj.get("city") or "N/A"),
          "- " + b("Region:") + " " + str(subj.get("region") or "N/A"),
          "- " + b("Submarket:") + " " + str(subj.get("submarket") or "N/A"),
          "- " + b("Year Built:") + " " + str(subj.get("year_built") or "N/A"),
          "- " + b("Number of Units:") + " " + str(subj.get("number_of_units") or "N/A"),
          "- " + b("Unit Size (SF):") + " {:,} SF".format(ssf),
          "- " + b("Amenity Tier:") + " " + sub_tier,
          "- " + b("Wealth Index (All):") + " " + ("{:.1f}".format(wi) if wi is not None else "N/A")]
    L.append("")
    L.append("## 2. Value Estimate")
    L += ["- " + b("Estimated Market Value:") + " " + money(value),
          "- " + b("Value Per SF:") + " " + psf(vpsf) + "/SF",
          "- " + b("Finish-Level Range:") + " " + money(band["low_value"]) + " to " +
          money(band["high_value"]) + " (" + psf(band["low_psf"]) + " to " +
          psf(band["high_psf"]) + "/SF)",
          "- " + b("Effective Date:") + " " + eff_long]
    L.append("")
    L.append("## 3. Market Value Summary")
    L.append("")
    L.append("### Tab 1 - Value Summary")
    L.append("")
    L.append(b("Valuation Overview"))
    L.append("")
    # v3.0 length discipline (matches the Cowork skill sck-unit-resale-valuation):
    # paragraph 1 is EXACTLY two sentences, 55-70 words; every sentence carries a figure
    # or a disclosure; no figure is restated across paragraphs. Sentence one is value,
    # $/SF, unit, project, tier, size. Sentence two is the comp evidence as one compound
    # clause leading with the same-project count, then the score band, then the largest
    # driver. No framing lead-ins.
    own = ns.get("own_sale_included")
    own_txt = ", including the unit's own prior sale," if own else ","
    dk, dv = ns["largest_adj"][0]
    p1_s1 = ("Unit " + b(subj.get("unit_number")) + " at " + b(subj["project"]) + ", a " +
             b("{:,}".format(ssf)) + " SF unit in a " + sub_tier + " project, carries an "
             "estimated market value of " + b(money(value)) + ", or " + b(psf(vpsf) + "/SF") + ".")
    if ns["class_a"]:
        p1_s2 = (b(ns["class_a"]) + " of the " + b(n) + " comparables are recorded sales inside " +
                 b(subj["project"]) + " itself" + own_txt + " a same-project core spanning "
                 "selection scores " + b("{:.2f}".format(ns["score_min"])) + " to " +
                 b("{:.2f}".format(ns["score_max"])) + ", with " + DRIVER_NAME[dk] +
                 " the largest adjustment driver at " + b(pct(dv)) + ".")
    else:
        p1_s2 = ("All " + b(n) + " comparables are drawn from adjacent projects, as " +
                 b(subj["project"]) + " recorded no qualifying sales in the analysis window, "
                 "spanning selection scores " + b("{:.2f}".format(ns["score_min"])) + " to " +
                 b("{:.2f}".format(ns["score_max"])) + ", with " + DRIVER_NAME[dk] +
                 " the largest adjustment driver at " + b(pct(dv)) + ".")
    p1 = p1_s1 + " " + p1_s2
    L.append(p1)
    L.append("")
    # Paragraph 2 stands alone and never restates paragraph 1's value, $/SF or unit size.
    p2 = ("The " + b(n) + " comparables average an unadjusted " + b(psf(t1["comp_avg_psf"]) + "/SF") +
          " before adjustment, and a " + b(pct(t1["total_adj"])) + " net adjustment for sale "
          "timing, wealth index, amenity tier, unit size and sale type reconciles them to the "
          "valued rate, with adjusted values spanning " + b(psf(band["low_psf"])) + " to " +
          b(psf(band["high_psf"]) + "/SF") + ", the finish-level band a shell versus a "
          "built-out unit could realize.")
    L.append(p2)
    L.append("")
    exc = ns.get("excluded_outliers", 0)
    extra = ""
    if exc:
        extra = (", and " + b(exc) + (" outlier sale was" if exc == 1 else " outlier sales were") +
                 " screened from the comp set")
    elif n < 7:
        extra = ", and the comp set is thin, so the band should be read with added care"
    p3 = ("Finish level is not observable in recorded sales, so the value reflects a "
          "market-average buildout (customized units may exceed it; shells may trail it)" +
          extra + ".")
    L.append(p3)
    L.append("")
    L.append(b("Table 1 - Value Summary"))
    L.append("")
    L.append(row("Line", "$/SF"))
    L.append(row("---", "---"))
    L.append(row("Comp Average", psf(t1["comp_avg_psf"])))
    L.append(row("Total Adjustment", pct(t1["total_adj"])))
    L.append(row("Market Value ({:,} SF)".format(ssf), psf(vpsf) + "/SF (" + money(value) + ")"))
    L.append("")
    L.append("### Tab 2 - Comparable Sales")
    L.append("")
    nc, rs = ns["new_construction"], ns["resale"]
    sub_mismatch = sum(1 for c in comps if (c.get("submarket") or subj.get("submarket")) != subj.get("submarket"))
    mm = ("; " + b(sub_mismatch) + (" comp sits" if sub_mismatch == 1 else " comps sit") +
          " outside the subject's submarket") if sub_mismatch else ""
    # own_txt carries a trailing comma for the paragraph-1 clause; this sentence supplies its
    # own ", scoring ..." continuation, so strip it here to avoid a doubled comma.
    _own_cs = own_txt.rstrip(",")
    a_txt = (b(ns["class_a"]) + " inside " + subj["project"] + " itself" + _own_cs) if ns["class_a"] \
        else ("all from adjacent projects with none inside " + subj["project"] + " itself")
    cs_sent = (b("Comp Selection") + ": the valuation draws on " + b(n) + " comparable sales, " +
               a_txt +
               ", scoring " + b("{:.2f}".format(ns["score_min"])) + " to " +
               b("{:.2f}".format(ns["score_max"])) + ", split " + b(nc) +
               " new-construction and " + b(rs) + " re-sale to bracket finish levels" + mm + ".")
    side = "above" if vpsf >= float(t1["comp_avg_psf"]) else "below"
    cs_pos = ("At " + b(psf(vpsf) + "/SF") + ", the unit anchors " + side +
              " its comp set's " + b(psf(t1["comp_avg_psf"]) + "/SF") +
              " unadjusted average within " + subj["project"] + "'s current market.")
    L.append(cs_sent + " " + cs_pos)
    L.append("")
    L.append(b("Table 2 - Comparable Sales"))
    L.append("")
    hdr2 = ["#", "Project", "Unit #", "Address", "Class", "Mos Ago", "Tier", "Sale Type", "SF", "Score"]
    L.append(row(*hdr2))
    L.append(row(*(["---"] * len(hdr2))))
    L.append(row("S", subj["project"], subj.get("unit_number"), subj.get("address") or "N/A",
                 "Subject", 0, sub_tier, "Re-Sale", "{:,}".format(ssf), ""))
    has_dagger = False
    for i, c in enumerate(comps, 1):
        u = str(c.get("unit") if c.get("unit") is not None else "N/A")
        if c.get("own_sale"):
            u += " \u2020"
            has_dagger = True
        L.append(row(i, c.get("project"), u, c.get("address") or "N/A", c.get("class"),
                     c.get("mos"), tier_label(c.get("amenity")), c.get("sale_type") or "N/A",
                     "{:,}".format(int(round(c["size"]))), "{:.2f}".format(c["score"])))
    t2a = out["table2_avg"]
    L.append(row("Avg", "", "", "", "", t2a["mos"], "", "", "{:,}".format(int(round(t2a["size"]))),
                 "{:.2f}".format(t2a["score"])))
    if has_dagger:
        L.append("")
        L.append("\u2020 the subject unit's own prior sale.")
    L.append("")
    L.append("### Tab 3 - Comp Adjustments")
    L.append("")
    # v3.0 length discipline: TWO short sentences, 45-65 words. Sentence one is framing plus
    # the dominant driver with its figure and the one fact explaining it; sentence two names
    # the next-largest drivers with figures and nothing else. No category parentheticals (the
    # five bullets define them) and no closing interpretive clause.
    _ranked = rank_drivers(out["table3_avg"])
    d1 = _ranked[0]
    _fact = driver_fact(d1[0], growth)
    adj_s1 = (b("Adjustments") + ": each comparable is translated to the subject through six "
              "standardized adjustments applied additively to its unadjusted $/SF; the dominant "
              "driver is " + DRIVER_NAME[d1[0]] + " at " + b(pct(d1[1])) +
              ((", " + _fact) if _fact else "") + ".")
    _next = [kv for kv in _ranked[1:3] if kv[0] != d1[0]]
    if len(_next) >= 2:
        adj_s2 = ("The next largest are " + DRIVER_NAME[_next[0][0]] + " at " + b(pct(_next[0][1])) +
                  " and " + DRIVER_NAME[_next[1][0]] + " at " + b(pct(_next[1][1])) + ".")
    elif _next:
        adj_s2 = ("The next largest is " + DRIVER_NAME[_next[0][0]] + " at " + b(pct(_next[0][1])) + ".")
    else:
        adj_s2 = ""
    # Honest cap disclosure: named only when the engine actually capped a category on at
    # least one comparable, silent otherwise.
    _capped = capped_categories(comps)
    if _capped:
        _names = [n for n, _ in _capped]
        _lead = (_names[0] if len(_names) == 1 else
                 (", ".join(_names[:-1]) + " and " + _names[-1]))
        _caps = [b("{:.0f}%".format(cv)) for _, cv in _capped]
        _capstr = _caps[0] if len(_caps) == 1 else (", ".join(_caps[:-1]) + " and " + _caps[-1])
        adj_s3 = (" On at least one comparable " + _lead +
                  (" reached its" if len(_names) == 1 else " reached their") +
                  " cap of " + _capstr + ", so the applied adjustment is held at the cap "
                  "rather than the full computed difference.")
    else:
        adj_s3 = ""
    # v2.9: build quality clips at +/-8%. The engine flags the comp when the MEASURED
    # difference exceeded the ceiling, which value-equality alone would not prove.
    _bqcap = [c for c in comps if c.get("bq_capped")]
    if _bqcap:
        _v = float(_bqcap[0].get("bq_adj", 0) or 0)
        adj_s3 += (" Build quality at " + b("{:+.1f}%".format(_v)) + ", the category ceiling, "
                   "with the measured difference exceeding it and capped.")
    L.append((adj_s1 + " " + adj_s2 + adj_s3).strip())
    L.append("")
    L += ["- " + b("Sale Timing") + ": compounded at the blended regional/statewide repeat-sales appreciation rate. Capped at 25%.",
          "- " + b("Wealth Index") + ": 4.0% per index point of difference. Capped at 25%.",
          "- " + b("Amenity Tier") + ": 5% to 20% depending on tier gap.",
          "- " + b("Build Quality") + ": 2.0% per Build Quality Index point of difference "
          "(construction materials plus common area finish above the tier floor). Capped at 8%.",
          "- " + b("Sale Type") + ": 5.0% pre-construction incentive added to new-construction comps (the subject is a re-sale).",
          "- " + b("Unit Size") + ": 2% per 100 SF of size difference. Capped at 20%."]
    L.append("")
    L.append(b("Table 3 - Comp Adjustments"))
    L.append("")
    hdr3 = ["#", "Project", "Unit #", "Wealth Index", "Sale Timing", "Amenity Tier",
            "Build Quality Adj", "Unit Size", "Sale Type", "Net Adj %", "$/SF", "Net Adj. $ PSF"]
    L.append(row(*hdr3))
    L.append(row(*(["---"] * len(hdr3))))
    for i, c in enumerate(comps, 1):
        u = str(c.get("unit") if c.get("unit") is not None else "N/A")
        if c.get("own_sale"):
            u += " \u2020"
        L.append(row(i, c.get("project"), u, pct(c["wi_adj"]), pct(c["time_adj"]),
                     pct(c["amen_adj"]), pct(c.get("bq_adj", 0)), pct(c["size_adj"]),
                     pct(c["type_adj"]),
                     pct(c["net_adj"]), psf(c["psf"]), psf(c["adj_psf"])))
    t3 = out["table3_avg"]
    avg_adj_psf = round(sum(c["adj_psf"] for c in comps) / len(comps), 2)
    L.append(row("Avg", "", "", pct(t3["wi_adj"]), pct(t3["time_adj"]), pct(t3["amen_adj"]),
                 pct(t3.get("bq_adj", 0)), pct(t3["size_adj"]), pct(t3["type_adj"]),
                 pct(t1["total_adj"]), psf(t1["comp_avg_psf"]), psf(avg_adj_psf)))
    L.append("")
    L.append(b("Table 4 - Adjustment Component Averages"))
    L.append("")
    L.append(row("Component", "Avg Adj %"))
    L.append(row("---", "---"))
    for label, key in (("Sale Timing", "time_adj"), ("Wealth Index", "wi_adj"),
                       ("Amenity Tier", "amen_adj"), ("Build Quality", "bq_adj"),
                       ("Sale Type", "type_adj"), ("Unit Size", "size_adj")):
        L.append(row(label, pct(t3.get(key, 0))))
    L.append(row("Total", pct(t1["total_adj"])))
    L.append("")
    L.append(b("Table 5 - Competitive Set"))
    L.append("")
    L.append(_table5_intro(out))
    L.append("")
    sel = out["competitive_set"].get("selected") or []
    if sel:
        hdr5 = ["Rank", "Project", "Submarket", "Tier", "Avg $/SF", "Comps Used",
                "Mos Since Last Sale", "Score"]
        L.append(row(*hdr5))
        L.append(row(*(["---"] * len(hdr5))))
        for r in sel:
            L.append(row(r["rank"], r["project"], r.get("submarket") or "N/A",
                         tier_label(r.get("tier")), psf(r["avg_psf"]), r.get("comps_used", 0),
                         r.get("mos_since_last") if r.get("mos_since_last") is not None else "N/A",
                         "{:.2f}".format(r["score"])))
        L.append("")
    L.append(b("Methodology") + ": " + METHODOLOGY)
    L.append("")
    L.append(DISCLOSURE)
    L.append("")
    L.append(unit_summary_block(out))
    return "\n".join(L)


def validate(report, out):
    """Structural contract checks. Returns a list of problems (empty = pass)."""
    p = []
    subj = out["subject"]

    def need(s, what):
        if s not in report:
            p.append("missing: " + what)
    need("# Luxury Garage Condo Unit Market Value Report", "H1 title")
    for h in ("## 1. Property Summary", "## 2. Value Estimate", "## 3. Market Value Summary",
              "### Tab 1 - Value Summary", "### Tab 2 - Comparable Sales",
              "### Tab 3 - Comp Adjustments"):
        need(h, h)
    need("| # | Project | Unit # | Address | Class | Mos Ago | Tier | Sale Type | SF | Score |",
         "exact Table 2 header")
    # v2.9 adds a Build Quality Adj column. Legacy five-category reports still validate.
    _t3_v29 = ("| # | Project | Unit # | Wealth Index | Sale Timing | Amenity Tier | "
               "Build Quality Adj | Unit Size | Sale Type | Net Adj % | $/SF | Net Adj. $ PSF |")
    _t3_v28 = ("| # | Project | Unit # | Wealth Index | Sale Timing | Amenity Tier | Unit Size | "
               "Sale Type | Net Adj % | $/SF | Net Adj. $ PSF |")
    if _t3_v29 not in report and _t3_v28 not in report:
        p.append("missing: exact Table 3 header")
    need("**Table 4 - Adjustment Component Averages**", "Table 4 label")
    need("**Table 5 - Competitive Set**", "Table 5 label")
    need("**Finish-Level Range:**", "finish-level range line")
    need("**Estimated Market Value:** " + money(out["estimated_market_value"]), "value line matches engine")
    need("prepared by Storage Condo King", "closing disclosure")
    if "Confidence is" in report:
        p.append("confidence statement present")
    if "## 4" in report or "five-year projection" in report.lower():
        p.append("banned section/projection present")
    if not report.rstrip().endswith("appraisal.*"):
        p.append("disclosure is not the final element")
    if report.count("prepared by Storage Condo King") != 2:
        p.append("disclosure must close both the valuation and the Unit Summary block")
    i_block = report.find("\n# Unit Summary")
    if i_block < 0:
        p.append("Unit Summary block missing")
    else:
        head = report[:i_block]
        if not head.rstrip().endswith("---"):
            p.append("Unit Summary block must follow a horizontal rule")
        if "prepared by Storage Condo King" not in head:
            p.append("valuation half must end with the disclosure before the block")
        # v3.2 section ORDER is part of the contract: Market Summary sits above Location
        # Overview, matching the developer sale listing order.
        order = ("## Unit Value Summary", "## Your Unit", "## Market Summary",
                 "## Location Overview", "## Unit Highlights")
        pos = []
        for sec in order:
            at = report.find(sec, i_block)
            if at < 0:
                p.append("block section missing: " + sec)
            else:
                pos.append((sec, at))
        if len(pos) == len(order) and [x[1] for x in pos] != sorted(x[1] for x in pos):
            p.append("Unit Summary sections out of order; expected " + " then ".join(order))
        # v3.2 Your Unit emits exactly four bold-headed bullets (Unit Profile is omitted only
        # when the unit has neither an address nor a parcel).
        yu = report.find("## Your Unit", i_block)
        if yu >= 0:
            ytail = report[yu:].split("\n\n")[0]
            ybul = sum(1 for ln in ytail.splitlines() if ln.startswith("- "))
            if ybul not in (3, 4):
                p.append("Your Unit must have 4 bullets (3 without Unit Profile), found %d" % ybul)
        # v3.1: Unit Highlights emits EXACTLY five bullets. Fail loudly rather than ship six.
        block = report[i_block:]
        hi = block.find("## Unit Highlights")
        if hi >= 0:
            tail = block[hi:].split("\n\n")[0]
            n_bul = sum(1 for ln in tail.splitlines() if ln.startswith("- "))
            if n_bul != 5:
                p.append("Unit Highlights must have exactly 5 bullets, found %d" % n_bul)
        # v3.1: the block authors NO links; the website owns the tab strip and the CTAs.
        if "](#tab-" in block or "](/pre-sale-deals)" in block or "](#contact)" in block:
            p.append("authored link found in the Unit Summary block (v3.1 removes all links)")
    for r in out["competitive_set"].get("selected") or []:
        if r["project"] == subj["project"]:
            p.append("subject project appears in Table 5")
    # v3.0: the contributed branch's compressed sentence one reads "ranked by comps used";
    # the legacy phrase is still accepted so older stored reports keep validating.
    if "ranked by comps used" not in report and \
       "supplying valuation comps rank first" not in report and \
       "valuation comps come from inside" not in report:
        p.append("Table 5 two-sentence intro missing")
    return p


if __name__ == "__main__":
    data = json.load(open(sys.argv[1]))
    rpt = render(data)
    problems = validate(rpt, data)
    if problems:
        sys.stderr.write("VALIDATION FAILED:\n" + "\n".join(" - " + x for x in problems) + "\n")
        sys.exit(1)
    print(rpt)
