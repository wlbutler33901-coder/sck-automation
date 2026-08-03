# Daily Rotation - Municipality Cluster by Day

The scanner runs daily and scans ONE cluster per ACTIVE track per day. Every track completes a
full sweep of its region once per week. Determine today's weekday, scan that day's row on every
track where the row's Status is ACTIVE, and log the cluster id per references/run-logging.md.

The cycle is Sunday to Saturday so the last clusters land just before the weekly report and
every cluster falls inside the report's lookback window.

Portal URLs and platforms: Track A lives in references/sources.md (certified, additive only).
Track B lives in references/sources-tampa.md, including per portal certification status.

## Track A - Southwest Florida

Counties: Lee, Charlotte, Collier, Sarasota, Manatee.

| Day | Cluster ID | Status | Jurisdictions (scan these portals today) |
|---|---|---|---|
| Sunday | SWFL-SUN-LEE-UNINC | ACTIVE | Lee County DCD; Village of Estero |
| Monday | SWFL-MON-LEE-CITIES | ACTIVE | City of Cape Coral; City of Bonita Springs; City of Fort Myers |
| Tuesday | SWFL-TUE-COLLIER | ACTIVE | Collier County; City of Naples |
| Wednesday | SWFL-WED-CHARLOTTE | ACTIVE | Charlotte County; City of Punta Gorda |
| Thursday | SWFL-THU-SARASOTA-N | ACTIVE | Sarasota County; City of Sarasota |
| Friday | SWFL-FRI-SARASOTA-S | ACTIVE | City of North Port; City of Venice |
| Saturday | SWFL-SAT-MANATEE | ACTIVE | Manatee County; City of Bradenton; City of Palmetto |

## Track B - Tampa MSA

Counties: Hillsborough, Pinellas, Pasco, Hernando. All clusters start PENDING and flip to
ACTIVE per cluster when every portal in the cluster has a certification status other than
UNTESTED in references/sources-tampa.md. While a cluster is PENDING, skip it and log one
coverage_gap row per references/run-logging.md so the report states plainly what is not yet
covered. Never improvise Tampa portals from memory or from a web search.

| Day | Cluster ID | Status | Jurisdictions (scan these portals today) |
|---|---|---|---|
| Sunday | TPA-SUN-HILLS-UNINC | PENDING | Hillsborough County (Unincorporated) |
| Monday | TPA-MON-TAMPA | PENDING | City of Tampa |
| Tuesday | TPA-TUE-PINELLAS-N | PENDING | Pinellas County (Unincorporated, Oldsmar, Kenneth City); City of Clearwater; City of Dunedin; City of Largo; City of Safety Harbor; City of Tarpon Springs |
| Wednesday | TPA-WED-PINELLAS-S | PENDING | City of St. Petersburg; City of Pinellas Park; City of Gulfport; City of Seminole; City of Treasure Island; City of Madeira Beach; Towns of Redington Beach and North Redington Beach; Town of Redington Shores; Town of Indian Shores |
| Thursday | TPA-THU-PASCO | PENDING | Pasco County (Unincorporated); City of Dade City (serves San Antonio and St. Leo); City of Port Richey; City of Zephyrhills; City of New Port Richey |
| Friday | TPA-FRI-HERNANDO | PENDING | Hernando County (Unincorporated, Weeki Wachee); City of Brooksville |
| Saturday | TPA-SAT-HILLS-CITIES | PENDING | City of Plant City; City of Temple Terrace |

Hillsborough is deliberately split across three days (unincorporated Sunday, Tampa city Monday,
small cities Saturday): the county portal and the Tampa city portal will be the two highest
volume portals in the entire system and each anchors its own day, matching the Track A pattern.

## Rules that make the rotation auditable

1. ALWAYS log the cluster id. Write a run_started row naming today's cluster ids (all tracks)
   before the first portal, and a run_summary row naming them again at the end. Without this the
   report cannot tell which cluster ran and the rotation cannot be audited. This was the single
   largest blind spot in the first six weeks of the scanner.
2. ZERO IS A RESULT. A portal that returns no qualifying permits still gets its own
   portal_result row with count 0 and the access tier used. Silence must never be the way a
   scanned portal and a skipped portal look the same. Venice has produced zero records since
   certification and nobody can currently say which of the two it is.
3. NEVER scan two clusters from the same track on one night, and never repeat yesterday's
   cluster to fill time. If a cluster failed, log it and let the next weekly pass recover it;
   the 14 day per portal lookback exists precisely so one missed night self heals.
4. IF A TRACK OR CLUSTER IS SKIPPED for any reason (browser unavailable, time budget exhausted,
   cluster pending), log a coverage_gap row naming the track, the cluster id, and the reason.
5. TIME BUDGET is per track. Roughly 15 minutes per portal; high volume portals page newest
   first and stop at the budget, logging how far they got. Finish Track A completely and write
   its run_summary before starting Track B, so a mid run suspension leaves a complete record of
   what finished.
6. FIRST RUN on any newly ACTIVE portal uses the standard 90 day first ever lookback, then the
   normal 14 days.
7. THE NEWS SCANNER mirrors the Track A county of the day so permits and press for one county
   land in the same morning report. It stays on Track A only until Tampa press sources are
   added and certified; that gap is a known open item.

## Adding a track

A new metro becomes a track, never an extra jurisdiction bolted onto an existing cluster.
Populate its seven cluster rows here, create a per track sources file on the
references/sources-tampa.md pattern (keeps sources.md untouched), certify each portal with a
real dated pull before flipping its cluster to ACTIVE, and record every new platform recipe as a
dated additive entry at the end of references/platform-playbook.md.
