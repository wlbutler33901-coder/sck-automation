# Track B Sources - Tampa MSA Municipality Portals

Portal inventory and certification ledger for Track B (Hillsborough, Pinellas, Pasco, Hernando).
This file is the Track B counterpart of references/sources.md, kept separate so the certified
Track A file is never touched. The Status column here is what flips Track B clusters to ACTIVE
in references/rotation.md.

Status vocabulary:
- UNTESTED: nobody has attempted this portal yet.
- CERTIFIED-LOCAL: a local session confirmed the platform, ran a dated commercial search, and
  recorded example permit numbers. The first cloud rotation confirms it under the egress proxy.
- CERTIFIED: confirmed working in a cloud run.
- BLOCKED-SUBSTITUTE: portal unusable for dated search; the named substitute covers it.
- PARKED: unusable and low value; reason recorded, revisit quarterly.

A cluster flips PENDING to ACTIVE in rotation.md when none of its portals is UNTESTED. BLOCKED
and PARKED are valid classifications; that is exactly how Track A handles Naples, Estero,
Punta Gorda and Palmetto.

## Platform expectations carried over from the Track A certification sweep

- Accela ACA: certified pattern, Tier 2 headless browser through the Node fetch TLS harness in
  references/platform-playbook.md. Expect the 5 Accela portals below to certify fastest.
- Tyler EnerGov (tylerhost.net): certified Tier 1 API pattern. Needs tyler-tenanturl,
  tyler-tenantid and tyler-tenantname headers, SearchModule 1, client side date windowing.
- Click2Gov (aspgov.com): the Punta Gorda precedent is lookup only with no date search. Expect
  the same; attempt anyway, some Click2Gov builds expose a date issued search. St. Petersburg
  is the one portal on this platform where a blocked result is not acceptable without first
  exhausting Tier 3 published permit report PDFs; flag to Will if both fail.
- BS&A (bsaonline.com): the Palmetto precedent is anti-bot connection resets. Park early on
  reset errors; substitute press plus agendas. Both BS&A towns below are low volume.
- New platforms with no recipe yet: Tyler Portico, MaintStar, iWorQ, Citizenserve, MGO Connect,
  SmartGov, CommunityCore, CivicGov. Certify from scratch; append every cracked recipe as a
  dated entry at the END of references/platform-playbook.md, never editing existing content.

## Portal inventory (26 portals, 27 plus jurisdictions; some portals are multi tenant)

### Hillsborough County

| # | Jurisdiction | Platform | URL | Expected tier | Status | Notes |
|---|---|---|---|---|---|---|
| 1 | Hillsborough County (Unincorporated) | Accela ACA | https://aca-prod.accela.com/hcfl/Default.aspx | 2 browser | CERTIFIED | 2026-08-03 cloud. Std Accela recipe, type "Commercial New Construction and Additions", no login gate. Ex: HC-BLD-26-0086823 (08/02/2026); HC-BLD-26-0086785 (07/30/2026); 26TMP-080778 (07/30/2026). |
| 2 | City of Tampa | Accela ACA | https://aca-prod.accela.com/tampa/Default.aspx | 2 browser | CERTIFIED | 2026-08-03 cloud. Type "Commercial New Construction and Additions", no login gate. Ex: BLD-26-0527034 (07/31/2026); BLD-26-0526903 (07/27/2026); BLD-26-0526818 (07/23/2026). |
| 3 | City of Plant City | MaintStar | https://h8.maintstar.co/plantcity/portal/ | lookup only | BLOCKED-SUBSTITUTE | 2026-08-03. Record/Search XHR has no date field; empty query returns []. Lookup only, cannot enumerate a window. Ex docs: PB-2020-17 (2026-07-08); BOA-2026-03 (2026-06-23). Substitute: Hillsborough County Accela (#1) + press. Recipe in playbook. |
| 4 | City of Temple Terrace | Click2Gov | https://temp-egov.aspgov.com/Click2GovBP/index.html | blocked | BLOCKED-SUBSTITUTE | 2026-08-03. Click2GovBP selectpermit.html = Application#/Address/Parcel/Name only, no date search (Punta Gorda precedent). Substitute: Tier-4 Hillsborough press + city commission agendas. |

### Pinellas County

| # | Jurisdiction | Platform | URL | Expected tier | Status | Notes |
|---|---|---|---|---|---|---|
| 5 | Pinellas County (Unincorporated, Oldsmar, Kenneth City) | Accela ACA | https://aca-prod.accela.com/pinellas/Default.aspx | 2 browser | CERTIFIED | 2026-08-03 cloud. Type "Commercial New Construction", low volume, no login gate. Ex: BC-NEW-26-00035 (07/29/2026, Clearwater). QUIRK: grid column order differs (record# in 3rd cell) - key off the BC-* pattern, not column index. |
| 6 | City of St. Petersburg | Click2Gov | https://stpe-egov.aspgov.com/Click2GovBP/index.html | blocked | BLOCKED-SUBSTITUTE | 2026-08-03. Click2Gov lookup-only, no date search; Tier-3 exhausted (ArcGIS Geohub 113 svcs no issued-permits layer; Socrata none; city site only an annual aggregate Utilization Report PDF). Substitute: Tier-4 press substitution with a coverage_gap flag (same treatment as Estero and Naples on Track A). A direct feed remains wanted. |
| 7 | City of Clearwater | Accela ACA | https://aca-prod.accela.com/CLEARWATER/Default.aspx | 2 browser | CERTIFIED | 2026-08-03 cloud. No commercial/residential split - generic "Building - Construction Permit" only, ~100-row date-desc cap; scan descriptions for CRE. No login gate. Ex: BCP2026-080016 (08/03/2026); BCP2026-080004 (08/01/2026). |
| 8 | City of Largo | Tyler EnerGov (via city info page) | https://cityoflargofl-energovweb.tylerhost.net/apps/selfservice | 1 API | CERTIFIED | 2026-08-03 cloud. largo.com/building_services/permits.php links to this Tyler EnerGov portal (known Tier-1 API). Ex: OFP-26-0051 (08/03/2026); MECH-26-000780 (07/31/2026); ROOF-26-000530 (07/31/2026). |
| 9 | City of Dunedin | Tyler EnerGov | https://cityofdunedinfl-energovweb.tylerhost.net/apps/selfservice | 1 API | CERTIFIED | 2026-08-03 cloud. URL corrected: host is energovweb (the on-file "energoweb" DNS-fails). API /apps/selfservice/api/energov/search/search; tenantname=DunedinFLProd, tenantid=1, tyler-tenanturl=Home. Ex: MECH-26-00574 (Commercial HVAC, 07/31/2026); BLDR-26-00265 (07/31/2026); ELEC-26-00287 (07/31/2026). |
| 10 | City of Pinellas Park | Tyler Portico | https://pinellasparkfl.tylerportico.com | blocked | BLOCKED-SUBSTITUTE | 2026-08-03. Portico launcher hosts only General-Billing CSS/Payments/311/HR - NO Community-Development permit app (moduleconfig empty). Substitute: Pinellas Park commission agendas + press. Recipe in playbook. |
| 11 | City of Tarpon Springs | Click2Gov | https://tarp-egov.aspgov.com/Click2GovBP/index.html | blocked | BLOCKED-SUBSTITUTE | 2026-08-03. Click2GovBP lookup-only, no date search. Substitute: Tier-4 press + city agendas (Pinellas County Accela does not issue Tarpon Springs permits). |
| 12 | City of Safety Harbor | BS&A | https://bsaonline.com/?uid=2774 | blocked | BLOCKED-SUBSTITUTE | 2026-08-03. Palmetto precedent confirmed: BuildingDepartmentRecordSearch behind a Robot/Captcha interstitial (honeypot fields), drops uid session; harness = ERR_CONNECTION_RESET (anti-bot). Substitute: Pinellas County + Safety Harbor agendas/press. |
| 13 | City of Gulfport | BS&A | https://bsaonline.com/?uid=3078 | blocked | BLOCKED-SUBSTITUTE | 2026-08-03. Same anti-bot block as #12. Substitute: Pinellas County + Gulfport agendas/press. |
| 14 | City of Seminole | Citizenserve | https://www4.citizenserve.com/Portal/PortalController?Action=showHomePage&ctzPagePrefix=Portal_&installationID=441 | blocked | BLOCKED-SUBSTITUTE | 2026-08-03. Permit search reachable (Datefrom/to fields) but gated by reCAPTCHA v3 enterprise; replay = HTTP 401 Access Denied. Substitute: Seminole council agendas + press. Recipe in playbook. |
| 15 | City of Treasure Island | MGO Connect | https://mgoconnect.org | blocked | BLOCKED-SUBSTITUTE | 2026-08-03. api.mgoconnect.org search endpoints auth-gated (405 unauth); no anonymous public permit route. Substitute: Treasure Island commission agendas + press. |
| 16 | City of Madeira Beach | MGO Connect | https://mgoconnect.org | blocked | BLOCKED-SUBSTITUTE | 2026-08-03. Same platform/blocker as #15 (single multi-tenant login-gated app). Substitute: Madeira Beach commission agendas + press. |
| 17 | Towns of Redington Beach and North Redington Beach | SmartGov | https://twn-redingtonbeach-fl.smartgovcommunity.com/ | 2 browser | CERTIFIED | 2026-08-03 cloud. Public /Public/PermitSearch works (recipe in playbook). 0 permits in window (tiny town); newest RB-BLDG-25-0913 (Commercial Fence, 11/10/2025). |
| 18 | Town of Redington Shores | SmartGov | https://twn-redingtonshores-fl.smartgovcommunity.com/ | 2 browser | CERTIFIED | 2026-08-03 cloud. 392 rows StatusDate DESC. In-window commercial: BLDG-25-1087 (Commercial Remodel, 7/29/2026); MIL1-26-0015 (Commercial Milestone, 7/27/2026); PLBG-26-0024 (Commercial Plumbing, 7/23/2026). |
| 19 | Town of Indian Shores | CommunityCore | https://app.communitycore.com/ | blocked | BLOCKED-SUBSTITUTE | 2026-08-03. Login wall (root -> /app/account/login), no guest search, swagger paths empty, contractor apply/inspection only. Substitute: town agendas/press (Tier 4). Pinellas County does not issue for Indian Shores. |

### Pasco County

| # | Jurisdiction | Platform | URL | Expected tier | Status | Notes |
|---|---|---|---|---|---|---|
| 20 | Pasco County (Unincorporated) | Accela ACA | https://aca-prod.accela.com/pasco/default.aspx | 2 browser | CERTIFIED | 2026-08-03 cloud. Type "Commercial New" (also "Commercial Multifamily"), richest of the Tampa Accela feeds, no login gate. Ex: COMNEW-2026-000550 (Discount Tire, 07/31/2026); 26TMP-074473 (Fifth Third Bank, Wesley Chapel, 07/31/2026); COMNEW-2026-000549 (Pasadena Ridge Amenity, 07/31/2026). 26TMP-*=draft, COMNEW-*=issued. |
| 21 | City of Dade City (serves San Antonio and St. Leo) | iWorQ | https://dadecity.portal.iworq.net/portalhome/dadecity | blocked | BLOCKED-SUBSTITUTE | 2026-08-03. iWorQ tenant exists but public portal NOT published ("Portal home not set up"; permit routes 404). Substitute: Pasco County Accela (#20) covers Dade City/San Antonio/St. Leo + press. |
| 22 | City of Port Richey | iWorQ | https://portrichey.portal.iworq.net/PORTRICHEY/permits/601 | 2 browser | CERTIFIED | 2026-08-03 cloud. GET /PORTRICHEY/permits/601 server-renders the full permit table newest-first, no login/captcha (recipe in playbook; date-range form is reCAPTCHA-gated, skip it). Ex: 3299 (07/30/2026); 3298 (07/29/2026); 3297 (07/29/2026) - residential/trade in window, scan for CRE. |
| 23 | City of Zephyrhills | Tyler EnerGov | https://zephyrhillsfl-energovweb.tylerhost.net/apps/selfservice | 1 API | CERTIFIED | 2026-08-03 cloud. API /apps/selfservice/api/energov/search/search; tenantname=EnerGovProd, tyler-tenanturl=EnerGovProd, tenantid=1. Ex: BGC-012002-2026 (commercial reroof, 07/29/2026); BGC-011900-2026 (commercial monument sign, 07/28/2026); TMPS-012008-2026 (07/31/2026). |
| 24 | City of New Port Richey | Tyler EnerGov | https://cityofnewportricheyfl-energovweb.tylerhost.net/apps/selfservice | 1 API | CERTIFIED | 2026-08-03 cloud. API /apps/selfservice/api/energov/search/search; tenantname=EnerGovProd, tyler-tenanturl=Home, tenantid=1. Ex: BLDC-26-06-0152 (Morgan's Sports Bar buildout, 07/30/2026); MECH-26-07-0666 (commercial chillers, 07/31/2026); BLDC-26-07-0159 (Commercial Remodel, 07/29/2026). |

### Hernando County

| # | Jurisdiction | Platform | URL | Expected tier | Status | Notes |
|---|---|---|---|---|---|---|
| 25 | Hernando County (Unincorporated, Weeki Wachee) | Tyler EnerGov (permit feed); property appraiser (parcel enrichment) | permits: https://hernandocountyfl-energovweb.tylerhost.net/apps/selfservice ; appraiser: https://pvweb.hernandopa-fl.us/ | 1 API | CERTIFIED | 2026-08-03 cloud. REAL permit feed located = Tyler EnerGov (the on-file appraiser URL is parcel-only; keep for enrichment). API tyler-tenanturl=hernandocountyflprod, tenantid=1, tenantname=hernandocountyflprod. Ex: BLDC-000202-2026 (medical office buildout, Spring Hill, issued 07/02/2026); BLDC-000205-2026 (Weeki Wachee, 07/11/2026); BLDC-000199-2026 (tenant build-out in shell). Tenant quirks + backoff in playbook. |
| 26 | City of Brooksville | CivicGov | https://www.civicgov4.com/fl_brooksville/portal/ | blocked | BLOCKED-SUBSTITUTE | 2026-08-03. CivicPlus Community Dev 4.0 Public Records Search = single location/parcel input only, no date search (Punta Gorda class). Substitute: Hernando County EnerGov (#25) + press + city commission agendas. |

## Certification procedure

Run per portal, time boxed at 5 minutes, in cluster order (Sunday cluster first):

1. Load the URL and confirm the platform matches the table; correct the Platform cell if not.
2. Attempt a date ranged search for commercial or building permits over the last 14 days, using
   the existing platform recipe where one exists.
3. On success, record 1 to 3 example permit numbers with dates in the Notes cell as evidence,
   set Status to CERTIFIED-LOCAL (or CERTIFIED if run from the cloud environment).
4. On failure, record the exact blocker (login, CAPTCHA, no date search, anti-bot reset,
   TLS, dead URL) in Notes, set Status to BLOCKED-SUBSTITUTE with the named substitute, or
   PARKED with a reason. County portals substitute for their blocked small cities where the
   county issues the permits; otherwise the substitute is Tier 3 report PDFs, then Tier 4 press
   with a coverage gap flag.
5. Every NEW platform recipe or blocker goes to the END of references/platform-playbook.md as a
   dated additive entry. Never edit or reorder existing playbook content.
6. When a cluster has no UNTESTED portal left, flip that cluster to ACTIVE in
   references/rotation.md.
7. The certification pass is READ ONLY against Supabase: never write portal findings to the
   database from a certification session. The first scheduled cloud rotation performs the first
   real writes with the standard 90 day first run lookback.
8. Local certification is provisional. The cloud egress proxy resets chromium TLS (see
   LEARNINGS.md); the first cloud run upgrades CERTIFIED-LOCAL to CERTIFIED or logs the cloud
   specific failure to LEARNINGS.md.

## Known open item

Track B covers permits only. The news scanner has no Tampa press sources yet; its deep dive
stays on Track A until a Tampa source list is provided and certified. The daily report's
rotation audit names this gap while it exists.
