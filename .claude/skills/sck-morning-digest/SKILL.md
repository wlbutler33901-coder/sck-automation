---
name: sck-morning-digest
description: 6am daily intelligence brief of the Storage Condo King overnight scan and enrichment activity. Summarizes new project candidates, database update recommendations, enrichment and contact-card progress, and pending developer outreach drafts from the Scan Activity Log, then delivers by POSTing to the Make webhook which emails will.butler@calusainvestments.com. Use whenever asked to run the SCK morning digest, send the scan summary, summarize last night's scans, or report overnight pipeline activity.
---

# SCK Daily Intelligence Brief (v3 - 6am)

Reads everything the scanner and enrichment agent logged since the last digest, buckets it, delivers it via the Make webhook, archives it, marks it digested.

PURPOSE AND FRAMING: this is a MARKET INTELLIGENCE brief about the project pipeline, NOT a financing-lead sheet. Will manages outreach in his own CRM. Therefore: no financing-watchlist section of any kind, no financing-opportunity column, no financing-relevance ranking, and no language recommending outreach beyond surfacing the prepared draft queue. Delivery is the Make webhook only; the prior delivery service is retired.

## Step 1 - Pull undigested activity
```sql
SELECT * FROM "Scan Activity Log"
WHERE digested_at IS NULL AND run_type IN ('scan','enrichment','digest','nightly_scan','project_scan')
ORDER BY ts;
```
(The IN-list is deliberately tolerant of the scanner's historical run_type drift; the scanner is standardized to 'scan' but the digest must never miss rows over a label again.)
Join new candidates to their staged rows:
```sql
SELECT p.* FROM "01 - Project - New" p WHERE p.discovered_at > now() - interval '26 hours';
```

## Step 2 - Compose, in EXACTLY this section order
1. WARNINGS (only if any): scan did not run / did not complete, blocked sources, errors, FAILED-DEV-CONTACTS from the enrichment summary; any 'skill_out_of_date' (SKILL-OUT-OF-DATE) rows; any 'outreach_skipped' rows with the reason; the unit reservation SLA breach line from section 3 when it applies. If the log has no scanner run_summary for last night, lead with "WARNING: 3am scan did not run or did not complete. Last scan: {ts} ({regions})."
2. NEW PROJECTS (the lead section): one line per new candidate -
   {Project Name} | {Region} / {Submarket} | {Status} | {Units} units | confidence {level} | {one-line note} | {source_url}
   High confidence first, then by region. If none: "No new candidates. Regions scanned: {list}."
   This section contains ONLY change_type new_candidate rows. Rediscoveries, near-match flags, and context notes never appear here; a rediscovery appears in section 4 only when it carries a potential change (possible duplicate, status difference), otherwise it is counts-line only.
3. UNIT RESERVATIONS: composed from "08 - Unit Reservation Requests" (columns Project Name, Unit SF, Price, PSF, Name, Email, Cell, Comments, Source Page, Status, created_at), in this order:
   a. SLA line FIRST, only when it applies: any row with Status = 'New' older than 24 hours renders as "SLA BREACH: {n} reservation(s) awaiting response over 24h", with those rows listed in full. This line is also promoted into the WARNINGS section.
   b. "Recap of yesterday's alerts": every row from the last 24 hours in full (Project, Unit SF, Price, PSF, Name, Email, Cell, Comments), one numbered item each, actionable straight from the email.
   c. Cumulative counts: trailing 30, 60 and 90 days, each with a per-project breakdown so converting listings are visible.
   d. When the table has no rows at all in the last 90 days, the whole section collapses to one line: "Unit reservations: none in the last 90 days."
   REAL-TIME PATH: a Postgres trigger (notify_on_unit_reservation) POSTs every new row to the same Make webhook this digest uses, so Will is alerted the moment a reservation lands. The digest never needs to alert on fresh rows; it only recaps them and flags aging ones, which is why block b is labeled a recap rather than a notification.
4. DATABASE UPDATE RECOMMENDATIONS (the action section), in this order:
   a. live_status_suggestions NEW since last digest (project, current -> suggested, confidence, evidence URL, one line).
   b. Open live_status_suggestions only: rows where resolution IS NULL. Before composing, auto-resolve: for each open suggestion, compare the suggested status in detail against the project's current "Project Status" in "01 - Projects" (normalized name match); if they now match, UPDATE that log row SET resolution = 'applied', resolved_at = now() and list it under a one-line "Applied since last digest" confirmation instead. Suggestions that cannot auto-resolve (at-risk, verify continuity) stay open until Will resolves them in a chat session, which sets resolution to approved or rejected.
   c. Staged status changes auto-applied (project, old -> new, evidence).
   d. Duplicate / merge recommendations and near-match flags, including which dedup signal fired.
   e. Data corrections applied or recommended.
   f. ROLE CORRECTIONS: any contact the known-contact cross-reference reclassified or flagged overnight (change_type 'role_correction' and 'broker_lead_flag' rows), each naming the matched table and row, for example "Robert Zinzell filed as Sales Broker not Developer, matches 08 - Brokers #52". Include outreach drafts skipped because the recipient is a known broker.
5. CONTACT CARD PROGRESS: "05 - Developers - New": X of Y rows with Contact, X of Y with Email (and the delta vs yesterday); "08 - Brokers - New": same; review-pass corrections; staged projects still missing a "Sales Broker" answer. If developer completeness did not move and NULLs remain, say so bluntly. Report the dedup pass as one numbered line (staged rows retired, canonical rows enriched, live standardizations), and exclude review_status retired rows from all developer counts. Then fold any undigested change_type learning rows from "Scan Activity Log" into LEARNINGS.md and set digested_at on the folded rows. Whenever any exist, add one numbered line "Proposed amenities awaiting review: {Amenity (source project)}, ..." listing Status 'proposed' rows in "11 - Property - Amenity Definition" created in the last 7 days, so Will approves or kills new types from the morning email.
6. DEVELOPER OUTREACH DRAFTS: new drafts created last night (Developer | Project | Subject) and the count of drafts still at Status='draft' in "Developer Outreach - Drafts". One reminder line: review the draft and send; the report is already linked in the body. Also report any outreach draft queued this morning by the fallback queue: developer, project, recipient, with the reminder "Review the draft and send; the report is already linked in the body." If the queue was skipped because a prior draft is still pending in your Drafts folder, say that instead.
7. PIPELINE SNAPSHOT: live "01 - Projects" counts by status (excl. Dead), staged totals ("01 - Project - New": total | added last 7 days | pending review), open suggestion count. Then one line for the owner campaign, composed from "04e - Campaign Sends": "BMV owner drip: {n} drafted this morning ({Region}, {sent so far} of {region total}; campaign {x} of 965 total)." When the asset reachability gate blocked the run, say that instead and name the failing URL, and promote it into WARNINGS.

Formatting: compose in MARKDOWN per the EMAIL FORMATTING RULES below (the markdown is the canonical saved artifact). Terse, no em-dashes, mobile-readable. Stage labels are fine; never rank by financing relevance.

## Step 3 - Deliver via the Make webhook
POST JSON to the webhook; Make emails it from Will's Outlook connection:
```
POST https://hook.us2.make.com/ms9ag6j37hic53tnuilvrfup1armt65y
Content-Type: application/json
{"subject": "SCK Daily Intelligence Brief - {YYYY-MM-DD}",
 "html": "<the markdown rendered to HTML per the EMAIL FORMATTING RULES>"}
```
Expect HTTP 200 "Accepted". On failure: retry once after 60 seconds; if still failing, write the brief to ~/sck-digests/{date}.md and log the delivery failure. Never silently skip. Always send, even on a zero-activity night.

## Step 3b - Archive the digest in Supabase (always, before marking digested)
```sql
INSERT INTO "Daily Digest Archive" ("Digest Date", "Subject", "Markdown", "Delivery Status")
VALUES (CURRENT_DATE, '<subject>', '<full markdown>', '<sent | failed: reason>');
```
Re-query to confirm. The email is a copy; the row is the record.

## Step 4 - Mark digested (only after a successful POST or fallback write)
```sql
UPDATE "Scan Activity Log" SET digested_at = now()
WHERE digested_at IS NULL AND run_type IN ('scan','enrichment','digest','nightly_scan','project_scan') AND ts < now();
```

## EMAIL FORMATTING RULES (mandatory - no wall-of-text emails)
Compose the report in MARKDOWN first (that markdown is the canonical saved artifact), then render the email HTML from it. Never send the whole report inside one <pre> block.
- Markdown: ## title with date, ### per section, one blank line between items, "- " bullets, **bold** project and developer names, plain URLs on their own.
- Email HTML rendering: <h2> title + date; <h3> per section; <hr> between major sections; items as <ul><li> with <b>bold</b> project names; a multi-field entry is ONE <li>; links as <a href>. Counts and snapshots as short <ul> lists. <pre> is allowed ONLY for the pipeline-snapshot count block. Keep the email under ~100 KB; when a section would exceed ~25 items, include the top items and one line saying the rest are in Supabase.


## Learnings file (read first, append on lessons)
At RUN START: read the repo-root file LEARNINGS.md (the last ~30 entries) and honor every lesson in it; it is the memory that keeps mistakes from repeating.
At RUN END: append an entry ONLY when something failed, was corrected, surprised you, or required a workaround (never for routine success), one line:
- {YYYY-MM-DD} | {routine} | {what happened} | {lesson or fix}
Then commit the file ("learnings: {routine} {date}") and push. If the push is blocked by branch policy, leave it committed and say so in the run summary.

## Version self-check (prevents skill/instruction drift)
This skill version's marker section is "DEVELOPER OUTREACH DRAFTS". If the routine instructions reference features this file does not contain, or this file lacks its marker, the deployed skill is stale: log change_type='skill_out_of_date' with run_type='digest' detail beginning "SKILL-OUT-OF-DATE", do what the loaded skill supports, and never improvise missing templates or rules.

## Scheduling
Daily 5:55 AM: claude -p "Run the SCK morning digest routine per the sck-morning-digest skill" --permission-mode acceptEdits
