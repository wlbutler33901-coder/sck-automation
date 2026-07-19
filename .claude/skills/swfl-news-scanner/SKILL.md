---
name: swfl-news-scanner
description: Daily sweep of Southwest Florida business journals, local news, and broker press for new commercial development projects across Lee, Charlotte, Collier, Sarasota, and Manatee counties (one SWFL region). Runs in Claude Code cloud; uses the virtual browser for JS-heavy or archive-pattern sites. Use when the user requests a news scan, a refresh of the Development Scanner news table, or a sweep of regional CRE press. Writes to the SCK Supabase table "Development Scanner - News Scanner" and cross-references permit records.
---

# SWFL News Scanner (daily)

You are a research agent surfacing SWFL development activity from local and regional press. Primary purpose right now: NEW PROJECTS and material project news; the financing classification fields are still captured on every record (they power the later financing-ops phase) but article selection optimizes for project discovery. Never fabricate data.

## 1. Runtime, Cadence, Scope
- Runtime: Claude Code cloud routine. Plain fetch for most sources; VIRTUAL BROWSER for JS-rendered pages, infinite-scroll sections, and the Wix-based broker pages noted in the playbook.
- Cadence: DAILY. Two passes each run: (a) REGION-WIDE skim of Tier 1 headlines (all five counties, last 48 hours), (b) DEEP DIVE on today's county per the permit scanner's rotation (references/sources.md tiers; match the county-of-the-day so permits and press for one county land the same morning).
- Lookback: 48 hours region-wide, 14 days on the deep-dive county. First-ever run: 90 days.
- Time budget: ~10 minutes per source; log paywalls/failures and move on.

## 2. Sources
Read references/sources.md (tiered: primary business press, local TV, broker releases) and references/platform-playbook.md for per-source access patterns (RSS where available, dated-URL patterns, paywall notes).

## 3. Qualification Filter
INCLUDE if the article: names a developer/sponsor with an active or upcoming SWFL project; reports a land sale signaling development intent; profiles a developer pipeline, capital raise, or active build; covers zoning/planning/site-plan approvals; or is a brokerage transaction report naming sponsors on commercial property.
EXCLUDE: residential-resale market reports, retailer openings into existing space, general commentary with no named sponsor/project, lifestyle coverage. Completed projects with no near-term event: capture only if the sponsor is high-value, low score, note why.

## 4. Extraction and Classification
Per qualifying article extract: URL, Publication, Title, Date, Author; project name, property type, city, county, address detail, size, cost, stage; developer/sponsor and named principals; 1-3 short attributed key quotes.
Classify: "Article Type", "Financing Opportunity Type", "Financing Relevance Score" (High/Medium/Low), "Outreach Recommendation" (High only). These fields persist for the financing-ops phase; do not let them gate whether a new project gets recorded.
Web search only when the article omits critical identity info; the article is the primary signal.

## 5. Cross-Reference to Permit Records
Before writing, match against "Development Scanner - Municipality Portals":
```sql
SELECT id, "Project Name", "Developer / Sponsor / Key Principal", "Address"
FROM "Development Scanner - Municipality Portals"
WHERE "Developer / Sponsor / Key Principal" ILIKE '%<dev>%'
   OR "Project Name" ILIKE '%<project>%'
   OR "Address" ILIKE '%<street>%';
```
Exactly one strong match: populate "Linked Portal Record" with that id. Ambiguous: leave null, note candidates in "Notes". A linked article is a stage-progression and enrichment signal.

## 6. Deduplication
Dedupe key = canonical "Article URL" (normalize with scripts/url_normalize.py). Existing URL: skip (or UPDATE only if materially better data). One row per article; multiple articles on one project are separate rows sharing "Linked Portal Record".

## 7. Write to Supabase
Read references/schema.md. Target: SCK Supabase project llwyvgkqhendgzsgngqh, table "Development Scanner - News Scanner", via the "Supabase - Storage Condo King" MCP connector. Quoted identifiers, named columns, omit unknown keys, numeric columns clean. Re-query to confirm writes. Connector unavailable: log and stop.

## 8. Logging and QA
Run log: sources scanned/skipped/paywalled; articles seen/qualified/inserted/skipped-duplicate; cross-reference hits. Self-QA: URL canonicalized; controlled vocab respected; quotes attributed; county one of the five (or null with a note); no fabricated values.

## Guardrails
Never bypass paywalls or logins; a paywalled article is logged and skipped (capture the free-preview facts only if unambiguous). Pace requests. Accuracy over completeness.
