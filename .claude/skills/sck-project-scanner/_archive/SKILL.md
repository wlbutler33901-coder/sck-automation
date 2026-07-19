---
name: sck-project-scanner
description: Nightly (3am) automated discovery scan for new car condo, luxury garage condo, and motor condo projects across the Storage Condo King coverage footprint (FL, GA, NC, SC). Use whenever asked to run the SCK project scanner, the 3am scan, the nightly project discovery routine, scan a region or submarket for new projects, or find new car condo projects for the pipeline. Writes candidates ONLY to the staging table "01 - Project - New", never to live tables.
---

# SCK Project Scanner (v2 - nightly discovery)

Discovers new deeded car-condo projects and stages them for Will's review. Runs unattended; every decision must be deterministic and logged. Output feeds the Daily Intelligence Brief: the job is finding NEW projects and material changes, not qualifying financing leads.

## Hard rules
1. WRITE ONLY to "01 - Project - New" and "Scan Activity Log". NEVER insert, update, or delete in "01 - Projects" or any other table.
2. Dedup before every insert (Step 4). When in doubt, log a near-match flag instead of inserting.
3. Normalize en/em dashes in every name comparison: regexp_replace(lower(trim(x)), '[\u2013\u2014]', '-', 'g').
4. No em-dashes in any text written to the database.

## Step 1 - Tonight's rotation
Regions rotate across the week by display_order. Pull tonight's set:
```sql
WITH r AS (SELECT region, state_code, status, ROW_NUMBER() OVER (ORDER BY display_order) AS rn
           FROM "Market Coverage - Regions")
SELECT region, state_code, status FROM r
WHERE (rn - 1) % 7 = EXTRACT(DOW FROM CURRENT_DATE)::int;
```
New regions automatically join the rotation. 'coverage' (catch-all) regions get a lighter pass: 2-3 broad searches, not the full submarket sweep.

## Step 2 - Load context for those regions
```sql
SELECT submarket, status FROM "Market Coverage - Submarkets" WHERE region = $REGION;
SELECT "Project Name", "City" FROM "01 - Projects" WHERE "Region" = $REGION;
SELECT "Project Name", "City", review_status FROM "01 - Project - New" WHERE "Region" = $REGION;
```

## Step 3 - Search (v2 expanded source checklist)
Definition: individually DEEDED garage condominium units sold to owners. Includes track-side garage condos, motor condos, toy barns, garage suites, flex/warehouse garage condos (tag tier-2 in scan_notes). Excludes leased-only self-storage, membership-only clubs (log as context, do not insert), residential condos with garages.

Per active submarket, work the FULL checklist; log any blocked source in run_summary rather than silently skipping:
1. Query set per anchor city: "{city} garage condos", "{city} car condo", "{city} motor condo", "luxury garage for sale {city}", "toy storage condos {metro}", "garage suites {city}", "{county} garage condo development", "{city} car condo groundbreaking".
2. OPERATOR BRAND SWEEP: known multi-site operators expand along the SE footprint; check each brand's locations / coming-soon / news pages for anything new touching tonight's regions: Motor Vault, The Vault, Storage Caves, Motor District, ReVest / Garage Lofts, The Garages at (LKN, Lake Oconee, and siblings), The Hangar Group, GarageForLife, AutoVault, CollectionSuites, Iron Gate-style entrants, GarageTown USA, Big Boy Garages. Add newly discovered operators to this mental list and note them in run_summary so the skill list gets updated.
3. Listing platforms: LoopNet, Crexi, CommercialSearch, CityFeet with "garage condo" / "car condo" / "motor condo" filters for tonight's metros. MLS-syndicated portals (realtor.com commercial, homes portals showing new flex/garage-condo product with year built = current or next year) are strong early signals.
4. News and journals: local business journals (Bisnow, BizJournals metro editions, urbanize sites), PR wires, "{metro} garage condo" news-tab queries restricted to the last 60 days.
5. Government: county planning commission and zoning board agendas plus permit portals for the region's anchor counties ("garage condominium", "motor condo", "luxury garage" in recent agendas). These surface projects 6 to 18 months before marketing does.
6. Aggregators: onlygaragecondos.com state pages (low confidence, rumored unless corroborated).
7. Track-anchored: known circuits in region (road courses, motorsport parks) for trackside real estate announcements.
8. Public social pages (no login): developer Facebook/Instagram business pages found via search; groundbreaking and pre-sale announcements often post there first.
Use a mobile user agent/viewport when a site serves mobile-only layouts. Never bypass logins or CAPTCHAs.

SUNDAY DEEP SWEEP (in addition to the night's rotation): once a week, sweep EVERY operator brand site (item 2) across the entire FL/GA/NC/SC footprint, not just tonight's regions. One pass per brand; stage anything new through the same dedup gate.

## Step 4 - Dedup gate (mandatory, per candidate)
```sql
SELECT 'live' AS src, "Project Name", "City" FROM "01 - Projects"
WHERE regexp_replace(lower(trim("Project Name")),'[\u2013\u2014]','-','g') = $NORM_NAME
   OR (lower("City") = lower($CITY) AND similarity("Project Name", $NAME) > 0.55)
UNION ALL
SELECT 'staged', "Project Name", "City" FROM "01 - Project - New"
WHERE regexp_replace(lower(trim("Project Name")),'[\u2013\u2014]','-','g') = $NORM_NAME
   OR (lower("City") = lower($CITY) AND similarity("Project Name", $NAME) > 0.55);
```
(If pg_trgm similarity() is unavailable, fall back to exact normalized name + same-city substring checks.)
Exact match -> skip, no log. Near match -> do NOT insert; log change_type='near_match_flag' with both names in detail. Also compare ADDRESSES when available: same street address with different names is a duplicate (the Charleston Toy Box / Motor District case) - flag it.

## Step 5 - Insert candidate
```sql
INSERT INTO "01 - Project - New"
("Project Name","Project Status","Address","City","County","Submarket","Region","Website","Developer","Units","Avg Unit Size (SF)","Key Amenities",source_url,confidence,scan_notes)
VALUES (...);
```
- "Project Status": Completed | Under Construction | Planned. Rumored -> Planned + confidence 'low'.
- confidence: high (developer site w/ address+units), medium (developer marketing, partial data), low (aggregator/rumor only).
- Region/Submarket: assign from the county and city against "Market Coverage - Submarkets". If no submarket fits, use the region's closest match and note "submarket provisional" in scan_notes. Region must NEVER be null; every county in FL/GA/NC/SC belongs to exactly one region.
- scan_notes: source caveats, tier-2 flag, buy-or-lease flag, price points.
- If the Developer is new, ensure a matching row exists in "05 - Developers - New" (name only is fine; enrichment completes contacts).

## Step 6 - Log
One row per insert: change_type='new_candidate', confidence, detail = one-line summary with price/units.
End of run: change_type='run_summary', detail = regions covered, searches run, candidates inserted, near-matches flagged, sources blocked, new operators discovered.

## Note on deep research
This routine runs headless and cannot invoke the claude.ai Research feature. The complement is a MONTHLY manual Deep Research per region run by Will in claude.ai (saved prompt provided separately); its findings are ingested in a Cowork session that stages candidates through this same dedup gate. Do not attempt to replicate that here; the nightly job's edge is consistency, not depth.

## Scheduling (document for the operator, do not self-schedule)
Windows Task Scheduler / cron, 3:00 AM daily:
claude -p "Run the SCK project scanner nightly routine per the sck-project-scanner skill" --permission-mode acceptEdits
