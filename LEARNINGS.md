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

- 2026-08-05 | swfl-permit-scanner | blocker | Charlotte County Accela date-range search returned
  no results for a THIRD time (after 2026-07-22), and the no-date-filter General Search now returns
  only 4 stale closed permits instead of the ~100-row grid seen at 2026-07-20 certification, so
  client-side windowing is not viable either. Rely on the Major Projects PDF (lagging, June 2026
  newest) plus press substitution for Charlotte County until a fresh certification fixes it.
- 2026-08-06 | swfl-news-scanner | blocker | LSI Cos (lsicos.com) DNS-failed outright
  (getaddrinfo ENOTFOUND) on two consecutive run days, 2026-08-05 and 2026-08-06. Treat as
  blocked/down, not paywalled; stop retrying it fresh each run until a health check shows the
  domain resolving again.
- 2026-08-05 | swfl-news-scanner | note | Yoursun is the weakest-covered Tier 1 source on the
  Charlotte deep dive: direct fetch 429'd, section pages returned only stale pre-2026 cached
  content, and site-scoped search surfaced archive articles only, so Charlotte-day runs lean
  entirely on Gulfshore Business and WINK. Charlotte is the one county Yoursun uniquely covers, so
  this is a real coverage gap on Charlotte nights, not noise.
- 2026-08-06 | swfl-news-scanner | note | The WINK News category URL (/category/news/local-news/)
  and Fox 4 (/news) both 404 - the entry URLs on file in references/sources.md no longer resolve
  and need correcting before the next Lee or Charlotte heavy run.
- 2026-08-05 | cre-report-writer | blocker | The 7 day CONTEXT window SELECT * queries against
  Municipality Portals and News Scanner now exceed the tool token limit (87k and 62k chars) once
  either table passes roughly 25-30 rows in a week. Select only the columns the identity check and
  progression logic need (id, Project Name, City, County, Parcel / Folio Number, Posting Date or
  Article Date, created_at, Project Stage, Developer / Sponsor, Linked Portal Record) instead of
  SELECT *.
- 2026-08-06 | swfl-permit-scanner | fixed | The Tyler EnerGov /apps/selfservice search body for the
  newer Angular build (Dunedin, Zephyrhills, New Port Richey) MUST carry a top-level FilterModule:2
  alongside SearchModule:1. Without it the API returns HTTP 200 with Success:false and Result:null,
  which looks like zero results but is a rejected request. With SearchModule:1, FilterModule:2,
  PageSize:50, SortBy IssueDate, SortAscending false, pagination plus client-side date windowing
  works (Zephyrhills PermitsFound 11954, New Port Richey 56550).
- 2026-08-06 | swfl-permit-scanner | note | Pasco County Accela is the richest CRE feed in the
  system and shows the pattern to try on other Accela tenants: list rows carry a hidden RecordId
  (PREFIX-00000-SUFFIX) that decodes into a public no-login CapDetail.aspx URL
  (capID1=PREFIX&capID2=00000&capID3=SUFFIX&agencyCode=PASCO) exposing Job Value, Building Area,
  Number of Units, Owner, Site Plan Number, Project Name and Parcel. Always pull CapDetail for every
  Commercial New or Multifamily hit before disqualifying it; the list view alone looks like noise
  but named projects hide inside it (Wave at Flora 300-unit approx $68.9M, Life Time Wesley Chapel
  $25M, a BJs fuel canopy, a $3.86M Discount Tire). Manatee, Charlotte and North Port CapDetail
  pages are login-gated by contrast.
- 2026-08-06 | swfl-permit-scanner | note | The Sarasota County Planning ddlGSPermitType dropdown
  has no option literally labeled "Conditional Use"; the value Planning/Conditional Use/NA/NA is
  labeled "Development Agreement/CDD" in the UI. The full working type list is exactly: Development
  Submittal, Rezone / Special Exception, General/Approved Plan Amendment, Development Agreement/CDD,
  Final Plat. There is no sixth type to search.

- 2026-08-06 | sck-project-scanner | blocker | The car condo cross-feed missed Hyper Club (Naples
  Racing Resort), a 542 acre Collier County motorsports conversion, purely because it had no
  motorsports keyword; the SWFL news scanner surfaced it on 2026-08-05 and it was staged manually
  on 2026-08-06. Cross-feed keywords are now broadened (motorsports, racing, race track, racing
  resort, motor club, car club, track club, paddock, parking, storage condo, garage villas, toy
  barn and more) and a two-stage screen decides staging: deeded/for-sale evidence stages normally,
  clearly public or leased product logs cross_feed_screened and is not staged, and high-prior
  unknown-ownership categories (motorsports, racing resorts, track developments) stage at medium
  with "verify deeded garage condo component before advancing" in scan_notes. A motorsports or
  track development is a car condo candidate until proven otherwise.
- 2026-08-06 | all routines | note | Nightly schedule reordered: the SWFL permit scanner runs 2:00
  AM and the SWFL news scanner 2:45 AM, both AHEAD of the car condo project scanner at 3:30 AM, so
  same-night SWFL rows are in scope for the cross-feed. The cross-feed window widened from 26 to 72
  hours to match, which also self-heals a missed night; re-staging is impossible because every hit
  still passes the Step 4 dedup gate.

- 2026-08-06 | swfl-permit-scanner | fixed | St. Pete and Charlotte recertified this session. ST.
  PETE: the 2026-08-03 "Tier 3 exhausted" conclusion was WRONG - the ArcGIS MultiFamily_Layer
  FeatureServer (services2.arcgis.com/9qPLjNtocjo438CJ, no auth) carries dated multifamily and
  affordable-housing site-plan ENTITLEMENTS and is now CERTIFIED-LOCAL. It does NOT cover building
  permits or any commercial, industrial, retail or self-storage project, so St. Pete commercial
  still runs as Tier 4 press substitution, and that substitution MUST log a portal_result row with
  tier press-substitute like Tarpon Springs, never a bare coverage_gap; the 2026-08-05 run logged a
  coverage_gap while five sibling towns got press substitutes, and that mismatch was the bug.
  Confirmed dead: Socrata stat.stpete.org is decommissioned, egis.stpete.org PermitsExternal is a
  frozen archive (max issue date 2021-12-20), DRC agenda PDFs are client-side rendered and Legistar
  is unprovisioned. CHARLOTTE: the date-range search WORKS again (14 day window returns 100+ rows)
  and the no-date fallback returns 100+ current rows, so both the 2026-07-22 and 2026-08-05 failures
  were transient, tied to the IP rate limit. Better still, the Pasco RecordId pattern transfers:
  each Charlotte grid row carries a hidden RecordId and an hlPermitNumber anchor that decode to an
  ANONYMOUS CapDetail.aspx exposing Construction Cost, Parcel, Job Description, Owner and unit
  counts. CRITICAL: CapDetail must be fetched with a plain Node fetch - loading it through the
  Playwright harness 302s to Error.aspx. Browser for the list, raw fetch for the detail. Pace
  requests 10-15s; this tenant rate-limits.

- 2026-08-08 | swfl-permit-scanner, swfl-news-scanner | note | "Est. Cost" is now written at INGEST
  and is authoritative: both scanners write a single explicit stated dollar figure (project cost,
  construction value, capitalization) as a plain number, and never estimate, derive or sum.
  Ambiguous or multiple figures stay prose-only with the column null, because a wrong number
  ranked confidently is worse than a null. TRANSITION: for 7 days from this date the report writer
  parses cost from prose for section 2 sorting, since rows created before the column exists carry
  cost only in text; after that window the column alone is authoritative.
- 2026-08-08 | cre-report-writer, sck-project-enrichment | blocker | "Developer Outreach - Drafts"
  is now PARTITIONED by the "Lane" column, default 'car-condo'. The enrichment queue filters every
  read and write to Lane 'car-condo'; the Monday Calusa lane writes only 'calusa-cre'. Neither may
  see, count, mark sent, or expire the other's rows. Without this partition the two queues share a
  table, and the enrichment sent-check would treat a Calusa draft as the occupied slot and refuse
  to draft a car condo developer all week, or expire it.
- 2026-08-08 | cre-report-writer | note | New Monday-only lane: after the report send, the report
  writer runs the Calusa CRE outreach lane per references/calusa-outreach-template.md, up to three
  Outlook drafts for the prior week's top NON car condo financing leads, positioning Will as an
  outsourced capital markets and underwriting arm. Selections also appear in the new Monday-only
  section 1c WEEKLY ROLLUP, which additionally carries 7 day totals, a 14 cluster-night coverage
  matrix, and the week's top 5 financeable items, and is written to the "Weekly Rollup" column
  (null on other days). Drafts are never sent; Will attaches the Calusa Financing Capabilities PDF
  himself. Section 6 also became movement-only in the same pass: numbered items are new entrants
  and changes measured against the prior "Top Opportunities" rows, with the standing pipeline
  compressed to one unnumbered line capped at five.

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
- 2026-08-04 | sck-project-enrichment | fix | The eight legacy outreach drafts created by the
  per-discovery drafter were backfilled with clean recipient addresses; developer Email fields
  often carry annotations and secondary addresses, so "Recipient Email" must hold a bare first
  valid address, preferring a named person over a generic inbox.
- 2026-08-04 | sck-project-enrichment | fix | The outreach queue sent-check now treats Status
  'draft' and 'queued' alike (most recent by "Queued At" then created_at) so legacy drafts
  cannot stall the rotation; unsent legacy drafts expire after 14 days rather than being
  deleted.
- 2026-08-04 | sck-project-enrichment | note | Developer rows contain unmerged duplicates
  (Harrod Properties, The Vault, ReVest, Storage Caves, Stables Motor Condos); outreach
  selection must match on normalized developer name and deduplicate first, or one developer
  gets drafted twice under variant records.
- 2026-08-08 | all-routines | constraint | Installed skills at /root/.claude/skills drift stale;
  the skill of record is ALWAYS the repo copy under .claude/skills on main. Read the repo copy
  directly at run start and ignore the Skill tool copy; if they differ, log a learning row.
- 2026-08-08 | sck-project-scanner | constraint | Dead sources as of 2026-08-08: bldup.com
  project pages and atlantamotorsportspark.com return HTTP 403, and onlygaragecondos.com
  per-project pages are paywalled. Skip all three without burning fetch budget; retry
  quarterly; log source_blocked when skipped.
- 2026-08-08 | sck-project-enrichment | constraint | Developer rows are created only after the
  normalized-name check against both developer tables; duplicates are retired, never deleted.
- 2026-08-08 | sck-project-enrichment | fix | The zero-new-developers trigger never fired
  because the scanner finds new developers nearly every night, so the outreach queue sat idle;
  outreach now runs every morning with new discoveries prioritized ahead of the backlog, and
  the market report rides as a public bucket link because the M365 connector cannot attach
  files.
- 2026-08-08 | sck-project-enrichment | fix | Per-discovery drafter retired; the Step 5b queue is
  the only outreach path.
- 2026-08-08 | all-routines | constraint | Key Amenities is a controlled vocabulary backed by
  "11 - Property - Amenity Definition"; skills never freestyle amenity text, and new types enter as
  proposed rows for Will to approve or kill.
- 2026-08-08 | all-routines | constraint | Amenity taxonomy tables renamed: "Amenity Type
  Definition" is now "11 - Property - Amenity Definition" and "Amenity Tier Definition" is now
  "11 - Property - Amenity Tier Definition". Two new property dimensions have their own tables,
  "11 - Property - Construction Materials" (Tilt Wall, Block, Metal, Wood-Frame, comma
  separated when mixed) and "11 - Property - Common Area Finish Level" (Luxury, High-Quality,
  Basic, Utility); construction and finish terms are no longer amenities and belong in those
  columns. Utility-level projects are excluded from comp sets by default.
- 2026-08-08 | all-routines | fix | The enrichment version self-check still named "TIDBIT MENU",
  a section retired with the per-discovery drafter, so the check would have logged a false
  SKILL-OUT-OF-DATE every night and trained everyone to ignore a real drift warning. Self-check
  markers now point at durable current headings: "Step 5b" for enrichment, "NORMALIZED
  DEVELOPER CHECK" for the scanner. When a section is retired, re-point any marker naming it in
  the same change.
