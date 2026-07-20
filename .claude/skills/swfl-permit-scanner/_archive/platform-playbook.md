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
