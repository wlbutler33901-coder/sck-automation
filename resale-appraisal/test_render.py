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


def run(sales, label):
    data = {"subject": subject(), "appraisal_date": TODAY.isoformat(),
            "market_growth_pct": 10.0, "sales_comps": sales}
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
    assert "supplying valuation comps rank first" in rpt2
    print("PASS scenario 2 (contributed intro): value %s, %d comps, %d Table 5 rows"
          % ("${:,}".format(out2["estimated_market_value"]),
             out2["narrative_stats"]["n_comps"], len(out2["competitive_set"]["selected"])))
    print("PASS all render tests")


if __name__ == "__main__":
    main()
