---
name: swfl-permit-scanner
description: Daily discovery of new commercial real estate development projects from municipal permit and zoning portals across Southwest Florida (Lee, Charlotte, Collier, Sarasota, and Manatee counties, one SWFL region). Runs in Claude Code cloud using the virtual browser to navigate portal filters and review permit PDFs. Use when the user requests a permit-scan run, the SWFL development scanner, a pipeline update, or new SWFL CRE project discovery. Writes structured records to the SCK Supabase table "Development Scanner - Municipality Portals".
---

# SWFL Permit Scanner (daily)

You are a research agent surfacing commercial development projects at the permit and zoning stage across SWFL. Primary purpose right now: find NEW PROJECTS and log clean records. Financing-opportunity framing comes later; a clean record with a named developer and parcel number is the unit of value. Never fabricate data.

## 1. Runtime, Cadence, Scope
- Read LEARNINGS.md at the repo root before anything else, and append a dated entry at run end per the contract in that file; in an unattended cloud run, record learnings as change_type learning rows in Scan Activity Log instead, and never commit, branch, or push.
- Runtime: Claude Code cloud routine. Use the VIRTUAL BROWSER for portal navigation (Accela ACA, Tyler EnerGov, eTRAKiT, Harris CityView, FastTrackGov, Click2Gov, BS&A all require it: search forms, date filters, result pagination, record detail pages). Use plain fetch only for static report pages and direct PDF links.
- Cadence: DAILY, one municipality cluster per ACTIVE track per day per references/rotation.md, so the full region is swept every week. Determine today's weekday and scan that row only.
- Lookback: last 14 days per portal (a missed day self-heals on the next weekly pass). First-ever run on a portal: 90 days.
- Time budget: ~15 minutes per portal. Log failures and move on; never stall.

## 2. Sources and Extraction
Read references/rotation.md for today's cluster, references/sources.md for portal URLs and platforms, references/platform-playbook.md for per-platform navigation and extraction steps, references/sources-tampa.md for Track B portal URLs and platforms, and references/run-logging.md for the mandatory Scan Activity Log contract.

ACCESS TIERS (try in this order per portal; log which tier was used in the run log):
- TIER 1, PLATFORM API (preferred, EnerGov and other JSON-backed SPAs): call the JSON endpoint behind the SPA directly, no browser. Recipes and discovery method in references/platform-playbook.md. Once a portal's endpoint+payload is captured, record it in the playbook so future runs are pure API.
- TIER 2, HEADLESS BROWSER (Accela and portals without a usable API): BOOTSTRAP AT RUN START before the portal loop: check for Playwright (npx playwright --version); if missing, install: npm i playwright && npx playwright install --with-deps chromium (fallback without deps flag; time-box the install to ~3 minutes). If the environment cannot get a browser, log "browser unavailable" ONCE and use tiers 3-4 for browser-only portals; never silently skip.
- TIER 3, PUBLISHED PERMIT REPORT PDFS: many cities post monthly permit-activity reports (the Fort Myers / Lee County pattern). Check the city site for "permit reports", "building statistics", "monthly activity" PDFs and parse the newest.
- TIER 4, PRESS SUBSTITUTION: cover the jurisdiction from trade press for the night and flag the coverage gap in the run log (as done for Midtown at Bonita).

Browser expectations per platform:
- Accela ACA (Charlotte, Manatee, Bradenton, Sarasota County, North Port): use Advanced Search, set date range, record type Commercial/Building, page through results, open each qualifying record for detail.
- Tyler EnerGov (Cape Coral, Bonita Springs): Self Service search with date + type filters.
- eTRAKiT (Venice), CityView (Naples), FastTrackGov (Sarasota city), Click2Gov (Punta Gorda), BS&A (Palmetto): per playbook.
- PDF sources (Lee County DCD reports, Fort Myers statistical reports, Collier monthly reports): download the newest report PDF in the browser, read it, extract qualifying commercial permits.
Capture raw fields per record: permit/case number, description, address, parcel, applicant/owner, valuation, dates, status, jurisdiction.

Prefer, in order: new commercial building permits; site development / site plan; zoning / rezoning / PUD / land use; large commercial additions and shells; demolition tied to redevelopment.

## 3. Qualification Filter
INCLUDE if commercial or income-producing AND any of: valuation >= $1,000,000; building >= 10,000 SF; multifamily >= 5 units; any commercial/multifamily rezoning, PUD, or site plan; a named developer/sponsor is identifiable.
EXCLUDE: single-family and duplex work, remodels, pools, fences, sheds; trade-only sub-permits; sign/awning/temporary-use; tenant interiors under $500K with no expansion; maintenance, demo-only, ROW/utility-only.
Borderline: capture with a confidence note in "References & Data Sources".
SITE-WORK-ONLY permits (vertical permit and full valuation not yet filed): capture them, note "awaiting vertical permit" in "Key Dates", and rely on the parcel-match dedupe path to UPGRADE the same row when the vertical permit lands - that upgrade is a Stage Progression for the daily report.

## 4. Web Research Enrichment (qualified records only)
1. Resolve applicant LLC to the operating developer; find website, LinkedIn, a 1-2 sentence description.
2. Search project name + city for press or agenda coverage; summarize scope.
3. Contacts: office address, main phone, key executives.
4. Cross-check placeholder valuations ($0/$1) against credible web figures; put estimates in text fields only, never numeric columns.
5. Capture parcel/folio from the permit or the county property appraiser (dedupe key).
6. Classify "Project Stage": Planned / Permitting (highest priority), Under Construction, On Hold / Stalled, Completed.
Cite every external fact by URL in "References & Data Sources".

## 5. Deduplication (BEFORE every write)
Natural key = permit/case number; fallback = parcel/folio (normalize: strip dashes/spaces); weak = Address + Project Name. Check in that order against "Development Scanner - Municipality Portals".
- No match: INSERT.
- Match: UPDATE the existing row (append to multi-line fields, advance "Project Stage", note progression in "Key Dates"). A parcel match with a new permit number means the project advanced a stage.
- Match, nothing new: skip, log "seen, no change".
Never create a second row for the same project.
PRESS SUBSTITUTE RECORDS (Tier 4) carry extra duplication risk because the news scanner drinks from the same press. Before inserting any press substitute record, also check "Development Scanner - News Scanner" by normalized address and by normalized project name plus city (same dash normalization). If a news row already covers the project with no new facts, do NOT insert; log portal_result detail as covered by News Scanner id N. Only insert a press substitute row when it adds facts no news row holds, and say which facts in "References & Data Sources".

## 6. Write to Supabase
Read references/schema.md for exact columns and format rules.
Target: SCK Supabase project llwyvgkqhendgzsgngqh, schema public, table "Development Scanner - Municipality Portals", via the "Supabase - Storage Condo King" MCP connector. Quote every identifier (spaces throughout). Named columns only. Omit unknown keys entirely; never empty strings in numeric columns. Re-query after writes to confirm they landed. If the connector is unavailable, log the failure and stop; do not invent another write path.

## 7. Logging and QA
Every run also writes rows to Scan Activity Log exactly per references/run-logging.md, incrementally, never buffered to the end of the run.
Run log: portals scanned/skipped/failed with the ACCESS TIER used per portal (api | browser | pdf | press-substitute | blocked); permits seen/qualified/inserted/updated/skipped; each new record (name + permit + id); data-quality warnings. Self-QA per record: numeric fields numeric or omitted; "Municipality Posting Look-Up Value" populated; parcel captured when obtainable; controlled vocab respected; dedupe ran; at least one cited source; no fabricated values.

## Guardrails
- Public-records portals only. Work through slow portals and parse PDFs patiently, but NEVER bypass logins, paywalls, or CAPTCHAs; a CAPTCHA-blocked portal is logged as blocked and skipped.
- Pace requests to avoid IP blocks.
- Accuracy over completeness: a null beats a guess.
