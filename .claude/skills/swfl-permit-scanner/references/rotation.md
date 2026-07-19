# Daily Rotation - Municipality Cluster by Day

This scanner runs daily and scans **one cluster per day**, rotating so the full SWFL region
(Lee, Charlotte, Collier, Sarasota, Manatee) is covered once per week before the Saturday
5:00 AM report. The cycle is Sunday→Saturday so the last clusters land just before the report,
and every cluster falls inside the report's 10-day lookback. Determine today's weekday and
scan that row only.

| Day | Cluster | Jurisdictions (scan these portals today) |
|---|---|---|
| **Sunday** | Lee County (unincorporated) | Lee County DCD; Village of Estero |
| **Monday** | Lee County cities | City of Cape Coral; City of Bonita Springs; City of Fort Myers |
| **Tuesday** | Collier County | Collier County; City of Naples |
| **Wednesday** | Charlotte County | Charlotte County; City of Punta Gorda |
| **Thursday** | Sarasota County (north) | Sarasota County; City of Sarasota |
| **Friday** | Sarasota County (south) | City of North Port; City of Venice |
| **Saturday** | Manatee County | Manatee County; City of Bradenton; City of Palmetto |

Notes:
- Each high-volume jurisdiction (Lee County, Cape Coral, Collier County, Sarasota County,
  Manatee County) anchors its own day.
- The news scanner uses the same county-of-the-day so permits and press for one county land on
  the same morning - tighter same-site cross-referencing.
- The 14-day per-portal lookback (§1) means a single missed daily run is recovered on the next
  cycle and still captured by the report's 10-day window.
- This is a fixed weekly cycle, not a state-tracked queue - no rotation table to maintain.
