#!/usr/bin/env python3
"""Offline end-to-end test: synthetic sales -> engine subprocess -> render -> validate.
Covers both Table 5 intro variants (same-project-only and contributed backfill).
Runs with no network; used locally and as a CI gate before every batch."""
import json, os, subprocess, sys, tempfile, datetime
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from render_report import render, validate

TODAY = datetime.date.today()


def sale(project, unit, mos, psf, sf, tier, styp, region="Test Region", sub="Test Sub", wi=6.0, pid=None):
    d = TODAY - datetime.timedelta(days=int(mos * 30.44) + 5)
    return {"Project Name": project, "Unit": str(unit), "Sale Type": styp,
            "Sale Date": d.isoformat(), "Sale Price": round(psf * sf),
            "Sq. Ft.": sf, "$ / SF": psf, "Region": region, "Submarket": sub,
            "Amenity": tier, "Year Built": 2021, "Wealth Index (All)": wi,
            "Parcel ID": pid or ("%s-%s" % (project[:3].upper(), unit)), "Address": "%s Test Ave" % unit}


def subject():
    return {"project": "Test Motor Condos", "unit_number": "204", "parcel_id": "TMC-SUBJ",
            "address": "204 Test Ave", "city": "Testville", "year_built": 2021,
            "unit_size_sf": 1200, "region": "Test Region", "submarket": "Test Sub",
            "number_of_units": 40, "amenity_tier": "Standard-Tier", "wealth_index": 6.0}


def tier_of(comp_row):
    """Normalized amenity tier of a rendered comp row (engine field `amenity`)."""
    a = str(comp_row.get("amenity") or "").lower()
    return "Track-Side" if "track" in a else a


def run(sales, label, subj=None, project_attributes=None):
    data = {"subject": subj or subject(), "appraisal_date": TODAY.isoformat(),
            "market_growth_pct": 10.0, "sales_comps": sales,
            "project_attributes": project_attributes or {}}
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        json.dump(data, f); path = f.name
    r = subprocess.run([sys.executable, os.path.join(HERE, "appraise_unit.py"), path],
                       capture_output=True, text=True)
    os.unlink(path)
    assert r.returncode == 0, "%s: engine failed: %s" % (label, r.stderr)
    out = json.loads(r.stdout)
    rpt = render(out)
    problems = validate(rpt, out)
    assert not problems, "%s: validation failed: %s" % (label, problems)
    return out, rpt


def main():
    # Scenario 1: same-project-only comp set, competitor projects present in the pool only
    s1 = [sale("Test Motor Condos", 200 + i, 2 + i * 3, 300 + i * 6, 1150 + i * 20,
               "Standard-Tier", "Re-Sale" if i % 3 else "New Construction") for i in range(10)]
    s1 += [sale("Rival Garage Park", 10 + i, 8 + i * 5, 340 + i * 5, 1300, "Premium-Tier", "Re-Sale")
           for i in range(3)]
    s1 += [sale("Bayline Motor Suites", 30 + i, 10 + i * 6, 275, 1100, "Flex-Tier", "Re-Sale")
           for i in range(3)]
    out1, rpt1 = run(s1, "same-project-only")
    assert all(r["comps_used"] == 0 for r in out1["competitive_set"]["selected"])
    assert "valuation comps come from inside" in rpt1
    # v3.2 voice pass: same disclosure, plain-owner wording.
    assert "cross-check against other projects" in rpt1, "concentration disclosure missing"
    assert "Prior Sale Trend" in rpt1, "prior-sale trend missing"
    print("PASS scenario 1 (same-project-only intro): value %s, %d comps, %d Table 5 rows"
          % ("${:,}".format(out1["estimated_market_value"]),
             out1["narrative_stats"]["n_comps"], len(out1["competitive_set"]["selected"])))

    # Scenario 2: thin same-project core, adjacent projects contribute comps
    s2 = [sale("Test Motor Condos", 300 + i, 3 + i * 4, 310 + i * 5, 1180, "Standard-Tier", "Re-Sale")
          for i in range(3)]
    s2 += [sale("Rival Garage Park", 50 + i, 4 + i * 2, 330 + i * 4, 1250, "Standard-Tier", "Re-Sale")
           for i in range(5)]
    s2 += [sale("Bayline Motor Suites", 70 + i, 6 + i * 3, 290 + i * 3, 1150, "Standard-Tier",
                "New Construction") for i in range(4)]
    out2, rpt2 = run(s2, "contributed")
    assert any(r["comps_used"] > 0 for r in out2["competitive_set"]["selected"])
    assert "ranked by comps used" in rpt2  # v3.0 compressed sentence one
    print("PASS scenario 2 (contributed intro): value %s, %d comps, %d Table 5 rows"
          % ("${:,}".format(out2["estimated_market_value"]),
             out2["narrative_stats"]["n_comps"], len(out2["competitive_set"]["selected"])))
    # Scenario 3: thin core forces cross-region Class D backfill -> honest region label
    s3 = [sale("Test Motor Condos", 400 + i, 3 + i * 5, 300 + i * 8, 1200, "Standard-Tier", "Re-Sale")
          for i in range(3)]
    s3 += [sale("Faraway Garage Works", 90 + i, 3 + i * 2, 320 + i * 4, 1250, "Premium-Tier", "Re-Sale",
                region="Other Region", sub="Other Sub", wi=7.0) for i in range(5)]
    out3, rpt3 = run(s3, "cross-region")
    assert "sit outside" in rpt3, "cross-region contributor label missing"
    print("PASS scenario 3 (cross-region contributor labeling)")

    # Scenario 4 (v2.8 direction A): NON-Track-Side subject must drop every Track-Side comp
    # from the pool before scoring, and still value cleanly off the remaining evidence.
    s4_subj = dict(subject(), amenity_tier="Premium-Tier")
    s4 = [sale("Test Motor Condos", 500 + i, 3 + i * 3, 320 + i * 6, 1200, "Premium-Tier", "Re-Sale")
          for i in range(8)]
    s4 += [sale("The Motor Enclave", 600 + i, 2 + i, 900 + i * 20, 1300, "Track-Side", "Re-Sale")
           for i in range(6)]
    out4, rpt4 = run(s4, "track-side excluded", subj=s4_subj)
    assert all(tier_of(c) != "Track-Side" for c in out4["comps"]), \
        "Track-Side comp leaked into a non-Track-Side subject's set"
    assert out4["estimated_market_value"] > 0
    print("PASS scenario 4 (Track-Side comps excluded for non-Track-Side subject): "
          "%d comps, none Track-Side, value %s"
          % (len(out4["comps"]), "${:,}".format(out4["estimated_market_value"])))

    # Scenario 5 (v2.8 direction B): Track-Side SUBJECT is restricted to Track-Side sales only
    # and the wealth-index adjustment is neutralized (track_mode, presale parity).
    s5_subj = dict(subject(), project="The Motor Enclave", amenity_tier="Track-Side",
                   parcel_id="TME-SUBJ", wealth_index=6.0)
    s5 = [sale("The Motor Enclave", 700 + i, 3 + i * 3, 880 + i * 10, 1250, "Track-Side",
               "Re-Sale", wi=7.0) for i in range(8)]
    s5 += [sale("Rival Garage Park", 800 + i, 2 + i, 330 + i * 5, 1200, "Premium-Tier",
                "Re-Sale", wi=7.0) for i in range(6)]
    out5, rpt5 = run(s5, "track-side subject", subj=s5_subj)
    assert all(tier_of(c) == "Track-Side" for c in out5["comps"]), \
        "non-Track-Side comp leaked into a Track-Side subject's set"
    assert all(abs(float(c["wi_adj"])) < 1e-9 for c in out5["comps"]), \
        "wealth-index adjustment not neutralized in track_mode"
    assert out5["estimated_market_value"] > 0
    print("PASS scenario 5 (Track-Side subject: track-only pool, WI neutralized): "
          "%d comps, all Track-Side, value %s"
          % (len(out5["comps"]), "${:,}".format(out5["estimated_market_value"])))

    # ================= v3.0 methodology =================
    def _pair(subj_mat, subj_fin, comp_mat, comp_fin, comp_styp="Re-Sale", subj_extra=None):
        sj = dict(subject(), construction_materials=subj_mat, common_area_finish=subj_fin)
        if subj_extra:
            sj.update(subj_extra)
        sl = [sale("Test Motor Condos", 900 + i, 4 + i * 3, 300 + i * 4, 1200, "Standard-Tier", "Re-Sale")
              for i in range(4)]
        sl += [sale("Peer Garage Works", 950 + i, 5 + i * 2, 290 + i * 3, 1210, "Standard-Tier", comp_styp)
               for i in range(4)]
        at = {"test motor condos": {"materials": subj_mat, "finish": subj_fin},
              "peer garage works": {"materials": comp_mat, "finish": comp_fin}}
        return sj, sl, at

    # (b) FINISH SPREAD, no floor: Luxury subject vs Basic comp = +8.00%.
    sj, sl, at = _pair("Block", "Luxury", "Block", "Basic")
    o, r = run(sl, "v3-finish", subj=sj, project_attributes=at)
    peer = [c for c in o["comps"] if c["project"] == "Peer Garage Works"]
    assert peer and all(abs(c["fin_adj"] - 8.00) < 1e-6 for c in peer), \
        "Luxury vs Basic must be +8.00%%, got %s" % [c["fin_adj"] for c in peer]
    print("PASS scenario 6 (v3.0 finish spread, no floor: Luxury subject vs Basic comp = %+.2f%%)"
          % peer[0]["fin_adj"])

    # (c) MATERIALS: metal comp against a concrete subject. Block 3 vs Metal 2 = +2.00%,
    #     translating the INFERIOR comp UP toward the subject, the same direction as
    #     AMEN_ADJ[("Premium","Standard")] = +8 and wi_adj = (s-c)*4.
    sj, sl, at = _pair("Block", "Basic", "Metal", "Basic")
    o, r = run(sl, "v3-materials", subj=sj, project_attributes=at)
    peer = [c for c in o["comps"] if c["project"] == "Peer Garage Works"]
    assert peer and all(abs(c["mat_adj"] - 2.00) < 1e-6 for c in peer), \
        "Block vs Metal must be +2.00%%, got %s" % [c["mat_adj"] for c in peer]
    print("PASS scenario 7 (v3.0 materials: metal comp vs concrete subject = %+.2f%%, comp translated toward subject)"
          % peer[0]["mat_adj"])

    # (d) SALE TYPE: a New Construction comp against a re-sale subject = +10.00%.
    sj, sl, at = _pair("Block", "Basic", "Block", "Basic", comp_styp="New Construction")
    o, r = run(sl, "v3-saletype", subj=sj, project_attributes=at)
    peer = [c for c in o["comps"] if c["project"] == "Peer Garage Works"]
    assert peer and all(abs(c["type_adj"] - 10.00) < 1e-6 for c in peer), \
        "New Construction comp must be +10.00%%, got %s" % [c["type_adj"] for c in peer]
    print("PASS scenario 8 (v3.0 sale type recalibrated: New Construction comp = %+.2f%%)"
          % peer[0]["type_adj"])

    # (e) WI SCALE GUARD: subject 7.6 against a comp recorded on the 0-100 scale (76).
    #     Both sides normalize to 0-10 first, so this is ~0.0%, NOT the -25 floor.
    sj = dict(subject(), wealth_index=7.6, construction_materials="Block", common_area_finish="Basic")
    sl = [sale("Test Motor Condos", 980 + i, 4 + i * 3, 300 + i * 4, 1200, "Standard-Tier", "Re-Sale", wi=7.6)
          for i in range(4)]
    sl += [sale("Scaled Peer Garages", 985 + i, 5 + i * 2, 295 + i * 3, 1205, "Standard-Tier", "Re-Sale", wi=76)
           for i in range(4)]
    at = {"test motor condos": {"materials": "Block", "finish": "Basic"},
          "scaled peer garages": {"materials": "Block", "finish": "Basic"}}
    o, r = run(sl, "v3-wi-guard", subj=sj, project_attributes=at)
    peer = [c for c in o["comps"] if c["project"] == "Scaled Peer Garages"]
    assert peer, "scaled peer comps missing"
    worst = max(abs(c["wi_adj"]) for c in peer)
    assert worst < 1.0, "wi scale guard failed: expected ~0%%, got %s" % [c["wi_adj"] for c in peer]
    print("PASS scenario 9 (v3.0 wi scale guard: subject 7.6 vs comp 76 = %+.2f%%, not -25)"
          % peer[0]["wi_adj"])

    # (f) CAP DISCLOSURE: Luxury/Tilt Wall subject vs Utility/Wood-Frame comp lands finish on
    #     its 12%% ceiling and materials on its 6%% ceiling; both must be disclosed.
    sj, sl, at = _pair("Tilt Wall", "Luxury", "Wood-Frame", "Utility")
    o, r = run(sl, "v3-caps", subj=sj, project_attributes=at)
    peer = [c for c in o["comps"] if c["project"] == "Peer Garage Works"]
    assert peer and all(abs(c["fin_adj"] - 12.00) < 1e-6 for c in peer), "finish should land on 12%% ceiling"
    assert peer and all(abs(c["mat_adj"] - 6.00) < 1e-6 for c in peer), "materials should land on 6%% ceiling"
    assert "finish level" in r and "construction materials" in r, "cap disclosure must name both categories"
    assert "reached their cap" in r or "reached its cap" in r, "cap disclosure sentence missing"
    print("PASS scenario 10 (v3.0 cap disclosure: finish +12.00%%, materials +6.00%%, both disclosed)")

    print("PASS all render tests")


if __name__ == "__main__":
    main()
