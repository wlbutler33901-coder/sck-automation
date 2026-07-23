# Platform Playbook

This reference provides extraction hints by software platform. Use this when scanning portals listed in `references/sources.md`.

## Accela ACA (aca-prod.accela.com/...)
**Used by:** Charlotte County, Manatee County, City of Bradenton, Sarasota County, City of North Port
**Extraction Hints:**
- Use Search Permits/Records.
- Set record type to Building/Commercial, date range to the lookback window.
- Results list → open each record for parcel, valuation, applicant, contacts, status history.
- Each ACA tenant lives at its own path (e.g., `/MANATEE`, `/BRADENTON`, `/SARASOTACO`, `/NORTHPORT`, `/BOCC` for Charlotte). The UI is identical across tenants; only the agency catalog of record types differs.

## Tyler EnerGov (*energov*, *tylerhost*)
**Used by:** Cape Coral and Bonita Springs
**Extraction Hints:**
- Use the public Search (Permits) or Report module.
- Filter by permit type = Commercial and date.
- Detail page holds valuation and contacts.

## Click2Gov (*Click2GovBP*)
**Used by:** Punta Gorda
**Extraction Hints:**
- Permit search by date/type.
- Limited fields - expect to enrich more via web.

## Harris CityView (cityview2.iharriscomputer.com)
**Used by:** Naples
**Extraction Hints:**
- Locate the public permit/application search.
- Filter to commercial + recent.
- If no commercial filter, scan descriptions for keywords: warehouse, distribution, retail, shopping, office, medical, hotel, multifamily, apartments, mixed-use, self-storage, industrial, flex, build-to-suit, shell, site development, PUD, rezoning.

## Periodic-report jurisdictions
**Used by:** Lee County, Fort Myers, Collier County
**Extraction Hints:**
- Download the newest monthly/statistical report.
- Parse the commercial/new-construction section.
- Permits there may need the jurisdiction's main portal for detail.

## Static page / forms
**Used by:** Village of Estero
**Extraction Hints:**
- No searchable database - check the page for posted permit applications or contact lists.
- Supplement via county-level data and web search for Estero-area projects.

## BS&A Online (bsaonline.com)
**Used by:** City of Palmetto (Manatee County)
**Extraction Hints:**
- BS&A is a property-records-first platform. From bsaonline.com, select the jurisdiction (City of Palmetto) from the community/municipality picker.
- Core data is assessing/tax: parcel number, owner, assessed values, sales history. This is excellent for confirming the `Parcel / Folio Number` and resolving owner identity, but it is not a permit feed.
- If the Palmetto deployment exposes a Building Department / permit search, use it filtered to commercial + recent. Many BS&A deployments expose limited or no permit data.
- If no permit module is exposed: use BS&A to confirm parcel/owner, and catch Palmetto-area commercial projects via the Manatee County Accela portal (`/MANATEE`) and web research (city commission agendas, trade press).

## FastTrackGov / Mitchell Humphrey (ftgportal.*)
**Used by:** City of Sarasota
**Extraction Hints:**
- Entry point: `Common/ApplicationLinks.aspx` → the Building and Engineering Permit search (`Permits/Search.aspx`).
- Search by location/street name, owner name, business name, or contractor. Enter the street NAME ONLY - no number, no directional prefix/suffix, no street type (per the portal's own instructions).
- No native commercial-only filter. Scan result descriptions for the commercial keyword list (see Harris CityView entry below).
- Open each result for permit/application number, address, valuation, status, applicant/contractor. Pre-1997 residential records may be missing - irrelevant to CRE.

## eTRAKiT / TRAKiT (trakit.*, *eTRAKiT*)
**Used by:** City of Venice
**Extraction Hints:**
- Use the public Permit search. Search by date range, permit type, parcel, or address.
- Set permit type to commercial/building where the dropdown allows; otherwise pull the date range and scan descriptions for the commercial keyword list (see Harris CityView entry below).
- Open each permit for valuation, applicant, status, and parcel.

## General Fallback
If a portal blocks automation or has no usable search, record the jurisdiction + date attempted in the log and rely on web search (trade press, county agendas) to catch major projects there.


## TIER 1 API RECIPES (JSON behind the SPA - no browser needed)

### Tyler EnerGov Self Service (Bonita Springs, Cape Coral)
The SPA is a shell over a JSON search API. Pattern (tenant path varies: /apps/selfservice or /EnerGov_Prod/SelfService):

POST https://<host>/<tenant>/api/energov/search/search
CERTIFIED 2026-07-20 against both tenants. Proven specifics (the earlier guessed shape was wrong):
- REQUIRED headers (a bare POST 500s without them): Content-Type: application/json; tyler-tenant-culture: en-US;
  tyler-tenanturl: <tenant>; tenantid: <n>; tenantname: <tenant>; plus Origin/Referer of the portal.
- Permit search is SearchModule=1, FilterModule=2 (NOT 2/1). Capture the VERBATIM search body once from the SPA
  (select "Permit" in select#SearchModule, click Search, copy the /search/search POST body) and reuse it as the template -
  a hand-trimmed payload 500s; the server wants the full multi-criteria object.
- The server IGNORES PermitCriteria.IssueDateFrom/To and ApplyDateFrom/To. Do NOT rely on server-side date filtering.
  Instead SortBy a VALID key (one of: relevance | PermitNumber.keyword | ProjectName.keyword | MainAddress | IssueDate | FinalDate),
  SortAscending:false, PageSize:50, paginate, and WINDOW CLIENT-SIDE on IssueDate/ApplyDate (drop garbage dates > today; Cape Coral has a record dated 2610).
- Response: Result.EntityResults[] -> CaseNumber, CaseType, CaseWorkclass, ProjectName, Description, Address/AddressDisplay, MainParcel, ApplyDate, IssueDate, CaseStatus.
Certified tenants:
- Bonita Springs (Lee): host egweb1.cityofbonitasprings.org, tenant path /energov/selfservice, tenant=BonitaSpringsFLProd, tenantid=1.
- Cape Coral (Lee): host energovweb.capecoral.gov, tenant path /EnerGovProd/SelfService, tenant=capecoralflprod, tenantid=1.

DISCOVERY (once per portal, then save the exact endpoint + working payload HERE): open the portal search page in the headless browser with network logging on, run one search, and copy the XHR request the page makes (URL, headers, JSON body). That captured request is the permanent Tier 1 recipe; subsequent nights never need the browser for this portal. If the endpoint 401/500s, include the same tenant headers the SPA sent.

### Accela ACA (Charlotte, Manatee, Bradenton, Sarasota County, North Port)
No usable public JSON API on these tenants; ViewState-heavy forms. TIER 2 (headless browser) required: Advanced Search -> set date range -> record type Commercial/Building -> paginate -> open record detail. Selectors are stable per tenant; save working selector notes here after the first successful browser run.

## TIER 2 BOOTSTRAP (headless browser in the CC cloud sandbox)
At run start, before the portal loop:
1. node --version && npx playwright --version  (if present, skip install)
2. npm i playwright && npx playwright install --with-deps chromium
   (if --with-deps fails for lack of sudo: npx playwright install chromium, then retry; if launch still fails on missing libs, log "browser unavailable" and fall to Tier 3/4 for browser-only portals.)
3. Driver pattern: launch chromium headless -> goto portal search URL -> fill date filters -> submit -> wait for results selector -> extract rows -> paginate -> open qualifying record detail pages. Screenshot on unexpected states for the run log.
Time-box the whole install to ~3 minutes; it repeats nightly if the environment is cold - acceptable cost.

PROXY / TLS WORKAROUND (CERTIFIED 2026-07-20, required in the CC cloud sandbox): the egress proxy re-terminates TLS
and RESETS chromium's own destination handshake (net::ERR_CONNECTION_RESET on every site, even example.com), while
curl and Node fetch through the same proxy succeed. Disabling ECH/post-quantum/TLS1.3 in chromium does NOT fix it.
The working pattern is to launch chromium but fulfill EVERY request via Node fetch (request interception), so the
browser never does its own destination TLS:
  - export NODE_USE_ENV_PROXY=1 and NODE_EXTRA_CA_CERTS=/root/.ccr/ca-bundle.crt
  - launch chromium ({ args:['--no-sandbox'] }); context { ignoreHTTPSErrors:true }
  - ctx.route('**', route => Node-fetch the request (forward headers incl. cookie; strip accept-encoding & content-length
    on the way back) and route.fulfill with the result). Cookies/session flow through the forwarded headers.
Pure API pulls (EnerGov Tier 1) and PDF/XLSX downloads need no browser - just Node fetch/curl through the proxy.

## 403 / bot-blocked news sources (news scanner shared note)
On HTTP 403 (e.g. Your Observer): retry once with a standard browser user agent; then try the site RSS feed; then use indexed excerpts and MARK the record lower-confidence with byline/address unconfirmed (as done for News id 109). Never bypass a paywall.

## PORTAL CERTIFICATION (one-time full sweep, all 5 counties, run 2026-07-20)
Every portal in references/sources.md was worked through the ACCESS TIERS and proven with a real 14-day pull
(window 2026-07-06..2026-07-20). "Proven tier" = the tier that actually returned data this run. CERTIFIED = usable now;
BLOCKED/LIMITED = needs Will's input (see the notes). All browser work used the Node-fetch harness above.

| Portal | Platform | Proven tier | Endpoint / selector notes | Date certified | Issues |
|---|---|---|---|---|---|
| Cape Coral | Tyler EnerGov | Tier 1 API (CERTIFIED) | POST /EnerGovProd/SelfService/api/energov/search/search; tenant headers tenant=capecoralflprod id=1; SearchModule=1; window client-side | 2026-07-20 | 0 qualifying CRE in window (all residential/trade). One record has a garbage IssueDate (2610) - filter <= today. |
| Bonita Springs | Tyler EnerGov | Tier 1 API (CERTIFIED) | POST /energov/selfservice/api/energov/search/search; tenant=BonitaSpringsFLProd id=1 | 2026-07-20 | Found 3 shell permits at Midtown at Bonita -> deduped as UPDATE to existing row (id 19), added real parcel + permit #s. |
| Lee County DCD | SharePoint report app | Tier 3 PDF (CERTIFIED) | Newest = ULC2026JunBPC.PDF (Jun 2026, 115 commercial permits). Index /dcd/reports 401s; enumerate via anonymous _api/web/lists + getfolderbyserverrelativeurl(...)/files, then direct PDF. | 2026-07-20 | UI + _api/web/folders return 401 (SharePoint auth); list-enumeration path works. 0 new after dedupe. No July report yet. |
| City of Fort Myers | CivicPlus DocumentCenter | Tier 3 PDF (CERTIFIED) | Newest = "202606 New Projects Report" (Jun 2026, DocumentCenter/View/26211). Index /2377/2026-Statistical-Reports. | 2026-07-20 | 1 new qualifying (The Forum 8-unit townhouse, id 31). No July report yet. |
| Collier County | OpenCities - monthly XLSX | Tier 3 XLSX (CERTIFIED) | Newest = 2026-6-issued.xlsx (5,508 rows) + 2026-6-applied.xlsx. | 2026-07-20 | sources.md index URL had a double-dash typo (404) - corrected in sources.md. 11 written (ids 20-30). Excluded 7 utility-district plants. |
| City of Sarasota | FastTrackGov (Mitchell Humphrey) | Tier 1 API (CERTIFIED) | GET Permits/Search.aspx?microapp=c (grab __VIEWSTATE/__EVENTVALIDATION + cookie) -> POST with FTGSearchControl$ddReportedOn=D30 & btnSearch -> GET Permits/SearchResults.aspx?...&page=N (20/page). Detail Inquiry.aspx?source=1&id=<guid>&microapp=c. Building-permit list columns are only Application ID/Type/Subtype/Date/Status/Address - no description or valuation, and detail page is 'qna' AJAX-gated (not cracked) - list-level triage only, mostly residential trade permits. SEPARATE search worth running: microapp=da (Development Applications, not building permits) at the same host/pattern - POST with FTGSearchControl$txtStreetName=<street name only, no number/suffix> & btnSearch is the only reliable filter (no working date range on "da"); this is where city-level rezonings/site plans (e.g. major redevelopment projects) actually live. | 2026-07-20 (c), 2026-07-23 (da) | "c" search: date granularity = "Last 30 days" only, 118-420+ records depending on status filter; 0 CRE identifiable at list level. "da" search: street-name search for "Ringling" surfaced 5 Development Application case numbers at 1660 Ringling Blvd (Benderson Class A office redevelopment of the former Sarasota County admin building) - case list only shows ID/date/status/address, so confirm project scope via press before writing a record. |
| Charlotte County | Accela ACA | Tier 2 browser (CERTIFIED) | Cap/CapHome.aspx?module=Building; date fields #...txtGSStartDate/_txtGSEndDate set via JS .value (NOT p.fill -> stale ViewState -> Error.aspx); submit #...btnNewSearch; results table[id*=dgvPermitList]; pager "Next >". | 2026-07-20 | ~100-row date-desc cap; no server-side type filter. 0 qualifying (trade subs). |
| Manatee County | Accela ACA | Tier 2 browser (CERTIFIED) | Same page; NO date fields - filter by Record Type; ddlGSPermitType="Commercial". Detail a[href*=CapDetail]. | 2026-07-20 | CapDetail exposes no valuation/SF/parcel publicly. 60 commercial TIs, 0 qualifying. Tier-3 lead: Reports menu -> "Commercial Projects (CSV)" (untested). |
| City of Bradenton | Accela ACA | Tier 2 browser (CERTIFIED) | Standard General Search w/ date + Record Type dropdown. | 2026-07-20 | "Commercial New"=0, "Commercial Multi-Family"=0; 50 commercial alterations. 0 qualifying. |
| City of North Port | Accela ACA | Tier 2 browser (CERTIFIED) | General Search + type dropdown "Commercial New"/"Multi-Family". | 2026-07-20 | 2 qualifying written (ids 32-33: Sunshine Rheumatology medical office; ~16-unit townhome dev). CapDetail needs auth -> numeric fields omitted. |
| City of Venice | eTRAKiT / TRAKiT (CentralSquare) | Tier 2 browser (CERTIFIED) | Search/permit.aspx; SearchBy #cplMain_ddSearchBy, Operator #cplMain_ddSearchOper, Value #cplMain_txtSearchString, Search #ctl00_cplMain_btnSearch; grid #ctl00_cplMain_rgSearchRslts_ctl00 (Permit#, Type, SubType, Parcel, Address, RECORDID); pager btnPageNext. XHR = ASP.NET AJAX partial postback (WebForms, no JSON API). | 2026-07-20 | No date filter; RECORDID encodes YYMMDD - use for the cut. Window = BLD26-04556..04930 (338 rows). Detail not viewable anonymously (needs login). 0 qualifying (church rebuild excluded as institutional). |
| Sarasota County | Accela ACA | Tier 2 browser (CERTIFIED, Planning module only) | module=Building still 302s to /SARASOTACO/Login.aspx (anonymous disabled, not usable). module=Planning IS anonymously searchable, confirmed working: Cap/CapHome.aspx?module=Planning&TabName=Planning has the same General Search fields as Building (txtGSStartDate/txtGSEndDate set via JS .value, ddlGSPermitType select, #ctl00_PlaceHolderMain_btnNewSearch). Run ddlGSPermitType filtered separately per relevant type (unfiltered search returns 100+ noise rows incl. test/junk entries) - values: "Planning/Rezoning/NA/NA", "Planning/LDS/Plan Amendment/NA", "Planning/LDS/Development Submittal/NA", "Planning/LDS/Plat/NA", "Planning/General Plan/Amendment/NA", "Planning/Conditional Use/NA/NA". Results table rows carry Date/PermitNumber/Type/Description/ProjectName/Address inline in the list view (no detail-page click needed) - richer list-level data than the Building module. | 2026-07-23 | 2 qualifying written this run (ids 63-64): Juniper Landscaping Office/Field Ops facility (Development Submittal, Englewood) directly from list view; Benderson 1660 Ringling Blvd office redevelopment found via City of Sarasota "da" microapp cross-reference + press (see City of Sarasota row). |
| City of Naples | Harris CityView | BLOCKED - CAPTCHA | Landing 200 at /CityofNaplesFlorida/Permit/Locator; permit search sits behind a BotDetect image CAPTCHA ("Naples, Florida Captcha - CityView Portal"). No anonymous JSON API. | 2026-07-20 | NEEDS WILL: manual CAPTCHA solve / paid solver / or use the Collier County monthly report as the substitute feed for Naples-area CRE. |
| City of Punta Gorda | Click2Gov (CentralSquare) | LIMITED - lookup only | selectpermit.html; searchMethod = Permit# | Address | Parcel only. CSRF OWASP_CSRFTOKEN. | 2026-07-20 | No date field anywhere - cannot enumerate "last 14 days". Not a discovery source; only answers a known permit#/address/parcel. Catch Punta Gorda CRE via Charlotte County + web. |
| City of Palmetto | BS&A Online | LIMITED - needs follow-up | Building Department Record Search exists: /SiteSearch/BuildingDepartmentRecordSearch?uid=2403 -> AdvancedRecordSearch. Form is JS/Telerik with obfuscated field names + per-session GUID. | 2026-07-20 | Corrects the old "no permit feed" note - a feed EXISTS. Harness hit ERR_CONNECTION_RESET (multi-redirect/anti-bot). NEEDS a dedicated Telerik token-POST build, or keep catching Palmetto via Manatee County Accela + web. |
| Village of Estero | Static page / CGA portal | LIMITED - no feed | estero-fl.gov posts PDF application forms + links a CGA "fl-estero.gov-easy.com" portal (login-oriented). | 2026-07-20 | Origin serves a broken/incomplete TLS cert chain (tunneled clients fail verify); read via browser if needed. No public date-searchable permit feed. Catch Estero CRE via Lee County + web. |

Sweep tally: 11 CERTIFIED (2 EnerGov API, 1 FastTrackGov API, 3 report-PDF/XLSX, 4 Accela browser, 1 eTRAKiT browser),
5 BLOCKED/LIMITED (Sarasota Co login, Naples CAPTCHA, Punta Gorda no-date-feed, Palmetto Telerik follow-up, Estero no-feed).
Records written this run: 14 new (Collier ids 20-30, Fort Myers id 31, North Port ids 32-33) + 1 dedupe update (Bonita id 19).
