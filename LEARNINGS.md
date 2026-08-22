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
  ONLY permitted values are: scan, enrichment, digest, swfl_permit_scan, swfl_news_scan,
  swfl_report, outreach. AMENDED 2026-08-22: 'outreach' was missing from this list while the
  Outlook drips had been writing it consistently since 2026-08-11 (15 rows), which three separate
  runs flagged and none could fix, because an unattended run cannot edit this file. It is now
  permitted and is the correct value for both outlook-unit-owner-drip and outlook-developer-drip.
  Adding a value here does NOT add it to the digest's SEEN_SCOPE, which is a separate editorial
  decision, and never needs to: the learnings FOLD_SCOPE is default-open and takes every run type
  automatically.
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
- 2026-08-17 | outlook-outreach-drip | change | BMV campaign body refined again. NEW SUBJECT:
  "Your {Project} unit value, plus founding pricing at Bonita Motor Vault", with a leading "The "
  stripped from the project name in the SUBJECT ONLY so the possessive reads naturally ("Your Motor
  Enclave unit value"); in-body references keep the full stored name. OPENING MERGED: the greeting
  stays its own block, and the warm opener, the platform sentence and the personalized unit value
  sentence now run together as ONE paragraph instead of four stacked short ones, which read as a
  form letter. LINK ARROWS: both anchors end with a space and the unicode right arrow, ordinary text
  inside the anchor, which survives the connector allowlist; never "->" and never an entity or
  styling. BONITA gained ONE sentence between the pricing sentence and the reply ask, carrying
  release counts from "Developer Listing Comments" plus clear height, mezzanine, construction and
  flood zone from "01 - Projects"."Key Amenities", "Construction Materials" and "Flood Zone". Those
  stored values are CATALOG LABELS for the platform UI, so render them as plain prose ("18'+ Clear
  Heights" to "clear heights over 18 feet", "Mezzanine Capabilities" to "mezzanines", "Block" to
  "block construction") and never paste a canonical label into copy. This is one sentence, not the
  deleted specs paragraph returning. P.S. cut to two sentences.
- 2026-08-17 | outlook-outreach-drip | rule | Trailing-year market color extends the submarket
  sentence only: "with {n} units trading in the trailing year at a {$median} per square foot
  median." SOURCE IS "Region Definition" (unit_sales_ttm, median_psf_ttm), the same row that
  supplies psf_growth_5yr_ann_pct, so growth, count and median are internally consistent.
  get_market_segmentation_v2 was evaluated and REJECTED for this clause: it exposes avg_psf only,
  with no median at all, and its rolling window returns a different count (42 versus 44 for
  Tampa; Brandon), so mixing sources would print a count and a median that disagree. The clause is
  additive and hangs off the compounding sentence, so a null growth figure drops the color with it.
  CONSEQUENCE worth knowing: psf_growth_5yr_ann_pct is null for most submarkets including
  Tampa; Brandon, so the entire submarket sentence, color included, does not ship for The Motor
  Enclave owners even though the count and median exist. The median is a PSF median, not a price,
  and the copy says "per square foot median" so it can never be read as a median sale price.
- 2026-08-17 | outlook-outreach-drip | rule | Shorter P.S., two sentences: "Founding pricing closes
  when Bonita breaks ground, which is {weeks away | on {Ground Breaking}}. The listing link above is
  the fastest way to lock the current ask and pick your unit." Conditions carry forward unchanged:
  "weeks away" only when "Ground Breaking" resolves to within 90 days (Q3 2026 resolves to
  2026-09-30, inside the window today), otherwise state the value; the refundable deposit claim
  returns only if "Deposit Refundable" confirms it, and that field is still NULL for Bonita Motor
  Vault so the clause stays absent; never characterize how much has sold. The deeded unit counts in
  the new Block 2 specs sentence describe the RELEASE, not sell-through, and are the only counts
  permitted anywhere in the body.
- 2026-08-17 | outlook-outreach-drip | data | "02 - Units" "Unit #" is NOT unique per project. Hideout
  Storage Park (Phase I) holds 38 unit rows collapsing to only 10 distinct "Unit #" values: units 1
  through 7 each carry FIVE rows with genuinely different sizes (501 to 1,555 SF) and different
  appraised PSF, so a join on Project plus Unit # fans out and no row can be defended as "their"
  unit. Every other project in this batch is clean (Bonita Breeze 25/25, Car Collective 10/10,
  Classic Ultra Tamiami Trail 24/24, The Motor Enclave 238/238). HANDLING: when the (Project,
  Unit #) join returns more than one row, do NOT pick one. Treat the unit value as unavailable, fall
  to the submarket variant, and report it. The 5:15 run independently reached the same outcome for
  these 8 recipients, which is the rule working. FIX BELONGS UPSTREAM: Hideout needs a building or
  phase qualifier on "Unit #", or a deduplication pass, before its owners can receive unit level
  numbers. Until then any campaign touching Hideout ships submarket color only.

## Fold of 2026-08-16 to 2026-08-22 Scan Activity Log learning rows (interactive session 2026-08-22)

Folded 57 rows: the 14 still pending plus the 43 dated 2026-08-16 to 2026-08-20 that earlier
digest runs marked digested without ever writing them here, because an unattended cloud run
cannot push. See the 2026-08-21 digest blocker below, which is the entry that caught it.

- 2026-08-22 | repo | SKILL RENAME | outlook-outreach-drip is now outlook-unit-owner-drip, and
  developer outreach split out into the new outlook-developer-drip skill. Every LEARNINGS entry
  tagged outlook-outreach-drip predates the split, is the unit owner skill's history, and still
  binds; the developer skill also reads them where they touch developer outreach. Historical
  entries are NOT rewritten, because this file is an append-only record of what was true when it
  was written.
- 2026-08-16 | sck-project-scanner | Cape Fear deeded boat slip false positive recurs | New Hanover
  County has genuine DEEDED dry-stack boat slip inventory (Inlet Watch, Wrightsville Yacht Club,
  Bradley Creek Boatominium) that surfaces on any deeded plus storage query and is NOT garage
  condo product. Pre-empt it rather than re-screening it every pass.
- 2026-08-16 | sck-project-scanner | onlygaragecondos.com state indexes fetch, detail pages do not |
  Narrowed the 2026-08-08 dead-source line. SUPERSEDED 2026-08-22: the site is now barred as a
  source of truth entirely, see the SOURCE TRUST rule. It may still contribute discovery signals.
- 2026-08-16 | sck-project-scanner | Source health | vaultmotorcondos.com/pages/our-locations 404s,
  so The Vault pipeline cannot be enumerated there; the real page is whythevault.com/locations/.
  DNS ENOTFOUND on lakesidestoragesuites.com and alicoitec.com.
- 2026-08-16 | sck-project-scanner | Dedup signal 5 contradicts the search playbook | Same
  developer in the same county blocked a genuine second location. RESOLVED 2026-08-22: signal 5 is
  now a FLAG, never a BLOCK, unless an address, parcel or distinctive-name collision also fires.
- 2026-08-16 | all routines | Supabase MCP reported 23505 on an INSERT that had already committed |
  All three rows existed with identical created_at. NEVER treat a duplicate-key error from this
  tool as proof the write failed. Re-read before retrying.
- 2026-08-16 | sck-project-scanner | Motor Vault removed both Georgia project pages | Deliberate
  removal, not link rot: gone from a sitemap regenerated 2026-07-09. Shelved or hidden is not
  determinable from the site.
- 2026-08-16 | sck-project-scanner | Brand-name collisions are the top dedup risk | Five unrelated
  firms share near-identical names (Motor Vault Phoenix, The Vault, Naples Auto Vault, Bonita
  Motor Vault, AUTO VAULT Fort Lauderdale). The token rule cannot resolve them alone.
- 2026-08-16 | sck-project-scanner | Sunday brand sweep source map corrections | CollectionSuites
  is collection-suites.com WITH the hyphen; the unhyphenated domain 301s to a Hilton page.
- 2026-08-16 | sck-project-enrichment | Distinctive-token rule strips product words but not the
  city | In metros that name projects after the city, every staged row reduces to the bare city
  token and collides. Collier produced a 3-way false positive.
- 2026-08-17 | sck-project-scanner | therealdeal.com 403s on direct WebFetch | Recoverable via
  search snippets, Commercial Observer or GlobeNewswire mirrors. Add to the standing blocked list.
- 2026-08-17 | sck-project-scanner | Step 2 region context hides cross-filed projects | Filtering
  on the scheduled region label hid three Atlanta MSA candidates filed under North Georgia and
  cost a full region pass. Load neighbouring regions too.
- 2026-08-17 | sck-project-scanner | Trigger trg_auto_stage_developer auto-creates the developer
  row | The Step 5 instruction to also insert one produces a near-duplicate pair whenever the
  manual string differs at all. Confirmed again 2026-08-22: never insert the developer row.
- 2026-08-17 | sck-project-scanner | Planning agendas are PDF-only and not full-text indexed |
  Keyword sweeps return nothing and read falsely as an empty market. Confirmed across eight SC and
  NC counties. Crawl the PDFs directly or stop counting the sweep as coverage.
- 2026-08-17 | sck-project-scanner | Raleigh-Durham is genuine white space, not a coverage gap |
  Zero for-sale garage condo product across 10 counties, corroborated two ways.
- 2026-08-17 | sck-project-enrichment | Writing "Developer" auto-creates the card from that exact
  string | Any qualifier embedded in the value becomes the card NAME, and the table carries a
  unique index on the normalized name. Keep "Developer" to the clean entity name; caveats go to
  scan_notes.
- 2026-08-17 | sck-project-enrichment | Sales Broker never-null rule conflicts with hard rule 5 on
  entitlement-stage rows | Lambert Place has no published applicant or marketing, so
  Developer-Direct would assert a sales channel nobody established. Leave null and log the gap.
- 2026-08-17 | sck-project-enrichment | Sent-check must search by RECIPIENT, not by date paging |
  A folder plus date search returned 61 messages and the confirming one was not in the newest 25,
  so a first-page check would have wrongly declared the queue occupied.
- 2026-08-17 | sck-morning-digest | Fold-versus-push conflict | Skill said fold and push, the
  contract forbids unattended pushes. See the 2026-08-21 blocker for the consequence and the
  2026-08-22 resolution.
- 2026-08-18 | sck-project-scanner | Melbourne; Space Coast holds zero live and zero staged rows |
  Real market gap on current evidence, not a search failure. Drop to a lighter pass if it repeats.
- 2026-08-18 | sck-project-scanner | Myrtle Beach Speedway closed in August 2020 | Dead lead for
  the track-anchored sweep. Darlington is the live anchor but publishes no trackside real estate
  program. Stop spending repeat queries on either.
- 2026-08-18 | sck-project-scanner | A wrong stored address silently disables a dedup signal |
  Indian River MotorHaus 3.0 stores 7443 US Hwy 1 while press gives 7420 U.S. 1; the token signal
  caught the rediscovery the address signal missed. Never rely on address alone.
- 2026-08-18 | sck-project-enrichment | change_type has drifted to 58 distinct values | Any
  change_type grouping in the digest is unreliable. Confirmed worse 2026-08-20 at 59 values, 30 of
  them used exactly once. Hard-code the vocabulary the way run_type was hard-coded.
- 2026-08-18 | sck-project-enrichment | WebFetch silently mistranscribed a mailto address |
  Reported Richard@re-invest.net where the raw markup says Richard@re-vest.net, and both domains
  resolve. NEVER overwrite a stored email or website on a WebFetch summary alone; confirm against
  raw markup first.
- 2026-08-18 | sck-project-enrichment | Census geocoder NO MATCH on new or private industrial
  streets | Five addresses failed under both benchmarks while a control matched. A NO MATCH there
  is TIGER coverage, not a bad address. See the 2026-08-22 geocoding rule.
- 2026-08-18 | sck-morning-digest | Fold conflict resolved toward pushing | The scheduled task
  carried a designated feature branch, an authorized push target. SUPERSEDED: the 2026-08-21
  blocker shows the fold still did not land.
- 2026-08-18 | sck-project-enrichment | Outreach queue selected a BROKER for a developer intro and
  Will deleted the draft | Staged id 80 Coral International Realty (Robert Zinzell) was built to
  the broker-fallback rung of the source ladder, which completes a card but does not make the row
  a developer. Selection must check HOW the card was sourced.
- 2026-08-19 | sck-project-enrichment | "05 - Developers" held a 52 row byte-identical duplicate
  block | Rows #148-#199 duplicated #96-#147 from a promotion job that ran twice. RESOLVED
  2026-08-22: live merged 198 rows to 143, 55 identical copies removed.
- 2026-08-19 | sck-project-enrichment | The 14 day expiry on unsent legacy drafts does real work |
  A morning's only selection existed because a 2026-08-04 draft expired and returned that
  developer to the rotation. Keep it.
- 2026-08-19 | sck-project-enrichment | Bulk-retiring against a polluted live table is destructive |
  42 of 44 active staged rows matched live purely because of the duplicate block. Sanity check the
  live match set for duplication BEFORE bulk-retiring.
- 2026-08-19 | sck-project-enrichment | Staged rows carry statuses the live vocabulary lacks | 37
  active rows on "Planned" or "Stalled" against a live vocabulary of Pre-Development, Developer
  Sale, Under Construction, Completed, Dead. They fall out of every rollup that groups by it.
- 2026-08-19 | sck-project-enrichment | Census worked, Nominatim returned zero through the proxy |
  CONTRADICTED on 2026-08-21 (both failing) and 2026-08-22 (Census failing, Nominatim exact). The
  services are not stably ranked from this sandbox; log which one answered, every run.
- 2026-08-19 | sck-project-enrichment | Bot gating is now the dominant cause of broker card gaps |
  sarasotawarehouses.com and saulscre.com answer with an HTTP 202 challenge stub, showcase.com
  403s, islandbreezerealestate.com returns a 114 byte shell. Recover from the developer project
  site instead.
- 2026-08-20 | all routines | "Scan Activity Log" timestamps live in ts, NOT created_at | Neither
  project table exposes an id column. Naming created_at on the log or id on a project table dies
  with 42703 and costs a retry. Confirmed again 2026-08-21 and 2026-08-22.
- 2026-08-20 | sck-project-enrichment | islandbreezerealestate.com is a PARKED domain | The rick@
  mailbox on it is the live published project contact, so its Website gap is structural.
  islandbreezerealty.com is a DIFFERENT firm and must never be attached to it.
- 2026-08-20 | sck-project-enrichment | The developer corporate site is not always the top rung |
  AR Coleman publishes no contact detail while the PROJECT site garageslakeoconee.com credits the
  developer and publishes the agent and both phone numbers. Read the project site too.
- 2026-08-20 | sck-project-enrichment | Two fetch traps | custombuildersfl.com serves an invalid
  self-signed cert over https and 200s over plain http, so the stored http:// URL is correct and
  must never be upgraded. toyvaultfortmyers.com DNS-fails in WebFetch but 200s to a browser-UA
  curl.
- 2026-08-20 | sck-project-enrichment | Live "05 - Developers" is a promoted MIRROR of the staging
  table, not an independent directory | Applied literally, Step 4c/4d would retire the entire
  active queue. RESOLVED 2026-08-22 by the live merge plus the Step 6b promotion lifecycle rule.
- 2026-08-20 | sck-project-enrichment | An unmerged skill update deploys nothing | A developer
  intro was queued to Robert Zinzell, a BROKER already in live "08 - Brokers" #52, because the
  known-contact cross-reference existed only in an unmerged edit. Merge before relying on a rule.
- 2026-08-21 | sck-project-scanner | jaxdailyrecord.com is paywalled past the headline | Search
  snippets still carry name, address, square footage and job cost. Snippet-recoverable, not
  blocked; do not burn fetch budget.
- 2026-08-21 | sck-project-enrichment | Backlog outreach selection needs a RECIPIENT-QUALITY gate |
  The Pre-Development and Under Construction Florida tier is fully contacted, so selection falls
  to tiers where the blocker is address quality rather than project status.
- 2026-08-21 | sck-project-enrichment | WebFetch returns an EMPTY DOCUMENT, not an error, on
  JS-rendered sites | Reads like "no contact published" and silently costs fills. Retry with curl
  plus a mailto and tel regex before recording a gap.
- 2026-08-21 | sck-project-enrichment | The broker guard can fire on a live-table DATA ERROR |
  Florida Garage Condos of Englewood was blocked because its own developer-domain address appears
  on a live "08 - Brokers" row for a DIFFERENT firm. Verify the match before trusting the guard.
- 2026-08-21 | sck-project-enrichment | Street-level geocoding unavailable from the sandbox |
  Both services returned nothing at street level this date. See the 2026-08-22 rule; this is why
  the preference is a preference and the run logs which service answered.
- 2026-08-21 | sck-morning-digest | THE FOLD HAS BEEN SILENTLY DROPPING ROWS | 42 rows dated
  2026-08-16 to 2026-08-20 were marked digested by prior runs while the repo file's newest entry
  was still 2026-08-17, because "fold then mark digested" writes the mark even when the push is
  forbidden. RESOLVED 2026-08-22: this session re-folded them. RULE: never set digested_at unless
  the fold actually landed in the committed file.
- 2026-08-22 | sck-project-scanner | The scanner must NEVER insert the developer row | The trigger
  auto-stages it; the manual insert collides with developers_new_name_uidx and hard-fails even
  when the developer is genuinely new.
- 2026-08-22 | sck-project-scanner | Storage Caves Concord II wrongly blocked | 2350 versus 2400
  Derita Rd, 140 versus 56 units, plainly two buildings. RESOLVED this session: same developer in
  the same county is a FLAG, never a BLOCK, absent an address, parcel or distinctive-name
  collision. It should stage cleanly on the next pass.
- 2026-08-22 | sck-project-scanner | "01 - Project - New" has NO id column | INSERT ... RETURNING
  id fails with 42703 and aborts the whole statement before anything is written. Return a natural
  key instead.
- 2026-08-22 | sck-project-enrichment | NC Secretary of State search now 403s behind Cloudflare |
  Same failure mode already on file for FL Sunbiz. Use press, mirrors and license lookups instead.
- 2026-08-22 | sck-project-enrichment | The sent-check had no branch for a DELETED draft | A draft
  Will deletes is absent from Sent Items forever, so the queued row never clears and the rotation
  stalls silently. Found with row id 28 (Ultimate Garages Naples). RESOLVED this session: a queued
  draft found in Deleted Items is marked 'declined - draft deleted in Outlook' and frees the
  rotation. A deletion is a decision, not an error state.
- 2026-08-22 | sck-project-enrichment | Census unusable from the container, Nominatim exact |
  Census returned NO MATCH for every address tried, including one Nominatim resolved to an exact
  house number. Nominatim needs a descriptive User-Agent. Record whether the hit was a house
  number or a street centroid: a centroid silently feeding radius work is the real hazard.
- 2026-08-22 | sck-project-enrichment | Address-collision check missed a real duplicate | It
  normalizes punctuation and case but NOT street-type abbreviations, so "3100 Fickling Hill Rd"
  and "3100 Fickling Hill Road" did not join and the Charleston Toy Box versus Motor District
  Johns Island pair was caught by hand. RESOLVED this session: Rd/Road, St/Street, Dr/Drive,
  Ln/Lane, Blvd/Boulevard, Hwy/Highway and directionals are expanded in both the scanner and
  enrichment address checks, which must stay identical.
- 2026-08-22 | onlygaragecondos.com | NEVER A SOURCE OF TRUTH | Largely AI-generated. Discovery
  signals only; every fact it suggests (status, delivery, pricing, unit counts) needs independent
  corroboration before entering any field, and corroborated-NEGATIVE claims may not rest on it
  either. Known failure: it reported Motocave in pre-sales when the project delivered in 2014.
- 2026-08-22 | sck-project-enrichment | Duplication warning retired | Live merged 198 rows to 143,
  55 byte-identical copies removed; staged queue gated to 7 pending. STOP re-raising the 40
  percent duplication warning. The only remaining known issue is 25 same-name live rows with
  differing payloads awaiting a field-level merge, which is a human decision and never an
  auto-merge.
- 2026-08-22 | repo | LEARNINGS FOLD SCOPE GAP, RESOLVED later the same day by splitting the list
  into FOLD_SCOPE (default-open, no run_type filter) and SEEN_SCOPE (unchanged, non-learning rows
  only), and folding all 126 orphans. The original finding is kept below as written. | The digest folded and marked digested
  only run_type IN ('scan','enrichment','digest','nightly_scan','project_scan'). Learning rows
  written under swfl_news_scan, swfl_permit_scan, swfl_report and outreach are therefore NEVER
  folded and never marked: 126 such rows were pending as of this session, the oldest from
  2026-08-05. Those routines' lessons are not reaching this file. Either widen the digest's
  run_type list or give those routines their own fold step. Flagged, not fixed, because widening
  that list also changes what the digest marks digested for non-learning rows.

## Fold of the 126 orphaned learning rows, 2026-08-05 to 2026-08-22 (interactive session 2026-08-22)

These rows were written correctly by swfl_permit_scan (51), swfl_news_scan (36), swfl_report (24)
and outreach (15), and were never folded because every one of those run types sat outside the
digest's single shared run_type IN list. Oldest 2026-08-05. FOLD_SCOPE is now default-open so this
cannot recur; see the regression note in sck-morning-digest.

Rows that were superseded by a later row are folded as one entry ending in the resolution, rather
than as a contradictory pair, and the supersession is named. Repeat observations of the same
source outage are folded once with the confirming dates.

### swfl-permit-scanner - portal recipes and platform behavior

- 2026-08-22 | swfl-permit-scanner | TYLER ENERGOV, the settled recipe | Capture the verbatim
  /search/search body ONCE from the SPA by network interception, then reuse it: the body is TENANT
  AGNOSTIC and works unchanged against another tenant by swapping the host and tenant header
  (proved Zephyrhills to New Port Richey). SearchModule 1 with FilterModule 2 is the correct pair
  for every /apps/selfservice tenant INCLUDING Hernando, which supersedes the 2026-08-07 Hernando
  note claiming SearchModule 2 / FilterModule 1. Paging and sorting are TOP LEVEL and PageNumber
  is ONE BASED: PageNumber 0 returns HTTP 200 with Success false and a null Result, which reads
  like zero rows but is a rejected request. SortBy and SortAscending must be set at top level as
  well as inside PermitCriteria or the response is oldest-first junk. To trigger the capture,
  loading /apps/selfservice/#/search and clicking the element reading Search does NOT fire the
  XHR; drive the Angular form the way the 2026-08-21 run documents.
- 2026-08-22 | swfl-permit-scanner | ACCELA, the settled recipe | The Pasco and Charlotte
  RecordId-to-CapDetail pattern TRANSFERS across tenants: each grid row carries a hidden RecordId
  input that decodes to an anonymous CapDetail.aspx with the tenant agencyCode. Confirmed for City
  of Tampa, City of North Port (overturning two prior notes that it needed auth) and Manatee County
  (overturning the playbook row saying CapDetail exposes no valuation, SF or parcel publicly).
  Date filters need the PAIRED _ext_ClientState hidden input set, not just .value, which is why
  the 2026-08-11 Pinellas run wrongly concluded server side date filtering was unavailable.
  Search and pager CLICKS are intercepted by iframe.mask_iframe inside div#divGlobalLoadingMask;
  dismiss or bypass the mask rather than retrying the click.
- 2026-08-22 | swfl-permit-scanner | Charlotte County Accela caps EVERY result set at 101 rows |
  Regardless of window width, so a documented 14 day pull silently covered ONE DAY: an 08/05 to
  08/19 window returned exactly 101 rows all dated 08/18. Any portal that returns a suspiciously
  round row count is capping, not reporting. Window narrowly and stitch.
- 2026-08-22 | swfl-permit-scanner | Pasco Accela pages 10 rows at a time | A 5 page loop cap
  silently truncated a 62 row Commercial New result to 50 and dropped the OLDEST four days of the
  window. Caught only because the COMNEW number series was checked for continuity. Check number
  series continuity, do not trust the page loop.
- 2026-08-22 | swfl-permit-scanner | Pasco CapDetail exposes TWO Job Value figures that disagree |
  Header Job Value versus a second inside Application Information (Lowes 14734414.08 vs 12000000).
  Also, 26EST RecordIds on 26TMP DRAFT rows decode to anonymous CapDetail exactly like issued
  rows, and drafts carry the RICHEST data in the feed. Do not skip drafts.
- 2026-08-22 | swfl-permit-scanner | eTRAKiT (City of Venice) | No date search field exists; use
  SearchBy=Permit Number with Operator=At Least and the first permit number of the target window.
  The 300 row cap is SELF PROVING because At Least is a lexicographic compare, so a BLD26 pull runs
  out of BLD26 rows and spills into legacy EBLD and ENG prefixes, which removes any need to bisect
  the start point precisely. The RECORDID column is CSS display:none on its header but still
  returns cell text via innerText, format ECON:YYMMDDHHMMSSmmm, a true creation timestamp.
- 2026-08-22 | swfl-permit-scanner | SmartGov (Granicus) recipe is BROKEN on build v2026.13.1 |
  /Public/PermitSearch still returns 200 but the hidden __submitFormValidator__ input the POST
  requires is gone from the served HTML. Separately, its free-text box returns zero rows for every
  broad token tried despite valid AJAX round trips, so a zero there is not evidence of an empty
  market.
- 2026-08-22 | swfl-permit-scanner | Periodic-report portals need a REPORT-SCOPED window, not 14
  days | Collier publishes one monthly XLSX about a week into the following month and then it does
  not change; a 14 day lookback silently discards most of it. collier.gov sits behind an Akamai
  edge filter that 403s plain curl and WebFetch on both the index and the XLSX, and passes with a
  Node fetch carrying a FULL browser header set.
- 2026-08-22 | swfl-permit-scanner | Fort Myers report index moved to /2377/2026-Statistical-Reports
  | About ten reports post roughly three days into the following month. The New Projects Report is
  APPLICATIONS RECEIVED, not permits issued, and its PDF has a summary count table near the top
  with no addresses plus a full itemized listing further down. Read the itemized section.
- 2026-08-22 | swfl-permit-scanner | Lee County DCD CurrentMonth weekly feed served STALE content |
  The slot that should have covered 8/9 to 8/15 served 7/12 to 7/18, confirmed by HTTP
  Last-Modified. Check Last-Modified against the claimed fold, never trust the slot name.
- 2026-08-22 | swfl-permit-scanner | Manatee weekly PDF feed stopped publishing after 2026-08-03 |
  The mymanatee.org Weekly Project List certified as a new Tier 3 source on 2026-08-15 went dark
  within a fortnight. Manatee is now covered through Accela CapDetail instead.
- 2026-08-22 | swfl-permit-scanner | Sarasota County | Planning ddlGSPermitType is larger than the
  five types on file; Community Development Amendment Request and Construction Submittal also carry
  CRE. Three record types (General Plan Amendment, Development Agreement/CDD, Final Plat) fail on
  every search submit and reset to blank. No working anonymous parcel lookup was found, so Sarasota
  rows carry a null parcel: ags3.scgov.net returns Service not found and sc-pa.com 302s away.
- 2026-08-22 | swfl-permit-scanner | City of Sarasota FastTrackGov is more capable than recorded |
  The Development Applications microapp DOES have a working date filter via the ddReportedOn
  dropdown, contrary to the note saying street name was the only reliable filter, and Inquiry.aspx
  RENDERS FULLY in the Playwright Node fetch harness after about 12 seconds, contrary to the note
  saying it was qna AJAX gated and uncracked. It exposes Project Name and Tracking ID.
- 2026-08-22 | swfl-permit-scanner | Cape Coral EnerGov returns an EMPTY Description on every
  search-index record | List level triage cannot see scope. Recover it from the permit detail page,
  which is public and renders Square Feet, Valuation, Description, Project Name and Contacts.
- 2026-08-22 | swfl-permit-scanner | City of Tampa Accela CapDetail hides Job Value and description
  in anonymous HTML | Unlike Charlotte and Pasco: the ValuationCalculator grid returns No records
  found and the Description block is a spellcheck placeholder. A Site Plan Review search returned
  no grid and fell back to the form, which is indistinguishable from a genuine zero.
- 2026-08-22 | swfl-permit-scanner | Bonita Springs EnerGov host returned HTTP 500 portal-wide |
  Confirmed by plain curl outside any harness, so it was an outage and not a proxy or TLS problem.
  Prove outages outside the harness before recording them as recipe failures.
- 2026-08-22 | swfl-permit-scanner | SANDBOX: playwright version versus bundled chromium | The
  sandbox ships chromium build 1194 at /opt/pw-browsers but npm i playwright installs a newer
  playwright demanding build 1234, and the launch error is misleading. Pin to the bundled build.
- 2026-08-22 | swfl-permit-scanner | SANDBOX: the Tier 2 bootstrap POLLUTES THE REPO TREE | npm i
  playwright from the default working directory creates node_modules/, package.json and
  package-lock.json in the repo root, leaving the tree dirty and tripping the session stop hook.
  Install outside the repo. Same class of problem as the __pycache__ artifact below.
- 2026-08-22 | swfl-permit-scanner | SANDBOX: no working PDF text extractor | pypdf panics with
  the _cffi_backend Rust panic and poppler-utils will not install (404 from the security mirror).
  The 2026-08-15 run documents the workaround that did work.
- 2026-08-22 | swfl-permit-scanner | Hillsborough Accela pagination via injected __doPostBack fails
  | Legacy MS AJAX ScriptResource.axd throws on strict mode functions and the failure is SILENT.
- 2026-08-22 | swfl-permit-scanner | Manatee/Bradenton Accela: element.click() can silently no-op |
  Even with force:true, under Playwright. Bradenton server side date filtering WORKS (Manatee has
  no date fields at all) and its CapDetail is anonymous, exposing Cost of Construction, Area of
  Work, Parcel Number, Owner and Licensed Professional email.
- 2026-08-22 | swfl-permit-scanner | DATA QUALITY, two open items | Rows 29 and 30 of Municipality
  Portals both describe parcel 77459000943 (Habitat for Humanity, Justin Lane) as Buildings 7 and
  8. A cross-county name collision was found and deliberately NOT merged: Sarasota
  LDS-DEVSUB-26-000045 and Pasco 26TMP-083734 are both Dutch Bros Coffee FL3501 at different
  addresses. Deliberate exclusion with an audit trail: Manatee BLD2608-2156, a $47,281,120 county
  wastewater equalization basin, is public infrastructure and out of scope.

### swfl-news-scanner - source health

- 2026-08-22 | swfl-news-scanner | HARD BLOCKS, search-snippet recovery only | yourobserver.com and
  businessobserverfl.com refuse WebFetch AND browser-UA curl on landings and articles alike.
  Confirmed repeatedly 08-17 through 08-20. They are the two strongest Sarasota and Manatee
  sources, so a blocked run leaves those counties uncovered; say so rather than reporting a quiet
  market.
- 2026-08-22 | swfl-news-scanner | DEAD DOMAINS | lsicos.com failed DNS on every run day from
  2026-08-05 through 2026-08-15 and beyond. Run one cheap getent check per run and skip without a
  fetch attempt. suncoastsvn.com is UNREACHABLE rather than paywalled (60s WebFetch timeout, 45s
  browser-UA curl timeout, zero bytes) and it is the gold standard Tier 3 feed for Manatee,
  Sarasota and Charlotte.
- 2026-08-22 | swfl-news-scanner | fox4now.com is SUPERSEDED, not broken | It 301s to
  winknews.com. Mark the sources.md row SUPERSEDED rather than deleting it. The WINK section URLs
  that actually resolve are winknews.com/news/lee, /news/collier and /news/charlotte; the
  /category/news/local-news/ path on file 404s, and /news/business/ 404s too. nbc-2.com now
  redirects to gulfcoastnewsnow.com, and nbc-2.com itself is refused at tool level.
- 2026-08-22 | swfl-news-scanner | TownNews/BLOX titles rate limit on burst | gulfshorebusiness.com,
  naplespress.com, yoursun.com and winknews.com all run BLOX. Space requests to the same domain
  across the run rather than batching section landings. A single 429 is not a block: it clears on
  retry later in the same run. Yoursun rate limits SECTION and search indexes while ARTICLE URLs
  fetch normally, so reach Yoursun by search first then fetch the article; a 2026-08-21 run found
  the section indexes serving cleanly again, confirming it is intermittent.
- 2026-08-22 | swfl-news-scanner | Reliable BLOX extraction pattern | Split the listing HTML on
  <article, then read the article_<uuid>.html href, the <time datetime> value and the aria-label
  headline from each block.
- 2026-08-22 | swfl-news-scanner | yoursun.com is NOT blocked | It fetched cleanly on every section
  tried using curl -sSL with a desktop Chrome user agent and an Accept-Language header, superseding
  the 2026-08-05 note. Its Venice section carries a weekly Planning Commission recap by Bob Mudge
  bundling every approval from one hearing into a single article: the highest yield single item for
  the Friday rotation.
- 2026-08-22 | swfl-news-scanner | Working substitutes found for blocked sources |
  sarasotamagazine.com covers Sarasota city and county development in full (it carried the Benderson
  1660 Ringling approval with vote count, square footages and principal name). tbbwmag.com covers
  Sarasota county CRE despite the Tampa name. pulseofmanatee.com is a working dated Manatee outlet
  with a fetchable /archive index.
- 2026-08-22 | swfl-news-scanner | MANATEE IS THE WEAKEST COVERED COUNTY | Worse than the Charlotte
  gap logged 2026-08-05. On a dedicated Manatee deep dive every certified Manatee source failed or
  was silent. Treat a quiet Manatee as a coverage failure until proven otherwise.
- 2026-08-22 | swfl-news-scanner | Tier 3 broker press has gone dormant | Lee and Associates
  Naples-Ft. Myers has published no monthly roundup since May 2026 (posted Jun 1), three cycles
  missed. SVN Suncoast has posted only research since 2026-06-12. Ian Black is client-side rendered
  with recoverable dates stopping at 2026-07-30. Downgrade the tier rather than re-querying it.
- 2026-08-22 | swfl-news-scanner | The 48 hour region-wide skim LEAKS qualifying items | Two named
  projects absent from the table were found outside the window and inserted as flagged gap fills.
  The window is a floor, not a guarantee.
- 2026-08-22 | swfl-news-scanner | A LAND PURCHASE PRICE IS NOT A PROJECT COST | The Fort Myers
  Costco story states $55 million for 55 acres and nothing about construction value, so that figure
  belongs in "Project Cost ($)" with "Est. Cost" left null. Do not promote an acquisition price
  into an estimated construction cost.
- 2026-08-22 | swfl-news-scanner | CAR CONDO CROSS FEED signal | Venice approved Suncoast Executive
  Storage LLC, a 26 UNIT facility measured in UNITS rather than square feet. Unit-count framing is
  the signature of deeded large-bay executive garage product rather than conventional self storage.
- 2026-08-22 | swfl-news-scanner | Article URLs are stored inconsistently | Some historical rows keep
  the www. prefix that scripts/url_normalize.py strips, so dedup on URL can miss. Rows written since
  2026-08-17 are canonicalized.
- 2026-08-22 | all routines | execute_sql returns ONLY the last statement's result | A dedup check
  batched with a second query looked like zero matches and caused a real duplicate insert. Run every
  verification as its own call. Also: importing scripts/url_normalize.py writes
  scripts/__pycache__/*.pyc into the repo and dirties the tree.
- 2026-08-22 | swfl-news-scanner | Mid-run cloud suspension pattern | The Friday 2026-08-14
  SWFL-FRI-SARASOTA-S run wrote run_started at 06:33 UTC then produced zero portal_result rows, zero
  run_summary and zero inserts. A run_started with no run_summary is a suspended run, not a clean
  one, and the report must flag it rather than read the silence as no news.

### cre-report-writer - report construction

- 2026-08-22 | cre-report-writer | The first-appearance identity key CANNOT match across the two
  source tables, and produced three false NEW readings in one run | The portal branch keys on parcel
  when one exists while the news branch cannot. FIXED 2026-08-19: after the CTE, run one ILIKE sweep
  against BOTH tables restricted to created_at <= window_start, matching on distinctive project
  tokens. Keep that sweep.
- 2026-08-22 | cre-report-writer | Name drift defeats the exact-match identity key repeatedly | Same
  project under drifted names: Icemann / Premier Sports Campus North; One Particular Harbor rebranded
  from Silver Sands Beach Resort Redevelopment; 1899 Fruitville as three differently worded rows.
  Exact name plus city is not sufficient; the ILIKE token sweep above is what catches these.
- 2026-08-22 | cre-report-writer | Section 3 PROJECT UPDATES is blind to in-place UPDATEs | The high
  water mark filters on created_at, so a progression written onto an existing row (Midtown at Bonita
  gained four Phase 2 permits) never moves that row into the window and is silently dropped. The
  window needs an updated_at arm or an explicit progression sweep. STILL OPEN.
- 2026-08-22 | cre-report-writer | The 7 day CONTEXT window is too short for the identity check |
  Murdock Square, created 2026-07-30, fell outside the 7 day lookback from a 2026-08-12 report and
  read as new. Restrict the identity sweep by created_at <= window_start with NO lower bound.
- 2026-08-22 | cre-report-writer | Bare numeric ids are AMBIGUOUS across the two tables | Both start
  at 1 and number independently, so a run log citing "existing row id X" nearly caused a
  misattribution twice. Always qualify an id with its table.
- 2026-08-22 | cre-report-writer | NEW PROJECTS counts go LUMPY after a scanner backfill | Charlotte
  contributed 3 rows one morning only because the permit scanner discovered the Accela 101 row cap
  and backfilled. A spike after a backfill is not market activity and must not be reported as one.
- 2026-08-22 | cre-report-writer | Section 5 NEW DEVELOPERS is inflated by tenant pad shells | 6 of
  19 first-appearance names in one run were single purpose owner LLCs behind national tenant pads.
  Filter or label them; they are not developers in any useful sense.
- 2026-08-22 | cre-report-writer | The Est. Cost ingest contract took nine days to actually land |
  Declared 2026-08-08, ignored by every row created 08-09 through 08-16, prose-parsing transition
  expired 08-15, and confirmed working 2026-08-17 (7 of 9 permit rows, 3 of 5 news rows). A contract
  is not in force until the writing routines are verified to honor it.
- 2026-08-22 | cre-report-writer | The Calusa Monday lane needs a recipient-quality tiebreak | Four
  candidates tied at Medium relevance, and strict Est. Cost descending would have spent all three
  drafts before reaching the only candidate with a verifiable published email. On the lane's first
  run all six ranked candidates were skipped for lack of a verified email within the lookup budget.
- 2026-08-22 | cre-report-writer | Report INSERT construction, three separate failures | A single
  large INSERT with long text containing apostrophes failed with a syntax error near RETURNING; an
  18 column INSERT with a 23 KB dollar quoted markdown literal was rejected with "INSERT has more
  target columns than expressions" even though the counts matched; and splitting a base64 blob at a
  raw character count broke decode() because the split was not a multiple of 4. WORKING METHOD: send
  the canonical markdown ONCE in a dollar quoted CTE and derive every section column from it with
  substring(md from '### N. TITLE(.*?)### N+1. TITLE'). Split base64 at len//2//4*4.
- 2026-08-22 | cre-report-writer | A portal_result log line can disagree with the row it describes |
  A log claiming three stage progressions did not match the Progression annotations embedded in
  those records. Trust the row, not the log line about the row.
- 2026-08-22 | cre-report-writer | Section 8 lists learning rows from the SWFL routines only | It
  closes with a count of the car condo learnings belonging to the SCK morning digest. That division
  is deliberate; do not merge the two.

### outlook drips

- 2026-08-22 | outlook-unit-owner-drip | CAMPAIGN Step 2 SQL referenced columns that do not exist |
  "Ground Breaking" and "Proj. Delivery" live in "01 - Projects", not "06 - Pre-Sales". The query
  now joins "01 - Projects" for groundbreaking, delivery, unit count and flood zone. A related note:
  an illustrative product sentence in the skill ("20 to 21 foot ceilings, Category 5 concrete") did
  not match live data (18 foot plus clear heights, Block construction), which is exactly why the
  2026-08-17 spec forbids copying illustrative figures forward.
- 2026-08-22 | outlook-unit-owner-drip | The campaign-bounce blind spot RECURRED and is still open |
  KICKBACK Step 1 keeps only NDR addresses that exist in 04d with Send Status='drafted', so with 04d
  empty a real BMV-Owner-1 hard bounce is silently discarded. First logged 2026-08-15, recurred
  2026-08-17. STILL OPEN: campaign sends need their own bounce path independent of the 04d queue.
- 2026-08-22 | outlook-unit-owner-drip | "02 - Units" duplicate "Unit #" defect, cost quantified |
  Five rows per unit for Hideout Storage Park (Phase I) units 1 through 7, each with a different
  size and PSF. On 2026-08-18 this hit 11 of 50 recipients, 22 percent of that morning's batch, who
  therefore received no unit value at all. Fold of the 2026-08-17 entry already in this file; the
  handling rule stands and the upstream fix is still owed.
- 2026-08-22 | outlook-unit-owner-drip | A project name ending in a PERIOD breaks its platform URL |
  "Naples Motor Condos - Naples Blvd." 404s at the host with a 9 byte body and the SPA never boots;
  %2E is normalized back to the dot. Those owners cannot be sent a working unit link at all.
  Related and important: CURL ALONE CANNOT VALIDATE a storagecondoking.com project link, because the
  site is a client-rendered SPA that returns the same 200 shell for valid and invalid names and only
  renders "Project Not Found" in the browser. A status code check proves nothing; render it.
- 2026-08-22 | outlook-unit-owner-drip | Fortified Storage Center CRM rows carry NO "Unit #" at all |
  All 7 recipients drafted had Unit # null, so Block 1 variants a and b cannot resolve, and its
  submarket "Vero Beach; Sebastian" has a null psf_growth_5yr_ann_pct, so variant c cannot resolve
  either. Those drafts ship with no personalized sentence, which the spec allows and the run report
  must state.
- 2026-08-22 | outlook drips | PROMPT VERSUS SKILL DIVERGENCE, twice in two days | The scheduled
  prompt said to ALWAYS run CAMPAIGN mode while the skill says CAMPAIGN runs only when DRAFT drafted
  nothing, and the prompt still demanded a gate on both PDF links after the report PDF had been
  removed from the gate on 2026-08-16. THE SKILL OF RECORD ON MAIN WINS. When a scheduled prompt
  contradicts it, follow the skill and say so in the run report; a stale prompt is not an
  instruction.
