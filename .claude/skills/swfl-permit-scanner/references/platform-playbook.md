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
| City of Sarasota | FastTrackGov (Mitchell Humphrey) | Tier 1 API (CERTIFIED) | GET Permits/Search.aspx?microapp=c (grab __VIEWSTATE/__EVENTVALIDATION + cookie) -> POST with FTGSearchControl$ddReportedOn=D30 & btnSearch -> GET Permits/SearchResults.aspx?...&page=N (20/page). Detail Inquiry.aspx?source=1&id=<guid>&microapp=c. | 2026-07-20 | Date granularity = "Last 30 days" only. 118 records pulled; 0 CRE at list level. Valuation/SF/desc behind a 'qna' AJAX postback (not cracked). |
| Charlotte County | Accela ACA | Tier 2 browser (CERTIFIED) | Cap/CapHome.aspx?module=Building; date fields #...txtGSStartDate/_txtGSEndDate set via JS .value (NOT p.fill -> stale ViewState -> Error.aspx); submit #...btnNewSearch; results table[id*=dgvPermitList]; pager "Next >". | 2026-07-20 | ~100-row date-desc cap; no server-side type filter. 0 qualifying (trade subs). |
| Manatee County | Accela ACA | Tier 2 browser (CERTIFIED) | Same page; NO date fields - filter by Record Type; ddlGSPermitType="Commercial". Detail a[href*=CapDetail]. | 2026-07-20 | CapDetail exposes no valuation/SF/parcel publicly. 60 commercial TIs, 0 qualifying. Tier-3 lead: Reports menu -> "Commercial Projects (CSV)" (untested). |
| City of Bradenton | Accela ACA | Tier 2 browser (CERTIFIED) | Standard General Search w/ date + Record Type dropdown. | 2026-07-20 | "Commercial New"=0, "Commercial Multi-Family"=0; 50 commercial alterations. 0 qualifying. |
| City of North Port | Accela ACA | Tier 2 browser (CERTIFIED) | General Search + type dropdown "Commercial New"/"Multi-Family". | 2026-07-20 | 2 qualifying written (ids 32-33: Sunshine Rheumatology medical office; ~16-unit townhome dev). CapDetail needs auth -> numeric fields omitted. |
| City of Venice | eTRAKiT / TRAKiT (CentralSquare) | Tier 2 browser (CERTIFIED) | Search/permit.aspx; SearchBy #cplMain_ddSearchBy, Operator #cplMain_ddSearchOper, Value #cplMain_txtSearchString, Search #ctl00_cplMain_btnSearch; grid #ctl00_cplMain_rgSearchRslts_ctl00 (Permit#, Type, SubType, Parcel, Address, RECORDID); pager btnPageNext. XHR = ASP.NET AJAX partial postback (WebForms, no JSON API). | 2026-07-20 | No date filter; RECORDID encodes YYMMDD - use for the cut. Window = BLD26-04556..04930 (338 rows). Detail not viewable anonymously (needs login). 0 qualifying (church rebuild excluded as institutional). |
| Sarasota County | Accela ACA | Tier 2 browser via Planning module (CERTIFIED) | Building search is login-gated (module=Building 302 -> /SARASOTACO/Login.aspx), but module=Planning is anonymously searchable and IS the rezoning/site-plan feed. Recipe: goto Cap/CapHome.aspx?module=Planning&TabName=Planning; select record type in #...ddlGSPermitType (CRE types: Rezone / Special Exception, General/Approved Plan Amendment, Development Agreement/CDD, DOCC/DRI, Final Plat, NOPC, Development Submittal); set #...txtGSStartDate/_txtGSEndDate via JS .value AND the paired _ext_ClientState (calendar extender); click #ctl00_PlaceHolderMain_btnNewSearch (Playwright .click - a raw anchor .click() does NOT fire the postback); results table[id*=dgvPermitList] cols Date/Record#/Type/Description/Project/Status; pager "Next >". Search one record type at a time (the all-types search returns no grid). | 2026-07-20 | CERTIFIED via Planning; wrote 5 entitlements (ids 34-38: Davis LWR Corporate Park, Midtown affordable-housing MF, Meridian Distribution industrial, Banyan Cove 58-townhome plat, a 0.39ac commercial rezoning). Detail pages need login -> parcel/valuation omitted. Per-type search is timing-sensitive (allow ~8s after submit); Building-permit data still needs ACA creds. |
| City of Naples | Harris CityView | BLOCKED - CAPTCHA | Landing 200 at /CityofNaplesFlorida/Permit/Locator; permit search sits behind a BotDetect image CAPTCHA ("Naples, Florida Captcha - CityView Portal"). No anonymous JSON API. | 2026-07-20 | NEEDS WILL: manual CAPTCHA solve / paid solver / or use the Collier County monthly report as the substitute feed for Naples-area CRE. |
| City of Punta Gorda | Click2Gov (CentralSquare) | LIMITED - lookup only | selectpermit.html; searchMethod = Permit# | Address | Parcel only. CSRF OWASP_CSRFTOKEN. | 2026-07-20 | No date field anywhere - cannot enumerate "last 14 days". Not a discovery source; only answers a known permit#/address/parcel. Catch Punta Gorda CRE via Charlotte County + web. |
| City of Palmetto | BS&A Online | LIMITED - needs follow-up | Building Department Record Search exists: /SiteSearch/BuildingDepartmentRecordSearch?uid=2403 -> AdvancedRecordSearch. Form is JS/Telerik with obfuscated field names + per-session GUID. | 2026-07-20 | Corrects the old "no permit feed" note - a feed EXISTS. Harness hit ERR_CONNECTION_RESET (multi-redirect/anti-bot). NEEDS a dedicated Telerik token-POST build, or keep catching Palmetto via Manatee County Accela + web. |
| Village of Estero | Static page / CGA portal | LIMITED - no feed | estero-fl.gov posts PDF application forms + links a CGA "fl-estero.gov-easy.com" portal (login-oriented). | 2026-07-20 | Origin serves a broken/incomplete TLS cert chain (tunneled clients fail verify); read via browser if needed. No public date-searchable permit feed. Catch Estero CRE via Lee County + web. |

Sweep tally: 12 CERTIFIED (2 EnerGov API, 1 FastTrackGov API, 3 report-PDF/XLSX, 5 Accela browser incl. Sarasota Co via its
Planning module, 1 eTRAKiT browser), 4 BLOCKED/LIMITED (Naples CAPTCHA, Punta Gorda no-date-feed, Palmetto Telerik follow-up,
Estero no-feed). Sarasota County Building-permit search still needs ACA creds; its Planning module is certified as the rezoning/site-plan feed.
Records written across the sweep + Planning follow-up: 19 new (ids 20-38) + 1 dedupe update (Bonita id 19).

# ============================================================================
# TAMPA TRACK B - NEW PLATFORM RECIPES AND BLOCKERS (appended 2026-08-03 cloud pass)
# 13 of 26 portals CERTIFIED; the rest blocked/lookup-only with substitutes. Additive only - do not reorder.
# ============================================================================

## Accela ACA - Tampa MSA tenant notes (certified 2026-08-03, cloud via Node-fetch harness)
Standard recipe (date fields via JS .value + ddlGSPermitType + btnNewSearch + table[id*=dgvPermitList] + "Next >" pager)
certified against 5 Tampa tenants: /hcfl, /tampa, /pinellas, /CLEARWATER, /pasco. None login-gated. Best commercial
new-construction record types: hcfl and tampa = "Commercial New Construction and Additions"; pinellas = "Commercial New
Construction"; pasco = "Commercial New" (also "Commercial Multifamily"); clearwater = "Building - Construction Permit".
- PINELLAS tenant grid column order DIFFERS: Date | Record Type | Record Number | Status | Address (record# in 3rd cell,
  not 2nd). Key the record number off the BC-*/permit pattern, not a fixed column index.
- CLEARWATER has NO commercial/residential record-type split (only generic "Building - Construction Permit") and enforces
  the ~100-row date-desc cap; scan descriptions for CRE keywords.
- PASCO uses 26TMP-* for draft/temp records and COMNEW-YYYY-###### for issued commercial-new; expect both in a range pull.

## Tyler EnerGov - newer /apps/selfservice build (Angular app.main) - CERTIFIED 2026-08-03 (Tampa Track B)
Distinct from the older /EnerGovProd|/energov builds. tylerhost.net "-energovweb" hosts (Dunedin, Zephyrhills, New Port
Richey) serve the SPA at /apps/selfservice/ (root 403s; /EnerGovProd/SelfService 404s). Same JSON API: POST
https://<host>/apps/selfservice/api/energov/search/search with the VERBATIM full search body (reuse the captured EnerGov
body template), SearchModule=1, FilterModule=2. Server IGNORES date filters, so SortBy:"IssueDate", SortAscending:false,
PageSize:50, paginate ~8 pages, WINDOW CLIENT-SIDE on IssueDate. Response Result.EntityResults[] -> CaseNumber, CaseType,
CaseWorkclass, IssueDate, ApplyDate, Description, AddressDisplay, MainParcel, CaseStatus. Tenant headers vary per host
(capture from a /api/CommonSetting XHR on the search route):
  - Dunedin #9:         tenantid=1, tenantname=DunedinFLProd, tyler-tenanturl=Home
  - Zephyrhills #23:    tenantid=1, tenantname=EnerGovProd,   tyler-tenanturl=EnerGovProd
  - New Port Richey #24: tenantid=1, tenantname=EnerGovProd,  tyler-tenanturl=Home
Source-file host typo: Dunedin is cityofdunedinfl-energovweb.tylerhost.net (the "energoweb" spelling DNS-fails).

## Click2Gov (aspgov.com Click2GovBP) - Tampa cities confirm the Punta Gorda precedent - 2026-08-03
Temple Terrace, St. Petersburg, Tarpon Springs all serve selectpermit.html with searchMethod = 0 Application Number,
1 Address, 2 Parcel Number, 3 Name ONLY. No date-issued / date-range search on any build, so a lookback cannot be
enumerated. Treat all Click2GovBP as lookup-only (known permit#/address/parcel/name), not a discovery feed. St. Petersburg
has NO Tier-3 substitute: ArcGIS Geohub (services2.arcgis.com/9qPLjNtocjo438CJ, 113 services) has no issued-permits layer,
StPeteStat/Socrata none, city site publishes only an annual aggregate Utilization Report. St. Pete is a standalone coverage
gap (Pinellas County Accela does not cover it) - needs Will's input.

## Tyler Portico (2026-08-03, Pinellas Park #10) - Tampa Track B
Forge SPA. Enumerate hosted apps via GET <host>/portal/launcher/api/AppLauncher (JSON: label/category/uri). EnerGov Community
Self Service, when present, mounts at <host>/css/<appname>/ with API base <host>/css/<appname>/api/ (AppConfig, features,
moduleconfig/<module>); permit search would be POST .../api/energov/search/search (standard EnerGov body, SearchModule=2).
CAVEAT: a tenant may host only a General-Billing CSS (Pinellas Park case) with NO CommunityDevelopment app -> no public permit
search. Check AppLauncher first before assuming EnerGov permits exist.

## Citizenserve (2026-08-03, Seminole #14) - Tampa Track B
Permit search recipe = GET Portal/PortalController?Action=showSearchPage&type=Permit&installationID=<id> (grab uniqueID +
cookies), then POST Portal/PortalController with Action=DisplayCasesNPagging, filetype=Permit, Datefrom=MM/DD/YYYY,
to=MM/DD/YYYY, PermitType, PermitStatus, PermitNumber, uniqueID, installationID. BLOCKER: reCAPTCHA v3 enterprise on
validateAndSearch(); replay without g-recaptcha-response = HTTP 401 Access Denied; token handshake doesn't complete through
the fetch-harness proxy. Treat Citizenserve installs as captcha-blocked unless a token can be minted.

## MGO Connect / MyGovernmentOnline (2026-08-03, Treasure Island #15 + Madeira Beach #16) - Tampa Track B
Angular SPA, API host https://api.mgoconnect.org, search POST /jpv2/projectmanager/search (+ /search/row-count). ENTIRELY
auth-gated: unauth = 405/redirect to /auth/login; no anonymous public permit-search route (app routes: auth,cp,mgo,pg,reports).
Legacy www.mygovernmentonline.org 301->landing.mgoconnect.org. All MGO tenants = login-required BLOCKED; no public date search.

## BS&A Online (2026-08-03, Safety Harbor #12 + Gulfport #13) - Tampa Track B
Confirms the Palmetto anti-bot precedent under the cloud proxy. Landing ?uid=<n> returns 200 via curl, but
/SiteSearch/BuildingDepartmentRecordSearch is behind a Robot/Captcha interstitial (honeypot inputs) and loses the uid session
(redirect to MunicipalDirectory); real Chromium (harness) hits net::ERR_CONNECTION_RESET. PARK on first reset; substitute =
county + city agendas/press.

## SmartGov / Granicus (*.smartgovcommunity.com) - CERTIFIED 2026-08-03 (Tampa Track B) - Tier 2 (AJAX form POST, HTML fragment)
GET {BASE}/ -> 302 /Public/Home. Public permit search at {BASE}/Public/PermitSearch (also /Public/ApplicationSearch).
Search fires: POST {BASE}/Public/PermitSearch/SearchPage
  Headers: X-Requested-With: XMLHttpRequest; Content-Type: application/x-www-form-urlencoded
  Body: _conv=1 & query=<TOKEN> & search_listState=<JSON> & __submitFormValidator__=<token from GET page> & ILS-Ajax=Y
  search_listState = {"Filter":[{"key":"Module","op":"=","val":"Permitting"},
    {"key":"Status.ProcessState","op":"!=","val":"Cancelled"},{"key":"Status.ProcessState","op":"!=","val":"Incomplete"},
    {"key":"CaseType.PublicPortalSearchable","op":"=","val":"True"}],
    "Sort":[{"key":"StatusDate","op":"DESC"}],"Group":"None","PageNumber":N,"ActiveWorkspaceId":""}
  Response: HTML fragment; each row = PermitNumber | CaseType | "<Status>, M/D/YYYY" | Address | Owner | Contractor.
GOTCHA: query MUST be non-empty (empty query -> 0 rows, even with a StatusDate date filter). Use a broad token (a street
  name like "gulf", or leading house-number digits like "18"); results come StatusDate DESC, page via PageNumber and window
  client-side on the per-row "M/D/YYYY". Needs a session cookie + fresh __submitFormValidator__ from the GET page; drive via
  the Node-fetch harness (or curl with the token). Confirmed: Redington Shores (392 rows); Redington Beach same portal.

## CommunityCore / SAFEbuilt (app.communitycore.com) - BLOCKED (login-gated) 2026-08-03 (Tampa Track B)
Root -> /app/account/login (Angular SPA; every route serves index.html so route-guessing is useless). swagger/v1/swagger.json
returns openapi 3.0.1 with paths:{} (schemas only). /api/v1/* requires auth. No anonymous/guest permit search, no public
report export; for Indian Shores the portal is contractor apply/inspection only. Substitute = town agendas/press (Tier 4).

## iWorQ (portal.iworq.net) - CERTIFIED 2026-08-03 via City of Port Richey (Tampa Track B)
Per-tenant subdomain <tenant>.portal.iworq.net; tenant code is UPPERCASE in-path (PORTRICHEY). CERTIFIED RECIPE (no
XHR/JSON - server-side rendered HTML, no captcha, no login): GET https://<tenant>.portal.iworq.net/<TENANT>/permits/601
returns the full permit list newest-first (Permit# desc). Parse the <table>: Permit#, Date (MM/DD/YYYY), Permit Type,
Parcel Address, Parcel#, Applicant, Status. No commercial-only filter -> scan Type/desc for CRE keywords. The on-page
date-range form (searchField="Permit Date" + #startDate/#endDate) is reCAPTCHA-gated - do NOT use it; the default 601
listing is already date-desc. Route id is per-tenant (Port Richey 601 = permit list); discover from /portalhome/<tenant>
links. GOTCHA: a tenant with "Portal home not set up" (Dade City) has no published public portal -> BLOCKED; substitute the county.

## Tyler EnerGov - Hernando County tenant - CERTIFIED 2026-08-03 (Tampa Track B)
Host https://hernandocountyfl-energovweb.tylerhost.net, tenant path /apps/selfservice, tyler-tenanturl=hernandocountyflprod,
tenantid=1, tenantname=hernandocountyflprod. Same Tier-1 recipe: POST /apps/selfservice/api/energov/search/search with the
verbatim EnerGov body (SearchModule=1, FilterModule=2) + tenant headers + Content-Type: application/json. PermitsFound=7553.
TENANT QUIRKS (differ from Cape/Bonita): paging is TOP-LEVEL body.PageSize/body.PageNumber (PermitCriteria paging IGNORED);
PermitCriteria date filters and top-level SortBy return a NULL Result -> window client-side over the CaseNumber-ascending set
(BLDC-*-2026 = Commercial Building, BLDR = residential). Public API is rate-limit-flaky under rapid replay - add backoff.
Keep pvweb.hernandopa-fl.us (appraiser) for parcel enrichment only. (The source-file URL was the appraiser, NOT the permit feed.)

## MaintStar (h8.maintstar.co/<tenant>/portal/) - BLOCKED lookup-only 2026-08-03 via Plant City (Tampa Track B)
Angular SPA. Captured search XHRs (both GET): GET /<tenant>/api/Public/Record/Search?query=<term>&skip=0&take=100 ->
{data:[{id,projectNumber,number,type,status,description}], total:-1} (NO date field); GET /<tenant>/api/Public/Record/
searchattachments?query=<term>&skip=0&take=100 -> {data:[{createdDate,projectNumber,number,description,link}]} (dated, newest
first). Types via GET /<tenant>/api/v2/Portal/TypesConfig/InitialTypes. BLOCKER: query is REQUIRED (empty -> []) and
Record/Search carries no date -> cannot enumerate a lookback window; only searchattachments is dated (doc-centric). Lookup-only;
discovery from county Accela + press.

## CivicGov / CivicPlus Community Development 4.0 (civicgov4.com/<tenant>/portal/) - BLOCKED lookup-only 2026-08-03 via Brooksville
Public entry index.php?r=publicRecordsSearch/index = "Search Public Records by Location", a SINGLE location_search input
(street address OR parcel #). No date field, no record-type filter; blank/wildcard returns nothing. Same class as
Click2Gov/Punta Gorda: answers a known address/parcel only, cannot enumerate a date window. Substitute county feed + agendas + press.


# ============================================================================
# RECOVERED PORTAL RESEARCH (appended 2026-08-04 from stranded unattended-run branches).
# Additive only. These supplement, and do not replace, the certification table above.
# ============================================================================

## Lee County DCD - CurrentMonth WEEKLY PDF feed (recovered from run of 2026-07-26; branch hopeful-heisenberg-bgxo71)
BEST SOURCE for Lee County, and it supersedes the monthly report for the daily scan. Weekly reports sit at fixed,
no-auth URLs under `/dcd/rpts/Documents/CurrentMonth/<PREFIX><TYPE>Week<1-5>.PDF` - a rolling 5-week window, no
SharePoint auth needed (this avoids the 401 that the /dcd/reports UI and _api/web/folders both return) and no
monthly-report lag.
- PREFIX = sub-area: ULC=Unincorporated Lee County, VE=Village of Estero, NFM=North Fort Myers, BG=Boca Grande,
  CI=Captiva Island, LA=Lehigh Acres.
- TYPE: BPC = "Building Permits Issued - Commercial" (the one to read weekly). BPR/BPD/BPT/BPP/BPRO/BPSO/BPEO/CPR
  also exist and are lower value.
- WeekN labels are NOT calendar-week numbers, they rotate. Check each file's own "From:/To:" header and its
  TimeLastModified to find the newest 2-3.
- Discovery: GET `https://www.leegov.com/dcd/rpts/_api/web/getfolderbyserverrelativeurl('/dcd/rpts/Documents/CurrentMonth')/files`
  with `Accept: application/json;odata=verbose` lists current filenames + mtimes; then plain GET the .PDF (no headers
  needed) and parse with `pdftotext -layout` (apt: poppler-utils).
- GOTCHA: pypdf/cffi is broken in the CC cloud sandbox (missing `_cffi_backend` -> Rust panic). Use `pdftotext -layout`,
  not a Python PDF library.
- The old monthly path `/dcd/rpts/Documents/<Area>/<Year>/<Mon>/<Area><Year><Mon>BPC.PDF` (e.g. ULC2026JunBPC.PDF) still
  works as a Tier 3 fallback/backfill but lags about a week into the next month.
VILLAGE OF ESTERO IS IN THIS SAME FEED under the VE prefix: `VEBPCWeek<1-5>.PDF` = "Building Permits Issued -
Commercial - Village of Estero", same format and columns as the ULC report. Read it alongside ULC each Sunday; no
separate Estero portal is needed. The estero-fl.gov static page / CGA portal remains a dead end (no date-searchable
feed, broken TLS chain) and can be skipped now that this feed is known. Run evidence 2026-07-26: ULCBPCWeek1-3 +
VEBPCWeek1-3 over the 7/5-7/25/2026 window produced 7 new Lee County projects and 3 dedupe progressions; Estero
returned 0 qualifying commercial permits (confirmed-empty, not a scan failure).

## Charlotte County - Accela date-search failure, IP rate limit, and a county-published Tier 3 source (run of 2026-07-22; branch hopeful-heisenberg-4eed0z)
ACCELA SYMPTOM: the BOCC tenant's date-range General Search (txtGSStartDate/txtGSEndDate set both via `.value` and via
realistic Playwright keyboard typing) reliably returned "Your search returned no results" for every date window tried,
including the exact window that had returned ~100 rows two days earlier and a 7-week super-window that should have
caught it. A no-date-filter search DID return a grid (8 rows), so the search engine itself works and only date-bounded
queries failed. Immediately after, `aca-prod.accela.com` became fully unreachable (curl timeout / connection reset on
`/BOCC/...` while google.com and leegov.com stayed fine), consistent with a temporary IP-level rate limit from repeated
automated hits during troubleshooting. Retrying was stopped per the pacing guardrail.
FOLLOW-UP: on a Wednesday cluster run, try the date search fresh (no repeated hits first) before assuming it is broken
again; the "no results on any date range" symptom may not recur once the block clears. If it does recur, use the
no-date-filter search plus a client-side date scan, the same pattern used for EnerGov.
NEW TIER 3 SOURCE: `https://www.charlottecountyfl.gov/departments/community-development/major-development-projects.stml`
links a monthly "Major Projects" spotlight PDF at `/file/363/major-projects-<month>-<year>.pdf` (e.g.
`major-projects-june-2026.pdf`), independent of the Accela portal. It lists named commercial projects with address,
parcel, SF, acreage and Under Review / Under Construction / Completed status - a genuine county-published feed, not
press substitution. Check it each run before falling back to Accela or press. Run evidence: 14 records written
(10 from the Major Projects PDF, 4 Punta Gorda / Charlotte County press substitution: Duncan Road U.S. 17 PD rezoning
approved 5/26/2026, Punta Gorda Waterfront Hotel revised master plan 5/21/2026, Punta Gorda Industrial Park
(Blueprint Industrial Capital), Duffie North industrial / Airport Commerce Center).

## City of Sarasota - "da" Development Applications search, and extra Sarasota County Planning detail (run of 2026-07-23; branch hopeful-heisenberg-rnikmc)
CITY OF SARASOTA (FastTrackGov): the certified `microapp=c` building-permit search is TRIAGE ONLY - its list columns are
just Application ID / Type / Subtype / Date / Status / Address, with no description or valuation, and the detail page is
'qna' AJAX-gated (not cracked); content is mostly residential trade permits. RUN THIS SEPARATE SEARCH INSTEAD for CRE:
`microapp=da` (Development Applications, not building permits) at the same host and request pattern. POST with
`FTGSearchControl$txtStreetName=<street name only, no number or suffix>` and `btnSearch`; street name is the only
reliable filter (there is no working date range on "da"). This is where city-level rezonings and site plans actually
live. Evidence: a street-name search for "Ringling" surfaced 5 Development Application case numbers at 1660 Ringling
Blvd (Benderson Class A office redevelopment of the former Sarasota County admin building). The "da" case list shows
only ID/date/status/address, so confirm project scope via press before writing a record.
SARASOTA COUNTY PLANNING (supplements the certified Planning-module row above): filter `ddlGSPermitType` separately per
relevant type, because an unfiltered search returns 100+ noise rows including test/junk entries. Working values seen:
"Planning/Rezoning/NA/NA", "Planning/LDS/Plan Amendment/NA", "Planning/LDS/Development Submittal/NA",
"Planning/LDS/Plat/NA", "Planning/General Plan/Amendment/NA", "Planning/Conditional Use/NA/NA". Results rows carry
Date/PermitNumber/Type/Description/ProjectName/Address inline in the list view, so no detail-page click is needed -
richer list-level data than the Building module. Run evidence 2026-07-23: 2 qualifying written (Juniper Landscaping
Office/Field Ops facility, Englewood, straight from the list view; Benderson 1660 Ringling Blvd via the "da"
cross-reference plus press).
