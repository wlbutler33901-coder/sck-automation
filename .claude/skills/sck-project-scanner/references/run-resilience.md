# Run Resilience (v3.2)

Why this exists: on 2026-08-03 the cloud container suspended mid run with five parallel research
agents open. The scanner logged zero rows and exited. From the outside that night was
indistinguishable from a night with nothing to find. These rules make a partial run legible.

## 1. Write run_started before any search

The very first database action of the run, before the rotation query results are used and before
any web search:

```sql
INSERT INTO "Scan Activity Log" (run_type, change_type, region, target_table, detail)
VALUES ('scan', 'run_started', $REGION_LIST, '01 - Project - New',
        'Scan started. Regions scheduled: ' || $REGION_LIST || '. Submarkets planned: ' || $N || '.');
```

If the run dies after this point, the morning brief can say the scan started and did not finish,
which is a completely different message from the scan not running.

## 2. Log each region the moment it completes

Do not hold results until the end. After every region finishes its submarket sweep:

```sql
INSERT INTO "Scan Activity Log" (run_type, change_type, region, target_table, detail)
VALUES ('scan', 'region_complete', $REGION, '01 - Project - New',
        'Region complete. Searches run: ' || $S || '. Candidates inserted: ' || $I ||
        '. Near matches flagged: ' || $F || '. Sources blocked: ' || $B || '.');
```

A `new_candidate` row is still written per insert, as before, at the moment of the insert.

## 3. Cap concurrency at 2

Never run more than TWO research agents or parallel search tasks at once. Five was the
configuration that suspended the container. If a region needs more breadth, run it in sequential
batches of two, not in one wide fan out. Latency is cheap; a silent night is not.

## 4. run_type is the literal string 'scan'

Hard-code it. The values `nightly_scan`, `project_scan`, `project_scanner` and `scanner` have all
appeared in production. The morning digest reads
`run_type IN ('scan','enrichment')`, so every drifted row was invisible to it and the candidates
in those rows were never surfaced to Will. Never compose run_type from a variable, a date, or a
skill name. The only permitted values anywhere in this repo are listed in LEARNINGS.md.

## 5. run_summary still closes the run

Unchanged from Step 6, and it now also reports how many regions reached `region_complete` out of
how many were scheduled. If those two numbers differ, say so in the detail string.

## 6. Self check before exiting

Re-query the log for tonight and confirm a `run_started` row exists, a `region_complete` row
exists for every scheduled region, and a `run_summary` row exists. If any are missing, write them
before exiting. If the run cannot write to Supabase at all, append the failure to LEARNINGS.md
and exit non-silently.
