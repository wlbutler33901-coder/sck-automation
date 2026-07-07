---
name: sck-project-enrichment
description: Daily (post-scan) enrichment agent for the Storage Condo King project pipeline. Fills empty fields on staged project candidates (developer, contacts, units, sizes, addresses, amenities), and monitors staged AND live projects for status transitions (Planned to Under Construction, Under Construction to Completed, stalled or dead projects). Use whenever asked to run the SCK enrichment routine, enrich the new projects table, fill missing project fields, check for project status updates, or verify whether a project is still alive. Covers all regions on a weekly rotation.
---

# SCK Project Enrichment Agent (daily)

Two jobs: (A) complete the data on staged candidates; (B) detect status changes on staged and live projects. Runs unattended.

## Hard rules
0. This file is the procedure. If a run session cannot read this skill file, log the failure and STOP. Never reconstruct the routine from memory or from table shapes.
1. UPDATE only "01 - Project - New" rows and INSERT only to "Scan Activity Log".
2. NEVER modify "01 - Projects" (live). Live status changes are SUGGESTIONS: log change_type='live_status_suggestion' and stop. Will approves manually.
3. Never overwrite a non-null staged field with lower-confidence data. Fill nulls; correct non-nulls only with a primary source (developer site, county record, major news), and append the old value to scan_notes.
4. Normalize dashes in name joins; no em-dashes in stored text.

## Step 1 - Today's rotation (same wheel as the scanner)
Use the identical rotation query from sck-project-scanner Step 1. Same-day overlap with the scanner is intentional: enrich what last night staged.

## Step 2A - Field enrichment (staged rows in today's regions)
Priority targets, in order:
```sql
SELECT * FROM "01 - Project - New"
WHERE "Region" = ANY($TONIGHT_REGIONS) AND review_status IN ('pending','approved')
ORDER BY (confidence='high') DESC, discovered_at DESC;
```
Field priority: 1) Address + County (needed for geocoding and region verification), 2) Developer + Sales Broker / Sales Broker Contact / Sales Broker Email (Will's financing-outreach fields), 3) Units + Avg Unit Size (SF), 4) Website, 5) Key Amenities, 6) Amenity Tier (Basic-Tier / Standard-Tier / Premium-Tier / Track-Side per "Amenity Tier Definition" - only when amenities are documented; track-integrated projects are Track-Side), 7) latitude/longitude (geocode only a verified street address, never a city centroid), 8) Proj. Delivery.
Sources: developer/project sites, county property appraiser and permit portals, business journals, state corporation registries (developer LLC contacts).
Each fill: UPDATE the row, append 'Enriched {field} from {source} {date}' to scan_notes, log change_type='field_enriched' (detail = field + value + source).

## Step 2B - Status watch (staged + live in today's regions)
For each project (staged: all statuses; live: "01 - Projects" where Region in tonight's set), check the project website, developer news, and permit/CO records for:
- Planned -> Under Construction (groundbreaking, vertical construction)
- Under Construction -> Completed (CO, grand opening, "now open")
- Any -> Dead/stalled (site offline + no activity 12+ months, entitlement denial, land re-listed)
Staged row: UPDATE "Project Status", append evidence to scan_notes, log change_type='status_change' (or 'dead_project') with the evidence URL in detail.
Live row: DO NOT TOUCH. Log change_type='live_status_suggestion', detail = '{project}: {current} -> {suggested}. Evidence: {url}'. The morning digest surfaces it.

## Step 3 - Run summary
Log change_type='run_summary': regions covered, rows enriched (count by field), status changes applied (staged), suggestions raised (live), dead projects flagged.

## Scheduling
Daily 4:15 AM (after the 3am scan):
claude -p "Run the SCK project enrichment daily routine per the sck-project-enrichment skill" --permission-mode acceptEdits

