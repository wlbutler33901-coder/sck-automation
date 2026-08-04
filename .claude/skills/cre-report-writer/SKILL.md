---
name: cre-report-writer
description: Daily synthesis of the SWFL development scanner. Reviews the last 26 hours of permit records and news articles (7-day context for progressions), leads with NEW PROJECTS, writes one brief to the SCK Supabase table "Development Scanner - Report Summary", and emails it via the Make webhook as its own message. Use when the user requests the SWFL daily development report, the development scanner summary, or a Report Summary record.
---

# SWFL Development Report Writer (daily)

Read LEARNINGS.md at the repo root before anything else, and append a dated entry at run end per the contract in that file; in an unattended cloud run, record learnings as change_type learning rows in Scan Activity Log instead, and never commit, branch, or push.

Daily decision-support brief for Will Butler / Calusa Capital Partners (Fort Myers CRE financing advisory). Runs every morning ~5:30 AM ET as a Claude Code cloud routine, after the permit (3:30) and news (4:30) scans. Autonomous scheduled run: execute end to end, do not pause for confirmation.

CURRENT PHASE: the brief leads with NEW PROJECTS. The financing lens (scoring per references/scoring-framework.md) stays as a compact secondary section; it becomes the lead in a later phase, not now. Focus geography: Lee, Charlotte, Collier, Sarasota, Manatee, one SWFL region, plus Hillsborough, Pinellas, Pasco and Hernando (Tampa MSA, Track B) once its clusters are active. Sweet spot when scoring: $3M to $30M capitalization.

Connection: "Supabase - Storage Condo King" MCP, project llwyvgkqhendgzsgngqh, schema public.
Sources: "Development Scanner - Municipality Portals" (permits), "Development Scanner - News Scanner" (press).
Output: "Development Scanner - Report Summary" plus the Make webhook email.

## 1. Workflow
1. Pull the PRIMARY window using the high water mark rule in references/report-structure.md and the CONTEXT window of the last 7 days, per references/schema.md (for progressions and first-appearance checks). Also pull the coverage and rotation queries from ../swfl-permit-scanner/references/run-logging.md.
2. Build the opportunity universe: a news row with "Linked Portal Record" enriches that permit record (one combined item); unlinked articles are standalone news leads; permit rows with no articles are standalone permit leads.
3. Compose the report in MARKDOWN per the EMAIL FORMATTING RULES below, sections per §2 exactly.
4. INSERT one row into "Development Scanner - Report Summary" (every column including "Report Markdown" = the full markdown, references/schema.md), read it back by id to confirm. Write every named column, including "Project Updates", "Rotation Audit" and "Updates Count", which already exist on the table.
5. Deliver the email per §3, then UPDATE the row's "Delivery Status".

## 2. Report Sections (exactly these, in order; empty sections say so explicitly)
Section order, numbering, the report window, the first appearance rules, and the rotation audit are defined in references/report-structure.md; follow that file exactly.

Formatting: terse, no em-dashes, mobile-readable, per the EMAIL FORMATTING RULES below.

## 3. Deliver the email (separate message, same Make pipe)
POST to the shared Make webhook (it emails whatever it receives; this is a SEPARATE email from the SCK car-condo digest):
```
POST https://hook.us2.make.com/ms9ag6j37hic53tnuilvrfup1armt65y
Content-Type: application/json
{"subject": "SWFL Development Scanner - Daily Report - {YYYY-MM-DD}",
 "html": "<the markdown rendered to HTML per the EMAIL FORMATTING RULES>"}
```
Expect 200 "Accepted". Failure: retry once after 60 seconds; then set "Delivery Status" = 'failed: <reason>' and still leave the Supabase row (the record is the source of truth). Success: "Delivery Status" = 'sent'. Always send, even on a zero-activity day (short email).

## 4. Guardrails
Facts only; the analyst owns every call decision. Never report a figure not present in a source row. If a scanner did not run last night (no rows and no run evidence), the Executive Summary must say so in the first sentence.

## EMAIL FORMATTING RULES (mandatory - no wall-of-text emails)
Compose the report in MARKDOWN first (that markdown is the canonical saved artifact), then render the email HTML from it. Never send the whole report inside one <pre> block.
- Markdown: ## title with date, ### per section, one blank line between items, numbered "1." items (never "- " bullets for report items), **bold** project and developer names, plain URLs on their own.
- Email HTML rendering: <h2> title + date; <h3> per section; <hr> between major sections; items as <ol><li> with <b>bold</b> project names; a multi-field project entry is ONE <li>: <b>Name</b>: type, size, cost | city, county | stage | developer | one-line note; source links as <a href>. Counts and snapshots as short <ul> lists, not tables. <pre> is allowed ONLY for the pipeline-snapshot count block, nothing else. Keep the email under ~100 KB; when a section would exceed ~25 items, include the top items and one line saying the rest are in Supabase.
