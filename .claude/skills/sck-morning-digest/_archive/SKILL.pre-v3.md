---
name: sck-morning-digest
description: 6am daily intelligence brief of the Storage Condo King overnight scan and enrichment activity. Summarizes new project candidates, database update recommendations, and enrichment progress from the Scan Activity Log, then delivers by POSTing to the Make webhook which emails will.butler@calusainvestments.com. Use whenever asked to run the SCK morning digest, send the scan summary, summarize last night's scans, or report overnight pipeline activity.
---

# SCK Daily Intelligence Brief (v2 - 6am)

Reads everything the scanner and enrichment agent logged since the last digest, buckets it, delivers it via the Make webhook, marks it digested.

PURPOSE AND FRAMING (v2 change): this is a MARKET INTELLIGENCE brief about the project pipeline, NOT a financing-lead sheet. Will manages financing outreach in his own CRM with context this system does not have. Therefore: no financing-watchlist section of any kind, no financing-opportunity column, no financing-relevance ranking, and no language recommending outreach. Delivery is the Make webhook only; the prior delivery service is retired. The brief answers three questions only: what NEW projects appeared, what CHANGED, and what DATABASE UPDATES are recommended.

## Step 1 - Pull undigested activity
```sql
SELECT * FROM "Scan Activity Log" WHERE digested_at IS NULL AND run_type IN ('scan','enrichment') ORDER BY ts;
```
Join new candidates to their staged rows for full detail:
```sql
SELECT p.* FROM "01 - Project - New" p WHERE p.discovered_at > now() - interval '26 hours';
```

## Step 2 - Compose, in EXACTLY this section order
1. WARNINGS (only if any): scan did not run / did not complete, blocked sources, errors. If the log has no scanner run_summary for last night, lead with "WARNING: 3am scan did not run or did not complete. Last scan: {ts} ({regions})."
2. NEW PROJECTS (the lead section): one line per new candidate -
   {Project Name} | {Region} / {Submarket} | {Status} | {Units} units | confidence {level} | {one-line note} | {source_url}
   High confidence first, then by region. If none: "No new candidates. Regions scanned: {list}."
3. DATABASE UPDATE RECOMMENDATIONS (the action section), in this order:
   a. live_status_suggestions NEW since last digest (each: project, current -> suggested, confidence, evidence URL, one-line reasoning).
   b. live_status_suggestions still PENDING from prior runs (compact list: project, change, confidence, date logged).
   c. Staged status changes auto-applied to "01 - Project - New" (project, old -> new, evidence).
   d. Duplicate / merge recommendations and near-match flags (both names, shared evidence, recommended action).
   e. Data corrections applied or recommended (wrong city, region reassignment, dead URL and so on).
4. ENRICHMENT PROGRESS: fields filled last night (count by field), developer-contact completeness ("05 - Developers - New": X of Y rows have Contact, X of Y have Email, and so on), and what remains unfillable with reason.
5. PIPELINE SNAPSHOT: live "01 - Projects" counts by status (excl. Dead), staged totals ("01 - Project - New": total | added last 7 days | pending review), open suggestion count.

Formatting: compose in MARKDOWN per the EMAIL FORMATTING RULES below (the markdown is the canonical saved artifact). Terse, no em-dashes, mobile-readable. Stage labels (Planned / Under Construction / Completed) are fine; never rank by financing relevance.

## Step 3 - Deliver via the Make webhook
POST JSON to the webhook; Make emails it from Will's Outlook connection:
```
POST https://hook.us2.make.com/ms9ag6j37hic53tnuilvrfup1armt65y
Content-Type: application/json
{"subject": "SCK Daily Intelligence Brief - {YYYY-MM-DD}",
 "html": "<the markdown rendered to HTML per the EMAIL FORMATTING RULES>"}
```
Expect HTTP 200 with body "Accepted". On any failure: retry once after 60 seconds; if still failing, write the brief to ~/sck-digests/{date}.md and log the delivery failure to "Scan Activity Log". Never silently skip. Always send, even on a zero-activity night (short email).


## Step 3b - Archive the digest in Supabase (always, before marking digested)
```sql
INSERT INTO "Daily Digest Archive" ("Digest Date", "Subject", "Markdown", "Delivery Status")
VALUES (CURRENT_DATE, '<subject>', '<full markdown>', '<sent | failed: reason>');
```
Re-query to confirm the row landed. This table is the searchable history of every brief; the email is a copy, the row is the record.

## Step 4 - Mark digested (only after a successful POST or fallback write)
```sql
UPDATE "Scan Activity Log" SET digested_at = now() WHERE digested_at IS NULL AND run_type IN ('scan','enrichment') AND ts < now();
```

## Scheduling
Daily 5:55 AM (email lands ~6:00):
claude -p "Run the SCK morning digest routine per the sck-morning-digest skill" --permission-mode acceptEdits

## EMAIL FORMATTING RULES (mandatory - no wall-of-text emails)
Compose the report in MARKDOWN first (that markdown is the canonical saved artifact), then render the email HTML from it. Never send the whole report inside one <pre> block.
- Markdown: ## title with date, ### per section, one blank line between items, "- " bullets, **bold** project and developer names, plain URLs on their own.
- Email HTML rendering: <h2> title + date; <h3> per section; <hr> between major sections; items as <ul><li> with <b>bold</b> project names; a multi-field project entry is ONE <li>: <b>Name</b>: type, size, cost | city, county | stage | developer | one-line note; source links as <a href>. Counts and snapshots as short <ul> lists, not tables. <pre> is allowed ONLY for the pipeline-snapshot count block, nothing else. Keep the email under ~100 KB; when a section would exceed ~25 items, include the top items and one line saying the rest are in Supabase.
