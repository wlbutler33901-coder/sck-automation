---
name: sck-project-scanner
description: Nightly (3am) automated discovery scan for new car condo, luxury garage condo, and motor condo projects across the Storage Condo King coverage footprint (FL, GA, NC, SC). Use whenever asked to run the SCK project scanner, the 3am scan, the nightly project discovery routine, scan a region or submarket for new projects, or find new car condo projects for the pipeline. Writes candidates ONLY to the staging table "01 - Project - New", never to live tables.
---

# SCK Project Scanner (v3 - nightly discovery)

Discovers new deeded car-condo projects and stages them for Will's review. Runs unattended; every decision must be deterministic and logged. Output feeds the Daily Intelligence Brief: the job is finding NEW projects and material changes, not qualifying financing leads.

## Hard rules
1. WRITE ONLY to "01 - Project - New", "05 - Developers - New", "08 - Brokers - New", and "Scan Activity Log". NEVER insert, update, or delete in "01 - Projects" or any other live table.
2. LOGGING CONSTANTS (exact strings, never variants): every scanner log row uses run_type = 'scan'. NOT 'nightly_scan', NOT 'project_scan', NOT anything else. The morning digest keys on this exact value; drift here has broken the digest repeatedly.
3. NEVER supply explicit id values on staging-table inserts; let the sequence assign them. On a duplicate-key error, retry once (the sequence self-corrects) and log the collision.
4. Dedup before every insert (Step 4). When in doubt, log a near-match flag instead of inserting.
5. Normalize en/em dashes in every name comparison: regexp_replace(lower(trim(x)), '[\u2013\u2014]', '-', 'g').
6. No em-dashes in any text written to the database.
7. Read LEARNINGS.md at the repo root before anything else, and append a dated entry at run end per the contract in that file; in an unattended cloud run, record learnings as change_type learning rows in Scan Activity Log instead, and never commit, branch, or push.
8. Follow references/run-resilience.md for run logging, region checkpointing, and concurrency limits; run_type is always the literal string scan.

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
SELECT "Project Name", "City", "County", "Developer" FROM "01 - Projects" WHERE "Region" = $REGION;
SELECT "Project Name", "City", "County", "Developer", review_status FROM "01 - Project - New" WHERE "Region" = $REGION;
```

## Step 3 - Search (expanded source checklist)
Definition: individually DEEDED garage condominium units sold to owners. Includes track-side garage condos, motor condos, toy barns, garage suites, flex/warehouse garage condos (tag tier-2 in scan_notes). Excludes leased-only self-storage, membership-only clubs (log as context, do not insert), residential condos with garages.

Per active submarket, work the FULL checklist; log any blocked source in run_summary rather than silently skipping:
1. Query set per anchor city: "{city} garage condos", "{city} car condo", "{city} motor condo", "luxury garage for sale {city}", "toy storage condos {metro}", "garage suites {city}", "{county} garage condo development", "{city} car condo groundbreaking".
2. OPERATOR BRAND SWEEP: known multi-site operators expand along the SE footprint; check each brand's locations / coming-soon / news pages for anything new touching tonight's regions: Motor Vault, The Vault, Storage Caves, Motor District, ReVest / Garage Lofts, The Garages at (LKN, Lake Oconee, and siblings), The Hangar Group, GarageForLife, AutoVault, CollectionSuites, GarageTown USA, Big Boy Garages. Add newly discovered operators to this list via run_summary.
3. Listing platforms: LoopNet, Crexi, CommercialSearch, CityFeet with "garage condo" / "car condo" / "motor condo" filters for tonight's metros. MLS-syndicated portals showing new flex/garage-condo product are strong early signals.
4. News and journals: local business journals (Bisnow, BizJournals metro editions, urbanize sites), PR wires, "{metro} garage condo" news-tab queries restricted to the last 60 days.
5. Government: county planning commission and zoning board agendas plus permit portals for the region's anchor counties. These surface projects 6 to 18 months before marketing does.
6. Aggregators: onlygaragecondos.com state pages (low confidence, rumored unless corroborated).
7. Track-anchored: known circuits in region for trackside real estate announcements.
8. Public social pages (no login): developer Facebook/Instagram business pages found via search.
Use a mobile user agent when a site serves mobile-only layouts. Never bypass logins or CAPTCHAs.

SUNDAY DEEP SWEEP (in addition to the night's rotation): once a week, sweep EVERY operator brand site (item 2) across the entire FL/GA/NC/SC footprint. One pass per brand; stage anything new through the same dedup gate.

## Step 3b - Development Scanner cross-feed (car condo hits from the SWFL permit and news scanners)
The SWFL Development Scanner writes commercial permits and press to "Development Scanner - Municipality Portals" and "Development Scanner - News Scanner" in the same database. Every night, sweep BOTH over a 72 HOUR window.

WHY 72 HOURS, NOT 26: the SWFL scanners now run BEFORE this one (permit 2:00 AM, news 2:45 AM, this scanner 3:30 AM), so same-night rows are in scope. The wider window also self-heals a missed night, and re-staging is impossible because every hit still passes the Step 4 dedup gate.

```sql
SELECT id, "Project Name", "Address", "City", "County", "Developer / Sponsor / Key Principal" AS dev, "Development Description" AS detail, "Municipality Posting Look-Up Value" AS src
FROM "Development Scanner - Municipality Portals"
WHERE created_at >= now() - interval '72 hours'
  AND ("Development Description" ILIKE ANY (ARRAY['%garage%','%parking%','%car condo%','%motor condo%','%storage condo%','%garage suites%','%garage villas%','%toy barn%','%toy storage%','%motorsports%','%racing%','%race track%','%racing resort%','%motor club%','%car club%','%track club%','%paddock%'])
    OR "Project Name" ILIKE ANY (ARRAY['%garage%','%parking%','%car condo%','%motor condo%','%storage condo%','%garage suites%','%garage villas%','%toy barn%','%toy storage%','%motorsports%','%racing%','%race track%','%racing resort%','%motor club%','%car club%','%track club%','%paddock%']));
SELECT id, "Project Name", "City", "County", "Developer / Sponsor" AS dev, "Article Summary" AS detail, "Article URL" AS src
FROM "Development Scanner - News Scanner"
WHERE created_at >= now() - interval '72 hours'
  AND ("Article Summary" ILIKE ANY (ARRAY['%garage%','%parking%','%car condo%','%motor condo%','%storage condo%','%garage suites%','%garage villas%','%toy barn%','%toy storage%','%motorsports%','%racing%','%race track%','%racing resort%','%motor club%','%car club%','%track club%','%paddock%'])
    OR "Project Name" ILIKE ANY (ARRAY['%garage%','%parking%','%car condo%','%motor condo%','%storage condo%','%garage suites%','%garage villas%','%toy barn%','%toy storage%','%motorsports%','%racing%','%race track%','%racing resort%','%motor club%','%car club%','%track club%','%paddock%']));
```

TWO-STAGE SCREEN (every keyword match passes this BEFORE staging). The keyword list is deliberately broad, so the screen, not the keyword, decides what gets staged:
1. DEEDED / FOR-SALE / CONDOMINIUM evidence present (deeded units, for sale, condominium, ownership, individually owned suites): STAGE normally through Step 4 dedup and Step 5, confidence per source (high permit-sourced, medium news-sourced).
2. CLEARLY PUBLIC OR LEASED product (public parking deck or garage, municipal parking, leased self-storage, rental-only flex): DO NOT STAGE. Log change_type='cross_feed_screened' with the reason in detail (for example "public parking deck, not deeded product").
3. HIGH-PRIOR CATEGORY, OWNERSHIP UNKNOWN (motorsports clubs, racing resorts, track developments): STAGE at confidence='medium' with a scan_notes line reading exactly: verify deeded garage condo component before advancing.

Rule 3 exists because Hyper Club (Naples Racing Resort), a 542 acre Collier County motorsports conversion, was surfaced by the SWFL news scanner on 2026-08-05 and MISSED by the cross-feed purely for lack of a motorsports keyword; it was staged manually on 2026-08-06. A motorsports or track development is a car-condo candidate until proven otherwise, not the reverse.

Every staged hit: source_url = the permit look-up value or article URL, note "via Development Scanner cross-feed" in scan_notes, and log change_type='crossfeed_candidate'. Screened-out hits log change_type='cross_feed_screened' and are never staged.

## Step 4 - Dedup gate (mandatory, per candidate, MULTI-SIGNAL)
A candidate is a DUPLICATE if ANY of these signals fires against EITHER "01 - Projects" (live) or "01 - Project - New" (staged), matched within the same COUNTY (not just the same city - the Bonita Auto Vault / Bonita Motor Vault miss happened because the check was city-scoped and name-threshold only):
1. Exact dash-normalized name match.
2. DISTINCTIVE-TOKEN match: strip the GENERIC PRODUCT TOKENS from both names (auto, motor, car, garage, vehicle, vault, condo, condos, suites, storage, club, luxury, premium, the, at, of), then compare what remains. "Bonita Auto Vault" and "Bonita Motor Vault" both reduce to "Bonita": same county + same distinctive tokens = DUPLICATE. Remaining-token similarity above 0.7 also counts as a match.
3. Same normalized street address (strip suite numbers, punctuation, case).
4. Same parcel / folio number.
5. Same Developer (dash-normalized) in the same county.
On ANY signal: DO NOT INSERT. Log change_type='near_match_flag' naming the signal that fired and both project names. When the match is against a LIVE project, say so explicitly (that is usually press using a naming variant for an existing asset).
When land size is available on both sides, a matching acreage within 10 percent strengthens a borderline call; note it in the flag.

## Step 5 - Insert candidate
```sql
INSERT INTO "01 - Project - New"
("Project Name","Project Status","Address","City","County","Submarket","Region","Website","Developer","Units","Avg Unit Size (SF)","Key Amenities","Sales Broker","Sales Broker Contact","Sales Broker Email",source_url,confidence,scan_notes)
VALUES (...);
```
- "Project Status": Completed | Under Construction | Planned. Rumored -> Planned + confidence 'low'.
- confidence: high (developer site w/ address+units), medium (developer marketing, partial data), low (aggregator/rumor only).
- Region/Submarket: assign from the county and city against "Market Coverage - Submarkets". Region must NEVER be null.
- AMENITY VOCABULARY. "Key Amenities" holds ONLY canonical Amenity values from "11 - Property - Amenity Definition", comma separated, matched via the Amenity and Aliases columns. Facts that are not amenities (unit counts, acreage, pricing, deed structure, location context) go to scan_notes, never into Key Amenities. A genuinely new amenity type gets INSERTed into "11 - Property - Amenity Definition" with Status 'proposed', a one line Definition, and the observed phrasing in Aliases, then used in the row; never invent a synonym for something the table already covers.
- PROPERTY DIMENSIONS. Two more dimensions have their own definition tables: "Construction Materials" (canonical values Tilt Wall, Block, Metal, Wood-Frame from "11 - Property - Construction Materials", comma separated when mixed) and "Common Area Finish Level" (one of Luxury, High-Quality, Basic, Utility from "11 - Property - Common Area Finish Level"). When source material states construction type or finish grade, write these columns instead of putting construction or finish words into Key Amenities; construction and finish terms are no longer amenities.
- BROKER CAPTURE: when the listing or project site names a sales broker, populate "Sales Broker", "Sales Broker Contact", and "Sales Broker Email" on the staged row, and ensure a matching row exists in "08 - Brokers - New" ("Broker" name minimum; enrichment completes the contact card). If sales are clearly developer-direct, write 'Developer-Direct' into "Sales Broker" so the field is never silently null. Every property should end up with BOTH a developer and a broker answer.
- KNOWN-CONTACT CROSS-REFERENCE. Run this whenever a contact name or email is attached to a staged project or an outreach draft.
  1. MATCH the contact against the live directory tables: "08 - Brokers" (Broker, Contact, Email), "05 - Developers", "05 - Developers - All Property Types", "09 - Lenders", and "04 - Unit Owner CRM". Match on exact email (split multi-address cells on ';', lower, trim) and on normalized name (lower, trim, dashes normalized). Append EVERY match to scan_notes, for example 'Contact matches 08 - Brokers #52 Robert Zinzell (Brokerage)'.
  2. ROLE ROUTING on a broker match: a contact found in "08 - Brokers" is NEVER written to the "Developer" field of "01 - Project - New". File them into "Sales Broker", "Sales Broker Contact" and "Sales Broker Email" on the staged project, leave "Developer" null when the true developer is unknown, and keep hunting the real developer through the county permit record, the SunBiz registration of the project LLC, and the project site. A broker marketing a project for sale is a LISTING SIGNAL, not a developer identification.
  Every reclassification or flag is logged to "Scan Activity Log" as change_type='role_correction' naming the matched table and row, so the morning digest can report it. These are READ-ONLY lookups: match and annotate, never modify a live row, never fabricate a contact, normalize dashes in every comparison, and write no em-dashes into stored text.
- NORMALIZED DEVELOPER CHECK. Normalize the candidate name (lowercase, trim, strip punctuation and parenthetical qualifiers, strip suffix words llc, inc, llp, co, corp, company, group, properties, development, developments, partners, holdings) and match against BOTH "05 - Developers" and "05 - Developers - New" on normalized name, and also on any shared email address, email domain (excluding freemail domains), or phone digits. On any match, do NOT insert; reference the existing row in the project row's scan_notes and log the reuse. Only genuinely new firms get a row.
- If the Developer is new, ensure a matching row exists in "05 - Developers - New" (name only is fine; enrichment completes contacts).
- scan_notes: source caveats, tier-2 flag, buy-or-lease flag, price points.

## Step 6 - Log
The run_started and region_complete rows required by references/run-resilience.md are in addition to the rows below.
One row per insert: run_type='scan', change_type='new_candidate', confidence, detail = one-line summary.
End of run: run_type='scan', change_type='run_summary', detail = regions covered, searches run, candidates inserted, near-matches flagged, sources blocked, new operators discovered.


## Learnings file (read first, append on lessons)
At RUN START: read the repo-root file LEARNINGS.md (the last ~30 entries) and honor every lesson in it; it is the memory that keeps mistakes from repeating.
At RUN END: append an entry ONLY when something failed, was corrected, surprised you, or required a workaround (never for routine success), one line:
- {YYYY-MM-DD} | {routine} | {what happened} | {lesson or fix}
Then commit the file ("learnings: {routine} {date}") and push. If the push is blocked by branch policy, leave it committed and say so in the run summary.

## Version self-check (prevents skill/instruction drift)
This skill version's marker section is "NORMALIZED DEVELOPER CHECK". If the routine instructions reference features this file does not contain, or this file lacks its marker, the deployed skill is stale: log change_type='skill_out_of_date' with run_type='scan' detail beginning "SKILL-OUT-OF-DATE", do what the loaded skill supports, and never improvise missing templates or rules.

## Scheduling (document for the operator, do not self-schedule)
3:00 AM daily: claude -p "Run the SCK project scanner nightly routine per the sck-project-scanner skill" --permission-mode acceptEdits
