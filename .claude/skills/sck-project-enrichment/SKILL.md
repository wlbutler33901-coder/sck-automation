---
name: sck-project-enrichment
description: Daily (post-scan) enrichment agent for the Storage Condo King project pipeline. Fills empty fields on staged project candidates (developer, contacts, units, sizes, addresses, amenities), and monitors staged AND live projects for status transitions (Pre-Development to Under Construction, Under Construction to Completed, Dead). Use whenever asked to run the SCK enrichment routine, enrich the new projects table, fill missing project fields, check for project status updates, or verify whether a project is still alive. Covers all regions on a weekly rotation.
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
Field priority: 1) Address + County (needed for geocoding and region verification), 2) Developer + Sales Broker / Sales Broker Contact / Sales Broker Email (Will's financing-outreach fields), 3) Units + Avg Unit Size (SF), 4) Website, 5) Key Amenities, 6) Amenity Tier (Flex-Tier / Standard-Tier / Premium-Tier / Track-Side (Flex-Tier = hybrid business + personal use; Basic-Tier is retired) per "Amenity Tier Definition" - only when amenities are documented; track-integrated projects are Track-Side), 7) latitude/longitude (geocode only a verified street address, never a city centroid), 8) Proj. Delivery.
Sources: developer/project sites, county property appraiser and permit portals, business journals, state corporation registries (developer LLC contacts), site:linkedin.com/company {developer} for principals, and a '{developer} headquarters office phone' pass for a direct contact path.
Each fill: UPDATE the row, append 'Enriched {field} from {source} {date}' to scan_notes, log change_type='field_enriched' (detail = field + value + source).

## Step 2B - Status watch (staged + live in today's regions)
For each project (staged: all statuses; live: "01 - Projects" where Region in tonight's set), check the project website, developer news, and permit/CO records for:
- Pre-Development -> Developer Sale (reservations open, pre-sales launch, units listed)
- Developer Sale -> Under Construction is NOT a transition: a selling project that breaks ground STAYS Developer Sale until sold out or delivered
- Developer Sale -> Completed (sold out and delivered)
- Pre-Development -> Under Construction (groundbreaking with no sales program found)
- Under Construction -> Completed (CO, grand opening, "now open")
- Any -> Dead (site offline + no activity 12+ months, entitlement denial, land re-listed). Staged rows: set "Project Status" = 'Dead' directly. Live rows: suggestion only, as ever.
Staged row: UPDATE "Project Status", append evidence to scan_notes, log change_type='status_change' (or 'dead_project') with the evidence URL in detail.
Live row: DO NOT TOUCH. Log change_type='live_status_suggestion', detail = '{project}: {current} -> {suggested}. Evidence: {url}'. The morning digest surfaces it.

## Step 2D - Developer table completeness and audit
The database auto-stages a developer row in "05 - Developers - New" whenever a project candidate carries a Developer name (trigger trg_auto_stage_developer; dedupe against live "05 - Developers" is automatic). The agent's jobs on top of that:
1. COMPLETENESS: for today's regions, find projects (staged AND live) whose Developer is missing entirely, or whose developer appears in neither "05 - Developers" nor "05 - Developers - New" (dash-normalized name match). Fill the project's Developer field when research supports it (the trigger then stages the row), and log change_type='field_enriched'.
2. ENRICH STAGED DEVELOPERS: for "05 - Developers - New" rows with review_status='pending' tied to today's regions (source_project join), fill Contact, Office, Cell, Email, Website from primary sources (company site, state corporation registry, LinkedIn company page). Append source + date to scan_notes. Never invent a contact; a wrong phone number is worse than an empty cell.
3. AUDIT: spot-check existing values (staged and, read-only, live) against current sources: dead websites, principals who left, brand duplicates (e.g. two spellings of the same operator - flag as near_match_flag, never merge without approval). Live "05 - Developers" rows are READ-ONLY: log change_type='live_status_suggestion' with the correction and evidence URL.
4. Log a per-run count of developers enriched in the run_summary.

## Step 2C - Financing classification maintenance
When a status change is applied or a sponsor/contact is found, update financing_relevance and financing_opportunity on the staged row (taxonomy in the scanner's references/search-playbook.md). A project advancing into Permitting/Pre-Sale with a named sponsor moves to High; reaching Completed drops to Low.

## Step 3 - Run summary
Log change_type='run_summary': regions covered, rows enriched (count by field), status changes applied (staged), suggestions raised (live), dead projects flagged.

## Scheduling
Daily 4:15 AM (after the 3am scan):
claude -p "Run the SCK project enrichment daily routine per the sck-project-enrichment skill" --permission-mode acceptEdits
