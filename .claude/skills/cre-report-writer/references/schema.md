# "Development Scanner - Report Summary" - Schema and Source Reads

Connection: "Supabase - Storage Condo King" MCP, project llwyvgkqhendgzsgngqh, schema public. Named columns; quote identifiers (spaces). Multi-line text uses real line breaks. Do not write id or created_at.

## Source reads (Step 1)
```sql
-- PRIMARY window: high water mark - everything created since the last report row.
-- window_start = coalesce(max(created_at) from "Development Scanner - Report Summary", now() - interval '26 hours')
SELECT * FROM "Development Scanner - Municipality Portals"
WHERE created_at > (SELECT coalesce(max(created_at), now() - interval '26 hours') FROM "Development Scanner - Report Summary")
ORDER BY "Posting Date" DESC NULLS LAST;
SELECT * FROM "Development Scanner - News Scanner"
WHERE created_at > (SELECT coalesce(max(created_at), now() - interval '26 hours') FROM "Development Scanner - Report Summary")
ORDER BY "Article Date" DESC NULLS LAST;

-- CONTEXT window: last 7 days (progressions, first-appearance)
SELECT * FROM "Development Scanner - Municipality Portals"
WHERE "Posting Date" >= CURRENT_DATE - 7 OR created_at >= now() - interval '7 days';
SELECT * FROM "Development Scanner - News Scanner"
WHERE "Article Date" >= CURRENT_DATE - 7 OR created_at >= now() - interval '7 days';
```

## First-appearance check (New Developers)
```sql
SELECT MIN("Posting Date"), MIN(created_at) FROM "Development Scanner - Municipality Portals"
WHERE "Developer / Sponsor / Key Principal" ILIKE '%<name>%';
SELECT MIN("Article Date"), MIN(created_at) FROM "Development Scanner - News Scanner"
WHERE "Developer / Sponsor" ILIKE '%<name>%';
```

## Output columns (INSERT exactly one row)
| Column | Value |
|---|---|
| "Summary Date" | CURRENT_DATE |
| "Period Start" | CURRENT_DATE - 1 |
| "Period End" | CURRENT_DATE |
| "Projects Reviewed" | integer, permit rows in the 26h window |
| "Articles Reviewed" | integer, news rows in the 26h window |
| "New Projects Count" | integer, items in the NEW PROJECTS section |
| "Executive Summary" | text (§2.1) |
| "New Projects" | text, preserve line breaks (§2.2) |
| "Top Opportunities" | text, the FINANCING LENS section (§2.3) |
| "New Developers Identified" | text (§2.4) |
| "Stage Progressions" | text (§2.5) |
| "Project Updates" | text, preserve line breaks (PROJECT UPDATES section, per references/report-structure.md) |
| "Rotation Audit" | text (ROTATION AND COVERAGE AUDIT section, per references/report-structure.md) |
| "Updates Count" | integer, items in the PROJECT UPDATES section |
| "Data Quality Notes" | text (§2.6) |
| "Report Markdown" | text, the FULL report as markdown (canonical saved artifact) |
| "Delivery Status" | set AFTER the email: 'sent' or 'failed: <reason>' |

## Confirm the write
```sql
SELECT id, "Summary Date", "New Projects Count", "Delivery Status"
FROM "Development Scanner - Report Summary" ORDER BY id DESC LIMIT 1;
```
