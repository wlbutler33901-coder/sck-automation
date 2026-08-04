# sck-automation Learnings

Shared operational memory for every scheduled routine in this repo. This file is the
institutional record of what has already broken, so no routine pays for the same failure twice.

## Contract (every routine, every run)

READ AT RUN START. Before any portal loop, search pass, or database write, read this entire
file. It is short by design. If a rule here conflicts with a skill file, this file wins on
operational matters (retries, concurrency, logging, run_type values) and the skill file wins
on subject matter (what qualifies, what gets written where).

APPEND AT RUN END. Interactive and local sessions append dated entries directly to this file.
Unattended cloud runs must NEVER commit, branch, or push; they record each learning as a Scan
Activity Log row with their own run_type and change_type learning, detail formatted as a contract
line from this file. Learning rows are folded into this file during interactive repo sessions,
which set digested_at on the rows they fold. Log a learning whenever a source failed or changed
shape, a write was rejected, a run was cut short, a rule here proved wrong, or a workaround was
found. A clean run logs nothing.

FORMAT. One entry per line, newest at the bottom of its section:
`YYYY-MM-DD | routine | severity | one sentence of what happened and what to do about it.`
Severity is one of blocker, degraded, fixed, note.

HOUSEKEEPING. Cap ACTIVE CONSTRAINTS at roughly 30 lines. When an entry is resolved, move it to
RESOLVED with the resolution date. Delete RESOLVED entries older than 90 days. Never delete an
ACTIVE entry to make room; if the list is full, escalate in the run summary instead.

NEVER put credentials, API keys, or personal contact details in this file.

## Active constraints

- 2026-07-20 | swfl-permit-scanner | blocker | The egress proxy resets chromium TLS on every
  site. Drive chromium via Playwright but fulfill every request through Node fetch. Full
  harness in references/platform-playbook.md; do not rebuild it from scratch.
- 2026-07-20 | swfl-permit-scanner | note | EnerGov requires tyler-tenanturl, tyler-tenantid and
  tyler-tenantname headers, SearchModule 1, and client-side date windowing. Server-side date
  filters are ignored.
- 2026-07-20 | swfl-permit-scanner | blocker | Sarasota County Accela building search is login
  gated. Use the approved Planning module substitute. Naples CityView is behind a CAPTCHA, use
  the Collier County feed. Punta Gorda Click2Gov is lookup only. Palmetto BS&A is anti-bot and
  parked, catch it through Manatee County. Estero serves a broken TLS chain, catch it through
  Lee County plus press. Never attempt to defeat a login or a CAPTCHA.
- 2026-08-03 | all routines | blocker | Scan Activity Log run_type has drifted repeatedly. The
  ONLY permitted values are: scan, enrichment, swfl_permit_scan, swfl_news_scan, swfl_report.
  Values nightly_scan, project_scan, project_scanner and scanner have all appeared in
  production and are invisible to the consuming digests. Hard-code the literal, never compose
  it, never abbreviate it. The consuming digests keep a tolerant IN-list as a backstop, but
  never rely on it.
- 2026-08-03 | sck-project-scanner | blocker | The cloud container suspended mid-run with five
  parallel research agents open and the run logged zero rows. Cap concurrent research agents at
  2, write a run_started row before any search, and log each region the moment it completes.
- 2026-08-03 | swfl-permit-scanner | blocker | A cluster that produces zero qualifying permits
  must still log a portal_result row per portal. Silence is indistinguishable from a run that
  never happened, which is how the Collier gap went unnoticed for a week.
- 2026-07-15 | all routines | note | Staging table id sequences have collided with existing
  rows. Never pass an explicit id in an INSERT; let the sequence assign it. On a duplicate-key
  collision retry once; the sequence self-corrects.
- 2026-07-15 | all routines | note | Windows Task Scheduler runs these through `claude -p`. An
  unmerged PR deploys nothing and the routines silently keep using the old skill files. Merging
  is part of shipping, not an optional follow-up.
- 2026-07-19 | make-pipeline | note | Bare webhook hits (link scanners) crashed the email module
  and auto-disabled the Make scenario; a filter now drops payloads without subject+html silently
  - never remove it.
- 2026-07-10 | resale-appraisal | blocker | Never set "Manual Update" to TRUE. It fires the
  legacy Make webhook.
- 2026-08-03 | cre-report-writer | blocker | Report windows are high water mark based per
  references/report-structure.md, never a fixed lookback. The old 26 hour window overlapped the
  prior morning's scan output and reported most items as new twice.
- 2026-08-03 | swfl-news-scanner | note | businessobserverfl.com and yourobserver.com return 403
  on direct fetches. Recover via search snippets or syndicated mirrors and mark that content as
  not independently verified.
- 2026-08-03 | swfl-permit-scanner | note | Track B platform expectations from Track A
  precedent: Click2Gov is lookup only for date searches (Punta Gorda) and BS&A is anti-bot
  (Palmetto). Certify Tampa portals on those platforms with substitutes ready per
  references/sources-tampa.md.
- 2026-08-03 | swfl-permit-scanner | note | The Hernando County URL on file is the property
  appraiser parcel lookup, not a permit feed. Locate the county's actual permit search at
  certification; keep the appraiser link for parcel enrichment.
- 2026-08-03 | swfl-permit-scanner | note | St. Petersburg (Click2Gov) has no date-searchable
  permit feed and no Tier-3 substitute (ArcGIS Geohub, Socrata, and the city site all lack
  itemized issued permits; only an annual aggregate report exists). Tier-4 press substitution
  with a coverage_gap flag is ACCEPTED for now, the same treatment Track A gives Estero and
  Naples; a direct feed remains wanted. Log a coverage_gap row for St. Pete each Wednesday.
- 2026-08-04 | swfl-permit-scanner | note | City of Clearwater Accela (TPA-TUE-PINELLAS-N) enforces
  a hard ~100-row date-desc cap on its only record type (generic "Building - Construction Permit"),
  so a 90-day first-run pull only actually reached back about 6 days (2026-07-29 to 2026-08-03) in
  the first cloud run. Expect the same shallow real coverage on every future pass, not just the
  first; the 90-day intent does not apply here, this portal is effectively last-100-rows-only.
- 2026-08-04 | swfl-permit-scanner | note | TPA-TUE-PINELLAS-N first real write pass complete
  (Dunedin/Largo EnerGov api, Pinellas Co/Clearwater Accela browser, Safety Harbor/Tarpon Springs
  press-substitute). 7 records inserted. The Dunedin/Largo EnerGov search-body template was not on
  file in references/platform-playbook.md (only headers/host); the run recaptured it live via a
  one-time Playwright network-interception pass but did not save it back to the playbook. Future
  runs on these two portals should capture-and-append the verbatim body once cracked so Tier-1 API
  pulls stop needing a browser at all.
- 2026-08-04 | swfl-news-scanner | note | news-press.com and naplesnews.com (Gannett) are not just
  metered-paywalled, WebFetch could not reach either site at all this run ("unable to fetch"), and
  WebSearch site: queries returned zero results for either domain in the scan window. Treat both as
  blocked, not paywalled, until proven otherwise; do not burn time on direct WebFetch retries.
- 2026-08-04 | swfl-news-scanner | note | yourobserver.com 403'd on every URL tried this run
  (landing pages and article pages alike), worse than the prior intermittent-403 note above.
  Recovered via WebSearch only. If this persists across runs, treat it as blocked like
  businessobserverfl.com rather than intermittent.
- 2026-08-04 | swfl-permit-scanner | blocker | Monday Aug 3 rotation (SWFL-MON-LEE-CITIES,
  TPA-MON-TAMPA) left zero trace: no Scan Activity Log rows and no portal-table writes for the
  full overnight window, versus normal writes on the nights before and after. Not a logging gap
  (the run-logging contract was already live); the run itself appears not to have executed.
  Needs investigation before next Monday; the 14-day lookback will self-heal the data once it
  does run, but the missed night is otherwise invisible without this note.
- 2026-08-04 | swfl-permit-scanner | note | The City of Naples press-substitute path inserted 2
  permit rows (The Avenue - Fifth Avenue South Mixed-Use; Dual-Brand Hotel at 870
  Goodlette-Frank Rd) that duplicate news scanner rows from Jul 19 and Jul 27 at the same
  address with no new facts. The report's exact-string identity key did not catch it because the
  two tables used different Project Name strings for the same project. The press-substitute
  cross-table dedup rule in the permit scanner section 5 now covers this; check the News Scanner
  table by address/parcel, not just by project name.
- 2026-08-04 | sck-project-enrichment | workaround | FL Sunbiz (search.sunbiz.org) sits behind a
  Cloudflare managed challenge that blocks both WebFetch and browser-UA curl, so LLC
  registered-agent/principal reads fail. Get principals from press, bizprofiles.com / city-data
  business-entity mirrors, and FL DBPR license lookups instead; cite the real Sunbiz doc number
  when the mirror confirms it.
- 2026-08-04 | sck-project-enrichment | note | The 25-oldest dev-contact budget is misleading once
  the oldest rows are already worked: they held documented genuine gaps from the prior run, so the
  real fillable work was the newer filled=0 rows (mostly FL). Spend the row budget where NULLs are
  actually fillable, not strictly oldest-first, or the top-priority contacts stay empty.
- 2026-08-04 | sck-project-enrichment | note | The distinctive-token audit earned its keep: it
  flagged two staged near-dupes the scanner missed - "Car Village Bluffton" vs "CarVillage USA"
  (same developer SKYHB-1, Beaufort Co) and "Naples Luxury Auto Storage" vs "Naples Luxury Motor
  Suites" (both reduce to "naples", Collier Co). Logged as merge_recommendation, not auto-merged,
  since the names differ and a live/high-value row was involved.
- 2026-08-04 | swfl-permit-scanner | fixed | Lee County has a weekly no-auth PDF feed under
  /dcd/rpts/Documents/CurrentMonth (ULCBPCWeek1-5.PDF), which avoids the SharePoint 401 and the
  monthly-report lag entirely, and Village of Estero permits are in that same feed under the VE
  prefix (VEBPCWeek1-5.PDF) - Estero is no longer a no-feed jurisdiction. Recipe recovered from
  the 2026-07-26 run (branch hopeful-heisenberg-bgxo71) into references/platform-playbook.md.
  Parse with pdftotext -layout; pypdf/cffi is broken in the CC cloud sandbox.
- 2026-08-04 | swfl-permit-scanner | note | Charlotte County Accela date-range search returned
  "no results" for every window on 2026-07-22 while an unfiltered search worked, then the host
  went unreachable - a temporary IP rate limit from repeated automated hits. Retry fresh on a
  later cluster night before assuming it is broken; if it recurs, use the no-date-filter search
  plus client-side date windowing. The county also publishes a monthly "Major Projects" PDF
  (charlottecountyfl.gov /file/363/major-projects-<month>-<year>.pdf) that is a genuine Tier 3
  feed, not press substitution. Recovered from branch hopeful-heisenberg-4eed0z.
- 2026-08-04 | swfl-permit-scanner | note | references/sources.md now marks retired access paths
  with a SUPERSEDED marker at the start of the Platform cell instead of deleting the row, so
  certification history survives. Scanners MUST skip any row marked SUPERSEDED; it is history,
  not a scan target. The file has no Status or Notes column, so the marker lives in the Platform
  cell, which the file already defines as the extraction cue. Same rule applies to
  references/sources-tampa.md, which does have a real Status column.
- 2026-08-04 | swfl-permit-scanner | note | City of Sarasota CRE lives in the FastTrackGov
  "da" (Development Applications) microapp, not the certified "c" building-permit search, which
  is list-level triage only (no description or valuation, detail page AJAX-gated). Search "da" by
  street name only; there is no working date range. Sarasota County Planning also needs
  ddlGSPermitType filtered per type or an unfiltered search returns 100+ noise rows. Recovered
  from branch hopeful-heisenberg-rnikmc.

## Resolved

- 2026-07-20 | swfl-permit-scanner | fixed | Portal certification sweep completed. 11 portals
  certified with real 14 day pulls across 4 access tiers. Recipes live in
  references/platform-playbook.md and references/sources.md. Those two files are additive only;
  never replace them wholesale.

## Log

- 2026-08-03 | swfl-permit-scanner | blocker | No SWFL routine has ever written to Scan Activity
  Log, so the daily report has had no way to audit its own rotation. Run logging contract added
  in references/run-logging.md.
- 2026-08-03 | cre-report-writer | fixed | Double counting root caused: report at 09:40 UTC with
  a 26 hour window reaches past the prior morning's 07:37 to 08:47 UTC scan writes, so 22 of 34
  New Projects entries across Aug 1 to Aug 3 were repeats, including Estero Oaks Portal id 98
  presented as a first appearance two days running. Fixed by the high water mark window in
  references/report-structure.md.
- 2026-08-03 | cre-report-writer | fixed | New Developers section re listed the same names for a
  week by spec (7 day window). Now first appearance within the report window only.
- 2026-08-03 | swfl-permit-scanner | note | Venice eTRAKiT has produced zero records since
  certification on Jul 20. Once portal_result logging lands, the first Friday run will show
  whether that is real zero volume or a silent failure.
- 2026-08-03 | swfl-permit-scanner | note | Rotation adherence verified from the database for
  Jul 19 to Aug 2: every night with rows hit its scheduled cluster. Two nights (Jul 24, Jul 28)
  produced zero rows with no way to tell a failed run from an empty one; run logging closes
  that gap.
- 2026-08-03 | swfl-permit-scanner | note | Track B (Tampa MSA) certified: 13 of 26 portals
  CERTIFIED (5 Accela, 5 EnerGov incl. Largo and Hernando, 2 SmartGov, 1 iWorQ), 12
  BLOCKED-SUBSTITUTE, 1 gap (St. Pete). All 7 Track B clusters flipped to ACTIVE in rotation.md;
  first cloud rotation performs the first real writes with the 90-day first-run lookback.
- 2026-08-03 | swfl-permit-scanner | fixed | Dunedin EnerGov host on file (energoweb) DNS-failed;
  correct host is cityofdunedinfl-energovweb.tylerhost.net; sources-tampa.md URL corrected.
- 2026-08-03 | swfl-permit-scanner | note | Hernando County real permit feed found = Tyler
  EnerGov (hernandocountyfl-energovweb.tylerhost.net, tenant hernandocountyflprod, top-level
  paging quirk); the on-file pvweb.hernandopa-fl.us is the appraiser (parcel enrichment only).
- 2026-08-03 | swfl-permit-scanner | note | New Track B platform recipes cracked and saved to
  platform-playbook.md: SmartGov (Granicus) and iWorQ are usable Tier-2; Tyler Portico,
  Citizenserve (reCAPTCHA), MGO Connect (login), MaintStar and CivicGov (lookup-only), BS&A
  (anti-bot) are blocked with substitutes.
- 2026-08-01 | sck-project-scanner | note | "Bonita Auto Vault" was staged as new but is Bonita
  Motor Vault (live); dedup is now multi-signal at COUNTY level - distinctive-token match after
  stripping generic product words, plus address, parcel, and developer.
- 2026-08-03 | sck-project-enrichment | note | Routine referenced an outreach template/menu not
  present in the repo skill (a skill update had not merged to origin/main); it correctly skipped
  rather than improvise. Skills carry a marker section; when instructions and skill drift, log
  SKILL-OUT-OF-DATE loudly and verify every skill update landed on origin/main.
- 2026-08-03 | sck-project-scanner | note | A 3am scan did not execute (no run_summary) and the
  digest warned correctly; check the routine Runs list for the failure reason - the 14-day
  lookback self-heals coverage the next night.
