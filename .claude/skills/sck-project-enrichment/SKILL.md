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
EMAIL HYGIENE. The "Email" field holds only bare addresses, semicolon separated, best direct address first; parenthetical annotations and context notes move to Comments. Apply when filling new cards and when touching any existing card.
Source ladder, in order: the developer's own site (contact/about/team) > state corporate registry (FL Sunbiz, GA/NC/SC SOS: registered agent and principals) > press naming principals > public LinkedIn (name and title only) > Google Business Profile phone > the project's listing broker as a labeled fallback ("broker contact, not developer").
Every fill logs change_type='field_enriched' with source. Unfillable after the full ladder: leave null, log change_type='enrichment_gap' with what was tried.
REVIEW PASS (nightly): re-verify up to 5 previously filled developer rows (oldest verification first): confirm the website resolves, the contact still holds the role, the email domain matches. Correct errors with sources; log change_type='contact_corrected'.
EMAIL HYGIENE. The "Email" field holds only bare addresses, semicolon separated, best direct address first; parenthetical annotations and context notes move to Comments. Apply when filling new cards and when touching any existing card.
Cross-link: every DISTINCT "Developer" on staged project rows must have a row here; INSERT missing ones (name only) and log it. Run the Step 4d DUPLICATE GATE FIRST on every such insert: a developer the gate confirms as a duplicate of a live firm is written already carrying the retired review_status from Step 4d rule 3, never as a fresh pending row.
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
Up to 25 rows per run. Field priority: Address + County, Developer, Sales Broker, Units + Avg Unit Size (SF), Website, Key Amenities, Amenity Tier (STAGED rows only, computed under the SCK Amenity Tier Standard v1.1 below, never judgment), latitude/longitude (geocode only a verified street address), Proj. Delivery.
Each fill: UPDATE, append 'Enriched {field} from {source} {date}' to scan_notes, log change_type='field_enriched'.
AMENITY STANDARDIZATION. For every staged row touched, rewrite "Key Amenities" into canonical vocabulary from "11 - Property - Amenity Definition" using the Amenity and Aliases columns, move non-amenity fragments into scan_notes, and repair rows whose amenity strings were broken by embedded commas (fragments like numbers, parenthetical halves, or SF figures are never amenities). New amenity types follow the same proposed-row rule: INSERT into "11 - Property - Amenity Definition" with Status 'proposed', a one line Definition, and the observed phrasing in Aliases, then use the canonical value. Also nightly, sweep any remaining staged rows whose Key Amenities contain tokens not in the table, up to 15 rows per night oldest first, so the existing backlog standardizes within a week.
PROPERTY DIMENSIONS. Two more dimensions have their own definition tables: "Construction Materials" (canonical values Tilt Wall, Block, Metal, Wood-Frame from "11 - Property - Construction Materials", comma separated when mixed) and "Common Area Finish Level" (one of Luxury, High-Quality, Basic, Utility from "11 - Property - Common Area Finish Level"). When source material states construction type or finish grade, write these columns instead of putting construction or finish words into Key Amenities; construction and finish terms are no longer amenities. The nightly standardization sweep also populates these two columns on staged rows from scan_notes and source text where stated, never guessed, otherwise left null for Will.
FINISH SCALE. Luxury, High-Quality and Basic are the CAR CONDO range; most projects land High-Quality. Basic means bare bones car condo product, flex-grade quality in the personal storage and condo bucket. Utility applies to FLEX product only and pairs with Flex-Tier; a car condo is never Utility and a flex building is never Basic. Assign Basic on strong evidence of bare-bones car condo product; assign Utility only to genuine business or industrial flex.

## Step 4 - Duplicate and error audit (every run)
a. DEVELOPER dedupe: normalize names (dashes, case, punctuation, strip LLC/Inc). EXACT normalized duplicates: auto-merge (keep oldest, coalesce fields, delete the shell, log change_type='dedupe_merge'). VARIANT names sharing a stem: log change_type='merge_recommendation', never auto-merge.
b. BROKER dedupe: same rules on "08 - Brokers - New".
c. PROJECT dedupe, including vs LIVE: apply the scanner's DISTINCTIVE-TOKEN rule (strip generic product tokens: auto, motor, car, garage, vehicle, vault, condo, condos, suites, storage, club, luxury, premium, the, at, of; compare what remains within the same county) across "01 - Project - New" AND against "01 - Projects". The Bonita Auto Vault vs Bonita Motor Vault pattern must be caught HERE even if the scanner missed it. Address collisions too. Staged-vs-staged exact: auto-merge; anything involving a live row: merge_recommendation only.
d. Error checks on rows touched tonight: Region/Submarket exist in coverage tables; "Project Status" valid; City/County agree with the address; Website resolves; phone/email format sanity.

## Step 4c - Developer dedup and canonicalization
Nightly, group "05 - Developers - New" rows with each other and against "05 - Developers" using the scanner's normalization plus shared email, email domain (non-freemail), or phone digits. When a staged row matches a LIVE developer: standardize the staged "Developer" value to the live canonical name exactly, note the live linkage in Comments, and if the staged row adds no contact detail the live row lacks, set review_status to 'retired - duplicate of live' with a dated Comments line. When staged rows match EACH OTHER: canonical is the row with the richest contact card, tiebreak lowest id; merge the others into it by filling blank fields only, never overwriting a non-null value (conflicting non-nulls are both recorded in the canonical row's Comments for Will to resolve); set the others' review_status to 'retired - duplicate of id N' with a dated Comments line. NEVER delete a row. Retired rows are excluded from the 25-row contact card budget, the re-verification pool, and outreach selection. When two same-named firms are verified genuinely distinct, note 'distinct from id N, verified {date}' in both Comments so future passes never re-merge them. Known first targets: Auto Clubhouse Properties matches the live AutoClubhouse (Auto Clubhouse Jupiter, principal Robert Zinzell); The Vault pair; the Stables Motor Condos trio; the ReVest pair; the Storage Caves pair; the Newgard pair; the Harrod variants stay retired-linked but keep their do-not-cold-draft Comments intact on every variant.

## Step 4d - DUPLICATE GATE (developers, email-aware)
Runs BEFORE any INSERT into "05 - Developers - New" and again nightly during the Step 4 audit. This gate is authoritative for MATCH DETERMINATION; where its email rules are more specific than the looser "shared email, email domain" phrasing in Step 4c, this section governs and Step 4c handles what to do with the match.
1. LIVE MATCH SET. Build it from "05 - Developers" by splitting each "Email" cell on ';' into individual addresses BEFORE comparing. Whole-cell equality silently under-reports, because many rows pack multiple addresses into one cell. Keep every address trimmed and lower-cased, and keep its domain (the text after '@') alongside it.
2. CONFIRMED DUPLICATE of a live firm when ANY of these holds:
   - exact full email address match;
   - email DOMAIN match, EXCLUDING free-mail domains (gmail.com, yahoo.com, outlook.com, hotmail.com, aol.com, icloud.com, me.com, msn.com, comcast.net, att.net, bellsouth.net, verizon.net). A free-mail address counts ONLY on exact full-address match, never on its domain;
   - exact normalized name match (lower, trim, dashes normalized).
3. ON A CONFIRMED DUPLICATE: set review_status = 'retired - duplicate of live #<n> <name>' using the LOWEST matching live row number, append the match evidence and the date to scan_notes, and log it to "Scan Activity Log" so the morning digest lists it under duplicate recommendations. NEVER delete the row. NEVER modify "05 - Developers".
4. NEAR MISS ONLY (similar name, shared free-mail domain, partial overlap): leave review_status = 'pending' and log a near_match_flag for the digest. A human decides; the gate never retires on a near miss.
5. STAGED VS STAGED: run the same three checks across "05 - Developers - New" itself, so the same firm is never staged twice across nights. Retire the later row using the existing 'retired - duplicate of id <n>' convention.
6. ENTITY NAME ALIGNMENT: when the gate matches a staged project's Developer entity name (an LLC or project entity) to a live firm, align that staged project's "Developer" to the live firm name and append the original entity name to the project row's scan_notes.
Every hard rule still applies in full: never modify a live table, never fabricate a contact, normalize dashes in every comparison, and write no em-dashes into stored text.

## Step 4e - KNOWN-CONTACT CROSS-REFERENCE
KNOWN-CONTACT CROSS-REFERENCE. Run this whenever a contact name or email is attached to a staged project or an outreach draft.
1. MATCH the contact against the live directory tables: "08 - Brokers" (Broker, Contact, Email), "05 - Developers", "05 - Developers - All Property Types", "09 - Lenders", and "04 - Unit Owner CRM". Match on exact email (split multi-address cells on ';', lower, trim) and on normalized name (lower, trim, dashes normalized). Append EVERY match to scan_notes, for example 'Contact matches 08 - Brokers #52 Robert Zinzell (Brokerage)'.
2. ROLE ROUTING on a broker match: a contact found in "08 - Brokers" is NEVER written to the "Developer" field of "01 - Project - New". File them into "Sales Broker", "Sales Broker Contact" and "Sales Broker Email" on the staged project, leave "Developer" null when the true developer is unknown, and keep hunting the real developer through the county permit record, the SunBiz registration of the project LLC, and the project site. A broker marketing a project for sale is a LISTING SIGNAL, not a developer identification.
Every reclassification or flag is logged to "Scan Activity Log" as change_type='role_correction' naming the matched table and row, so the morning digest can report it. These are READ-ONLY lookups: match and annotate, never modify a live row, never fabricate a contact, normalize dashes in every comparison, and write no em-dashes into stored text.

## Step 5 - Status watch (rotation-gated)
Use the scanner's rotation for tonight's regions. Staged rows: UPDATE "Project Status" with evidence, log change_type='status_change' (or 'dead_project'). Live rows: DO NOT TOUCH; log change_type='live_status_suggestion' with evidence URL.

## Step 5b - FL developer outreach queue
OUTREACH DRAFTER GUARD: before queuing a row in "Developer Outreach - Drafts", run the Step 4e KNOWN-CONTACT CROSS-REFERENCE on the recipient. If the recipient matches "08 - Brokers", do NOT compose a developer pitch: log it to "Scan Activity Log" as a broker-lead flag (change_type='broker_lead_flag') for the morning digest and skip the draft. If the recipient matches an existing "05 - Developers" row, address the draft using that row's named contacts, not a scraped generic address.
EVERY morning, run the outreach queue exactly per references/outreach-template.md, using the reworked selection priority in that file (newest staged developers with a usable email first, then the standing backlog): sent-check first against Outlook Sent Items, rotate only when the queue is clear, one Outlook draft per morning to Will's Drafts folder with chance.friedman@calusainvestments.com CCd, Supabase row with Status queued, log outreach_queued or outreach_skipped with the reason. The database columns "Recipient Email" and "Queued At" on "Developer Outreach - Drafts" and resolution / resolved_at on "Scan Activity Log" already exist.
LANE FILTER: every read and write this step makes against "Developer Outreach - Drafts" filters "Lane" = 'car-condo', and every row it inserts carries "Lane" = 'car-condo'. Rows with any other Lane value, including the Monday 'calusa-cre' lane owned by cre-report-writer, are invisible to this queue and must never be counted, marked sent, or expired by it.

## Step 6 - FL DEVELOPER OUTREACH DRAFTS (new)
Superseded 2026-08-08. All developer outreach, including newly discovered developers, flows through the every-morning queue in Step 5b; this step creates nothing.

## Step 7 - Run summary
Log run_type='enrichment', change_type='run_summary': developer rows completed and completeness % (count of rows with Contact AND Email), broker rows completed and completeness %, review-pass corrections, project fields filled, merges applied, merge recommendations, status changes, drafts created. If Step 1 processed zero rows while NULLs remain, the summary begins FAILED-DEV-CONTACTS.


## Learnings file (read first, append on lessons)
At RUN START: read the repo-root file LEARNINGS.md (the last ~30 entries) and honor every lesson in it; it is the memory that keeps mistakes from repeating.
At RUN END: append an entry ONLY when something failed, was corrected, surprised you, or required a workaround (never for routine success), one line:
- {YYYY-MM-DD} | {routine} | {what happened} | {lesson or fix}
Then commit the file ("learnings: {routine} {date}") and push. If the push is blocked by branch policy, leave it committed and say so in the run summary.

## Version self-check (prevents skill/instruction drift)
This skill version's marker section is "Step 5b". If the routine instructions reference features this file does not contain, or this file lacks its marker, the deployed skill is stale: log change_type='skill_out_of_date' with run_type='enrichment' detail beginning "SKILL-OUT-OF-DATE", do what the loaded skill supports, and never improvise missing templates or rules.

## Scheduling
4:15 AM daily: claude -p "Run the SCK project enrichment daily routine per the sck-project-enrichment skill: developer contacts first, then brokers, project fields, audit, status watch, and FL outreach drafts" --permission-mode acceptEdits

## SCK AMENITY TIER STANDARD v1.1 (ratified 2026-08-21)
Tier is deterministic from amenities and finish; enforced portfolio-wide by the Supabase view v_amenity_tier_audit (a row = stored tier disagrees with computed; empty = compliant).
1. Track-Side: Key Amenities include Track Access or Paddock Access. Automatic.
2. Flex-Tier: DECLARED product type, never inferred from amenities.
3. Premium-Tier: Common Area Finish Level High-Quality or Luxury AND at least one of Owners' Clubhouse/Lounge, Concierge Services, or Social Programming PLUS one other Premium-signal amenity. Social Programming ALONE never qualifies (free to announce; Premium keys on capital or staffing).
4. Standard-Tier: everything else. The default.
ENRICHMENT RULES. Record an amenity only on concrete evidence (site plans, renderings, named facilities). Social Programming has a higher bar: an actual named program, events calendar, or membership program, never marketing community language; when in doubt, omit. STAGED rows ("01 - Project - New"): fill Amenity Tier only as computed under this standard from the amenities recorded. LIVE rows ("01 - Projects"): NEVER write Amenity Tier; after updating Key Amenities on a live project, check v_amenity_tier_audit, and if the project appears there, report the implied tier change in the digest as a recommendation for Will (tier changes move valuations).
