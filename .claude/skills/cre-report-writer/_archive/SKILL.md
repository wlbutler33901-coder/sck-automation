---
name: cre-report-writer
description: Daily synthesis of the SWFL development scanner. Reviews the last 26 hours of permit records and news articles (7-day context for progressions), leads with NEW PROJECTS, writes one brief to the SCK Supabase table "Development Scanner - Report Summary", and emails it via the Make webhook as its own message. Use when the user requests the SWFL daily development report, the development scanner summary, or a Report Summary record.
---

# SWFL Development Report Writer (daily)

Daily decision-support brief for Will Butler / Calusa Capital Partners (Fort Myers CRE financing advisory). Runs every morning ~5:30 AM ET as a Claude Code cloud routine, after the permit (3:30) and news (4:30) scans. Autonomous scheduled run: execute end to end, do not pause for confirmation.

CURRENT PHASE: the brief leads with NEW PROJECTS. The financing lens (scoring per references/scoring-framework.md) stays as a compact secondary section; it becomes the lead in a later phase, not now. Focus geography: Lee, Charlotte, Collier, Sarasota, Manatee, one SWFL region. Sweet spot when scoring: $3M to $30M capitalization.

Connection: "Supabase - Storage Condo King" MCP, project llwyvgkqhendgzsgngqh, schema public.
Sources: "Development Scanner - Municipality Portals" (permits), "Development Scanner - News Scanner" (press).
Output: "Development Scanner - Report Summary" plus the Make webhook email.

## 1. Workflow
1. Pull both windows per references/schema.md: PRIMARY last 26 hours (new since yesterday), CONTEXT last 7 days (for progressions and first-appearance checks).
2. Build the opportunity universe: a news row with "Linked Portal Record" enriches that permit record (one combined item); unlinked articles are standalone news leads; permit rows with no articles are standalone permit leads.
3. Compose the sections in §2 exactly.
4. INSERT one row into "Development Scanner - Report Summary" (every column, references/schema.md), read it back by id to confirm.
5. Deliver the email per §3, then UPDATE the row's "Delivery Status".

## 2. Report Sections (exactly these, in order; empty sections say so explicitly)
1. EXECUTIVE SUMMARY (2-3 sentences): counts reviewed (permits, articles), new projects found in the last 26 hours, cluster scanned last night, aggregate disclosed cost, anything unusual.
2. NEW PROJECTS (the lead): every project appearing for the first time in the last 26 hours, permits and news merged. One block per project: Name (source id: Portal id X and/or News id Y) | property type, SF, cost | city, county | stage | developer and contact actionability | one-line why it matters. Order by disclosed cost descending, unknown-cost last.
3. FINANCING LENS (compact, secondary for now): the 3-5 highest-scoring opportunities per references/scoring-framework.md, one line each with score rationale. No outreach scripting.
4. NEW DEVELOPERS IDENTIFIED: first appearance across BOTH tables inside the 7-day window (verification queries in schema.md): name, asset class, source, one-line signal.
5. STAGE PROGRESSIONS: permit-internal advances (parcel match, new permit type) and news-confirmed advances in the 7-day window.
6. COVERAGE AND DATA QUALITY: last night's cluster per the permit rotation, portals blocked/failed, paywalls hit, null-heavy records worth a manual look.

Formatting: plain text, terse, pipe separators, real line breaks, no em-dashes, mobile-readable.

## 3. Deliver the email (separate message, same Make pipe)
POST to the shared Make webhook (it emails whatever it receives; this is a SEPARATE email from the SCK car-condo digest):
```
POST https://hook.us2.make.com/ms9ag6j37hic53tnuilvrfup1armt65y
Content-Type: application/json
{"subject": "SWFL Development Scanner - Daily Report - {YYYY-MM-DD}",
 "html": "<the brief as simple HTML: h3 section headers, <pre> for blocks>"}
```
Expect 200 "Accepted". Failure: retry once after 60 seconds; then set "Delivery Status" = 'failed: <reason>' and still leave the Supabase row (the record is the source of truth). Success: "Delivery Status" = 'sent'. Always send, even on a zero-activity day (short email).

## 4. Guardrails
Facts only; the analyst owns every call decision. Never report a figure not present in a source row. If a scanner did not run last night (no rows and no run evidence), the Executive Summary must say so in the first sentence.
