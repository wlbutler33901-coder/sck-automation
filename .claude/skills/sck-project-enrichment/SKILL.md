---
name: sck-project-enrichment
description: Daily (post-scan) enrichment agent for the Storage Condo King pipeline. TOP PRIORITY: complete developer contact cards in "05 - Developers - New" and broker contact cards in "08 - Brokers - New" (these feed Will's outreach CRM), then complete staged project fields, run a duplicate and error audit, watch status transitions, and draft Florida developer outreach emails into "Developer Outreach - Drafts". Use whenever asked to run the SCK enrichment routine, enrich developers or brokers, fill missing contact info, dedupe staged rows, check status updates, or draft developer outreach.
---

# SCK Project Enrichment Agent (v3 - daily)

Priority order is deliberate and NON-NEGOTIABLE: (1) developer contacts, (2) broker contacts, (3) project fields, (4) audit, (5) status watch, (6) FL outreach drafts. Contact completion outranks everything because it feeds Will's outreach; this has been under-delivered by prior versions and is now the first thing every run does and the first thing every run reports.

## Hard rules
1. UPDATE only "01 - Project - New", "05 - Developers - New", "08 - Brokers - New"; INSERT only to those staging tables, "Developer Outreach - Drafts", and "Scan Activity Log", plus INSERT and Status / "Sent At" updates on "Developer Outreach - Drafts" for the outreach queue step. NEVER modify "01 - Projects", "05 - Developers", "08 - Brokers", or any live table. Live changes are SUGGESTIONS: log change_type='live_status_suggestion' and stop.
2. LOGGING CONSTANT: every log row uses run_type = 'enrichment', exactly.
3. NEVER supply explicit id values on inserts; on a duplicate-key error, retry once and log the collision.
4. Never overwrite a non-null field with lower-confidence data. Fill nulls; correct non-nulls only with a primary source, appending the old value to a notes field.
5. Never fabricate contact details. A field stays null with a logged reason before it ever holds a guess; every fill carries its source.
6. Normalize dashes in name joins; no em-dashes in stored text.

## Step 1 - DEVELOPER CONTACTS (first, always)
```sql
SELECT * FROM "05 - Developers - New"
WHERE "Contact" IS NULL OR "Office" IS NULL OR "Cell" IS NULL OR "Email" IS NULL OR "Website" IS NULL
ORDER BY created_at ASC;
```
Process up to 25 rows per run, oldest first, until the table is complete; then delta-only on new rows. Fill: Contact (principal or sales lead full name), Office, Cell (only if publicly published), Email (direct if published, else the published sales/info address, labeled), Website.
Source ladder, in order: the developer's own site (contact/about/team) > state corporate registry (FL Sunbiz, GA/NC/SC SOS: registered agent and principals) > press naming principals > public LinkedIn (name and title only) > Google Business Profile phone > the project's listing broker as a labeled fallback ("broker contact, not developer").
Every fill logs change_type='field_enriched' with source. Unfillable after the full ladder: leave null, log change_type='enrichment_gap' with what was tried.
REVIEW PASS (nightly): re-verify up to 5 previously filled developer rows (oldest verification first): confirm the website resolves, the contact still holds the role, the email domain matches. Correct errors with sources; log change_type='contact_corrected'.
Cross-link: every DISTINCT "Developer" on staged project rows must have a row here; INSERT missing ones (name only) and log it.
FAILURE LANGUAGE: a run that ends with NULL contact fields remaining while processing capacity remained is a FAILED run; the run_summary must begin "FAILED-DEV-CONTACTS" and say why. Silence on this step is not acceptable.

## Step 2 - BROKER CONTACTS (new)
Same mechanics against "08 - Brokers - New" (columns: "Broker", "Brokerage", "Contact", "Office", "Cell", "Email", "Website", "Projects", "Notes"). Up to 15 rows per run.
Sources: the project's sales page ("sales by", "marketed by") > the brokerage's site > FL DBPR / state license lookup (confirms name and brokerage) > listing platforms (LoopNet/Crexi agent cards) > public LinkedIn.
Cross-link both directions: every staged project must carry a "Sales Broker" value (a broker name or 'Developer-Direct', never silently null: backfill it), and every named broker must have a row here with "Projects" listing the associated project names. Create missing rows; log fills as change_type='field_enriched'.

## Step 3 - Project field completion (whole table, not rotation-gated)
```sql
SELECT * FROM "01 - Project - New"
WHERE review_status IN ('pending','approved')
  AND ("Address" IS NULL OR "County" IS NULL OR "Developer" IS NULL OR "Units" IS NULL
       OR "Avg Unit Size (SF)" IS NULL OR "Website" IS NULL OR "Key Amenities" IS NULL
       OR "Proj. Delivery" IS NULL OR latitude IS NULL OR "Sales Broker" IS NULL)
ORDER BY (confidence='high') DESC, discovered_at ASC;
```
Up to 25 rows per run. Field priority: Address + County, Developer, Sales Broker, Units + Avg Unit Size (SF), Website, Key Amenities, Amenity Tier (per "Amenity Tier Definition"), latitude/longitude (geocode only a verified street address), Proj. Delivery.
Each fill: UPDATE, append 'Enriched {field} from {source} {date}' to scan_notes, log change_type='field_enriched'.

## Step 4 - Duplicate and error audit (every run)
a. DEVELOPER dedupe: normalize names (dashes, case, punctuation, strip LLC/Inc). EXACT normalized duplicates: auto-merge (keep oldest, coalesce fields, delete the shell, log change_type='dedupe_merge'). VARIANT names sharing a stem: log change_type='merge_recommendation', never auto-merge.
b. BROKER dedupe: same rules on "08 - Brokers - New".
c. PROJECT dedupe, including vs LIVE: apply the scanner's DISTINCTIVE-TOKEN rule (strip generic product tokens: auto, motor, car, garage, vehicle, vault, condo, condos, suites, storage, club, luxury, premium, the, at, of; compare what remains within the same county) across "01 - Project - New" AND against "01 - Projects". The Bonita Auto Vault vs Bonita Motor Vault pattern must be caught HERE even if the scanner missed it. Address collisions too. Staged-vs-staged exact: auto-merge; anything involving a live row: merge_recommendation only.
d. Error checks on rows touched tonight: Region/Submarket exist in coverage tables; "Project Status" valid; City/County agree with the address; Website resolves; phone/email format sanity.

## Step 5 - Status watch (rotation-gated)
Use the scanner's rotation for tonight's regions. Staged rows: UPDATE "Project Status" with evidence, log change_type='status_change' (or 'dead_project'). Live rows: DO NOT TOUCH; log change_type='live_status_suggestion' with evidence URL.

## Step 5b - FL developer outreach queue (fallback)
On mornings when the last 26 hours produced zero new developer rows, run the outreach queue exactly per references/outreach-template.md: sent-check first against Outlook Sent Items, rotate only when the queue is clear, one Outlook draft per morning to Will's Drafts folder with chance.friedman@calusainvestments.com CCd, Supabase row with Status queued, log outreach_queued or outreach_skipped with the reason. The database columns "Recipient Email" and "Queued At" on "Developer Outreach - Drafts" and resolution / resolved_at on "Scan Activity Log" already exist.

## Step 6 - FL DEVELOPER OUTREACH DRAFTS (new)
For each developer whose contact card gained at least a Contact name or Email this run (or is complete but has no draft yet), AND whose staged/live projects sit in FLORIDA (FL only for now: that is where the market report covers):
```sql
INSERT ... WHERE NOT EXISTS (SELECT 1 FROM "Developer Outreach - Drafts" WHERE "Developer" = <name>)
```
One draft per developer, ever. Compose per the TEMPLATE below into "Developer Outreach - Drafts" ("Developer", "Project" = their most advanced FL project, "Region", "Subject", "Body", "Status"='draft'). Will reviews and sends from Outlook, attaching the Q2 report himself.

### OUTREACH TEMPLATE (tight version of Will's proven email; 150 to 180 words, no em or en dashes, hyphens fine)
Subject: Financing and pre-sale resources for {Project} - {City}
Body structure:
1. Greeting: "{FirstName}, hope you're doing well." (Contact name known) else "Hi there, hope you're doing well."
2. Who + why: "I provide non-recourse construction financing and pre-sale solutions for luxury storage condo developers, and {Project} in {City} caught my attention as it {stage phrase: moves through pre-development / goes vertical / opens sales}."
3. Platform + ONE region-matched data tidbit: "I run Storage Condo King (storagecondoking.com), the Florida garage and car condo platform connecting developers, capital providers, and 2,000+ unit owners with market data, underwriting resources, and pre-sale distribution. {TIDBIT}. The attached Q2 2026 Florida Market Report has the full picture for {Region}."
4. Three or four capability bullets, one line each: Construction financing: non-recourse options with limited pre-sale requirements, or low-cost recourse bank debt. / Pre-sale distribution: 2,000+ unit-owner database for founding-member sales. / Live sale comps and an institutional development model for underwriting. / Site and pricing evaluation across every Florida market.
5. CTA: "I'm local in Fort Myers and would enjoy connecting over coffee or a quick call to talk through {Project}."
6. Sign-off: Will Butler, Calusa Capital Partners | Storage Condo King.

### TIDBIT MENU (Q2 2026 report figures; pick the line matching the project's region, else the statewide line; never invent others)
- Statewide: "Q2 cleared $530 per SF statewide, up 48% year over year"
- New construction premium: "new construction cleared $531 per SF YTD versus $421 for re-sales"
- Southwest Florida: "Southwest Florida averages $361 per SF on the deepest volume in the state"
- South Florida: "South Florida is averaging $480 per SF"
- Tampa MSA: "Tampa is averaging $420 per SF on strong volume"
- Orlando MSA: "Orlando leads the state at $674 per SF"
- Jacksonville MSA: "Jacksonville averages $344 per SF with room to run"
- Central-East Florida: "Central-East Florida averages $281 per SF, the value corridor of the state"
Personalize lightly (project name, city, stage, one tidbit); do not go overboard, and never state a fact about the developer's project that is not in the staged row.

## Step 7 - Run summary
Log run_type='enrichment', change_type='run_summary': developer rows completed and completeness % (count of rows with Contact AND Email), broker rows completed and completeness %, review-pass corrections, project fields filled, merges applied, merge recommendations, status changes, drafts created. If Step 1 processed zero rows while NULLs remain, the summary begins FAILED-DEV-CONTACTS.


## Learnings file (read first, append on lessons)
At RUN START: read the repo-root file LEARNINGS.md (the last ~30 entries) and honor every lesson in it; it is the memory that keeps mistakes from repeating.
At RUN END: append an entry ONLY when something failed, was corrected, surprised you, or required a workaround (never for routine success), one line:
- {YYYY-MM-DD} | {routine} | {what happened} | {lesson or fix}
Then commit the file ("learnings: {routine} {date}") and push. If the push is blocked by branch policy, leave it committed and say so in the run summary.

## Version self-check (prevents skill/instruction drift)
This skill version's marker section is "TIDBIT MENU". If the routine instructions reference features this file does not contain, or this file lacks its marker, the deployed skill is stale: log change_type='skill_out_of_date' with run_type='enrichment' detail beginning "SKILL-OUT-OF-DATE", do what the loaded skill supports, and never improvise missing templates or rules.

## Scheduling
4:15 AM daily: claude -p "Run the SCK project enrichment daily routine per the sck-project-enrichment skill: developer contacts first, then brokers, project fields, audit, status watch, and FL outreach drafts" --permission-mode acceptEdits
