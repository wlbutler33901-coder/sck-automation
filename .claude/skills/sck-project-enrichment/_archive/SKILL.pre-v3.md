---
name: sck-project-enrichment
description: Daily (post-scan) enrichment agent for the Storage Condo King project pipeline. Completes ALL missing fields on staged project candidates ("01 - Project - New") and staged developer contacts ("05 - Developers - New" - contact person, office, cell, email, website for the CRM), runs a duplicate and error audit on both staging tables, and monitors staged AND live projects for status transitions. Use whenever asked to run the SCK enrichment routine, enrich the new projects or developers tables, fill missing contact info, dedupe staged rows, check for project status updates, or verify whether a project is still alive.
---

# SCK Project Enrichment Agent (v2 - daily)

Three jobs: (A) COMPLETE the data on staged projects AND staged developers - all missing fields, whole table, not just a region slice; (B) AUDIT both staging tables for duplicates and errors; (C) detect status changes on staged and live projects. Runs unattended.

## Hard rules
1. UPDATE only "01 - Project - New" and "05 - Developers - New" rows; INSERT only to "Scan Activity Log" (and new "05 - Developers - New" rows when a staged project's developer is missing from it).
2. NEVER modify "01 - Projects", "05 - Developers", or any other live table. Live changes are SUGGESTIONS: log change_type='live_status_suggestion' and stop. Will approves manually.
3. Never overwrite a non-null staged field with lower-confidence data. Fill nulls; correct non-nulls only with a primary source (developer site, county record, state registry, major news), and append the old value to scan_notes.
4. Never fabricate contact details. A field stays null with a logged reason before it ever holds a guess. Verifiable-source rule: every contact fill carries its source.
5. Normalize dashes in name joins; no em-dashes in stored text.

## Step 1 - Field completion, PROJECTS (v2: whole table, not rotation-gated)
```sql
SELECT * FROM "01 - Project - New"
WHERE review_status IN ('pending','approved')
  AND ("Address" IS NULL OR "County" IS NULL OR "Developer" IS NULL OR "Units" IS NULL
       OR "Avg Unit Size (SF)" IS NULL OR "Website" IS NULL OR "Key Amenities" IS NULL
       OR "Proj. Delivery" IS NULL OR latitude IS NULL)
ORDER BY (confidence='high') DESC, discovered_at ASC;
```
Process up to 25 rows per run, oldest first, until the table is complete; then this step becomes a nightly delta check on new rows only.
Field priority: 1) Address + County, 2) Developer, 3) Units + Avg Unit Size (SF), 4) Website, 5) Key Amenities, 6) Amenity Tier (per "Amenity Tier Definition"; track-integrated = Track-Side), 7) latitude/longitude (geocode only a verified street address, never a city centroid), 8) Proj. Delivery.
Sources: developer/project sites, county property appraiser and permit portals, business journals, state corporation registries.
Each fill: UPDATE the row, append 'Enriched {field} from {source} {date}' to scan_notes, log change_type='field_enriched'.

## Step 2 - Field completion, DEVELOPERS (v2: new - feeds Will's CRM)
```sql
SELECT * FROM "05 - Developers - New"
WHERE "Contact" IS NULL OR "Office" IS NULL OR "Cell" IS NULL OR "Email" IS NULL OR "Website" IS NULL
ORDER BY created_at ASC;
```
Process up to 25 rows per run until complete; then delta-only. For each developer fill: Contact (principal or sales lead full name), Office (main line), Cell (only if publicly published), Email (direct if published, else the published sales/info address, labeled in notes), Website.
Source ladder, in order: 1) the developer's own site (contact/about/team pages), 2) the state corporate registry for the LLC (FL Sunbiz, GA/NC/SC Secretary of State - registered agent and principal names), 3) press coverage naming principals, 4) public LinkedIn pages (name and title only; never scrape behind login), 5) Google Business Profile phone, 6) the project's listing broker as a labeled fallback contact when the developer publishes nothing (mark "broker contact, not developer" in notes).
Every fill logs change_type='field_enriched' with source. Unfillable after the full ladder: leave null, log change_type='enrichment_gap' with what was tried.
Cross-link check: every DISTINCT "Developer" on staged project rows must have a row here; INSERT missing ones (name only) and log it.

## Step 3 - Duplicate and error audit (v2: new, both staging tables, every run)
a. DEVELOPER dedupe: normalize names (dashes, case, punctuation, strip suffixes like LLC/Inc). EXACT normalized duplicates: auto-merge - keep the oldest row, coalesce non-null fields into it, append merged-from note, delete the shell duplicate, log change_type='dedupe_merge'. VARIANT names sharing a stem (e.g. "Stables Motor Condos" vs "Stables Motor Condos / PW Development"): do NOT auto-merge; log change_type='merge_recommendation' with both rows and the evidence.
b. PROJECT dedupe: same rule set on "01 - Project - New", plus address-collision check (same street address, different names = probable duplicate; the Charleston Toy Box / Motor District pattern). Auto-merge exact only; recommend the rest.
c. Error checks, each staged row touched tonight: Region/Submarket values exist in the coverage tables; "Project Status" is a valid enum; City/County actually match (the Awendaw vs Mount Pleasant pattern - verify against the address when present); Website resolves (dead URL -> note, do not delete); phone/email format sanity.
d. Everything found lands in the log so the Daily Intelligence Brief's DATABASE UPDATE RECOMMENDATIONS section surfaces it.

## Step 4 - Status watch (rotation-gated as before)
Use the scanner's rotation query for tonight's regions. For each project (staged: all statuses; live: "01 - Projects" where Region in tonight's set), check the project website, developer news, and permit/CO records for:
- Planned -> Under Construction (groundbreaking, vertical construction)
- Under Construction -> Completed (CO, grand opening, "now open")
- Any -> Dead/stalled (site offline + no activity 12+ months, entitlement denial, land re-listed)
Staged row: UPDATE "Project Status", append evidence to scan_notes, log change_type='status_change' (or 'dead_project').
Live row: DO NOT TOUCH. Log change_type='live_status_suggestion', detail = '{project}: {current} -> {suggested}. Evidence: {url}'.

## Step 5 - Run summary
Log change_type='run_summary': project rows completed (count by field), developer rows completed (count by field), completeness percentages for both tables, merges applied, merge recommendations raised, errors corrected/flagged, status changes applied (staged), suggestions raised (live), dead projects flagged.

## Scheduling
Daily 4:15 AM (after the 3am scan):
claude -p "Run the SCK project enrichment daily routine per the sck-project-enrichment skill" --permission-mode acceptEdits
