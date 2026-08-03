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
| 1 | Hillsborough County (Unincorporated) | Accela ACA | https://aca-prod.accela.com/hcfl/Default.aspx | 2 browser | UNTESTED | Highest volume portal in the system. |
| 2 | City of Tampa | Accela ACA | https://aca-prod.accela.com/tampa/Default.aspx | 2 browser | UNTESTED | Second highest volume; anchors its own day. |
| 3 | City of Plant City | MaintStar | https://h8.maintstar.co/plantcity/portal/ | unknown | UNTESTED | New platform. |
| 4 | City of Temple Terrace | Click2Gov | https://temp-egov.aspgov.com/Click2GovBP/index.html | 2 or blocked | UNTESTED | Punta Gorda precedent says lookup only. |

### Pinellas County

| # | Jurisdiction | Platform | URL | Expected tier | Status | Notes |
|---|---|---|---|---|---|---|
| 5 | Pinellas County (Unincorporated, Oldsmar, Kenneth City) | Accela ACA | https://aca-prod.accela.com/pinellas/Default.aspx | 2 browser | UNTESTED | County portal covers three jurisdictions. |
| 6 | City of St. Petersburg | Click2Gov | https://stpe-egov.aspgov.com/Click2GovBP/index.html | 2 or 3 | UNTESTED | High value. If date search fails, hunt published permit report PDFs before accepting blocked. |
| 7 | City of Clearwater | Accela ACA | https://aca-prod.accela.com/CLEARWATER/Default.aspx | 2 browser | UNTESTED | |
| 8 | City of Largo | City web page | https://www.largo.com/building_services/permits.php | 3 | UNTESTED | URL is an information page, not a portal; classify what it links to at certification. |
| 9 | City of Dunedin | Tyler EnerGov | https://cityofdunedinfl-energoweb.tylerhost.net | 1 API | UNTESTED | URL spelling energoweb recorded as provided; confirm host at certification. |
| 10 | City of Pinellas Park | Tyler Portico | https://pinellasparkfl.tylerportico.com | unknown | UNTESTED | New platform; check for an EnerGov style JSON API behind it. |
| 11 | City of Tarpon Springs | Click2Gov | https://tarp-egov.aspgov.com/Click2GovBP/index.html | 2 or blocked | UNTESTED | |
| 12 | City of Safety Harbor | BS&A | https://bsaonline.com/?uid=2774 | blocked likely | UNTESTED | Palmetto precedent; park early on resets. |
| 13 | City of Gulfport | BS&A | https://bsaonline.com/?uid=3078 | blocked likely | UNTESTED | Same. |
| 14 | City of Seminole | Citizenserve | https://www4.citizenserve.com/Portal/PortalController?Action=showHomePage&ctzPagePrefix=Portal_&installationID=441 | unknown | UNTESTED | New platform. |
| 15 | City of Treasure Island | MGO Connect | https://mgoconnect.org | unknown | UNTESTED | Multi tenant; select the jurisdiction in app. |
| 16 | City of Madeira Beach | MGO Connect | https://mgoconnect.org | unknown | UNTESTED | Same portal, second tenant. |
| 17 | Towns of Redington Beach and North Redington Beach | SmartGov | https://twn-redingtonbeach-fl.smartgovcommunity.com/ | unknown | UNTESTED | One portal, two towns. |
| 18 | Town of Redington Shores | SmartGov | https://twn-redingtonshores-fl.smartgovcommunity.com/ | unknown | UNTESTED | |
| 19 | Town of Indian Shores | CommunityCore | https://app.communitycore.com/ | unknown | UNTESTED | Multi tenant; select the jurisdiction in app. |

### Pasco County

| # | Jurisdiction | Platform | URL | Expected tier | Status | Notes |
|---|---|---|---|---|---|---|
| 20 | Pasco County (Unincorporated) | Accela ACA | https://aca-prod.accela.com/pasco/default.aspx | 2 browser | UNTESTED | |
| 21 | City of Dade City (serves San Antonio and St. Leo) | iWorQ | https://dadecity.portal.iworq.net/portalhome/dadecity | unknown | UNTESTED | New platform. |
| 22 | City of Port Richey | iWorQ | https://portrichey.portal.iworq.net/portalhome/portrichey | unknown | UNTESTED | |
| 23 | City of Zephyrhills | Tyler EnerGov | https://zephyrhillsfl-energovweb.tylerhost.net | 1 API | UNTESTED | Existing EnerGov recipe should apply. |
| 24 | City of New Port Richey | Tyler EnerGov | https://cityofnewportricheyfl-energovweb.tylerhost.net | 1 API | UNTESTED | Same. |

### Hernando County

| # | Jurisdiction | Platform | URL | Expected tier | Status | Notes |
|---|---|---|---|---|---|---|
| 25 | Hernando County (Unincorporated, Weeki Wachee) | Property appraiser lookup | https://pvweb.hernandopa-fl.us/ | see note | UNTESTED | The URL on file is the Hernando property appraiser, a parcel lookup, NOT a date searchable permit feed. Keep it for parcel enrichment. At certification, locate the county's actual public permit search from the county site and record it here as an additive note; if none is public, classify Tier 3 or 4. |
| 26 | City of Brooksville | CivicGov | https://www.civicgov4.com/fl_brooksville/portal/ | unknown | UNTESTED | New platform. |

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
