#!/usr/bin/env python3
"""Deterministic report renderer for the SCK unit re-sale appraisal engine.

Fills references/report-template.md (skill v1.9 spec) from the engine's JSON
output. No model in the loop: every number comes from the engine, every
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
               "wi_adj": "wealth index"}

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
               "finish-level dispersion. Five standardized adjustments follow, and the "
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
    note = cs.get("note")
    if contributed:
        subj_region = str(subj.get("region") or "")
        off = sum(1 for r in sel if str(r.get("region") or "") != subj_region)
        scope = (region + " projects competing for the same regional buyer pool") if off == 0 else \
                "projects competing for the subject's buyer pool"
        cross = "" if off == 0 else (" (" + b(off) + " of the ranked projects sit outside " + region + ")")
        s1 = ("The subject's competitive set groups the " + b(len(sel)) + " " + scope + ": the " +
              b(len(contributed)) +
              (" project" if len(contributed) == 1 else " projects") +
              " supplying valuation comps rank first" + cross + ", backfilled by comparability, "
              "spanning " + tier_mix + ".")
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
    if vpsf > hi:
        pos = ("sits above the set's " + b(psf(lo)) + " to " + b(psf(hi)) +
               "/SF range, a " + b(psf(gap)) + "/SF premium to " + nearest["project"] + recency)
    elif vpsf < lo:
        pos = ("sits below the set's " + b(psf(lo)) + " to " + b(psf(hi)) +
               "/SF range, a " + b(psf(gap)) + "/SF discount to " + nearest["project"] + recency)
    else:
        side = "above" if vpsf >= npsf else "below"
        pos = ("sits within the set's " + b(psf(lo)) + " to " + b(psf(hi)) +
               "/SF range, " + b(psf(gap)) + "/SF " + side + " " + nearest["project"] + recency)
    s2 = "The subject's valued " + b(psf(vpsf) + "/SF") + " " + pos + "."
    return s1 + " " + s2


DEVELOPER_SALES_URL = "/pre-sale-deals"  # live Developer Sales listing route (App.tsx)

def unit_summary_block(out):
    """Owner-facing Unit Summary block appended after the valuation half.
    Mirrors the presale Sale Listing Summary skeleton (H1 delimiter, five
    H2 sections, arrow link idiom, brand/project bolding, closing disclosure)
    reoriented as a valuation resource for unit owners, ending with the
    Developer Sales funnel link. Every figure comes from engine output."""
    subj = out["subject"]
    ns = out["narrative_stats"]
    t1 = out["table1"]
    band = out["finish_level_band"]
    proj = str(subj["project"])
    bp = b(proj)
    unit = str(subj.get("unit_number") or "N/A")
    vpsf = float(out["value_psf"])
    n = ns["n_comps"]
    a = ns["class_a"]
    sel = out["competitive_set"].get("selected") or []
    L = []
    L.append("---")
    L.append("")
    L.append("# Unit Summary")
    L.append("")
    L.append("## Unit Value Summary")
    own = ", including this unit's own prior sale" if ns.get("own_sale_included") else ""
    L.append(b("Storage Condo King") + " values Unit " + b(unit) + " at " + bp + " at " +
             b(money(out["estimated_market_value"])) + " (" + b(psf(vpsf) + "/SF") + ") as of " +
             fmt_date_long(out["appraisal_date"]) + ". Recorded comparable evidence supports " +
             b(money(band["low_value"])) + " to " + b(money(band["high_value"])) +
             " depending on interior buildout.")
    L.append("- [Value Summary →](#tab-value-summary)")
    L.append("- [Contact Storage Condo King →](#contact)")
    L.append("")
    L.append("## Your Unit")
    yr = subj.get("year_built")
    L.append("Unit " + b(unit) + " at " + bp + " in " + str(subj.get("city") or "N/A") +
             " is a " + b("{:,} SF".format(int(round(float(subj["unit_size_sf"]))))) + " " +
             tier_label(subj.get("amenity_tier")) + " unit" +
             (" built in " + b(yr) if yr else "") + ".")
    if a:
        vb = (b(n) + " recorded comparable sales, " + b(a) + " inside " + bp + " itself" + own + ".")
    else:
        vb = ("All " + b(n) + " comparables come from neighboring projects; " + bp +
              " recorded no qualifying sales in the 60 month analysis window.")
    L.append("- " + b("Unit Profile:") + " " + b("{:,} SF".format(int(round(float(subj["unit_size_sf"]))))) +
             " of " + tier_label(subj.get("amenity_tier")) + " space, unit " + b(unit) + ".")
    L.append("- " + b("Value Basis:") + " " + vb)
    L.append("- " + b("Finish-Level Range:") + " " + b(money(band["low_value"])) + " to " +
             b(money(band["high_value"])) + " (" + b(psf(band["low_psf"])) + " to " +
             b(psf(band["high_psf"]) + "/SF") + "), reflecting buildout differences invisible in recorded sales.")
    L.append("")
    L.append("## Location")
    L.append(bp + " sits in the " + str(subj.get("submarket") or "N/A") + " submarket of " +
             str(subj.get("region") or "Florida") + ", where " + b("Storage Condo King") +
             " tracks every recorded garage condo sale.")
    L.append("- [Demographic Profile →](#tab-demographic-profile)")
    L.append("")
    L.append("## Market Overview")
    src = ("drawn largely from inside " + bp) if a and a >= n / 2 else \
          ("drawn from " + b(max(len([r for r in sel if r.get("comps_used", 0) > 0]), 1)) + " competing projects") if sel else \
          ("drawn from neighboring projects")
    L.append("Unit " + b(unit) + " is valued at " + b(psf(vpsf) + "/SF") +
             " against an unadjusted comp average of " + b(psf(t1["comp_avg_psf"]) + "/SF") +
             ", evidence " + src + ".")
    if sel:
        avgs = [float(r["avg_psf"]) for r in sel]
        lo, hi = min(avgs), max(avgs)
        pos = "above" if vpsf > hi else ("below" if vpsf < lo else "within")
        L.append("The unit prices " + pos + " its competing set's " + b(psf(lo)) + " to " +
                 b(psf(hi) + "/SF") + " range.")
    L.append("- [Competitive Set →](#tab-competitive-set)")
    L.append("- [Market Summary →](#tab-market-data)")
    L.append("")
    L.append("## Owner Highlights")
    side = "above" if vpsf >= float(t1["comp_avg_psf"]) else "below"
    L.append("- " + b("Current Value:") + " " + b(money(out["estimated_market_value"])) + " at " +
             b(psf(vpsf) + "/SF") + ", " + side + " the comp set's " +
             b(psf(t1["comp_avg_psf"]) + "/SF") + " unadjusted average.")
    L.append("- " + b("Value Anchor:") + " " + vb)
    L.append("- " + b("Appreciation Basis:") + " Sale timing compounded at the measured " +
             b("{:.1f}%".format(float(out.get("growth_pct_used", 0)))) + " blended annual rate, capped by policy.")
    if sel:
        L.append("- " + b("Market Position:") + " Valued " + pos + " the competing set's " +
                 b(psf(lo)) + " to " + b(psf(hi) + "/SF") + " range across " + b(len(sel)) +
                 " ranked " + ("project" if len(sel) == 1 else "projects") + ".")
    else:
        L.append("- " + b("Market Position:") + " No competing projects in " +
                 str(subj.get("region") or "the region") + " recorded qualifying sales in the analysis window.")
    L.append("- " + b("Next Step:") + " Owners considering a sale can contact " +
             b("Storage Condo King") + "; new developer offerings across Florida are listed on the platform.")
    L.append("- [Explore Developer Sales →](" + DEVELOPER_SALES_URL + ")")
    L.append("- [Get an Updated Valuation →](#contact)")
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
    own = ns.get("own_sale_included")
    own_txt = ", including the unit's own prior sale" if own else ""
    dk, dv = ns["largest_adj"][0]
    p1 = ("The unit carries an estimated market value of " + b(money(value)) + " (" +
          b(psf(vpsf) + "/SF") + "), Unit " + b(subj.get("unit_number")) + " at " +
          b(subj["project"]) + ", a " + sub_tier + " project. " +
          b(ns["class_a"]) + " of " + b(n) + " comparables are sales inside " +
          subj["project"] + " itself" + own_txt + ", anchoring the value in the "
          "project's own trading history. The largest adjustment driver this run is " +
          DRIVER_NAME[dk] + " at " + b(pct(dv)) + ".")
    L.append(p1)
    L.append("")
    p2 = ("The " + b(n) + " comparables average an unadjusted " + b(psf(t1["comp_avg_psf"]) + "/SF") +
          " and a " + b(pct(t1["total_adj"])) + " total adjustment reconciles to " +
          b(psf(vpsf) + "/SF") + " (" + b(money(value)) + " at " + b("{:,}".format(ssf)) +
          " SF), with adjusted values spanning " + b(psf(band["low_psf"])) + " to " +
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
    cs_sent = (b("Comp Selection") + ": the valuation draws on " + b(n) + " comparable sales, " +
               b(ns["class_a"]) + " inside " + subj["project"] + " itself" + own_txt +
               ", spanning selection scores " + b("{:.2f}".format(ns["score_min"])) + " to " +
               b("{:.2f}".format(ns["score_max"])) + ", with " + b(nc) +
               " new-construction and " + b(rs) + " re-sale transactions, deliberate variety "
               "that brackets unobservable finish levels" + mm + ".")
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
    d1, d2 = ns["largest_adj"][0], ns["largest_adj"][1] if len(ns["largest_adj"]) > 1 else ns["largest_adj"][0]
    adj_sent = (b("Adjustments") + ": each comparable is translated to the subject through five "
                "standardized adjustments applied additively to its unadjusted $/SF; this run's "
                "largest drivers are " + driver_clause(d1[0], d1[1], growth) + " and " +
                driver_clause(d2[0], d2[1], growth) + ".")
    L.append(adj_sent)
    L.append("")
    L += ["- " + b("Sale Timing") + ": compounded at the blended regional/statewide repeat-sales appreciation rate. Capped at 25%.",
          "- " + b("Wealth Index") + ": 4.0% per index point of difference. Capped at 25%.",
          "- " + b("Amenity Tier") + ": 5% to 20% depending on tier gap.",
          "- " + b("Sale Type") + ": 5.0% pre-construction incentive added to new-construction comps (the subject is a re-sale).",
          "- " + b("Unit Size") + ": 2% per 100 SF of size difference. Capped at 20%."]
    L.append("")
    L.append(b("Table 3 - Comp Adjustments"))
    L.append("")
    hdr3 = ["#", "Project", "Unit #", "Wealth Index", "Sale Timing", "Amenity Tier", "Unit Size",
            "Sale Type", "Net Adj %", "$/SF", "Net Adj. $ PSF"]
    L.append(row(*hdr3))
    L.append(row(*(["---"] * len(hdr3))))
    for i, c in enumerate(comps, 1):
        u = str(c.get("unit") if c.get("unit") is not None else "N/A")
        if c.get("own_sale"):
            u += " \u2020"
        L.append(row(i, c.get("project"), u, pct(c["wi_adj"]), pct(c["time_adj"]),
                     pct(c["amen_adj"]), pct(c["size_adj"]), pct(c["type_adj"]),
                     pct(c["net_adj"]), psf(c["psf"]), psf(c["adj_psf"])))
    t3 = out["table3_avg"]
    avg_adj_psf = round(sum(c["adj_psf"] for c in comps) / len(comps), 2)
    L.append(row("Avg", "", "", pct(t3["wi_adj"]), pct(t3["time_adj"]), pct(t3["amen_adj"]),
                 pct(t3["size_adj"]), pct(t3["type_adj"]), pct(t1["total_adj"]),
                 psf(t1["comp_avg_psf"]), psf(avg_adj_psf)))
    L.append("")
    L.append(b("Table 4 - Adjustment Component Averages"))
    L.append("")
    L.append(row("Component", "Avg Adj %"))
    L.append(row("---", "---"))
    for label, key in (("Sale Timing", "time_adj"), ("Wealth Index", "wi_adj"),
                       ("Amenity Tier", "amen_adj"), ("Sale Type", "type_adj"),
                       ("Unit Size", "size_adj")):
        L.append(row(label, pct(t3[key])))
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
    need("| # | Project | Unit # | Wealth Index | Sale Timing | Amenity Tier | Unit Size | "
         "Sale Type | Net Adj % | $/SF | Net Adj. $ PSF |", "exact Table 3 header")
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
        for sec in ("## Unit Value Summary", "## Your Unit", "## Location",
                    "## Market Overview", "## Owner Highlights"):
            if sec not in report[i_block:]:
                p.append("block section missing: " + sec)
        if "[Explore Developer Sales →](" not in report[i_block:]:
            p.append("Developer Sales funnel link missing")
    for r in out["competitive_set"].get("selected") or []:
        if r["project"] == subj["project"]:
            p.append("subject project appears in Table 5")
    if "supplying valuation comps rank first" not in report and \
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
