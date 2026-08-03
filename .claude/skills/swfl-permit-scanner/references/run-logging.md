# SWFL Run Logging Contract

Every SWFL routine writes its own run trail to the shared "Scan Activity Log" table in the SCK
Supabase, project llwyvgkqhendgzsgngqh, via the "Supabase - Storage Condo King" MCP connector.
This is what lets the daily report audit its own coverage and lets a suspended run be told
apart from a run that found nothing.

Until this contract shipped, no SWFL routine wrote to this table at all.

## run_type (hard-coded literal, never composed)

| Routine | run_type |
|---|---|
| swfl-permit-scanner | `swfl_permit_scan` |
| swfl-news-scanner | `swfl_news_scan` |
| cre-report-writer | `swfl_report` |

These values are deliberately outside the set the SCK morning digest consumes
(`scan`, `enrichment`), so SWFL rows never leak into the car condo brief. Do not add new
run_type values without updating LEARNINGS.md and every consumer.

## Columns

The table is generic. Map SWFL concepts onto it as follows and do not invent columns.

| Column | Use |
|---|---|
| run_type | From the table above. |
| change_type | From the change_type table below. |
| region | The CLUSTER ID from references/rotation.md, for example SWFL-TUE-COLLIER. For portal level rows use the cluster id, not the county. |
| project_name | The portal or jurisdiction name for portal rows. The project name for record rows. Leave null on run level rows. |
| target_table | The table the row is about, for example "Development Scanner - Municipality Portals". |
| detail | One line of plain text. No em-dashes, no en-dashes. |
| confidence | Leave null for SWFL rows. |
| ts | Leave to the default. |
| digested_at | Never set. The SWFL report reads by ts window, it does not mark rows digested. |

## change_type values

| change_type | When | detail must contain |
|---|---|---|
| `run_started` | ONCE, before the first portal or source is touched | Track and cluster ids scheduled tonight, and the portal count planned. |
| `portal_result` | Immediately after EACH portal, including empty ones | Portal name, access tier used (api, browser, pdf, press-substitute), permits seen, qualified, inserted, updated, skipped. Count 0 is a valid and required result. |
| `portal_blocked` | A portal could not be reached or is gated | Portal name and the reason (login, CAPTCHA, TLS, timeout, anti-bot). |
| `coverage_gap` | A track or cluster was skipped entirely | Track, cluster id, and reason. |
| `run_summary` | ONCE, at the very end | Cluster ids actually completed, portals scanned, portals blocked, records inserted, records updated, and total runtime. |

## Incremental logging is mandatory

Write each row the moment the thing it describes happens. Do not buffer log rows to the end of
the run. A cloud container suspension mid run must still leave behind a `run_started` row and
one `portal_result` row per completed portal, so the next morning's report can state exactly
how far the run got. Buffering is how a suspended run produced a completely silent night.

## Reads

Last night's coverage for the report:

```sql
SELECT change_type, region AS cluster_id, project_name AS portal, detail, ts
FROM "Scan Activity Log"
WHERE run_type IN ('swfl_permit_scan','swfl_news_scan')
  AND ts >= now() - interval '26 hours'
ORDER BY ts;
```

Seven day rotation audit, which cluster ran on which night:

```sql
SELECT date(ts AT TIME ZONE 'America/New_York') AS run_date,
       region AS cluster_id,
       count(*) FILTER (WHERE change_type = 'portal_result')  AS portals_done,
       count(*) FILTER (WHERE change_type = 'portal_blocked') AS portals_blocked
FROM "Scan Activity Log"
WHERE run_type = 'swfl_permit_scan'
  AND ts >= now() - interval '8 days'
GROUP BY 1, 2
ORDER BY 1 DESC, 2;
```

Clusters that should have run in the last 7 days but left no trace at all are the
report's MISSED CLUSTERS list. Compare the result above against the seven cluster ids per
active track in references/rotation.md.
