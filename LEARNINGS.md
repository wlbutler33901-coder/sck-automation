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
  ONLY permitted values are: scan, enrichment, digest, swfl_permit_scan, swfl_news_scan, swfl_report.
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

- 2026-08-10 | cre-report-writer | fixed | The Calusa Monday lane could silently produce fewer than
  three drafts: the old rule allowed ONE time-boxed lookup per candidate and skipped anyone whose
  email was not found, with no record that the candidate was ever considered. Now: research each
  candidate up to 5 minutes (Sunbiz, firm site, LinkedIn, press, pattern evidence) and continue
  down the ranking until 3 drafts exist or 10 candidates are exhausted; a strong lead with no
  VERIFIED address still gets a draft with To left EMPTY and its contact path named (phone, form,
  LinkedIn, PropStream parcel skip-trace), never a guessed address; and section 1c lists every
  candidate considered with its outcome (drafted, drafted-needs-address, skipped and why). Section
  1c item 4 in report-structure.md was reworded to match, since it still said to list only the
  three drafted, which would have re-hidden the skips this fix exists to expose.

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
- 2026-08-09 | sck-morning-digest | note | Unit reservation requests land in "08 - Unit
  Reservation Requests" and are alerted in real time by the Postgres trigger
  notify_on_unit_reservation, which POSTs each new row to the same Make webhook the digest
  uses. The digest therefore never alerts on fresh rows: its UNIT RESERVATIONS section recaps
  the last 24 hours, reports trailing 30/60/90 day counts per project, and flags any row still
  at Status 'New' after 24 hours as an SLA breach, promoted into WARNINGS.
- 2026-08-11 | outlook-outreach-drip | note | CAMPAIGN mode added as a third mode for the
  BMV-Owner-1 owner campaign. It runs last in each 5:15 run and only when the verification queue
  had nothing to draft, so 04d work always outranks marketing. Selection is 50 per morning from
  "04 - Unit Owner CRM" in fixed region order (South Florida, Tampa MSA, Southwest Florida,
  Central-East Florida, Jacksonville MSA, Orlando MSA), "Email 1" only, excluding Litigator rows,
  suppressed addresses, and anyone already in the ledger. Campaign drafts carry NO CC, which is a
  deliberate exception to the drip CC rule; the four line Calusa signature is also replaced by a
  three line Storage Condo King block.
- 2026-08-11 | outlook-outreach-drip | note | "04e - Campaign Sends" is the per-campaign ledger
  (Email, Campaign, Project, Unit, Region, Drafted At), unique on lower(Email) plus Campaign, so an
  address receives a given campaign exactly once. Write the ledger row only AFTER the draft exists;
  a failed draft must leave no row so the contact returns in tomorrow's batch. Unsubscribe replies
  go to "04a - Email Suppression" as Suppression Type 'Opt-Out', and the selection cross-check then
  excludes them permanently.
- 2026-08-11 | outlook-outreach-drip | blocker | Hosted-asset reachability gate is mandatory before
  the first campaign draft of any run: HEAD or ranged GET both the brochure and the report URL and
  require a 2xx or 206 with content type application/pdf. Supabase storage answers a missing object
  with a JSON not_found/NoSuchKey body, so a JSON content type is a failure even when the status
  line looks survivable. On failure draft nothing, write no ledger rows, and say which URL failed;
  50 emails with a dead download button is worse than a day's delay. As of this entry the public
  "Marketing Materials" bucket is EMPTY, so BMV_Marketing_Brochure_v2.pdf 404s and the gate blocks
  the campaign until that file is uploaded. The Q2 2026 report URL passes.
- 2026-08-13 | all-routines | constraint | FINISH SCALE. Luxury, High-Quality and Basic are the
  CAR CONDO range; most projects land High-Quality. Basic means bare bones car condo product,
  flex-grade quality in the personal storage and condo bucket. Utility applies to FLEX product
  only and pairs with Flex-Tier; a car condo is never Utility and a flex building is never
  Basic. Assign Basic on strong evidence of bare-bones car condo product; assign Utility only
  to genuine business or industrial flex. Vehicle Fortress (all phases) and Hideout Phase I
  were reclassified Basic on 2026-08-13, and Utility now marks flex only.
- 2026-08-12 | outlook-outreach-drip | fix | BMV-Owner-1 selection deduplicates on
  lower(btrim("Email 1")) BEFORE the 50 limit, so a run delivers 50 UNIQUE RECIPIENTS rather than
  50 CRM rows. Owners hold multiple units and a plain row limit collapsed 50 rows to 21 people on
  2026-08-12. Rank each owner's rows by unit number (digits stripped from "Unit #" cast to bigint,
  raw text as fallback) and keep the lowest, which supplies the unit named in the copy and the
  Project, Region and Unit written to the ledger; an owner spanning regions is worked once under
  their lowest-numbered unit. One draft and one ledger row per recipient, never per unit. Eligible
  population at this date: 823 rows collapsing to 658 unique recipients, about 14 mornings. Report
  people, not rows, or the runway reads long.
- 2026-08-12 | outlook-outreach-drip | note | Campaign body order now puts the bold "Storage Condo
  King Unit Benefits" heading and its five bullets ABOVE the signature, with the four line Calusa
  signature (Will Butler / Calusa Capital Partners / C: 239-898-5840 / E:
  will.butler@calusainvestments.com) as the last content block. Order: greeting, unit paragraph,
  unit link, comps paragraph, report link, Bonita paragraph, brochure link, "Happy to answer
  anything about unit values or about Bonita. Just reply.", benefits block, signature.
- 2026-08-12 | outlook-outreach-drip | constraint | The BMV campaign body carries NO UNSUBSCRIBE
  FOOTER. Will instructed this directly and repeated it; it is a standing decision, not an
  oversight, so never add one back and never flag it again. These are personal correspondence from
  a named person rather than a bulk send. Opt-outs are still honored in full: a recipient who
  replies asking out is written to "04a - Email Suppression" as Suppression Type 'Opt-Out' with
  Suppress true, and the campaign selection cross-check then excludes them permanently. With no
  footer prompting them, reply-watching in CAMPAIGN mode Step 6 is the entire opt-out mechanism, so
  act on every such reply.
- 2026-08-12 | outlook-outreach-drip | blocker | FONT CANNOT BE SET through the M365 connector.
  Both methods were tested on this date and BOTH were rejected on create AND on update: inline
  style (font-family Aptos, font-size 12pt) fails because style= is outside the outbound allowlist,
  and legacy <font face size> fails because font is named in the reject list with span and
  blockquote. Rejection is a hard VALIDATION_ERROR, not silent stripping, so any font attempt kills
  the outlook_create_draft call and would abort the morning batch. Drafts inherit Outlook's default
  HTML font; Aptos 12 must come from a mailbox or client setting instead. Do not retry either
  method.
- 2026-08-12 | outlook-outreach-drip | fix | The empty gap above the greeting was the default TOP
  MARGIN Outlook gives the first <p>, not stray whitespace in the body string. Campaign bodies now
  build blocks with <div> and space them with <div><br></div>, which removes the gap and keeps
  paragraph spacing; the body string starts flush at the greeting div. Graph prepends its own \r\n
  to stored content (confirmed by reading a draft back), which is inert HTML whitespace and renders
  nothing, so do not chase it.
- 2026-08-13 | outlook-outreach-drip | note | The BMV campaign Bonita section now sells rather
  than dumping specs: it pulls "Founding Cap", "Units Committed", "# of Units", "Asking $ PSF",
  "Ground Breaking" and "Developer Listing Comments" live from "06 - Pre-Sales" every run,
  states positions remaining as Founding Cap minus Units Committed, and omits the scarcity
  sentence entirely (noting it in the run report) when either field is null. The body links the
  project listing page instead of the brochure, the brochure is no longer gated, and the
  reachability gate now covers the Q2 report PDF plus a 2xx check on the listing URL.
- 2026-08-13 | outlook-outreach-drip | constraint | CAMPAIGN mode Step 4 is now the COMPLETE COPY
  SPECIFICATION for the BMV owner campaign and every future edit must preserve every item in it.
  Several rounds of approved changes were lost by editing one line in isolation, so when changing
  one item, re-read the whole block and carry the rest forward. The spec is: one fixed subject
  "Your unit at {Project} and a first look at Bonita Motor Vault" with an explicit guard against
  the DRAFT-mode three-subject rotation; CC chance.friedman@calusainvestments.com on EVERY campaign
  draft (the old no-CC exception is removed); NEVER assert ownership, the unit is described as
  carrying a market value on the platform and never as the recipient's property; greeting "Hi
  {First Name}," or exactly "Hello," when no first name; the Bonita section sells and reads
  Founding Cap, Units Committed, # of Units, Asking $ PSF, Ground Breaking and Developer Listing
  Comments live from "06 - Pre-Sales" each run, omitting the scarcity sentence when either scarcity
  field is null; the listing link replaces the brochure link and the brochure is no longer linked
  or gated; five benefits bullets each with a bold lead-in header above the signature; the four
  line Calusa signature LAST; no unsubscribe footer; 50 unique recipients deduplicated on
  lower(btrim("Email 1")) before the cap with the owner's lowest unit; div spacing and no font
  styling.
- 2026-08-13 | outlook-outreach-drip | blocker | A 5:15 run applied the DRAFT-mode three-subject
  rotation to CAMPAIGN mode and 43 of 50 drafts went out titled "{Project} resale values" or "Quick
  question about your unit at {Project}" instead of the campaign subject; all 43 were corrected by
  hand. The bodies were correct, so the failure was subject-only and easy to miss. The subject
  guard now lives in Step 4 and in Hard rules. Campaign gate assets are the report PDF (2xx or 206
  with content type application/pdf) and the listing page (any 2xx, no content type test); both
  passed on this date.
- 2026-08-15 | outlook-outreach-drip | constraint | FONT STYLING IS CONFIRMED IMPOSSIBLE AND NO RUN
  MAY EVER ATTEMPT IT. The M365 connector allowlist (p, br, a, b/strong, i/em, ul/ol/li, h1-h6,
  table, code, pre, hr, div, strike) has no styling hook at all: inline style= and the legacy
  <font> tag are both rejected outright on create AND on update, and rejection is a hard
  VALIDATION_ERROR that kills the whole draft call, so one attempt would abort a morning batch. Do
  not re-test either method and do not hunt for a third. Drafts inherit Outlook's default HTML font;
  Aptos 12 must come from a mailbox or client setting. Any lingering instruction to try font
  styling is an error and should be deleted on sight.
- 2026-08-15 | outlook-outreach-drip | constraint | The BMV campaign Bonita section is PRICING LED
  and carries NO HARDCODED FIGURES. Every dollar, PSF, percent and count is read live per CAMPAIGN
  Step 2: asking PSF, appraised PSF and unit size from "06 - Pre-Sales", asking price / market value
  / dollar discount DERIVED as PSF times unit size, and submarket annual growth plus trailing twelve
  month sales count and median PSF from the get_presale_appraisal_data RPC under project_context
  (the last two nested in region_kpis). Founding Cap, Units Committed, # of Units, Ground Breaking
  and Developer Listing Comments come from "06 - Pre-Sales". ROUNDING MATTERS: floor every dollar
  figure to the nearest $1,000 and compute the discount percent from unrounded values to one
  decimal. "Appraised $ / SF" is stored already rounded, so rounding derived dollars up overstates
  the equity and drifts off the published valuation; flooring reconciles to the listing page and is
  conservative for a discount claim. Verified this date: $480 and $597 PSF on 1,125 SF gives
  $540,000 asking, $671,000 value, $131,000 discount, 19.6 percent, matching the appraisal. If any
  figure is null, omit its sentence and note it in the run report.
- 2026-08-15 | outlook-outreach-drip | note | Campaign body now opens warm before it opens with
  data: greeting, then a summer-pleasantry and one line on what Storage Condo King is and why Will
  is writing, then the unit line. The no-ownership rule covers the new blocks too; nothing in the
  body may say the recipient owns anything.
- 2026-08-16 | outlook-outreach-drip | change | BMV campaign body restructured to FOUR BLOCKS and
  cut materially shorter. Block 1 intro and unit value: greeting, the summer warm opener and the
  platform sentence as two separate paragraphs, ONE personalized unit value sentence, then the unit
  link. Block 2 Bonita: the whole two-paragraph section collapsed to ONE paragraph carrying ask,
  ask PSF, valuation, day one equity and discount percent, ending with the reply ask, then the
  listing link. Block 3 benefits unchanged except the Verified Sale Comps bullet now ends "plus
  quarterly Florida market reports". Block 4 signature, then the P.S. AFTER it. Deleted outright:
  the standalone comps paragraph (redundant with the benefits list), the market report paragraph
  and its download link, the Bonita specs paragraph (buildings released, ceilings, construction,
  flood zone; the listing page carries it), the standalone "Take a look at the listing" line and the
  standalone closing line. The report PDF also came OUT of the Step 1 reachability gate; the Bonita
  listing URL is now the only gated asset, so a bad report URL can no longer block a morning.
- 2026-08-16 | outlook-outreach-drip | rule | POSITIVE CHANGE ONLY in the unit value sentence.
  Priority: (a) value plus a comparison to the most recent recorded sale, but ONLY when the change
  is positive AND at least $25,000; (b) value alone, followed by the submarket compounding sentence
  when growth is available; (c) the submarket sentence alone; omit the sentence entirely if none
  resolve. Never state a decline, never state a change of zero, never compare when the gain is
  under $25,000. Rationale: roughly half these owners currently sit BELOW their last recorded sale
  price, and a mass email telling an owner their unit is worth less than they paid is unrecoverable;
  the $25,000 floor also kills near-flat comparisons, which read as a bad investment even when the
  sign is positive. Sourcing: unit value is "Suite Size (SF)" times "Appraised $ / SF" from
  "02 - Units"; the prior sale is the most recent row in "03 - Sales" matched on "Project Name" plus
  "Unit". "Sale Date" is TEXT in mixed formats (1,525 rows M/D/YY, 186 M/D/YYYY as of this date), so
  parse with a three branch CASE and drop anything unparseable. Some units carry DUPLICATE sale
  rows, so dedupe on date and price before selecting the latest. Value and increase round to the
  nearest thousand (NOT the Bonita floor rule, which exists only to reconcile to a published listing
  page). Submarket growth is "Region Definition".psf_growth_5yr_ann_pct matched on the FULL stored
  submarket value; NEVER substitute psf_growth_1yr_pct, which is volatile and frequently negative
  (Naples; Bonita Springs is -3.8 today). Most submarkets are null there, including Tampa; Brandon,
  so omitting the submarket sentence is the normal case. Label the submarket with the text before
  the first semicolon: the stored value is a pair like "Tampa; Brandon" and reads wrong in a
  sentence.
- 2026-08-16 | outlook-outreach-drip | rule | The campaign P.S. carries THREE conditions checked
  from live data every run, never assumed. (1) The "fully refundable deposit" clause ships only when
  "06 - Pre-Sales"."Deposit Refundable" confirms it; that field is NULL for Bonita Motor Vault
  today, so the clause and the "no cost to reserving" phrase are currently DROPPED and the sentence
  ends after "before the rest of the release opens." It is a contractual claim and is never shipped
  on a guess. (2) "breaks ground shortly" and "measured in weeks" ship only when "Ground Breaking"
  resolves to within 90 days of the run date; the value is TEXT, so resolve a quarter string to the
  END of that quarter (Q3 2026 to 2026-09-30, which is inside 90 days today, so the urgency wording
  ships). Further out, state the groundbreaking value plainly instead; null, "Delivered" or
  unparseable, omit the first sentence entirely. (3) NEVER characterize how much has sold: no
  "majority sold", "nearly gone", "filling fast", and no position counts, because the live record
  shows the founding program at cap 10 with 5 committed, so any stronger claim would be false.
  Urgency comes only from the groundbreaking deadline and the founding pricing close.
