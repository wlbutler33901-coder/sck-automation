---
name: swfl-permit-scanner
description: Daily discovery of new commercial real estate development projects from municipal permit and zoning portals across Southwest Florida (Lee, Charlotte, Collier, Sarasota, and Manatee counties, one SWFL region). Runs in Claude Code cloud using the virtual browser to navigate portal filters and review permit PDFs. Use when the user requests a permit-scan run, the SWFL development scanner, a pipeline update, or new SWFL CRE project discovery. Writes structured records to the SCK Supabase table "Development Scanner - Municipality Portals".
---

# SWFL Permit Scanner (daily)

You are a research agent surfacing commercial development projects at the permit and zoning stage across SWFL. Primary purpose right now: find NEW PROJECTS and log clean records. Financing-opportunity framing comes later; a clean record with a named developer and parcel number is the unit of value. Never fabricate data.

## 1. Runtime, Cadence, Scope
- Runtime: Claude Code cloud routine. Use the VIRTUAL BROWSER for portal navigation (Accela ACA, Tyler EnerGov, eTRAKiT, Harris CityView, FastTrackGov, Click2Gov, BS&A all require it: search forms, date filters, result pagination, record detail pages). Use plain fetch only for static report pages and direct PDF links.
- Cadence: DAILY, one municipality cluster per day per references/rotation.md, so the full region is swept every week. Determine today's weekday and scan that row only.
- Lookback: last 14 days per portal (a missed day self-heals on the next weekly pass). First-ever run on a portal: 90 days.
- Time budget: ~15 minutes per portal. Log failures and move on; never stall.

## 2. Sources and Extraction
Read references/rotation.md for today's cluster, references/sources.md for portal URLs and platforms, references/platform-playbook.md for per-platform navigation and extraction steps.

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

## 6. Write to Supabase
Read references/schema.md for exact columns and format rules.
Target: SCK Supabase project llwyvgkqhendgzsgngqh, schema public, table "Development Scanner - Municipality Portals", via the "Supabase - Storage Condo King" MCP connector. Quote every identifier (spaces throughout). Named columns only. Omit unknown keys entirely; never empty strings in numeric columns. Re-query after writes to confirm they landed. If the connector is unavailable, log the failure and stop; do not invent another write path.

## 7. Logging and QA
Run log: portals scanned/skipped/failed; permits seen/qualified/inserted/updated/skipped; each new record (name + permit + id); data-quality warnings. Self-QA per record: numeric fields numeric or omitted; "Municipality Posting Look-Up Value" populated; parcel captured when obtainable; controlled vocab respected; dedupe ran; at least one cited source; no fabricated values.

## Guardrails
- Public-records portals only. Work through slow portals and parse PDFs patiently, but NEVER bypass logins, paywalls, or CAPTCHAs; a CAPTCHA-blocked portal is logged as blocked and skipped.
- Pace requests to avoid IP blocks.
- Accuracy over completeness: a null beats a guess.
